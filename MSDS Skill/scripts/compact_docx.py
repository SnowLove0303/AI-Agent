#!/usr/bin/env python3
"""Conservative content-aware compactor.
Does NOT delete template items. It only removes obvious whitespace artifacts from non-bold value areas.
Always audit + render after use.
"""
import argparse, re
from copy import deepcopy
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

def unique_cells(row):
    out=[]; seen=set()
    for c in row.cells:
        k=id(c._tc)
        if k not in seen: seen.add(k); out.append(c)
    return out

def has_locked_label(p): return any(r.bold and r.text.strip() for r in p.runs)
def remove_p(p):
    el=p._element; parent=el.getparent()
    if parent is not None: parent.remove(el)

def find_exemplar(d,text):
    for t in d.tables:
        for row in t.rows:
            for c in unique_cells(row):
                for p in c.paragraphs:
                    for r in p.runs:
                        if text in r.text and not r.bold and r._r.rPr is not None:
                            return deepcopy(r._r.rPr)
    return None

def normalize_run_text(r):
    if r.bold: return
    s=r.text.replace('\t',' ')
    s=re.sub(r'[ \u3000]{2,}',' ',s)
    s=re.sub(r'[ \u3000]+$','',s)
    r.text=s

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); ap.add_argument('--body-exemplar',default='水性羟基丙烯酸乳液'); a=ap.parse_args()
    d=Document(a.input); exemplar=find_exemplar(d,a.body_exemplar)
    for t in d.tables:
        for row in t.rows:
            for c in unique_cells(row):
                # Remove trailing empty paragraphs only when the cell has real content and the empty paragraph is not a label anchor.
                while len(c.paragraphs)>1 and c.paragraphs[-1].text.strip()=='' and not has_locked_label(c.paragraphs[-1]):
                    remove_p(c.paragraphs[-1])
                for p in c.paragraphs:
                    for r in p.runs: normalize_run_text(r)
                    # remove empty non-bold runs, never bold/label runs
                    for r in list(p.runs):
                        if not r.bold and r.text=='' and len(p.runs)>1:
                            try: p._p.remove(r._r)
                            except Exception: pass
                    if not has_locked_label(p):
                        p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(0)
                        if exemplar is not None:
                            for r in p.runs:
                                if not r.bold and r.text:
                                    if r._r.rPr is not None: r._r.remove(r._r.rPr)
                                    r._r.insert(0,deepcopy(exemplar))
    d.save(a.output)
if __name__=='__main__': main()
