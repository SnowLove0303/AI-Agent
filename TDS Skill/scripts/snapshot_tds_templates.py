from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from tds_common import ROOT, dump, doc_snapshot, package_inventory, sha256

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'snapshots'/'template_baselines.json'); args=ap.parse_args()
    variants={}
    for p in sorted((ROOT/'templates'/'active').glob('*.docx')):
        source=ROOT/'templates'/'source'/(p.stem+'.doc')
        variants[p.stem]={'file':str(p.relative_to(ROOT)),'sha256':sha256(p),'source_file':str(source.relative_to(ROOT)),'source_sha256':sha256(source) if source.is_file() else None,'snapshot':doc_snapshot(Document(str(p))),'package_parts':package_inventory(p)}
    if len(variants)!=4: raise SystemExit(f'expected 4 active templates, found {len(variants)}')
    dump(args.output,{'schema_version':'1.0.0','variants':variants}); print(f'baselines={args.output} variants={len(variants)}')
if __name__=='__main__': main()
