#!/usr/bin/env python3
"""Flag MSDS table cells/rows likely to create unnecessary vertical height.

Explicit line breaks are valid controlled structure in Section 11/14 and in
multi-line hazard/precaution fields.  They are reported as metrics, not as
release failures; empty paragraphs, trailing spaces and literal tabs remain
failures when they are not part of the preserved template geometry.
"""
import argparse, json, re, sys
from docx import Document
from docx.oxml.ns import qn

def unique_cells(row):
    out=[]; seen=set()
    for c in row.cells:
        k=id(c._tc)
        if k not in seen: seen.add(k); out.append(c)
    return out

def run(docx, document=None):
    """Audit one built DOCX; return the report dict. Import-safe core of main()."""
    d = document or Document(docx); issues=[]; intentional_breaks=0; intentional_tabs=0
    for ti,t in enumerate(d.tables):
        for ri,row in enumerate(t.rows):
            trPr=row._tr.trPr
            if trPr is not None:
                for h in trPr.findall(qn('w:trHeight')):
                    rule=h.get(qn('w:hRule')); val=h.get(qn('w:val'))
                    if rule == 'exact':
                        issues.append({'type':'exact_row_height_constraint','table':ti,'row':ri,'rule':rule,'val':val})
            for ci,c in enumerate(unique_cells(row)):
                ps=list(c.paragraphs)
                nonempty=[p for p in ps if p.text.strip()]
                if nonempty and len(ps)>1:
                    # empty paragraph anywhere after real content is suspicious
                    for pi,p in enumerate(ps):
                        if not p.text.strip():
                            issues.append({'type':'empty_paragraph_in_populated_cell','table':ti,'row':ri,'cell':ci,'paragraph':pi})
                for pi,p in enumerate(ps):
                    for line_no, line in enumerate(p.text.splitlines(), 1):
                        if line.strip() in {"/", "／"}:
                            issues.append({'type':'slash_only_line','table':ti,'row':ri,
                                           'cell':ci,'paragraph':pi,'line':line_no})
                    locked = any(r.bold and r.text.strip() for r in p.runs)
                    for xi,r in enumerate(p.runs):
                        txt=r.text
                        if not locked and not r.bold and txt == '' and len(p.runs)>1:
                            issues.append({'type':'empty_nonbold_run','table':ti,'row':ri,'cell':ci,'paragraph':pi,'run':xi})
                        if not locked and '\t' in txt:
                            issues.append({'type':'tab_in_text','table':ti,'row':ri,'cell':ci,'paragraph':pi,'run':xi})
                        if not locked and re.search(r'[ \u3000]+$',txt):
                            issues.append({'type':'trailing_space','table':ti,'row':ri,'cell':ci,'paragraph':pi,'run':xi})
                    # explicit breaks/tabs can exist even when run.text hides details
                    xml=p._p.xml
                    if not locked and '<w:br' in xml: intentional_breaks += 1
                    if not locked and '<w:tab' in xml: intentional_tabs += 1
    return {'pass':not issues,'issue_count':len(issues),'intentional_break_count':intentional_breaks,'intentional_tab_count':intentional_tabs,'issues':issues}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('docx'); ap.add_argument('--json'); a=ap.parse_args()
    rep = run(a.docx)
    s=json.dumps(rep,ensure_ascii=False,indent=2); print(s)
    if a.json: open(a.json,'w',encoding='utf-8').write(s)
    sys.exit(0 if rep['pass'] else 1)
if __name__=='__main__': main()
