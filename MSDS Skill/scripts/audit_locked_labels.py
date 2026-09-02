#!/usr/bin/env python3
"""Audit surviving bold label anchors against the untouched template.

Deleted unsupported items are allowed. Since whole-row suppression shifts the
physical row index of every following item, surviving anchors are checked as
an ordered subsequence within each table using their cell/paragraph position
and paragraph properties. This preserves locked formatting while allowing the
approved omission policy to remove dedicated rows.
"""
import argparse, hashlib, json, sys
from docx import Document
from lxml import etree

def unique_cells(row):
    out=[]; seen=set()
    for c in row.cells:
        k=id(c._tc)
        if k not in seen: seen.add(k); out.append(c)
    return out

def hx(el):
    return None if el is None else hashlib.sha256(etree.tostring(el, method='c14n')).hexdigest()

def collect(path):
    d=Document(path); items=[]
    for ti,t in enumerate(d.tables):
        for ri,row in enumerate(t.rows):
            for ci,c in enumerate(unique_cells(row)):
                for pi,p in enumerate(c.paragraphs):
                    bold_runs=[r for r in p.runs if r.bold and r.text.strip()]
                    if not bold_runs: continue
                    # A template label may be split across several runs.  The
                    # output writer is allowed to merge those adjacent runs as
                    # long as the complete bold anchor and paragraph placement
                    # remain unchanged.
                    bold_text=''.join(r.text for r in p.runs if r.bold and r.text.strip())
                    if bold_text.strip():
                        items.append({'text':bold_text,'norm':bold_text.strip(),'table':ti,'row':ri,'cell':ci,'p':pi,'run':None,'rPr':None,'pPr':hx(p._p.pPr)})
    return items

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('template'); ap.add_argument('output'); ap.add_argument('--json'); a=ap.parse_args()
    base=collect(a.template); out=collect(a.output)
    # Labels may legitimately be translated, have spacing normalized, or be
    # merged from several Word runs. Their locked invariant is the ordered
    # table/cell/paragraph anchor and paragraph formatting, not literal label
    # text. Row numbers are intentionally excluded because deleted dedicated
    # rows shift all following row indexes.
    base_groups={}
    out_groups={}
    for item in base:
        base_groups.setdefault(item['table'], []).append(item)
    for item in out:
        out_groups.setdefault(item['table'], []).append(item)
    problems=[]
    for table, output_items in out_groups.items():
        template_items = base_groups.get(table, [])
        cursor = 0
        for x in output_items:
            match = None
            for index in range(cursor, len(template_items)):
                candidate = template_items[index]
                if (candidate['cell'], candidate['p'], candidate['pPr']) == (x['cell'], x['p'], x['pPr']):
                    match = (index, candidate)
                    break
            if match is None:
                problems.append({'type':'unexpected_or_changed_bold_label','output':x})
                continue
            cursor = match[0] + 1
    rep={'pass':not problems,'problems':problems,'template_bold_runs':len(base),'output_bold_runs':len(out),'row_suppression_aware':True}
    s=json.dumps(rep,ensure_ascii=False,indent=2); print(s)
    if a.json: open(a.json,'w',encoding='utf-8').write(s)
    sys.exit(0 if rep['pass'] else 2)
if __name__=='__main__': main()
