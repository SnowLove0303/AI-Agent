"""TDS-only primitives. No MSDS imports or shared business rules."""
from __future__ import annotations
import hashlib, json, re, subprocess, zipfile
from copy import deepcopy
from pathlib import Path
from typing import Iterable
from docx.document import Document as DocumentObject
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
SOFFICE = Path(r"C:\Program Files\LibreOffice\program\soffice.com")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def load(path: Path) -> dict: return json.loads(path.read_text(encoding='utf-8'))
def norm(s: str) -> str: return re.sub(r'\s+','', (s or '').strip()).replace('（','(').replace('）',')').replace('：',':')

def text_sha256(value: str|None) -> str:
    return hashlib.sha256((value or '').encode('utf-8')).hexdigest()

def split_body_paragraphs(text: str) -> list[str]:
    raw = (text or '').strip()
    if not raw: return []
    if re.search(r'(?:^|\n)\s*\d+[.、]', raw):
        chunks = re.split(r'(?=(?:^|\n)\s*\d+[.、])', raw)
        res = []
        for c in chunks:
            c_strip = c.strip()
            if not c_strip: continue
            lines = [l.strip() for l in c_strip.splitlines() if l.strip()]
            merged = []
            for l in lines:
                if not merged:
                    merged.append(l)
                else:
                    prev = merged[-1]
                    if re.search(r'[\u4e00-\u9fff]$', prev):
                        merged[-1] = prev + l
                    elif re.search(r'[\u4e00-\u9fff\u3000-\u303f\uff01-\uff5e]$', prev):
                        merged[-1] = prev + l
                    else:
                        merged[-1] = prev + ' ' + l
            res.append(''.join(merged) if re.search(r'[\u4e00-\u9fff]', c_strip) else ' '.join(merged))
        return res

    raw_lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not raw_lines: return []
    res = []
    for l in raw_lines:
        if not res:
            res.append(l)
        else:
            prev = res[-1]
            if re.search(r'[。！？.!?]$', prev):
                res.append(l)
            else:
                if re.search(r'[\u4e00-\u9fff]$', prev):
                    res[-1] = prev + l
                else:
                    res[-1] = prev + ' ' + l
    return res

def application_lines(value: str|None) -> list[str]:
    return split_body_paragraphs(value)

def source_text_lines(value: str|None, field_id: str) -> list[str]:
    """Return the exact source lines after only registered presentation splits."""
    if field_id == 'product.features':
        lines=[line.strip() for line in (value or '').splitlines() if line.strip()]
        return [re.sub(r'^\s*\d+[.、]\s*','',line).strip() for line in lines]
    return split_body_paragraphs(value)

def _runtime_field(item: dict, lang: str) -> dict:
    """Use frozen source text for CN; use approved normalized text for EN."""
    if lang == 'zh-CN' and 'source_values' in item:
        return {**item, 'values': item.get('source_values', {})}
    if 'normalized_values' in item:
        return {**item, 'values': item.get('normalized_values', {})}
    return item

def source_value(item: dict, lang: str) -> str|None:
    values=item.get('source_values') if lang == 'zh-CN' and 'source_values' in item else item.get('normalized_values', item.get('values', {}))
    if not isinstance(values, dict) or lang not in values:
        return None
    return values.get(lang)

def source_fidelity_contract(fields: dict, performance_rows: list[dict], fact_paths: list[Path]) -> dict:
    field_hashes={}
    for field_id,item in fields.items():
        values=item.get('source_values',{}) or {}
        if values:
            field_hashes[field_id]={lang:text_sha256(value) for lang,value in values.items()}
    row_hashes={}
    for row in performance_rows:
        row_hashes[row['field_id']]={}
        for lang in set((row.get('source_label_values') or {})) | set((row.get('source_values') or {})):
            row_hashes[row['field_id']][lang]={
                'label':text_sha256((row.get('source_label_values') or {}).get(lang)),
                'value':text_sha256((row.get('source_values') or {}).get(lang)),
                'unit':text_sha256((row.get('source_unit_values') or {}).get(lang)),
                'test_method':text_sha256((row.get('source_test_method_values') or {}).get(lang)),
            }
    return {
        'schema_version':'1.0.0',
        'strict_language':'zh-CN',
        'source_facts_sha256':{str(path.resolve()):sha256(path) for path in fact_paths},
        'field_sha256':field_hashes,
        'performance_row_sha256':row_hashes,
    }

def source_fidelity_errors(mapping: dict, strict_language: str='zh-CN') -> list[str]:
    """Fail closed when a normalized value or its evidence hash diverges from source."""
    errors=[]; model=mapping.get('normalized_model') or {}
    fields=model.get('fields') or mapping.get('mapped_fields') or {}
    contract=mapping.get('source_fidelity') or {}
    for path_text,expected in (contract.get('source_facts_sha256') or {}).items():
        path=Path(path_text)
        if not path.is_file(): errors.append(f'source_facts_missing:{path}'); continue
        if sha256(path)!=expected: errors.append(f'source_facts_hash_mismatch:{path}')
    raw_fields=mapping.get('mapped_fields') or {}
    for field_id,item in fields.items():
        if not isinstance(item,dict): continue
        raw_item=raw_fields.get(field_id,{}) if model.get('fields') else item
        source_values=item.get('source_values') if 'source_values' in item else raw_item.get('source_values',raw_item.get('values',{}))
        normalized_values=item.get('normalized_values',item.get('values',{}))
        if not isinstance(source_values,dict) or strict_language not in source_values: continue
        source=source_values.get(strict_language)
        normalized=normalized_values.get(strict_language) if isinstance(normalized_values,dict) else None
        if normalized != source: errors.append(f'field_mutation:{strict_language}:{field_id}')
        expected_hash=(contract.get('field_sha256') or {}).get(field_id,{}).get(strict_language)
        if expected_hash and text_sha256(source)!=expected_hash: errors.append(f'field_hash_mismatch:{strict_language}:{field_id}')
    rows=model.get('performance_rows') if 'performance_rows' in model else mapping.get('performance_rows')
    raw_rows=mapping.get('performance_rows') or []
    for index,row in enumerate(rows or []):
        if not isinstance(row,dict): continue
        field_id=row.get('field_id','unknown')
        raw_row=raw_rows[index] if index<len(raw_rows) else row
        has_source_evidence=any(key in row for key in ('source_label_values','source_values','source_unit_values','source_test_method_values'))
        sources={
            'label':(row.get('source_label_values') if 'source_label_values' in row else raw_row.get('label_values',{})).get(strict_language),
            'value':(row.get('source_values') if 'source_values' in row else raw_row.get('values',{})).get(strict_language),
            'unit':(row.get('source_unit_values') if 'source_unit_values' in row else raw_row.get('unit_values',{})).get(strict_language),
            'test_method':(row.get('source_test_method_values') if 'source_test_method_values' in row else raw_row.get('test_method_values',{})).get(strict_language),
        }
        normalized={
            'label':(row.get('normalized_label_values') or row.get('label_values') or {}).get(strict_language),
            'value':(row.get('normalized_values') or row.get('values') or {}).get(strict_language),
            'unit':(row.get('normalized_unit_values') or row.get('unit_values') or {}).get(strict_language),
            'test_method':(row.get('normalized_test_method_values') or row.get('test_method_values') or {}).get(strict_language),
        }
        if model.get('performance_rows') is not None and not has_source_evidence and not raw_rows:
            errors.append(f'missing_source_evidence:{strict_language}:{field_id}')
        if any(sources[key] is not None and normalized[key] != sources[key] for key in sources):
            errors.append(f'performance_row_mutation:{strict_language}:{field_id}')
        expected_row=(contract.get('performance_row_sha256') or {}).get(field_id,{}).get(strict_language,{})
        for key,value in sources.items():
            if expected_row.get(key) and text_sha256(value)!=expected_row[key]:
                errors.append(f'performance_row_hash_mismatch:{strict_language}:{field_id}:{key}')
    return errors

def _source_field_item(mapping: dict, field_id: str) -> dict:
    model=mapping.get('normalized_model') or {}
    return (model.get('fields') or {}).get(field_id) or (mapping.get('mapped_fields') or {}).get(field_id) or {}

def _source_row_component(row: dict, component: str, lang: str) -> str:
    source_key = 'source_values' if component == 'value' else f'source_{component}_values'
    fallback_key = {'label': 'label_values', 'value': 'values', 'unit': 'unit_values', 'test_method': 'test_method_values'}[component]
    values = row.get(source_key) if source_key in row else row.get(fallback_key, {})
    return (values or {}).get(lang, '')

def source_output_fidelity_errors(doc, mapping: dict, registry: dict, variant_id: str) -> list[str]:
    """Compare generated CN text to source text after only allowed list splitting."""
    variant=registry['variants'][variant_id]
    if variant.get('language')!='zh-CN': return []
    errors=[]; hidden=set(hidden_field_ids(mapping)); headings=body_heading_texts(variant) | {'【性能指标】','Technical Data'}
    fields=mapping.get('normalized_model',{}).get('fields') or mapping.get('mapped_fields',{}) or {}
    slots={item['field_id']:item for item in variant.get('slots',[])}
    title_slot=slots.get('product.title',{}).get('locator',{}).get('paragraph_index')
    title_item=_source_field_item(mapping,'product.title')
    expected_title=(source_value(title_item,'zh-CN') or '').strip()
    if title_slot is None or title_slot>=len(doc.paragraphs):
        errors.append('title_output_slot_missing')
    elif doc.paragraphs[title_slot].text.strip()!=expected_title:
        errors.append('field_output_mismatch:zh-CN:product.title')
    for field_id in ('product.description','product.supply_form','product.features','product.application','product.storage'):
        if field_id in hidden: continue
        heading=SECTION_HEADINGS[field_id]['zh-CN']; hi=next((i for i,p in enumerate(doc.paragraphs) if p.text.strip()==heading),None)
        if hi is None:
            errors.append(f'section_heading_missing:{field_id}'); continue
        end=next((i for i in range(hi+1,len(doc.paragraphs)) if doc.paragraphs[i].text.strip() in headings),len(doc.paragraphs))
        actual=[p.text.strip() for p in doc.paragraphs[hi+1:end] if p.text.strip()]
        item=fields.get(field_id) or {}
        raw=source_value(item,'zh-CN')
        expected=source_text_lines(raw,field_id) or ['无数据']
        if actual!=expected: errors.append(f'field_output_mismatch:zh-CN:{field_id}')
    rows=(mapping.get('normalized_model',{}).get('performance_rows') if 'performance_rows' in mapping.get('normalized_model',{}) else mapping.get('performance_rows'))
    if rows is not None and doc.tables:
        start=variant.get('performance_table',{}).get('data_start_row_index',1); topology=performance_topology(mapping,variant)
        expected=[]
        for row in rows:
            values=[_source_row_component(row,'label','zh-CN') or '无数据',_source_row_component(row,'value','zh-CN') or '无数据']
            if topology in ('3-col','4-col'): values.append(_source_row_component(row,'unit','zh-CN'))
            if topology=='4-col': values.append(_source_row_component(row,'test_method','zh-CN'))
            expected.append(values)
        actual=[[cell.text for cell in row.cells[:len(expected[0])]] for row in doc.tables[0].rows[start:]] if expected else []
        if actual!=expected: errors.append('performance_output_mismatch:zh-CN')
    return errors

PERFORMANCE_TOPOLOGIES = {'2-col': 2, '3-col': 3, '4-col': 4}

def _localized_value(item: dict, keys: tuple[str, ...], lang: str|None) -> str:
    for key in keys:
        value = item.get(key, '')
        if isinstance(value, dict): value = value.get(lang or '', '')
        if value: return str(value).strip()
    return ''

def infer_performance_topology(rows=None, fields=None, lang: str|None=None) -> str:
    """Choose the narrowest table topology that preserves source data."""
    rows_provided = rows is not None
    rows = rows or []
    fields = fields or {}
    has_unit = any(_localized_value(row, ('normalized_unit_values','unit_values','unit'), lang) for row in rows)
    has_method = any(_localized_value(row, ('normalized_test_method_values','test_method_values','test_method'), lang) for row in rows)
    if not rows_provided and not has_unit and not has_method:
        has_unit = any(_localized_value(item, ('unit',), lang) for item in fields.values() if isinstance(item, dict))
        has_method = any(_localized_value(item, ('test_method',), lang) for item in fields.values() if isinstance(item, dict))
    return '4-col' if has_method else '3-col' if has_unit else '2-col'

def performance_topology(mapping: dict, variant: dict) -> str:
    lang = variant['language']
    model = mapping.get('normalized_model') or {}
    for source in (mapping.get('performance_table_topology'), model.get('performance_table_topology')):
        if isinstance(source, dict) and source.get(lang) in PERFORMANCE_TOPOLOGIES:
            return source[lang]
    rows = model.get('performance_rows')
    if rows is None: rows = mapping.get('performance_rows')
    if rows is None: rows = mapping.get('performance_extra_rows')
    topology = infer_performance_topology(rows, mapping.get('mapped_fields'), lang)
    return topology if topology in variant.get('performance_table', {}).get('allowed_topologies', ['4-col']) else variant.get('performance_table', {}).get('default_topology', '4-col')

def iter_blocks(parent: DocumentObject|_Cell):
    elm=parent.element.body if isinstance(parent,DocumentObject) else parent._tc
    for child in elm.iterchildren():
        if child.tag==qn('w:p'): yield Paragraph(child,parent)
        elif child.tag==qn('w:tbl'): yield Table(child,parent)

def iter_paragraphs(doc: DocumentObject) -> Iterable[Paragraph]:
    for block in iter_blocks(doc):
        if isinstance(block,Paragraph): yield block
        else:
            for row in block.rows:
                for cell in row.cells:
                    yield from iter_cell_paragraphs(cell)

def iter_cell_paragraphs(cell: _Cell):
    for block in iter_blocks(cell):
        if isinstance(block,Paragraph): yield block
        else:
            for row in block.rows:
                for nested in row.cells: yield from iter_cell_paragraphs(nested)

def _text_anchor_run(runs):
    """Choose the template run carrying the longest original text.

    The run is a formatting anchor only; all existing runs remain in place so
    replacement changes text nodes, not the template's run structure.
    """
    return max(runs, key=lambda run: len(run.text or ''), default=None)

def replace_paragraph(p: Paragraph, text: str) -> None:
    """Replace text while preserving every template paragraph/run property."""
    runs=list(p.runs)
    target=_text_anchor_run(runs)
    if target is None:
        p.add_run(text)
        return
    for run in runs:
        run.text=text if run is target else ''

def replace_feature_paragraph(p: Paragraph, text: str) -> None:
    """Replace feature text without rebuilding or restyling the paragraph."""
    replace_paragraph(p, text)

def replace_cell(cell: _Cell, text: str) -> None:
    if not cell.paragraphs: cell.add_paragraph(text)
    else:
        paragraph=cell.paragraphs[0]
        if text or paragraph.runs:
            replace_paragraph(paragraph,text)
        for p in cell.paragraphs[1:]: replace_paragraph(p,'')

def xml_attrs(element):
    if element is None: return None
    return {key.split('}')[-1]: value for key, value in element.attrib.items()}

def child_attrs(parent, tag):
    return xml_attrs(parent.find(qn(tag))) if parent is not None else None

def numbering_shape(paragraph: Paragraph):
    ppr=paragraph._p.pPr
    num=ppr.find(qn('w:numPr')) if ppr is not None else None
    if num is None: return None
    return {child.tag.split('}')[-1]: child.get(qn('w:val')) for child in num}

def run_style(run) -> dict:
    rpr=run._r.rPr
    return {'bold':run.bold,'italic':run.italic,'underline':str(run.underline) if run.underline is not None else None,'font':run.font.name,'size_pt':run.font.size.pt if run.font.size else None,'color':str(run.font.color.rgb) if run.font.color and run.font.color.rgb else None,'character_spacing':child_attrs(rpr,'w:spacing'),'kerning':child_attrs(rpr,'w:kern'),'position':child_attrs(rpr,'w:position')}

def paragraph_shape(paragraph: Paragraph) -> dict:
    pf=paragraph.paragraph_format; ppr=paragraph._p.pPr
    return {'style':paragraph.style.name if paragraph.style else None,'alignment':str(paragraph.alignment) if paragraph.alignment is not None else None,'numbering':numbering_shape(paragraph),'spacing':{'xml':child_attrs(ppr,'w:spacing'),'line_spacing':str(pf.line_spacing),'line_spacing_rule':str(pf.line_spacing_rule),'space_before':str(pf.space_before),'space_after':str(pf.space_after),'left_indent':str(pf.left_indent),'right_indent':str(pf.right_indent),'first_line_indent':str(pf.first_line_indent)},'runs':[run_style(r) for r in paragraph.runs]}

def feature_spacing_signature(paragraph: Paragraph) -> dict:
    shape=paragraph_shape(paragraph)
    return {'spacing':shape['spacing'],'run_spacing':[{k:r[k] for k in ('character_spacing','kerning','position')} for r in shape['runs']]}

def typography_spacing_contract(variant: dict) -> dict:
    return variant.get('standard_typography',{})

def _spacing_contract_values(paragraph: Paragraph) -> dict:
    pPr=paragraph._p.pPr
    spacing=pPr.find(qn('w:spacing')) if pPr is not None else None
    attrs=xml_attrs(spacing) or {}
    return {key:attrs.get(key, '0' if key in {'before','after'} else None) for key in ('before','after','line','lineRule')}

def typography_contract_errors(doc, variant: dict) -> list[str]:
    """Validate the spacing contract without asserting or changing fonts, indents or numbering."""
    contract=typography_spacing_contract(variant)
    if not contract: return ['standard_typography_missing']
    errors=[]
    lang=variant.get('language','zh-CN')
    title_spec=contract.get('product_title')
    if title_spec:
        title_slot=next((item for item in variant.get('slots',[]) if item.get('field_id')=='product.title'),None)
        title_index=(title_slot or {}).get('locator',{}).get('paragraph_index')
        if title_index is None or title_index>=len(doc.paragraphs):
            errors.append('title_alignment_missing')
        else:
            paragraph=doc.paragraphs[title_index]
            ppr=paragraph._p.pPr
            alignment=xml_attrs(ppr.find(qn('w:jc')) if ppr is not None else None) or {}
            if alignment.get('val')!=title_spec.get('alignment'):
                errors.append(f'title_alignment:{alignment.get("val")}!={title_spec.get("alignment")}')
            indent=xml_attrs(ppr.find(qn('w:ind')) if ppr is not None else None) or {}
            left_indent=indent.get('left')
            if left_indent not in (None,str(title_spec.get('left_indent_twips'))):
                errors.append(f'title_left_indent:{left_indent}!={title_spec.get("left_indent_twips")}')
    headings={SECTION_HEADINGS[field][lang] for field in HIDEABLE_FIELDS} | {OUTPUT_HEADINGS[field][lang] for field in HIDEABLE_FIELDS}
    heading_paragraphs=[p for p in doc.paragraphs if p.text.strip() in headings]
    heading_spec=contract.get('section_heading',{})
    for index,p in enumerate(heading_paragraphs):
        expected={'before':str(heading_spec.get('first_before_twips' if index==0 else 'before_twips')),'after':str(heading_spec.get('after_twips'))}
        actual=_spacing_contract_values(p)
        for key,value in expected.items():
            if actual.get(key)!=value: errors.append(f'heading_spacing:{index}:{key}:{actual.get(key)}!={value}')
    feature_spec=contract.get('feature_items',{})
    indices=variant.get('feature_format_contract',{}).get('paragraph_indices',[])
    for index in indices:
        if index>=len(doc.paragraphs): errors.append(f'feature_spacing_missing:{index}'); continue
        actual=_spacing_contract_values(doc.paragraphs[index])
        for key,config_key in (('before','before_twips'),('after','after_twips'),('line','line_twips'),('lineRule','line_rule')):
            expected=str(feature_spec.get(config_key))
            if actual.get(key)!=expected: errors.append(f'feature_spacing:{index}:{key}:{actual.get(key)}!={expected}')
    body_spec=contract.get('body_paragraphs',{})
    slots={x.get('field_id'):x for x in variant.get('slots',[])}
    for field_id in ('product.description','product.supply_form','product.application','product.storage'):
        locator=(slots.get(field_id) or {}).get('locator',{})
        index=locator.get('paragraph_index')
        if index is None or index>=len(doc.paragraphs): errors.append(f'body_spacing_missing:{field_id}'); continue
        actual=_spacing_contract_values(doc.paragraphs[index])
        for key,config_key in (('before','before_twips'),('after','after_twips'),('line','line_twips'),('lineRule','line_rule')):
            expected=str(body_spec.get(config_key))
            if actual.get(key)!=expected: errors.append(f'body_spacing:{field_id}:{key}:{actual.get(key)}!={expected}')
    return errors

def cell_shape(cell: _Cell) -> dict:
    p=cell._tc.tcPr; span=p.gridSpan.get(qn('w:val')) if p is not None and p.gridSpan is not None else None; vm=p.vMerge.get(qn('w:val')) if p is not None and p.vMerge is not None else None; w=p.tcW.get(qn('w:w')) if p is not None and p.tcW is not None else None
    return {'props':{'width':w,'grid_span':span,'vmerge':vm},'paragraphs':[{'text':x.text,**paragraph_shape(x)} for x in cell.paragraphs],'nested_tables':[table_snapshot(x) for x in cell.tables]}

def table_snapshot(table: Table) -> dict:
    grid=table._tbl.tblGrid
    return {'row_count':len(table.rows),'column_count':len(table.columns),'grid_widths':[x.get(qn('w:w')) for x in grid.gridCol_lst] if grid is not None else [],'rows':[{'cells':[{'text':c.text,'shape':cell_shape(c)} for c in row.cells]} for row in table.rows]}

def doc_snapshot(doc) -> dict:
    def ps(paras): return [{'text':p.text,'shape':paragraph_shape(p)} for p in paras]
    return {'sections':[{'page_width':s.page_width.twips,'page_height':s.page_height.twips,'top_margin':s.top_margin.twips,'bottom_margin':s.bottom_margin.twips,'left_margin':s.left_margin.twips,'right_margin':s.right_margin.twips,'header':ps(s.header.paragraphs),'footer':ps(s.footer.paragraphs)} for s in doc.sections],'paragraphs':ps(doc.paragraphs),'tables':[table_snapshot(t) for t in doc.tables]}

def package_inventory(path: Path) -> dict:
    with zipfile.ZipFile(path) as z: return {n:hashlib.sha256(z.read(n)).hexdigest() for n in sorted(z.namelist())}

def convert_legacy(source: Path, outdir: Path) -> Path:
    if source.suffix.lower()=='.docx': return source
    if source.suffix.lower()!='.doc': raise ValueError(f'unsupported source: {source}')
    outdir.mkdir(parents=True,exist_ok=True)
    r=subprocess.run([str(SOFFICE),'--headless','--convert-to','docx:Office Open XML Text','--outdir',str(outdir),str(source)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    out=outdir/(source.stem+'.docx')
    if r.returncode or not out.is_file(): raise RuntimeError(f'DOC conversion failed: {r.stdout}\n{r.stderr}')
    return out

def fresh_write(template: Path, output: Path, edit) -> None:
    from docx import Document
    doc=Document(str(template)); edit(doc)
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_name(output.name+'.edited.docx'); doc.save(str(tmp))
    with zipfile.ZipFile(template) as src, zipfile.ZipFile(tmp) as changed, zipfile.ZipFile(output,'w') as dst:
        xml=changed.read('word/document.xml')
        for info in src.infolist(): dst.writestr(info, xml if info.filename=='word/document.xml' else src.read(info.filename))
    tmp.unlink()

SECTION_HEADINGS={
 'product.description':{'zh-CN':'【产品描述】','en-US':'【Characterization】'},
 'product.supply_form':{'zh-CN':'【供应形式】','en-US':'【Supply Form】'},
 'product.features':{'zh-CN':'【产品特性】','en-US':'【Product features】'},
 'product.application':{'zh-CN':'【应用】','en-US':'【Application】'},
 'product.storage':{'zh-CN':'【储存】','en-US':'【Storage】'},
}
OUTPUT_HEADINGS={
 'product.description':{'zh-CN':'【产品描述】','en-US':'Product Description'},
 'product.supply_form':{'zh-CN':'【供应形式】','en-US':'Supply Form'},
 'product.features':{'zh-CN':'【产品特性】','en-US':'Product Features'},
 'product.application':{'zh-CN':'【应用】','en-US':'Application'},
 'product.storage':{'zh-CN':'【储存】','en-US':'Storage'},
}
HIDEABLE_FIELDS=list(SECTION_HEADINGS)
def hidden_field_ids(mapping):
    """Section fields the Agent approved for whole-section hiding (heading + body removed, no NO_DATA placeholder). Empty unless the normalized decision ledger carries decision=hide_no_source with needs_judgment resolved and both languages empty. product.title can never hide."""
    model=mapping.get('normalized_model') or {}
    fields=model.get('fields') or {}
    ledger={d.get('field_id'):d for d in model.get('decision_ledger',[]) if isinstance(d,dict)}
    hidden=[]
    for fid in HIDEABLE_FIELDS:
        d=ledger.get(fid)
        if not d or d.get('decision')!='hide_no_source' or d.get('needs_judgment',True): continue
        vals=(fields.get(fid) or {}).get('normalized_values',{}) or {}
        if vals.get('zh-CN') or vals.get('en-US'): continue
        hidden.append(fid)
    return hidden
FEATURE_NUM_ID='1'
FEATURE_NUMBER_START=480
FEATURE_TEXT_START=840
FEATURE_HANGING=360
def ensure_feature_numbering(paragraph: Paragraph, num_id: str|None=None) -> bool:
    """Attach auto numbering at schema-valid pPr position. Returns True when added."""
    from docx.oxml import OxmlElement
    pPr=paragraph._p.get_or_add_pPr()
    if pPr.find(qn('w:numPr')) is not None: return False
    numPr=OxmlElement('w:numPr')
    ilvl=OxmlElement('w:ilvl'); ilvl.set(qn('w:val'),'0')
    numId=OxmlElement('w:numId'); numId.set(qn('w:val'),num_id or FEATURE_NUM_ID)
    numPr.append(ilvl); numPr.append(numId)
    after={'w:suppressLineNumbers','w:pBdr','w:shd','w:tabs','w:suppressAutoHyphens','w:kinsoku','w:wordWrap','w:overflowPunct','w:topLinePunct','w:autoSpaceDE','w:autoSpaceDN','w:bidi','w:adjustRightInd','w:snapToGrid','w:spacing','w:ind','w:contextualSpacing','w:mirrorIndents','w:suppressOverlap','w:jc','w:textDirection','w:textAlignment','w:textboxTightWrap','w:outlineLvl','w:divId','w:cnfStyle','w:rPr','w:sectPr','w:pPrChange'}
    for child in pPr:
        if child.tag in after:
            child.addprevious(numPr); break
    else:
        pPr.append(numPr)
    return True

def _remove_ppr_child(pPr, tag):
    child=pPr.find(qn(tag))
    if child is not None: pPr.remove(child)

def feature_layout_signature(paragraph: Paragraph) -> dict:
    pPr=paragraph._p.pPr
    ind=pPr.find(qn('w:ind')) if pPr is not None else None
    tabs=pPr.find(qn('w:tabs')) if pPr is not None else None
    return {
        'ind': xml_attrs(ind),
        'tabs':[xml_attrs(tab) for tab in tabs] if tabs is not None else [],
    }

def normalize_feature_list_paragraph(paragraph: Paragraph, num_id: str|None=None) -> None:
    raise RuntimeError('template authority violation: feature paragraph formatting is immutable')

def clear_feature_empty_paragraph(paragraph: Paragraph) -> None:
    raise RuntimeError('template authority violation: blank paragraph formatting is immutable')

def slot_paragraph_lines(text: str) -> list:
    """Split a slot value into non-empty lines for template-paragraph writing. Blank lines never land on the page."""
    return [line.strip() for line in (text or '').splitlines() if line.strip()]

def hidden_block_indices(paragraphs, lang: str, slots: dict, hidden_ids) -> set|None:
    """Template-authority hiding rule shared by overwrite and audit: a hidden section loses its heading, its body paragraphs and its own adjacent blank separators (one leading, one trailing). Returns None when a heading cannot be located (fail closed)."""
    kill=set()
    for fid in hidden_ids:
        heads={SECTION_HEADINGS[fid][lang]}
        if lang=='en-US': heads.add(OUTPUT_HEADINGS[fid][lang])
        hi=next((i for i,p in enumerate(paragraphs) if p.text.strip() in heads),None)
        if hi is None: return None
        kill.add(hi)
        loc=slots[fid]['locator']
        idxs=loc['paragraph_indices'] if slots[fid]['kind']=='paragraph_list' else [loc['paragraph_index']]
        for j in idxs: kill.add(j)
        if hi-1>=0 and not paragraphs[hi-1].text.strip(): kill.add(hi-1)
        body_max=max([hi]+list(idxs))
        for i in range(hi+1,body_max):
            if not paragraphs[i].text.strip(): kill.add(i)
        nxt=body_max+1
        if nxt<len(paragraphs) and not paragraphs[nxt].text.strip(): kill.add(nxt)
    return kill

def body_heading_texts(variant: dict) -> set[str]:
    lang=variant['language']
    return {SECTION_HEADINGS[field][lang] for field in HIDEABLE_FIELDS} | {OUTPUT_HEADINGS[field][lang] for field in HIDEABLE_FIELDS}

def _compact_blank_paragraph(paragraph, line_twips: int) -> None:
    pPr=paragraph._p.get_or_add_pPr()
    spacing=pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing=OxmlElement('w:spacing'); pPr.append(spacing)
    spacing.set(qn('w:line'),str(line_twips)); spacing.set(qn('w:lineRule'),'exact')

def _compact_blank_snapshot(paragraph: dict, line_twips: int) -> None:
    spacing=paragraph.setdefault('shape',{}).setdefault('spacing',{})
    xml=dict(spacing.get('xml') or {})
    xml['line']=str(line_twips); xml['lineRule']='exact'
    spacing['xml']=xml
    spacing['line_spacing']=str(int(line_twips)*635)
    spacing['line_spacing_rule']='EXACTLY (4)'

def trim_body_blank_paragraphs(doc, variant: dict) -> int:
    """Remove body placeholders according to the registered section-gap policy."""
    policy=variant.get('body_blank_trim',{})
    if not policy.get('allowed',False): return 0
    paragraphs=list(doc.paragraphs); headings=body_heading_texts(variant)
    start=next((i for i,p in enumerate(paragraphs) if p.text.strip() in headings),None)
    if start is None: return 0
    removed=0; kept_gap=False
    separator_limit=int(policy.get('separator_paragraphs',policy.get('max_body_blank_paragraphs',0)))
    for i in range(len(paragraphs)-1,start-1,-1):
        if paragraphs[i].text.strip():
            kept_gap=False
            continue
        previous=next((paragraphs[j].text.strip() for j in range(i-1,start-1,-1) if paragraphs[j].text.strip()),'')
        following=next((paragraphs[j].text.strip() for j in range(i+1,len(paragraphs)) if paragraphs[j].text.strip()),'')
        keep=separator_limit>0 and bool(following in headings and (previous or i == start)) and not kept_gap
        if keep:
            _compact_blank_paragraph(paragraphs[i],int(policy.get('compact_line_twips',120)))
            kept_gap=True
        else:
            paragraphs[i]._p.getparent().remove(paragraphs[i]._p); removed+=1
    return removed

def trim_body_blank_snapshot(paragraphs: list[dict], variant: dict) -> list[dict]:
    """Mirror trim_body_blank_paragraphs for geometry audit snapshots."""
    policy=variant.get('body_blank_trim',{})
    if not policy.get('allowed',False): return paragraphs
    headings=body_heading_texts(variant)
    start=next((i for i,p in enumerate(paragraphs) if p.get('text','').strip() in headings),None)
    if start is None: return paragraphs
    kept=[]; kept_gap=False
    separator_limit=int(policy.get('separator_paragraphs',policy.get('max_body_blank_paragraphs',0)))
    for i,p in enumerate(paragraphs):
        if i<start or p.get('text','').strip():
            kept.append(p); kept_gap=False if p.get('text','').strip() else kept_gap
            continue
        previous=next((paragraphs[j].get('text','').strip() for j in range(i-1,start-1,-1) if paragraphs[j].get('text','').strip()),'')
        following=next((paragraphs[j].get('text','').strip() for j in range(i+1,len(paragraphs)) if paragraphs[j].get('text','').strip()),'')
        keep=separator_limit>0 and bool(following in headings and (previous or i == start)) and not kept_gap
        if keep:
            _compact_blank_snapshot(p,int(policy.get('compact_line_twips',120))); kept.append(p); kept_gap=True
    return kept

def body_blank_count(doc, variant: dict) -> int:
    headings=body_heading_texts(variant); start=next((i for i,p in enumerate(doc.paragraphs) if p.text.strip() in headings),None)
    return 0 if start is None else sum(1 for p in doc.paragraphs[start:] if not p.text.strip())

def inter_section_gap_errors(doc, variant: dict) -> list[str]:
    """Check that section transitions have no unregistered blank separator."""
    policy=variant.get('inter_section_spacing',{})
    if not policy: return []
    headings=body_heading_texts(variant)
    start=next((i for i,p in enumerate(doc.paragraphs) if p.text.strip() in headings),None)
    if start is None: return ['section_heading_start_missing']
    errors=[]; expected=str(policy.get('heading_before_twips',160))
    for i in range(start+1,len(doc.paragraphs)):
        if doc.paragraphs[i].text.strip() not in headings: continue
        j=i-1
        while j>=start and not doc.paragraphs[j].text.strip():
            errors.append(f'blank_separator_before_heading:{i}'); j-=1
        ppr=doc.paragraphs[i]._p.pPr; spacing=ppr.find(qn('w:spacing')) if ppr is not None else None
        actual=(xml_attrs(spacing) or {}).get('before')
        if actual!=expected: errors.append(f'heading_before:{i}:{actual}!={expected}')
    return errors

def vertical_budget_profile(variant: dict, total_items: int) -> dict|None:
    policy = variant.get('vertical_budget', variant.get('english_vertical_budget', {}))
    if not bool(policy.get('allowed', False)):
        return None
    threshold = int(policy.get('threshold_total_items', 16))
    if total_items < threshold:
        return None
    levels = policy.get('levels') or [
        {'name': 'level-2', 'max_total_items': None, 'heading_before_twips': 80,
         'heading_after_twips': 40, 'item_after_twips': 20, 'line_twips': 260,
         'line_rule': 'exact'}
    ]
    for level in levels:
        maximum = level.get('max_total_items')
        if maximum is None or total_items <= int(maximum):
            return level
    return levels[-1]

def vertical_budget_enabled(variant: dict, total_items: int) -> bool:
    policy = variant.get('vertical_budget', variant.get('english_vertical_budget', {}))
    threshold = int(policy.get('threshold_total_items', 12))
    return bool(policy.get('allowed', False)) and total_items >= threshold

def vertical_budget_level(variant: dict, total_items: int) -> int:
    if not vertical_budget_enabled(variant, total_items):
        return 0
    return 1

def apply_vertical_budget(doc, variant: dict, total_items: int) -> bool:
    lvl = vertical_budget_level(variant, total_items)
    if lvl == 0:
        return False
    headings = body_heading_texts(variant)
    start = next((i for i, p in enumerate(doc.paragraphs) if p.text.strip() in headings), None)
    if start is None:
        return False
    first_h = True
    for paragraph in doc.paragraphs[start:]:
        text = paragraph.text.strip()
        if not text:
            continue
        pPr = paragraph._p.get_or_add_pPr()
        spacing = pPr.find(qn('w:spacing'))
        if spacing is None:
            spacing = OxmlElement('w:spacing')
            pPr.append(spacing)
        if text in headings:
            before = '60' if first_h else '80'
            after = '40'
            spacing.set(qn('w:before'), before)
            spacing.set(qn('w:after'), after)
            first_h = False
        else:
            line = '280' if lvl == 1 else '260'
            after = '30' if lvl == 1 else '20'
            spacing.set(qn('w:line'), line)
            spacing.set(qn('w:lineRule'), 'exact')
            spacing.set(qn('w:after'), after)
    return True

def apply_vertical_budget_snapshot(paragraphs: list[dict], variant: dict, total_items: int) -> None:
    lvl = vertical_budget_level(variant, total_items)
    if lvl == 0:
        return
    headings = body_heading_texts(variant)
    start = next((i for i, p in enumerate(paragraphs) if p.get('text', '').strip() in headings), None)
    if start is None:
        return
    first_h = True
    for paragraph in paragraphs[start:]:
        text = paragraph.get('text', '').strip()
        if not text:
            continue
        spacing = paragraph.setdefault('shape', {}).setdefault('spacing', {})
        xml = dict(spacing.get('xml') or {})
        if text in headings:
            before = '60' if first_h else '80'
            after = '40'
            xml['before'] = before
            xml['after'] = after
            spacing['xml'] = xml
            spacing['space_before'] = str(int(before) * 635)
            spacing['space_after'] = str(int(after) * 635)
            first_h = False
        else:
            line = '280' if lvl == 1 else '260'
            after = '30' if lvl == 1 else '20'
            xml['line'] = line
            xml['lineRule'] = 'exact'
            xml['after'] = after
            spacing['xml'] = xml
            spacing['line_spacing'] = str(int(line) * 635)
            spacing['line_spacing_rule'] = 'EXACTLY (4)'
            spacing['space_after'] = str(int(after) * 635)
