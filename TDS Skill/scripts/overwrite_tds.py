from __future__ import annotations
import argparse, re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from tds_common import OUTPUT_HEADINGS, PERFORMANCE_TOPOLOGIES, ROOT, SECTION_HEADINGS, dump, fresh_write, hidden_block_indices, hidden_field_ids, load, performance_topology, replace_cell, replace_feature_paragraph, replace_paragraph, sha256

NO_DATA={'zh-CN':'无数据','en-US':'No data available'}
def feature_lines(text): return [re.sub(r'^\s*\d+[.、]\s*','',line) for line in (text or '').splitlines()]
def paragraph_lines(text, field_id):
    lines=[line.strip() for line in (text or '').splitlines() if line.strip()]
    if field_id=='product.application': lines=[re.sub(r'^\s*\d+[.、]\s*','',line).strip() for line in lines]
    return lines
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

def _set_cell_width(cell, width):
    tcPr=cell._tc.get_or_add_tcPr(); tcW=tcPr.find(qn('w:tcW'))
    if tcW is None: tcW=OxmlElement('w:tcW'); tcPr.append(tcW)
    tcW.set(qn('w:w'),str(width)); tcW.set(qn('w:type'),'dxa')

def adapt_performance_table(table, variant, topology):
    """Prune only unneeded performance columns and retain all surviving cell formatting."""
    spec=variant.get('performance_table',{}); widths=spec.get('topology_widths',{}).get(topology)
    if not widths: raise RuntimeError(f'unsupported performance topology: {topology}')
    target=len(widths)
    for row in list(table._tbl.tr_lst):
        for cell in list(row.tc_lst)[target:]: row.remove(cell)
    grid=table._tbl.tblGrid
    while len(grid.gridCol_lst)>target: grid.remove(grid.gridCol_lst[-1])
    while len(grid.gridCol_lst)<target: grid.append(OxmlElement('w:gridCol'))
    for col,width in zip(grid.gridCol_lst,widths): col.set(qn('w:w'),str(width))
    for row in table.rows:
        for index,cell in enumerate(row.cells[:target]): _set_cell_width(cell,widths[index])
    return target

def write_source_performance_rows(doc, rows, variant, lang, topology):
    table=doc.tables[0]; columns=adapt_performance_table(table,variant,topology); table_spec=variant.get('performance_table',{}); start=table_spec.get('data_start_row_index',1); template_index=variant.get('performance_extension',{}).get('row_template_index',len(table.rows)-1)
    while len(table.rows)>start+len(rows): table._tbl.remove(table.rows[-1]._tr)
    while len(table.rows)<start+len(rows): table._tbl.append(deepcopy(table.rows[template_index]._tr))
    for i,item in enumerate(rows):
        row=table.rows[start+i]
        values=[row_value(item,'label_values',lang,'label_values') or NO_DATA[lang],row_value(item,'values',lang,'values') or NO_DATA[lang]]
        if columns>=3: values.append(row_value(item,'unit_values',lang,'unit_values') or item.get('unit',''))
        if columns>=4: values.append(row_value(item,'test_method_values',lang,'test_method_values') or item.get('test_method',''))
        for column,text in enumerate(values): replace_cell(row.cells[column],text)
def _write_variant(mapping, registry, variant_id, output, event=None, generation_path=None, execution_log_file=None):
    variant=registry['variants'][variant_id]; lang=variant['language']; fields=semantic_fields(mapping); slots={x['field_id']:x for x in variant['slots']}
    if event: event('mapping_loaded', language=lang, field_count=len(fields), slot_count=len(slots))
    sample_tokens=load(ROOT/'mapping'/'tds_mutation_whitelist.json')['sample_fact_tokens']
    extension_rows = mapping.get('performance_extra_rows', [])
    source_rows = semantic_rows(mapping)
    if len(extension_rows)>variant.get('performance_extension',{}).get('max_rows',100): raise RuntimeError(f'too many additional performance rows for {variant_id}')
    if source_rows is not None and len(source_rows)>variant.get('performance_table',{}).get('max_source_rows',100): raise RuntimeError(f'too many source performance rows for {variant_id}')
    hidden=set(hidden_field_ids(mapping))
    topology=performance_topology(mapping,variant)
    def edit(doc):
        if event: event('template_opened', paragraph_count=len(doc.paragraphs), table_count=len(doc.tables))
        columns=adapt_performance_table(doc.tables[0],variant,topology)
        paragraph_values={}
        feature_values=[]
        for fid,slot in slots.items():
            if fid in hidden: continue
            fact=fields.get(fid,{}); loc=slot['locator']
            if slot['kind']=='performance_row':
                if source_rows is not None: continue
                row=doc.tables[loc['table_index']].rows[loc['row_index']]
                values=[None,value(fact,lang)]
                if columns>=3: values.append(fact.get('unit') or '')
                if columns>=4: values.append(fact.get('test_method') or '')
                for column,text in enumerate(values):
                    if text is not None: replace_cell(row.cells[column],text)
            elif slot['kind']=='paragraph_list':
                vals=feature_lines(fact.get('values',{}).get(lang)) if fid=='product.features' else paragraph_lines(fact.get('values',{}).get(lang),fid)
                if fid=='product.features': feature_values=vals
                for i,pi in enumerate(loc['paragraph_indices']):
                    text=vals[i] if i<len(vals) else NO_DATA[lang] if i==0 else ''
                    replace_feature_paragraph(doc.paragraphs[pi], text) if fid=='product.features' else replace_paragraph(doc.paragraphs[pi], text)
            else:
                lines=paragraph_lines(fact.get('values',{}).get(lang),fid)
                if fid=='product.title' and len(lines)>1: raise RuntimeError(f'title must be a single line: {fid}')
                paragraph_values[fid]=lines or [value(fact,lang)]
                replace_paragraph(doc.paragraphs[loc['paragraph_index']],paragraph_values[fid][0])
        if event: event('semantic_fields_written', field_ids=sorted(slots))
        kill=set()
        if hidden:
            kill=hidden_block_indices(list(doc.paragraphs),lang,slots,hidden)
            if kill is None: raise RuntimeError('hidden section heading not found')
        removed=sorted(kill)
        if event and removed: event('sections_hidden', removed=removed)
        hidden_paras=[]
        for j in sorted(kill,reverse=True):
            p=doc.paragraphs[j]; p._p.getparent().remove(p._p); hidden_paras.append(j)
        shifts=[]
        def current_index(original):
            return original-sum(1 for h in kill if h<original)+sum(count for anchor,count in shifts if anchor<original)
        if 'product.features' not in hidden and len(feature_values)>len(slots['product.features']['locator']['paragraph_indices']):
            extension=variant.get('feature_extension',{})
            if not extension.get('allowed',False): raise RuntimeError(f'feature extension disabled by template policy: {variant_id}')
            if len(feature_values)>extension.get('max_items',100): raise RuntimeError(f'too many product features for {variant_id}')
            anchor_original=extension.get('paragraph_template_index',slots['product.features']['locator']['paragraph_indices'][-1])
            template_paragraph=doc.paragraphs[current_index(anchor_original)]
            anchor=template_paragraph._p
            added=len(feature_values)-len(slots['product.features']['locator']['paragraph_indices'])
            for text in feature_values[-added:]:
                clone=deepcopy(template_paragraph._p); anchor.addnext(clone); anchor=clone
                replace_feature_paragraph(Paragraph(clone,doc),text)
            shifts.append((anchor_original,added))
            if event: event('feature_list_extended', added=added, cloned_from=anchor_original)
        for fid,lines in sorted(((fid,lines) for fid,lines in paragraph_values.items() if fid!='product.title' and fid not in hidden and len(lines)>1), key=lambda item: slots[item[0]]['locator']['paragraph_index']):
            original=slots[fid]['locator']['paragraph_index']; pos=current_index(original)
            template_paragraph=doc.paragraphs[pos]; anchor=template_paragraph._p
            for text in lines[1:]:
                clone=deepcopy(template_paragraph._p); anchor.addnext(clone); anchor=clone
                replace_paragraph(Paragraph(clone,doc),text)
            shifts.append((original,len(lines)-1))
            if event: event('slot_paragraphs_expanded', field_id=fid, lines=len(lines), cloned_from=original)
        if source_rows is not None:
            write_source_performance_rows(doc, source_rows, variant, lang, topology)
        else:
            table=doc.tables[0]
            template_index=variant.get('performance_extension',{}).get('row_template_index',len(table.rows)-1)
            for extra in extension_rows:
                clone=deepcopy(table.rows[template_index]._tr); table._tbl.append(clone); row=table.rows[-1]
                values=[extra.get('label_values',{}).get(lang) or NO_DATA[lang],value(extra,lang)]
                if columns>=3: values.append(extra.get('unit') or '')
                if columns>=4: values.append(extra.get('test_method') or '')
                for column,text in enumerate(values): replace_cell(row.cells[column],text)
        if event: event('performance_rows_written', row_count=len(source_rows) if source_rows is not None else len(extension_rows), source_led=source_rows is not None, topology=topology)
        if lang=='en-US':
            for fid in ('product.description','product.supply_form','product.features','product.application','product.storage'):
                old=SECTION_HEADINGS[fid][lang]; new=OUTPUT_HEADINGS[fid][lang]
                for p in doc.paragraphs:
                    if p.text.strip()==old: replace_paragraph(p,new)
            for p in doc.paragraphs:
                if p.text.strip()=='【Technical Data】': replace_paragraph(p,'Technical Data')
        tail_trimmed=[]
        if variant.get('tail_blank_trim',{}).get('allowed',False):
            while doc.paragraphs and not doc.paragraphs[-1].text.strip():
                p=doc.paragraphs[-1]; p._p.getparent().remove(p._p); tail_trimmed.append(p)
        if event and tail_trimmed: event('tail_blank_paragraphs_trimmed', count=len(tail_trimmed))
        if event: event('sections_finalized', hidden_paragraph_count=len(hidden_paras), english_headings=lang=='en-US')
        edit.hidden_paras=sorted(hidden_paras)
        edit.tail_blank_count=len(tail_trimmed)
    fresh_write(ROOT/variant['template'],output,edit)
    if event: event('docx_written', output_bytes=output.stat().st_size)
    text='\n'.join(p.text for p in Document(str(output)).paragraphs)+'\n'+'\n'.join(c.text for t in Document(str(output)).tables for r in t.rows for c in r.cells)
    leaked=[x for x in sample_tokens if x.lower() in text.lower() and x not in (mapping.get('allowed_source_tokens') or [])]
    feature_values=feature_lines(fields.get('product.features',{}).get('values',{}).get(lang,'')); feature_slots=len(variant.get('feature_format_contract',{}).get('paragraph_indices',[21,23]))
    record={'schema_version':'1.3.19','variant_id':variant_id,'template':variant['template'],'template_sha256':variant['template_sha256'],'output':str(output),'output_sha256':sha256(output),'generated_at':datetime.now(timezone.utc).isoformat(),'fresh_clone':True,'source_led_performance_rows':source_rows is not None,'performance_table_topology':topology,'performance_extra_rows':len(extension_rows),'feature_extra_items':max(0,len(feature_values)-feature_slots),'hidden_fields':sorted(hidden_field_ids(mapping)),'hidden_paragraphs':getattr(edit,'hidden_paras',[]),'tail_blank_paragraphs_trimmed':getattr(edit,'tail_blank_count',0),'sample_fact_leaks':leaked,'normalization_model_status':mapping.get('normalized_model',{}).get('status','legacy-mapping'),'translation_source':mapping.get('normalized_model',{}).get('translation',{}).get('source','legacy-mapping'),'decision_ledger_entries':len(mapping.get('decision_ledger',mapping.get('normalized_model',{}).get('decision_ledger',[]))),'execution_log_file':execution_log_file or output.name+'.overwrite.log.json','ready_for_user_proofreading':not leaked,'customer_ready':False}
    dump(generation_path or output.with_suffix(output.suffix+'.generation.json'),record)
    if leaked: raise RuntimeError(f'sample facts leaked in {output.name}: {leaked}')

def write_variant(mapping, registry, variant_id, output, log_dir=None, generation_dir=None, artifact_root=None):
    output=Path(output)
    log_path=(Path(log_dir) / (output.name+'.overwrite.log.json')) if log_dir else output.with_name(output.name+'.overwrite.log.json')
    generation_path=(Path(generation_dir) / (output.name+'.generation.json')) if generation_dir else output.with_suffix(output.suffix+'.generation.json')
    log_path.parent.mkdir(parents=True,exist_ok=True); generation_path.parent.mkdir(parents=True,exist_ok=True)
    execution_log_file=log_path.name
    if artifact_root:
        try: execution_log_file=log_path.relative_to(Path(artifact_root)).as_posix()
        except ValueError: pass
    log={'schema_version':'1.0.0','status':'running','variant_id':variant_id,'output':str(output),'started_at':datetime.now(timezone.utc).isoformat(),'events':[]}
    def event(name, **details):
        log['events'].append({'at':datetime.now(timezone.utc).isoformat(),'event':name,**details})
        dump(log_path,log)
    dump(log_path,log)
    event('overwrite_started')
    try:
        _write_variant(mapping, registry, variant_id, output, event, generation_path, execution_log_file)
        event('leak_scan_passed')
        log['status']='completed'; log['finished_at']=datetime.now(timezone.utc).isoformat(); log['output_sha256']=sha256(output)
        dump(log_path,log)
    except Exception as exc:
        event('overwrite_failed', error_type=type(exc).__name__, error=str(exc))
        log['status']='failed'; log['finished_at']=datetime.now(timezone.utc).isoformat()
        dump(log_path,log)
        raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--log-dir',type=Path); ap.add_argument('--generation-dir',type=Path); ap.add_argument('--artifact-root',type=Path); ap.add_argument('--model',required=True); args=ap.parse_args()
    m=load(args.mapping); r=load(args.registry)
    if m.get('status')!='ready': raise SystemExit('mapping is blocked; no DOCX written')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    names={'TDS_CN_冠志模板':'TDS_CN_冠志','TDS_CN_国彩模板':'TDS_CN_国彩','TDS_EN_冠志模板':'TDS_EN_冠志','TDS_EN_国彩模板':'TDS_EN_国彩'}
    for vid,v in r['variants'].items():
        stem=names[vid]; write_variant(m,r,vid,args.output_dir/f'{args.model}_{stem}.docx',args.log_dir,args.generation_dir,args.artifact_root)
    print(f'docx_variants=4 output={args.output_dir}')
if __name__=='__main__': main()
