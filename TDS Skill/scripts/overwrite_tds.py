from __future__ import annotations
import argparse, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from tds_common import ROOT, dump, fresh_write, load, norm, replace_cell, replace_paragraph, sha256

NO_DATA={'zh-CN':'无数据','en-US':'No data available'}
def value(fact,lang): return fact.get('values',{}).get(lang) or NO_DATA[lang]
def write_variant(mapping, registry, variant_id, output):
    variant=registry['variants'][variant_id]; lang=variant['language']; fields=mapping['mapped_fields']; slots={x['field_id']:x for x in variant['slots']}
    sample_tokens=load(ROOT/'mapping'/'tds_mutation_whitelist.json')['sample_fact_tokens']
    def edit(doc):
        for fid,slot in slots.items():
            fact=fields.get(fid,{}); loc=slot['locator']
            if slot['kind']=='performance_row':
                row=doc.tables[loc['table_index']].rows[loc['row_index']]
                replace_cell(row.cells[1],value(fact,lang)); replace_cell(row.cells[2],fact.get('unit') or ''); replace_cell(row.cells[3],fact.get('test_method') or '')
            elif slot['kind']=='paragraph_list':
                vals=(fact.get('values',{}).get(lang) or '').splitlines() if fact.get('values',{}).get(lang) else []
                for i,pi in enumerate(loc['paragraph_indices']): replace_paragraph(doc.paragraphs[pi], vals[i] if i<len(vals) else NO_DATA[lang] if i==0 else '')
            else: replace_paragraph(doc.paragraphs[loc['paragraph_index']],value(fact,lang))
    fresh_write(ROOT/variant['template'],output,edit)
    text='\n'.join(p.text for p in Document(str(output)).paragraphs)+'\n'+'\n'.join(c.text for t in Document(str(output)).tables for r in t.rows for c in r.cells)
    leaked=[x for x in sample_tokens if x.lower() in text.lower() and x not in (mapping.get('allowed_source_tokens') or [])]
    record={'schema_version':'1.0.0','variant_id':variant_id,'template':variant['template'],'template_sha256':variant['template_sha256'],'output':str(output),'output_sha256':sha256(output),'generated_at':datetime.now(timezone.utc).isoformat(),'fresh_clone':True,'sample_fact_leaks':leaked,'ready_for_user_proofreading':not leaked,'customer_ready':False}
    dump(output.with_suffix(output.suffix+'.generation.json'),record)
    if leaked: raise RuntimeError(f'sample facts leaked in {output.name}: {leaked}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--model',required=True); args=ap.parse_args()
    m=load(args.mapping); r=load(args.registry)
    if m.get('status')!='ready': raise SystemExit('mapping is blocked; no DOCX written')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    names={'TDS_CN_冠志模板':'TDS_CN_冠志','TDS_CN_国彩模板':'TDS_CN_国彩','TDS_EN_冠志模板':'TDS_EN_冠志','TDS_EN_国彩模板':'TDS_EN_国彩'}
    for vid,v in r['variants'].items():
        stem=names[vid]; write_variant(m,r,vid,args.output_dir/f'{args.model}_{stem}.docx')
    print(f'docx_variants=4 output={args.output_dir}')
if __name__=='__main__': main()
