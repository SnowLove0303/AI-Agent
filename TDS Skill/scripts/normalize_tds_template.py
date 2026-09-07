"""Validate active TDS template feature slots without changing their numbering."""
from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from register_tds_registry import feature_layout

def normalize_document(source: Path, output: Path) -> list[int]:
    doc=Document(str(source)); language='en-US' if '_EN_' in source.name else 'zh-CN'
    feature_layout(doc,language)
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_name(output.name+'.validated.docx'); doc.save(str(tmp)); tmp.replace(output)
    return []

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    removed=normalize_document(args.input,args.output); print(f'normalized={args.output} removed_numbering={removed}')

if __name__=='__main__': main()
