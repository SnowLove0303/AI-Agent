from __future__ import annotations
import argparse
from pathlib import Path
from tds_common import dump,load,norm
ALIASES={'乳液外观':'performance.appearance','appearance':'performance.appearance','环氧当量（EEW）':'performance.eew','epoxy equivalent weight (eew)':'performance.eew','固含量':'performance.solid_content','solid content':'performance.solid_content','ph值（25℃）':'performance.ph_25c','ph value (25°c)':'performance.ph_25c','粘度（25℃）':'performance.viscosity_25c','viscosity (25°c)':'performance.viscosity_25c'}
TEXT=['product.description','product.supply_form','product.features','product.application','product.storage']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cn',type=Path); ap.add_argument('--en',type=Path); ap.add_argument('--registry',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); paths=[p for p in (a.cn,a.en) if p]
    if not paths: raise SystemExit('one source facts file is required')
    fields={}; extra_rows=[]; blockers=[]
    for path in paths:
        s=load(path); lang=s['language']
        if s.get('title',{}).get('text'): fields.setdefault('product.title',{'field_id':'product.title','values':{},'sources':{}}); fields['product.title']['values'][lang]=s['title']['text']; fields['product.title']['sources'][lang]=s['title']
        for f in TEXT:
            section=s.get('sections',{}).get(f,{}); v=section.get('text','')
            if v: fields.setdefault(f,{'field_id':f,'values':{},'sources':{}}); fields[f]['values'][lang]=v; fields[f]['sources'][lang]=section
        for row in s.get('performance_rows',[]):
            if row.get('source_column_count',4)>4:
                blockers.append({'kind':'template_capacity','source_location':row['source_location'],'reason':'source performance row has more columns than the maintained four-column TDS table'}); continue
            f=ALIASES.get(norm(row['item']))
            if not f:
                key=next((x for x in extra_rows if norm(x['label_values'].get(lang,''))==norm(row['item'])),None)
                if key is None:
                    ordinal=sum(1 for x in extra_rows if lang in x['label_values'])
                    candidate=extra_rows[ordinal] if ordinal<len(extra_rows) else None
                    key=candidate if candidate is not None and lang not in candidate['label_values'] else None
                if key is None:
                    key={'field_id':f'performance.extra.{len(extra_rows)+1:03d}','label_values':{},'values':{},'sources':{}}; extra_rows.append(key)
                if lang in key['values']: blockers.append({'kind':'conflict','field_id':key['field_id'],'language':lang,'source_location':row['source_location']}); continue
                key['label_values'][lang]=row['item']; key['values'][lang]=row['value']; key['sources'][lang]=row; key['unit']=row['unit']; key['test_method']=row['test_method']; continue
            item=fields.setdefault(f,{'field_id':f,'values':{},'sources':{}})
            if lang in item['values']: blockers.append({'kind':'conflict','field_id':f,'language':lang,'source_location':row['source_location']}); continue
            item['values'][lang]=row['value']; item['sources'][lang]=row; item['unit']=row['unit']; item['test_method']=row['test_method']
    registry=load(a.registry); required={x['field_id'] for v in registry['variants'].values() for x in v['slots']}
    for f in required: fields.setdefault(f,{'field_id':f,'values':{},'sources':{}})
    dump(a.output,{'schema_version':'1.1.0','source_facts':[str(p.resolve()) for p in paths],'mapped_fields':fields,'performance_extra_rows':extra_rows,'blockers':blockers,'status':'blocked' if blockers else 'ready'}); print(f'mapping={a.output} fields={len(fields)} extra_rows={len(extra_rows)} blockers={len(blockers)}'); raise SystemExit(1 if blockers else 0)
if __name__=='__main__': main()
