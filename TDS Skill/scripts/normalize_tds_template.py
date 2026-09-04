"""Normalize only the active TDS template feature slots."""
from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from tds_common import feature_spacing_signature

FEATURE_PARAGRAPH_INDICES=(21,23)

def normalize_document(source: Path, output: Path) -> list[int]:
    doc=Document(str(source)); removed=[]
    for index in FEATURE_PARAGRAPH_INDICES:
        p=doc.paragraphs[index]; ppr=p._p.pPr
        num=ppr.find(qn('w:numPr')) if ppr is not None else None
        if num is not None:
            ppr.remove(num); removed.append(index)
    if feature_spacing_signature(doc.paragraphs[21]) != feature_spacing_signature(doc.paragraphs[23]):
        raise ValueError(f'{source.name}: feature paragraph spacing is not equal')
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_name(output.name+'.normalized.docx'); doc.save(str(tmp)); tmp.replace(output)
    return removed

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    removed=normalize_document(args.input,args.output); print(f'normalized={args.output} removed_numbering={removed}')

if __name__=='__main__': main()
