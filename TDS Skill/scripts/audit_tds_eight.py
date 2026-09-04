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
def semantic_fields(mapping):
    model=mapping.get('normalized_model',{})
    normalized=model.get('fields',{})
    return normalized or mapping.get('mapped_fields',{})
def semantic_rows(mapping):
    rows=mapping.get('normalized_model',{}).get('performance_rows')
    return rows if rows is not None else mapping.get('performance_rows')
def semantic_values(item,lang):
    return (item.get('normalized_values',{}) if 'normalized_values' in item else item.get('values',{})).get(lang)
def semantic_labels(item,lang):
    return (item.get('normalized_label_values',{}) if 'normalized_label_values' in item else item.get('label_values',{})).get(lang)
def semantic_units(item,lang):
    return (item.get('normalized_unit_values',{}) if 'normalized_unit_values' in item else item.get('unit_values',{})).get(lang)
def semantic_methods(item,lang):
    return (item.get('normalized_test_method_values',{}) if 'normalized_test_method_values' in item else item.get('test_method_values',{})).get(lang)
def audit_shape(base_doc, output_doc, variant, mapping):
    left, right = shape(doc_snapshot(base_doc)), shape(doc_snapshot(output_doc))
    left_table, right_table = left['tables'][0], right['tables'][0]
    if left['sections'] != right['sections'] or left_table['grid_widths'] != right_table['grid_widths']: return False
    source_rows=semantic_rows(mapping)
    if source_rows is not None:
        start=variant.get('performance_table',{}).get('data_start_row_index',1)
        if right_table['rows'][:start] != left_table['rows'][:start]: return False
        for i,row in enumerate(right_table['rows'][start:]):
            expected=left_table['rows'][start+min(i,len(left_table['rows'])-start-1)]
            if row != expected: return False
    else:
        if left_table['rows'][:6] != right_table['rows'][:6]: return False
        extras=mapping.get('performance_extra_rows',[])
        if len(right_table['rows']) != 6+len(extras): return False
        rows=right_table['rows'][6:]
    for row in (rows if source_rows is None else []):
        if [c['shape'] for c in row['cells']] != [c['shape'] for c in left_table['rows'][5]['cells']]: return False
    def heading_index(doc, names):
        return next((i for i,p in enumerate(doc.paragraphs) if p.text.strip() in names),None)
    names={'【应用】','【Application】'}
    li,ri=heading_index(base_doc,names),heading_index(output_doc,names)
    if li is None or ri is None: return False
    return left['paragraphs'][:24]+left['paragraphs'][li:] == right['paragraphs'][:24]+right['paragraphs'][ri:]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--model',required=True); ap.add_argument('--report',type=Path,required=True); args=ap.parse_args()
    reg=load(args.registry); mapping=load(args.mapping); results=[]; errors=[]; warnings=[]
    fields=semantic_fields(mapping)
    model=mapping.get('normalized_model',{})
    decisions=mapping.get('decision_ledger',model.get('decision_ledger',[]))
    if mapping.get('schema_version')=='1.3.0':
        if not model: errors.append('missing_normalized_model')
        if model.get('translation',{}).get('source')!='normalized_model': errors.append('translation_not_from_normalized_model')
        if model.get('status')!='approved': errors.append(f'normalized_model_not_approved:{model.get("status","missing")}')
        decision_by_field={item.get('field_id'):item for item in decisions}
        for row in semantic_rows(mapping) or []:
            decision=decision_by_field.get(row.get('field_id'))
            if not decision: errors.append(f'missing_decision_ledger:{row.get("field_id")}'); continue
            if not decision.get('provenance'): errors.append(f'missing_provenance:{row.get("field_id")}')
        pending=sum(1 for item in decisions if item.get('needs_judgment'))
        if pending: warnings.append(f'pending_agent_judgments:{pending}')
    required_fields=['product.title','product.description','product.supply_form','product.features','product.application','product.storage']
    for language in ('zh-CN','en-US'):
        for field in required_fields:
            item=fields.get(field,{})
            values=item.get('normalized_values',item.get('values',{}))
            if language not in values: errors.append(f'missing_language_source_value:{language}:{field}')
        if semantic_rows(mapping) is not None:
            for row in semantic_rows(mapping):
                if language not in row.get('normalized_label_values',row.get('label_values',{})) or language not in row.get('normalized_values',row.get('values',{})): errors.append(f'missing_language_source_row:{language}:{row.get("field_id")}')
        else:
            for extra in mapping.get('performance_extra_rows',[]):
                if language not in extra.get('label_values',{}) or language not in extra.get('values',{}): errors.append(f'missing_language_extra_metric:{language}:{extra.get("field_id")}')
    for vid,v in reg['variants'].items():
        stem={'TDS_CN_冠志模板':'TDS_CN_冠志','TDS_CN_国彩模板':'TDS_CN_国彩','TDS_EN_冠志模板':'TDS_EN_冠志','TDS_EN_国彩模板':'TDS_EN_国彩'}[vid]
        out=args.output_dir/f'{args.model}_{stem}.docx'
        if not out.is_file(): errors.append(f'missing_docx:{out.name}'); continue
        base=Document(str(ROOT/v['template'])); product=Document(str(out));
        geometry_ok=audit_shape(base,product,v,mapping)
        if not geometry_ok: errors.append(f'geometry_changed:{vid}')
        parts0=package_inventory(ROOT/v['template']); parts1=package_inventory(out)
        for part,h in parts0.items():
            if part!='word/document.xml' and parts1.get(part)!=h: errors.append(f'package_part_changed:{vid}:{part}')
        text='\n'.join(p.text for p in product.paragraphs)+'\n'+'\n'.join(c.text for t in product.tables for r in t.rows for c in r.cells)
        leaks=[x for x in load(ROOT/'mapping'/'tds_mutation_whitelist.json')['sample_fact_tokens'] if x.lower() in text.lower()]
        if leaks: errors.append(f'sample_fact_leak:{vid}:{leaks}')
        pdf=out.with_suffix('.pdf')
        if not pdf.is_file(): errors.append(f'missing_pdf:{pdf.name}')
        results.append({'variant_id':vid,'docx':str(out),'docx_sha256':sha256(out),'pdf':str(pdf),'pdf_sha256':sha256(pdf) if pdf.is_file() else None,'pdf_derived_name_match':pdf.stem==out.stem,'geometry':'pass' if geometry_ok else 'fail'})
        if pdf.stem!=out.stem: errors.append(f'pdf_pair_name_mismatch:{vid}')
        if semantic_rows(mapping) is not None:
            start=v.get('performance_table',{}).get('data_start_row_index',1)
            actual=[[c.text for c in row.cells] for row in product.tables[0].rows[start:]]
            expected=[]
            for source_row in semantic_rows(mapping):
                expected.append([
                    semantic_labels(source_row,v['language']) or ('无数据' if v['language']=='zh-CN' else 'No data available'),
                    semantic_values(source_row,v['language']) or ('无数据' if v['language']=='zh-CN' else 'No data available'),
                    semantic_units(source_row,v['language']) or source_row.get('unit','') or '',
                    semantic_methods(source_row,v['language']) or source_row.get('test_method','') or ''
                ])
            if actual!=expected: errors.append(f'performance_source_parity:{vid}')
    pdfs=sorted(args.output_dir.glob('*.pdf'))
    if len(pdfs)!=4: errors.append(f'pdf_count:{len(pdfs)}')
    docxs=sorted(args.output_dir.glob('*.docx'))
    if len(docxs)!=4: errors.append(f'docx_count:{len(docxs)}')
    report={'schema_version':'1.1.0','status':'RELEASE_PASS' if not errors else 'RELEASE_FAIL','release_blocker':bool(errors),'docx_count':len(docxs),'pdf_count':len(pdfs),'errors':sorted(set(errors)),'warnings':sorted(set(warnings)),'normalization_model_status':model.get('status','legacy-mapping'),'translation_source':model.get('translation',{}).get('source','legacy-mapping'),'variants':results,'customer_ready':False,'ready_for_user_proofreading':not errors and not warnings}
    dump(args.report,report); print(f"status={report['status']} errors={len(errors)}")
    raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
