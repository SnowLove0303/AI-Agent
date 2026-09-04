from __future__ import annotations
import argparse, subprocess
from pathlib import Path
from tds_common import SOFFICE
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-dir',type=Path,required=True); args=ap.parse_args(); pdfs=[]
    for docx in sorted(args.input_dir.glob('*.docx')):
        if docx.name.endswith('.generation.json'): continue
        if docx.with_suffix('.pdf').is_file() and docx.with_suffix('.pdf').stat().st_mtime >= docx.stat().st_mtime: pdfs.append(docx.with_suffix('.pdf').name); continue
        command=[str(SOFFICE),'--headless','--norestore','--nodefault','--nofirststartwizard','--convert-to','pdf','--outdir',str(args.input_dir),str(docx)]
        try: r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        except subprocess.TimeoutExpired:
            if not docx.with_suffix('.pdf').is_file(): raise SystemExit(f'PDF conversion timed out: {docx}')
            r=None
        if r is not None and r.returncode and not docx.with_suffix('.pdf').is_file(): raise SystemExit(f'PDF conversion failed: {docx}\n{r.stdout}\n{r.stderr}')
        if not docx.with_suffix('.pdf').is_file(): raise SystemExit(f'PDF conversion produced no file: {docx}')
        pdfs.append(docx.with_suffix('.pdf').name)
    print(f'pdf_count={len(pdfs)}')
if __name__=='__main__': main()
