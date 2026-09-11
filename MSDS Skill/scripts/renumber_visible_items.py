#!/usr/bin/env python3
"""Renumber surviving MSDS N.x item labels continuously after omission.

Conservative helper: scans table-cell paragraphs in document order. It only edits a
leading numeric prefix when a paragraph/run starts with ``<section>.<item>`` and the
paragraph contains a label-like colon/heading text. Section headings such as ``2.危险性概述``
are excluded because they have no second numeric component.

Use --audit-only to report gaps without modifying the file.
Always run locked-label/style audit and render QA after modification.
"""
from __future__ import annotations
import argparse, re, sys
from collections import defaultdict
from docx import Document

PREFIX = re.compile(r'^(\s*)(\d{1,2})\.(\d{1,2})(\s*)')

def iter_paragraphs(doc):
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p

def leading_run(p):
    for r in p.runs:
        if r.text and r.text.strip():
            return r
    return None

def collect(doc):
    seen=set(); out=[]
    for p in iter_paragraphs(doc):
        # merged cells can surface the same underlying paragraph more than once.
        # IMPORTANT: do not use id(p._p): python-docx wrapper lifetimes can make id() values
        # appear reused while scanning and silently skip legitimate rows. Use the lxml element
        # object itself as the stable identity key.
        key=p._p
        if key in seen: continue
        seen.add(key)
        text=''.join(r.text or '' for r in p.runs)
        m=PREFIX.match(text)
        if not m: continue
        sec=int(m.group(2)); item=int(m.group(3))
        # Label guard: numbered item must have content after prefix; H/P codes won't match.
        rest=text[m.end():].strip()
        # A measured value such as ``7.0-9.0`` is not a numbered label.  The
        # maintained structured endpoint sections retain their standard
        # endpoint numbers after source-gated omission (for example 11.7 and
        # 12.2), so continuity is checked there as ordered numbering.
        if not rest or rest[0] in '-+<>=~' or rest[0].isdigit(): continue
        out.append((p,sec,item,text))
    return out

def audit(items):
    """Audit continuity by UNIQUE visible item number within each section.

    Repeated numbers are allowed only for adjacent subrows belonging to the same main item
    (e.g. 11.1 acute toxicity: 经口/经皮/吸入). They do not increment the expected
    main-item sequence. A later return to an already-finished number is an ordering error.
    """
    by=defaultdict(list)
    for _,sec,item,text in items: by[sec].append((item,text))
    problems=[]
    for sec, vals in sorted(by.items()):
        if sec in {11, 12}:
            last = None
            closed = set()
            for item, text in vals:
                if item == last:
                    continue
                if last is not None:
                    closed.add(last)
                if item in closed:
                    problems.append(f'Section {sec}: item {sec}.{item} appears again after a later item: {text}')
                last = item
            continue
        expected=1; last=None; closed=set()
        for item,text in vals:
            if item == last:
                continue
            if last is not None:
                closed.add(last)
            if item in closed:
                problems.append(f'Section {sec}: item {sec}.{item} appears again after a later item: {text}')
                last=item
                continue
            if item != expected:
                problems.append(f'Section {sec}: expected {sec}.{expected}, found {sec}.{item}: {text}')
            expected += 1
            last=item
    return problems

def replace_prefix_in_runs(p, sec, new_item, *, prefix_width=None):
    # Modify only characters participating in the leading prefix, preserving run formatting.
    full=''.join(r.text or '' for r in p.runs)
    m=PREFIX.match(full)
    if not m: return False
    old_prefix=full[:m.end()]
    separator = m.group(4)
    if prefix_width is not None:
        separator = ' ' * max(1, prefix_width - len(f'{sec}.{new_item}'))
    new_prefix=f'{m.group(1)}{sec}.{new_item}{separator}'
    # Locate prefix across runs and replace it without rebuilding paragraph.
    remain=len(old_prefix); first=None
    for r in p.runs:
        t=r.text or ''
        if remain<=0: break
        if first is None and t:
            first=r
        take=min(len(t),remain)
        if take:
            r.text=t[take:]
            remain-=take
    if first is None: return False
    first.text=new_prefix + (first.text or '')
    return True

def renumber(doc):
    """Renumber unique visible main items; keep adjacent repeated subrows on same number."""
    items=collect(doc)
    state={}  # sec -> {last_old, new}
    changes=[]
    for p,sec,item,text in items:
        st=state.setdefault(sec, {'last_old':None,'new':0})
        if item != st['last_old']:
            st['new'] += 1
            st['last_old'] = item
        new_item=st['new']
        if item!=new_item:
            if replace_prefix_in_runs(
                p, sec, new_item, prefix_width=5 if sec == 9 else None
            ):
                changes.append((f'{sec}.{item}',f'{sec}.{new_item}',text))
    return changes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--out')
    ap.add_argument('--audit-only',action='store_true')
    args=ap.parse_args()
    doc=Document(args.input)
    if args.audit_only:
        probs=audit(collect(doc))
        if probs:
            print('\n'.join(probs)); return 2
        print('Numbering continuity audit: PASS'); return 0
    if not args.out: ap.error('--out is required unless --audit-only')
    changes=renumber(doc); doc.save(args.out)
    print(f'Renumbered {len(changes)} item(s).')
    for a,b,t in changes: print(f'{a} -> {b}: {t}')
    # reopen and audit
    outdoc=Document(args.out); probs=audit(collect(outdoc))
    if probs:
        print('\n'.join(probs),file=sys.stderr); return 2
    print('Post-renumber audit: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
