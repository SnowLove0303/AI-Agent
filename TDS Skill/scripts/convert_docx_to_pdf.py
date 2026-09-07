from __future__ import annotations
import argparse, subprocess
from pathlib import Path
from tds_common import SOFFICE
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-dir',type=Path,required=True); ap.add_argument('--output-dir',type=Path); args=ap.parse_args(); pdfs=[]; output_dir=args.output_dir or args.input_dir; output_dir.mkdir(parents=True,exist_ok=True)
    for docx in sorted(args.input_dir.glob('*.docx')):
        if docx.name.endswith('.generation.json'): continue
        pdf=output_dir/(docx.stem+'.pdf')
        if pdf.is_file() and pdf.stat().st_mtime >= docx.stat().st_mtime: pdfs.append(pdf.name); continue
        command=[str(SOFFICE),'--headless','--norestore','--nodefault','--nofirststartwizard','--convert-to','pdf','--outdir',str(output_dir),str(docx)]
        try: r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        except subprocess.TimeoutExpired:
            if not pdf.is_file(): raise SystemExit(f'PDF conversion timed out: {docx}')
            r=None
        if r is not None and r.returncode and not pdf.is_file(): raise SystemExit(f'PDF conversion failed: {docx}\n{r.stdout}\n{r.stderr}')
        if not pdf.is_file(): raise SystemExit(f'PDF conversion produced no file: {docx}')
        pdfs.append(pdf.name)
    print(f'pdf_count={len(pdfs)}')
if __name__=='__main__': main()
