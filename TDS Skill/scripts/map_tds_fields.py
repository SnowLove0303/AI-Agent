from __future__ import annotations
import argparse
from pathlib import Path
from tds_common import dump,load,norm
ALIASES={norm(k):v for k,v in {
    '乳液外观':'performance.appearance', '外观':'performance.appearance', 'appearance':'performance.appearance',
    '环氧当量（EEW）':'performance.eew', 'epoxy equivalent weight (eew)':'performance.eew',
    '固含量':'performance.solid_content', '固体份含量':'performance.solid_content', 'solid content':'performance.solid_content',
    'ph值（25℃）':'performance.ph_25c', 'ph value (25°c)':'performance.ph_25c',
    '粘度（25℃）':'performance.viscosity_25c', 'viscosity (25°c)':'performance.viscosity_25c'
}.items()}
TEXT=['product.description','product.supply_form','product.features','product.application','product.storage']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cn',type=Path); ap.add_argument('--en',type=Path); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); paths=[p for p in (a.cn,a.en) if p]
    if not paths: raise SystemExit('one source facts file is required')
    fields={}; extra_rows=[]; blockers=[]; source_rows_by_lang={}
    for path in paths:
        s=load(path); lang=s['language']
        if s.get('title',{}).get('text'): fields.setdefault('product.title',{'field_id':'product.title','values':{},'sources':{}}); fields['product.title']['values'][lang]=s['title']['text']; fields['product.title']['sources'][lang]=s['title']
        for f in TEXT:
            section=s.get('sections',{}).get(f,{}); v=section.get('text','')
            if v: fields.setdefault(f,{'field_id':f,'values':{},'sources':{}}); fields[f]['values'][lang]=v; fields[f]['sources'][lang]=section
        source_rows=[]
        for row in s.get('performance_rows',[]):
            if row.get('source_column_count',4)>4:
                blockers.append({'kind':'template_capacity','source_location':row['source_location'],'reason':'source performance row has more columns than the maintained four-column TDS table'}); continue
            source_rows.append(row)
            f=ALIASES.get(norm(row['item']))
            if not f:
                continue
            item=fields.setdefault(f,{'field_id':f,'values':{},'sources':{}})
            if lang in item['values']: blockers.append({'kind':'conflict','field_id':f,'language':lang,'source_location':row['source_location']}); continue
            item['values'][lang]=row['value']; item['sources'][lang]=row; item['unit']=row['unit']; item['test_method']=row['test_method']
        source_rows_by_lang[lang]=source_rows
    row_count=max((len(x) for x in source_rows_by_lang.values()),default=0)
    if len({len(x) for x in source_rows_by_lang.values()})>1: blockers.append({'kind':'source_row_count_mismatch','reason':'CN and EN performance tables do not have the same number of rows'})
    performance_rows=[]
    for i in range(row_count):
        item={'field_id':f'performance.row.{i+1:03d}','label_values':{},'values':{},'unit_values':{},'test_method_values':{},'sources':{},'canonical_field_ids':{}}
        for lang,rows in source_rows_by_lang.items():
            if i>=len(rows): continue
            row=rows[i]; item['label_values'][lang]=row['item']; item['values'][lang]=row['value']; item['unit_values'][lang]=row.get('unit',''); item['test_method_values'][lang]=row.get('test_method',''); item['sources'][lang]=row
            if row.get('unit'): item['unit']=row['unit']
            if row.get('test_method'): item['test_method']=row['test_method']
            if ALIASES.get(norm(row['item'])): item['canonical_field_ids'][lang]=ALIASES[norm(row['item'])]
        performance_rows.append(item)
        if not item['canonical_field_ids']:
            extra_rows.append({k:v for k,v in item.items() if k!='canonical_field_ids'})
    registry=load(a.registry); required={x['field_id'] for v in registry['variants'].values() for x in v['slots']}
    for f in required: fields.setdefault(f,{'field_id':f,'values':{},'sources':{}})
    dump(a.output,{'schema_version':'1.2.0','source_facts':[str(p.resolve()) for p in paths],'mapped_fields':fields,'performance_rows':performance_rows,'performance_extra_rows':extra_rows,'blockers':blockers,'status':'blocked' if blockers else 'ready'}); print(f'mapping={a.output} fields={len(fields)} rows={len(performance_rows)} extra_rows={len(extra_rows)} blockers={len(blockers)}'); raise SystemExit(1 if blockers else 0)
if __name__=='__main__': main()
