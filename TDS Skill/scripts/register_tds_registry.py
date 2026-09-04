from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from tds_common import ROOT, dump, feature_spacing_signature, norm, numbering_shape, sha256
ROWS_CN=['乳液外观','环氧当量（EEW）','固含量','PH值（25℃）','粘度（25℃）']
ROWS_EN=['Emulsion Appearance','Epoxy Equivalent Weight','Solids Content','pH Value (25°C)','Viscosity (25°C)']
def content_after_heading(doc, heading):
    index=next(i for i,p in enumerate(doc.paragraphs) if norm(p.text)==norm(heading))
    return next(i for i in range(index+1,len(doc.paragraphs)) if doc.paragraphs[i].text.strip())
def registry_for(path):
    d=Document(str(path)); en='_EN_' in path.name; rows=[]; labels=ROWS_EN if en else ROWS_CN
    section_names={'description':'【Characterization】' if en else '【产品描述】','supply':'【Supply Form】' if en else '【供应形式】','application':'【Application】' if en else '【应用】','storage':'【Storage】' if en else '【储存】'}
    title=next(i for i,p in enumerate(d.paragraphs[6:],6) if p.text.strip() and not p.text.strip().startswith('【'))
    description=content_after_heading(d,section_names['description']); supply=content_after_heading(d,section_names['supply']); application=content_after_heading(d,section_names['application']); storage=content_after_heading(d,section_names['storage'])
    feature_paragraphs=[d.paragraphs[i] for i in (21,23)]
    if any(numbering_shape(p) is not None for p in feature_paragraphs): raise ValueError(f'{path.name}: feature numbering must be disabled')
    if feature_spacing_signature(feature_paragraphs[0]) != feature_spacing_signature(feature_paragraphs[1]): raise ValueError(f'{path.name}: feature paragraph spacing is not equal')
    slots=[{'field_id':'product.title','kind':'paragraph','locator':{'paragraph_index':title}},{'field_id':'product.description','kind':'paragraph','locator':{'paragraph_index':description}},{'field_id':'product.supply_form','kind':'paragraph','locator':{'paragraph_index':supply}},{'field_id':'product.features','kind':'paragraph_list','locator':{'paragraph_indices':[21,23]}},{'field_id':'product.application','kind':'paragraph','locator':{'paragraph_index':application}},{'field_id':'product.storage','kind':'paragraph','locator':{'paragraph_index':storage}}]
    for idx,label in enumerate(labels,1):
        if norm(d.tables[0].rows[idx].cells[0].text)!=norm(label): raise ValueError(f'{path.name}: locked row {idx} mismatch')
        rows.append({'field_id':'performance.'+['appearance','eew','solid_content','ph_25c','viscosity_25c'][idx-1],'kind':'performance_row','label':label,'locator':{'table_index':0,'row_index':idx}})
    return {'template':str(path.relative_to(ROOT)),'template_sha256':sha256(path),'language':'en-US' if en else 'zh-CN','company':'guocai' if '国彩' in path.name else 'guanzhi','slots':slots+rows,'performance_table':{'header_row_index':0,'data_start_row_index':1,'source_led':True,'max_source_rows':100},'performance_extension':{'allowed':True,'row_template_index':5,'insert_after_row_index':5,'max_rows':100,'label_cell_allowed_for_new_rows':True},'feature_extension':{'allowed':True,'paragraph_template_index':23,'insert_after_paragraph_index':23,'max_items':100},'feature_format_contract':{'paragraph_indices':[21,23],'numbering':'disabled','equal_paragraph_spacing':True,'equal_character_spacing':True}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'mapping'/'template_field_registry.json'); args=ap.parse_args(); variants={p.stem:registry_for(p) for p in sorted((ROOT/'templates'/'active').glob('*.docx'))}; dump(args.output,{'schema_version':'1.0.0','variants':variants}); print(f'registry={args.output} variants={len(variants)}')
if __name__=='__main__': main()
