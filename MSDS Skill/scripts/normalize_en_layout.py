"""Normalize the maintained English template's inherited layout quirks.

The supplied English template keeps the authoritative table geometry, but a
few paragraphs carry legacy Chinese-font placeholders, large indents and
justified alignment.  LibreOffice exposes those inherited properties as
visible word gaps and broken short labels.  This module changes only output
paragraph/run formatting; it never changes table rows, columns, merges or
content.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from template_mutation_whitelist import unique_cells as whitelist_unique_cells


EN_BODY_FONT = "Arial"
EN_BODY_SIZE = Pt(10.5)
EN_SUBLABEL_SIZE = Pt(9)
EN_FOOTER_SIZE = Pt(7.5)


def unique_cells(row):
    return whitelist_unique_cells(row)


def _set_run_font(run, name: str, size: Pt | None = None) -> None:
    """Set all four Word font slots so stale East Asia placeholders cannot win."""
    run.font.name = name
    if size is not None:
        run.font.size = size
    r_pr = run._r.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    for slot in ("ascii", "hAnsi", "eastAsia", "cs"):
        r_fonts.set(qn(f"w:{slot}"), name)


def _set_paragraph_alignment(paragraph, alignment=WD_ALIGN_PARAGRAPH.LEFT) -> None:
    paragraph.alignment = alignment
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.right_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0


def _normalize_runs(paragraph, size: Pt) -> None:
    for run in paragraph.runs:
        _set_run_font(run, EN_BODY_FONT, size)


def _replace_child(parent, tag, source):
    target = parent.find(tag)
    if target is not None:
        parent.remove(target)
    if source is not None:
        parent.insert(0, deepcopy(source))


def sync_en_template_text_format(document, template_path: str | Path) -> None:
    """Restore body paragraph/run properties from the maintained EN template.

    The document is already a fresh clone of ``template_path``.  This explicit
    pass is still required after text replacement because output helpers can
    create new runs and because row cloning can introduce a new physical row.
    It copies only paragraph and run properties, never text, table geometry,
    merges, widths or borders.  Extra cloned rows use the last template row as
    their formatting anchor.
    """
    reference = Document(str(template_path))
    for table_index, table in enumerate(document.tables[:16]):
        if table_index >= len(reference.tables):
            break
        reference_table = reference.tables[table_index]
        for row_index, row in enumerate(table.rows):
            ref_row = reference_table.rows[min(row_index, len(reference_table.rows) - 1)]
            seen = set()
            cells = unique_cells(row)
            ref_cells = unique_cells(ref_row)
            for cell_index, cell in enumerate(cells):
                key = id(cell._tc)
                if key in seen:
                    continue
                seen.add(key)
                if not ref_cells:
                    continue
                # The first physical cell is the template-owned sequence /
                # label cell.  It is intentionally excluded from this pass;
                # only value and explicitly writable subvalue cells may have
                # their properties synchronized.
                if len(cells) > 1 and cell_index == 0:
                    continue
                ref_cell = ref_cells[min(cell_index, len(ref_cells) - 1)]
                for paragraph_index, paragraph in enumerate(cell.paragraphs):
                    if paragraph_index >= len(ref_cell.paragraphs):
                        ref_paragraph = ref_cell.paragraphs[-1]
                    else:
                        ref_paragraph = ref_cell.paragraphs[paragraph_index]
                    _replace_child(paragraph._p, qn("w:pPr"), ref_paragraph._p.pPr)
                    if paragraph.runs:
                        ref_rpr = ref_paragraph.runs[0]._r.rPr if ref_paragraph.runs else None
                        _replace_child(paragraph.runs[0]._r, qn("w:rPr"), ref_rpr)


def normalize_en_document(document, template_path: str | Path | None = None) -> None:
    """Apply the controlled English output layout policy.

    When ``template_path`` is supplied, the maintained template is the
    formatting authority and its paragraph/run properties are restored
    exactly.  The legacy no-argument mode remains available for compatibility
    tests and isolated documents; production generation must pass the
    language-specific template path.

    The first heading is intentionally left without a literal ``1.`` because
    the maintained template supplies that number through Word numbering.  A
    literal number in the output would render as ``1. 1. Identification``.
    Other section headings retain the generator's explicit section number.
    """
    if template_path is not None:
        sync_en_template_text_format(document, template_path)
        return

    for table_index, table in enumerate(document.tables[:16]):
        for row_index, row in enumerate(table.rows):
            cells = unique_cells(row)
            if not cells:
                continue
            if row_index == 0:
                # Keep the template heading's automatic numbering and only
                # normalize its literal text font.
                for paragraph in cells[0].paragraphs:
                    _normalize_runs(paragraph, Pt(12))
                continue

            for cell_index, cell in enumerate(cells):
                is_value_cell = len(cells) == 1 or cell_index > 0
                if not is_value_cell:
                    # Sequence/label cell: formatting is owned by the
                    # template and must never be normalized here.
                    continue
                for paragraph in cell.paragraphs:
                    _set_paragraph_alignment(paragraph)
                    _normalize_runs(paragraph, EN_BODY_SIZE)

            # Section 11's sublabel column is deliberately narrow in the
            # approved geometry.  A small Arial bold label is the stable way
            # to keep the English labels on one line without changing the
            # grid widths or merge topology.
            if table_index == 10 and len(cells) >= 3 and cells[1].text.strip():
                sublabel = cells[1].text.strip()
                if sublabel.rstrip(":：") in {
                    "Oral",
                    "Inhalation",
                    "Dermal",
                    "Overall assessment",
                    "Fertility",
                    "Teratogenicity",
                    "In vitro genotoxicity",
                }:
                    for paragraph in cells[1].paragraphs:
                        _set_paragraph_alignment(paragraph, WD_ALIGN_PARAGRAPH.CENTER)
                        _normalize_runs(paragraph, EN_SUBLABEL_SIZE)

    for section in document.sections:
        for table in section.footer.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    for paragraph in cell.paragraphs:
                        _set_paragraph_alignment(paragraph)
                        _normalize_runs(paragraph, EN_FOOTER_SIZE)


__all__ = ["normalize_en_document", "sync_en_template_text_format"]
