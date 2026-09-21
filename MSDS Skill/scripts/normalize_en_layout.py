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
import re

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from template_mutation_whitelist import (
    composite_prefix_text,
    composite_value_cell_index,
    english_body_cells as whitelist_english_body_cells,
    is_s15_locked_heading_row,
    unique_cells as whitelist_unique_cells,
)


EN_BODY_FONT = "Times New Roman"
# MSDS EN ordinary values and value tails are maintained at Times New Roman 12 pt.
# This constant is also used by the compatibility/no-template path; keeping it
# here prevents a caller from silently reintroducing the 10.5 pt patch style.
EN_BODY_SIZE = Pt(12)
EN_SUBLABEL_SIZE = Pt(9)
EN_FOOTER_SIZE = Pt(7.5)


def unique_cells(row):
    return whitelist_unique_cells(row)


def english_body_cells(table_index, row_index, row):
    return whitelist_english_body_cells(table_index, row_index, row)


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


def _approved_body_rpr(reference_document):
    """Return one maintained English body-value character-format exemplar.

    The active EN template contains legacy sample values with inconsistent
    character anchors.  A value's meaning must not determine its font, and a
    blank template value has no run to copy.  Select one non-bold Times New Roman body
    run from the maintained template and use only its ``w:rPr`` for inserted
    non-bold value text.  Paragraph properties remain destination-specific.
    """
    for table_index, table in enumerate(reference_document.tables[:16]):
        for row_index, row in enumerate(table.rows):
            if row_index == 0:
                continue
            if table_index == 14 and is_s15_locked_heading_row(row):
                continue
            cells = unique_cells(row)
            for cell_index, cell in enumerate(cells):
                if len(cells) > 1 and cell_index == 0:
                    continue
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if not run.text.strip() or run.bold:
                            continue
                        r_pr = run._r.rPr
                        if r_pr is None:
                            continue
                        r_fonts = r_pr.find(qn("w:rFonts"))
                        size = r_pr.find(qn("w:sz"))
                        if (r_fonts is not None
                                and r_fonts.get(qn("w:hAnsi")) == EN_BODY_FONT
                                and size is not None
                                and size.get(qn("w:val")) == "24"):
                            return deepcopy(r_pr)
    raise RuntimeError("active EN template has no approved Times New Roman 12pt body-value exemplar")


def _anchor_label(text: str) -> str:
    text = re.sub(r"\t.*$", "", text or "").strip()
    return re.sub(r"^\s*\d+\.\d+\s*", "", text)


def _reference_row(reference_table, output_table, table_index: int,
                   output_row, output_index: int):
    """Find the fresh-template row by semantic label after allowed omissions."""
    output_cells = unique_cells(output_row)
    if not output_cells:
        return None
    if table_index == 2 and output_index >= 4:
        return reference_table.rows[min(output_index, len(reference_table.rows) - 1)] \
            if len(reference_table.rows) > 4 else None
    if table_index == 7 and output_index >= 14:
        return reference_table.rows[min(output_index, len(reference_table.rows) - 1)] \
            if len(reference_table.rows) > 14 else None
    cell_count = len(output_cells)
    label = _anchor_label(output_cells[0].text)
    if cell_count == 1:
        output_one_cell_index = sum(
            len(unique_cells(row)) == 1
            for row in output_table.rows[:output_index + 1]
        ) - 1
        candidates = [row for row in reference_table.rows if len(unique_cells(row)) == 1]
        if candidates:
            return candidates[min(output_one_cell_index, len(candidates) - 1)]
    candidates = [
        row for row in reference_table.rows
        if len(unique_cells(row)) == cell_count
        and (cell_count == 1 or _anchor_label(unique_cells(row)[0].text) == label)
    ]
    if candidates:
        occurrence = sum(
            len(unique_cells(row)) == cell_count
            and _anchor_label(unique_cells(row)[0].text) == label
            for row in output_table.rows[:output_index + 1]
        ) - 1
        return candidates[min(occurrence, len(candidates) - 1)]
    if output_index < len(reference_table.rows):
        row = reference_table.rows[output_index]
        if len(unique_cells(row)) == cell_count:
            return row
    return None


def sync_en_template_text_format(document, template_path: str | Path, reference_document=None) -> None:
    """Restore EN layout and one body-value character format from the template.

    The document is already a fresh clone of ``template_path``.  This explicit
    pass is still required after text replacement because output helpers can
    create new runs and because row cloning can introduce a new physical row.
    It copies paragraph properties from the destination template row and one
    approved character-format exemplar to every non-bold value run.  It never
    changes text, table geometry, merges, widths or borders.  Extra cloned rows
    use the last template row as their paragraph-format anchor.
    """
    reference = reference_document or Document(str(template_path))
    body_rpr = _approved_body_rpr(reference)
    for table_index, table in enumerate(document.tables[:16]):
        if table_index >= len(reference.tables):
            break
        reference_table = reference.tables[table_index]
        for row_index, row in enumerate(table.rows):
            if table_index == 14 and is_s15_locked_heading_row(row):
                # Section 15 structural headings keep the exact fresh-clone
                # paragraph/run properties; they are not EN body values.
                continue
            ref_row = _reference_row(reference_table, table, table_index, row, row_index)
            if ref_row is None:
                continue
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
                body_cells = english_body_cells(table_index, row_index, row)
                is_body_cell = any(hash(cell._tc) == hash(body_cell._tc)
                                   for body_cell in body_cells)
                composite_index = composite_value_cell_index(row) \
                    if table_index == 1 else None
                if composite_index == cell_index:
                    # S2.8's route prefix shares a physical cell with the
                    # value tail in the maintained template.  Normalize only
                    # runs after the prefix; the prefix run properties are
                    # template-owned even when the prefix itself is non-bold.
                    prefix = composite_prefix_text(row)
                    cursor = 0
                    for paragraph_index, paragraph in enumerate(cell.paragraphs):
                        if paragraph_index >= len(ref_cell.paragraphs):
                            ref_paragraph = ref_cell.paragraphs[-1]
                        else:
                            ref_paragraph = ref_cell.paragraphs[paragraph_index]
                        # This cell is already a fresh clone of the matching
                        # S2.8 template row.  Its paragraph properties include
                        # row-specific border/merge presentation; replacing
                        # them with a label-occurrence anchor can select the
                        # wrong repeated child row.  Preserve the destination
                        # pPr and normalize only the writable value-tail RPR.
                        for run_index, run in enumerate(paragraph.runs):
                            text = run.text or ""
                            prefix_run = cursor < len(prefix)
                            if text and not prefix_run and not run.bold:
                                _replace_child(run._r, qn("w:rPr"), body_rpr)
                            elif text and prefix_run:
                                # Keep the route-prefix RPR exactly as cloned.
                                pass
                            else:
                                ref_runs = ref_paragraph.runs
                                ref_run = ref_runs[min(run_index, len(ref_runs) - 1)] \
                                    if ref_runs else None
                                ref_rpr = ref_run._r.rPr if ref_run is not None else None
                                _replace_child(run._r, qn("w:rPr"), ref_rpr)
                            cursor += len(text)
                    continue
                if len(cells) > 1 and cell_index == 0 and not is_body_cell:
                    continue
                ref_cell = ref_cells[min(cell_index, len(ref_cells) - 1)]
                for paragraph_index, paragraph in enumerate(cell.paragraphs):
                    if paragraph_index >= len(ref_cell.paragraphs):
                        ref_paragraph = ref_cell.paragraphs[-1]
                    else:
                        ref_paragraph = ref_cell.paragraphs[paragraph_index]
                    _replace_child(paragraph._p, qn("w:pPr"), ref_paragraph._p.pPr)
                    for run_index, run in enumerate(paragraph.runs):
                        if not run.text.strip():
                            continue
                        if is_body_cell and not run.bold:
                            _replace_child(run._r, qn("w:rPr"), body_rpr)
                            continue
                        ref_runs = ref_paragraph.runs
                        ref_run = ref_runs[min(run_index, len(ref_runs) - 1)] \
                            if ref_runs else None
                        ref_rpr = ref_run._r.rPr if ref_run is not None else None
                        _replace_child(run._r, qn("w:rPr"), ref_rpr)


def normalize_en_document(document, template_path: str | Path | None = None,
                          template_document=None) -> None:
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
        sync_en_template_text_format(document, template_path, template_document)
        return

    for table_index, table in enumerate(document.tables[:16]):
        for row_index, row in enumerate(table.rows):
            cells = unique_cells(row)
            if not cells:
                continue
            if table_index == 14 and is_s15_locked_heading_row(row):
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
            # approved geometry.  A small Times New Roman bold label is the stable way
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
