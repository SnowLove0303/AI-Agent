from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from tds_common import ROOT, dump, norm, sha256
ROWS=['乳液外观','环氧当量（EEW）','固含量','PH值（25℃）','粘度（25℃）']
def registry_for(path):
    d=Document(str(path)); en='_EN_' in path.name; storage=31 if en else 32; rows=[]
    slots=[{'field_id':'product.title','kind':'paragraph','locator':{'paragraph_index':7}},{'field_id':'product.description','kind':'paragraph','locator':{'paragraph_index':11}},{'field_id':'product.supply_form','kind':'paragraph','locator':{'paragraph_index':14}},{'field_id':'product.features','kind':'paragraph_list','locator':{'paragraph_indices':[21,23]}},{'field_id':'product.application','kind':'paragraph','locator':{'paragraph_index':27}},{'field_id':'product.storage','kind':'paragraph','locator':{'paragraph_index':storage}}]
    for idx,label in enumerate(ROWS,1):
        if norm(d.tables[0].rows[idx].cells[0].text)!=norm(label): raise ValueError(f'{path.name}: locked row {idx} mismatch')
        rows.append({'field_id':'performance.'+['appearance','eew','solid_content','ph_25c','viscosity_25c'][idx-1],'kind':'performance_row','label':label,'locator':{'table_index':0,'row_index':idx}})
    return {'template':str(path.relative_to(ROOT)),'template_sha256':sha256(path),'language':'en-US' if en else 'zh-CN','company':'guocai' if '国彩' in path.name else 'guanzhi','slots':slots+rows,'performance_extension':{'allowed':True,'row_template_index':5,'insert_after_row_index':5,'max_rows':100,'label_cell_allowed_for_new_rows':True},'feature_extension':{'allowed':True,'paragraph_template_index':23,'insert_after_paragraph_index':23,'max_items':100}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'mapping'/'template_field_registry.json'); args=ap.parse_args(); variants={p.stem:registry_for(p) for p in sorted((ROOT/'templates'/'active').glob('*.docx'))}; dump(args.output,{'schema_version':'1.0.0','variants':variants}); print(f'registry={args.output} variants={len(variants)}')
if __name__=='__main__': main()
