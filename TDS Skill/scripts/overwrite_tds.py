from __future__ import annotations
import argparse, json, re, zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from tds_common import ROOT, SECTION_HEADINGS, dump, ensure_feature_numbering, fresh_write, hidden_field_ids, load, norm, replace_cell, replace_paragraph, sha256

NO_DATA={'zh-CN':'无数据','en-US':'No data available'}
def feature_lines(text): return [re.sub(r'^\s*\d+[.、]\s*','',line) for line in (text or '').splitlines()]
def value(fact,lang): return fact.get('values',{}).get(lang) or NO_DATA[lang]
def semantic_fields(mapping):
    model=mapping.get('normalized_model',{})
    normalized=model.get('fields',{})
    if not normalized: return mapping['mapped_fields']
    return {fid:{**item,'values':item.get('normalized_values',{})} for fid,item in normalized.items()}
def semantic_rows(mapping):
    rows=mapping.get('normalized_model',{}).get('performance_rows')
    return rows if rows is not None else mapping.get('performance_rows')
def row_value(item,key,lang,fallback_key=None):
    normalized=item.get(f'normalized_{key}',{})
    if lang in normalized: return normalized.get(lang) or ''
    return item.get(fallback_key or key,{}).get(lang) or ''
def write_source_performance_rows(doc, rows, variant, lang):
    table=doc.tables[0]; table_spec=variant.get('performance_table',{}); start=table_spec.get('data_start_row_index',1); template_index=variant.get('performance_extension',{}).get('row_template_index',len(table.rows)-1)
    while len(table.rows)>start+len(rows): table._tbl.remove(table.rows[-1]._tr)
    while len(table.rows)<start+len(rows): table._tbl.append(deepcopy(table.rows[template_index]._tr))
    for i,item in enumerate(rows):
        row=table.rows[start+i]
        replace_cell(row.cells[0],row_value(item,'label_values',lang,'label_values') or NO_DATA[lang])
        replace_cell(row.cells[1],row_value(item,'values',lang,'values') or NO_DATA[lang])
        replace_cell(row.cells[2],row_value(item,'unit_values',lang,'unit_values') or item.get('unit',''))
        replace_cell(row.cells[3],row_value(item,'test_method_values',lang,'test_method_values') or item.get('test_method',''))
def write_variant(mapping, registry, variant_id, output):
    variant=registry['variants'][variant_id]; lang=variant['language']; fields=semantic_fields(mapping); slots={x['field_id']:x for x in variant['slots']}
    sample_tokens=load(ROOT/'mapping'/'tds_mutation_whitelist.json')['sample_fact_tokens']
    extension_rows = mapping.get('performance_extra_rows', [])
    source_rows = semantic_rows(mapping)
    if len(extension_rows)>variant.get('performance_extension',{}).get('max_rows',100): raise RuntimeError(f'too many additional performance rows for {variant_id}')
    if source_rows is not None and len(source_rows)>variant.get('performance_table',{}).get('max_source_rows',100): raise RuntimeError(f'too many source performance rows for {variant_id}')
    hidden=set(hidden_field_ids(mapping))
    feature_indices=variant.get('feature_format_contract',{}).get('paragraph_indices',[21,23])
    feature_extension=variant.get('feature_extension',{})
    feature_count=len(feature_indices)
    def edit(doc):
        for fid,slot in slots.items():
            if fid in hidden: continue
            fact=fields.get(fid,{}); loc=slot['locator']
            if slot['kind']=='performance_row':
                if source_rows is not None: continue
                row=doc.tables[loc['table_index']].rows[loc['row_index']]
                replace_cell(row.cells[1],value(fact,lang)); replace_cell(row.cells[2],fact.get('unit') or ''); replace_cell(row.cells[3],fact.get('test_method') or '')
            elif slot['kind']=='paragraph_list':
                vals=feature_lines(fact.get('values',{}).get(lang)) if fid=='product.features' else ((fact.get('values',{}).get(lang) or '').splitlines() if fact.get('values',{}).get(lang) else [])
                for i,pi in enumerate(loc['paragraph_indices']): replace_paragraph(doc.paragraphs[pi], vals[i] if i<len(vals) else NO_DATA[lang] if i==0 else '')
            else: replace_paragraph(doc.paragraphs[loc['paragraph_index']],value(fact,lang))
        feature_fact=fields.get('product.features',{}); feature_values=feature_lines(feature_fact.get('values',{}).get(lang))
        if len(feature_values)>variant.get('feature_extension',{}).get('max_items',100): raise RuntimeError(f'too many product features for {variant_id}')
        if 'product.features' not in hidden:
            for i in feature_indices:
                if i < len(doc.paragraphs): ensure_feature_numbering(doc.paragraphs[i])
        if len(feature_values)>feature_count:
            item_src=doc.paragraphs[feature_extension.get('paragraph_template_index',feature_indices[-1])]._p
            sep_src=doc.paragraphs[feature_extension.get('separator_paragraph_index',feature_indices[-1]+1)]._p
            anchor=item_src
            for text in feature_values[2:]:
                sep_clone=deepcopy(sep_src); anchor.addnext(sep_clone); anchor=sep_clone
                replace_paragraph(Paragraph(sep_clone,doc),'')
                clone=deepcopy(item_src); anchor.addnext(clone); anchor=clone
                replace_paragraph(Paragraph(clone,doc),text)
        if source_rows is not None:
            write_source_performance_rows(doc, source_rows, variant, lang)
        else:
            table=doc.tables[0]
            for extra in extension_rows:
                clone=deepcopy(table.rows[5]._tr); table._tbl.append(clone); row=table.rows[-1]
                replace_cell(row.cells[0],extra.get('label_values',{}).get(lang) or NO_DATA[lang]); replace_cell(row.cells[1],value(extra,lang)); replace_cell(row.cells[2],extra.get('unit') or ''); replace_cell(row.cells[3],extra.get('test_method') or '')
        hidden_paras=[]
        if hidden:
            extra_count=0
            if 'product.features' not in hidden:
                extra_count=max(0,len(feature_values)-feature_count)*2
            kill=set()
            for fid in hidden:
                head=SECTION_HEADINGS[fid][lang]
                hi=next((i for i,p in enumerate(doc.paragraphs) if p.text.strip()==head),None)
                if hi is None: raise RuntimeError(f'hidden section heading not found: {fid}')
                kill.add(hi)
                loc=slots[fid]['locator']
                idxs=loc['paragraph_indices'] if slots[fid]['kind']=='paragraph_list' else [loc['paragraph_index']]
                for j in idxs: kill.add(j+extra_count if j>feature_indices[-1] else j)
            for j in sorted(kill,reverse=True):
                p=doc.paragraphs[j]; p._p.getparent().remove(p._p); hidden_paras.append(j)
        else: hidden_paras=[]
        edit.hidden_paras=sorted(hidden_paras)
    fresh_write(ROOT/variant['template'],output,edit)
    text='\n'.join(p.text for p in Document(str(output)).paragraphs)+'\n'+'\n'.join(c.text for t in Document(str(output)).tables for r in t.rows for c in r.cells)
    leaked=[x for x in sample_tokens if x.lower() in text.lower() and x not in (mapping.get('allowed_source_tokens') or [])]
    record={'schema_version':'1.3.5','variant_id':variant_id,'template':variant['template'],'template_sha256':variant['template_sha256'],'output':str(output),'output_sha256':sha256(output),'generated_at':datetime.now(timezone.utc).isoformat(),'fresh_clone':True,'source_led_performance_rows':source_rows is not None,'performance_extra_rows':len(extension_rows),'feature_extra_items':max(0,len(fields.get('product.features',{}).get('values',{}).get(lang,'').splitlines())-len(variant.get('feature_format_contract',{}).get('paragraph_indices',[21,23]))),'hidden_fields':sorted(hidden_field_ids(mapping)),'hidden_paragraphs':getattr(edit,'hidden_paras',[]),'sample_fact_leaks':leaked,'normalization_model_status':mapping.get('normalized_model',{}).get('status','legacy-mapping'),'translation_source':mapping.get('normalized_model',{}).get('translation',{}).get('source','legacy-mapping'),'decision_ledger_entries':len(mapping.get('decision_ledger',mapping.get('normalized_model',{}).get('decision_ledger',[]))),'ready_for_user_proofreading':not leaked,'customer_ready':False}
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
