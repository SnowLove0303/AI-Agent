from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
from docx import Document
from tds_common import ROOT, dump, load, package_inventory, sha256, doc_snapshot

def shape(s):
    s=json.loads(json.dumps(s));
    for p in s['paragraphs']: p['text']=''
    for t in s['tables']:
        for row in t['rows']:
            for c in row['cells']: c['text']=''
    for sec in s['sections']:
        for p in sec['header']+sec['footer']: p['text']=''
    return s
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--model',required=True); ap.add_argument('--report',type=Path,required=True); args=ap.parse_args()
    reg=load(args.registry); mapping=load(args.mapping); results=[]; errors=[]
    for vid,v in reg['variants'].items():
        stem={'TDS_CN_冠志模板':'TDS_CN_冠志','TDS_CN_国彩模板':'TDS_CN_国彩','TDS_EN_冠志模板':'TDS_EN_冠志','TDS_EN_国彩模板':'TDS_EN_国彩'}[vid]
        out=args.output_dir/f'{args.model}_{stem}.docx'
        if not out.is_file(): errors.append(f'missing_docx:{out.name}'); continue
        base=Document(str(ROOT/v['template'])); product=Document(str(out));
        if shape(doc_snapshot(base))!=shape(doc_snapshot(product)): errors.append(f'geometry_changed:{vid}')
        parts0=package_inventory(ROOT/v['template']); parts1=package_inventory(out)
        for part,h in parts0.items():
            if part!='word/document.xml' and parts1.get(part)!=h: errors.append(f'package_part_changed:{vid}:{part}')
        text='\n'.join(p.text for p in product.paragraphs)+'\n'+'\n'.join(c.text for t in product.tables for r in t.rows for c in r.cells)
        leaks=[x for x in load(ROOT/'mapping'/'tds_mutation_whitelist.json')['sample_fact_tokens'] if x.lower() in text.lower()]
        if leaks: errors.append(f'sample_fact_leak:{vid}:{leaks}')
        pdf=out.with_suffix('.pdf')
        if not pdf.is_file(): errors.append(f'missing_pdf:{pdf.name}')
        results.append({'variant_id':vid,'docx':str(out),'docx_sha256':sha256(out),'pdf':str(pdf),'pdf_sha256':sha256(pdf) if pdf.is_file() else None,'pdf_derived_name_match':pdf.stem==out.stem,'geometry':'pass' if shape(doc_snapshot(base))==shape(doc_snapshot(product)) else 'fail'})
        if pdf.stem!=out.stem: errors.append(f'pdf_pair_name_mismatch:{vid}')
    pdfs=sorted(args.output_dir.glob('*.pdf'))
    if len(pdfs)!=4: errors.append(f'pdf_count:{len(pdfs)}')
    docxs=sorted(args.output_dir.glob('*.docx'))
    if len(docxs)!=4: errors.append(f'docx_count:{len(docxs)}')
    report={'schema_version':'1.0.0','status':'RELEASE_PASS' if not errors else 'RELEASE_FAIL','release_blocker':bool(errors),'docx_count':len(docxs),'pdf_count':len(pdfs),'errors':sorted(set(errors)),'variants':results,'customer_ready':False,'ready_for_user_proofreading':not errors}
    dump(args.report,report); print(f"status={report['status']} errors={len(errors)}")
    raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
