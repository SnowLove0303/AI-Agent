"""TDS-only primitives. No MSDS imports or shared business rules."""
from __future__ import annotations
import hashlib, json, re, subprocess, zipfile
from copy import deepcopy
from pathlib import Path
from typing import Iterable
from docx.document import Document as DocumentObject
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
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
