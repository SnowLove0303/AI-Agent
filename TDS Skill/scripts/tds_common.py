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

def replace_paragraph(p: Paragraph, text: str) -> None:
    runs=list(p.runs)
    if not runs: p.add_run(text); return
    runs[0].text=text
    for run in runs[1:]: run.text=''

def replace_cell(cell: _Cell, text: str) -> None:
    if not cell.paragraphs: cell.add_paragraph(text)
    else:
        replace_paragraph(cell.paragraphs[0],text)
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
    tmp=output.with_name(output.name+'.edited.docx'); doc.save(str(tmp)); output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(template) as src, zipfile.ZipFile(tmp) as changed, zipfile.ZipFile(output,'w') as dst:
        xml=changed.read('word/document.xml')
        for info in src.infolist(): dst.writestr(info, xml if info.filename=='word/document.xml' else src.read(info.filename))
    tmp.unlink()
