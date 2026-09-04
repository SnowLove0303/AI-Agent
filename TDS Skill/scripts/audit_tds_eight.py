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
def audit_shape(base_doc, output_doc, variant, mapping):
    left, right = shape(doc_snapshot(base_doc)), shape(doc_snapshot(output_doc))
    left_table, right_table = left['tables'][0], right['tables'][0]
    if left['sections'] != right['sections'] or left_table['grid_widths'] != right_table['grid_widths']: return False
    if left_table['rows'][:6] != right_table['rows'][:6]: return False
    extras=mapping.get('performance_extra_rows',[])
    if len(right_table['rows']) != 6+len(extras): return False
    for row in right_table['rows'][6:]:
        if [c['shape'] for c in row['cells']] != [c['shape'] for c in left_table['rows'][5]['cells']]: return False
    def heading_index(doc, names):
        return next((i for i,p in enumerate(doc.paragraphs) if p.text.strip() in names),None)
    names={'【应用】','【Application】'}
    li,ri=heading_index(base_doc,names),heading_index(output_doc,names)
    if li is None or ri is None: return False
    return left['paragraphs'][:24]+left['paragraphs'][li:] == right['paragraphs'][:24]+right['paragraphs'][ri:]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--model',required=True); ap.add_argument('--report',type=Path,required=True); args=ap.parse_args()
    reg=load(args.registry); mapping=load(args.mapping); results=[]; errors=[]
    for vid,v in reg['variants'].items():
        stem={'TDS_CN_冠志模板':'TDS_CN_冠志','TDS_CN_国彩模板':'TDS_CN_国彩','TDS_EN_冠志模板':'TDS_EN_冠志','TDS_EN_国彩模板':'TDS_EN_国彩'}[vid]
        out=args.output_dir/f'{args.model}_{stem}.docx'
        if not out.is_file(): errors.append(f'missing_docx:{out.name}'); continue
        base=Document(str(ROOT/v['template'])); product=Document(str(out));
        if not audit_shape(base,product,v,mapping): errors.append(f'geometry_changed:{vid}')
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
