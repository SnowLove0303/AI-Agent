#!/usr/bin/env python3
from pathlib import Path
import argparse, sys

SUFFIX_GROUPS = [
    ("MSDS_CN_冠志", "MSDS_CN_Guanzhi"),
    ("MSDS_CN_国彩", "MSDS_CN_Guocai"),
    ("MSDS_EN_冠志", "MSDS_EN_Guanzhi"),
    ("MSDS_EN_国彩", "MSDS_EN_Guocai"),
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("model")
    a=ap.parse_args()
    d=Path(a.directory)
    missing=[]; empty=[]; found=[]
    for aliases in SUFFIX_GROUPS:
        for ext in ("docx","pdf"):
            candidates=[d/f"{a.model}_{s}.{ext}" for s in aliases]
            existing=[p for p in candidates if p.exists()]
            if not existing:
                names={p.name for p in candidates}
                existing=[p for p in d.rglob(f"{a.model}_*.{ext}") if p.name in names]
            if not existing:
                missing.append(" or ".join(str(p) for p in candidates))
            elif all(p.stat().st_size==0 for p in existing):
                empty.append(" or ".join(str(p) for p in existing))
            else:
                found.append(str(next(p for p in existing if p.stat().st_size > 0)))
    if missing or empty:
        if missing: print("MISSING:", *missing, sep="\n")
        if empty: print("EMPTY:", *empty, sep="\n")
        return 1
    print(f"eight-file matrix: PASS ({len(found)} files; Chinese and English company-name aliases accepted)")
    return 0
if __name__=='__main__': sys.exit(main())
