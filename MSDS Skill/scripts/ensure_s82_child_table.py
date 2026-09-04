#!/usr/bin/env python3
"""Install the approved Section 8.2 child control-parameter table.

This maintenance utility is intentionally narrow: it adds the child table to
the existing 8.2 engineering-controls row and removes one known accidental CN
placeholder appended to the EN ``Hand protection:`` label.  It never edits
the sequence/label column, parent table geometry, headers, footers, or product
facts.  The 8.2 parent row is marked non-splittable so WPS/Word keeps the
subtable together at a page boundary.  The child table starts with one header
row and one blank source-data slot; the generation whitelist may clone that
styled data row when verified source records require additional rows.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


# Word XML stores grid/tc widths in twentieths of a point (twips).  These are
# the established child-table widths observed in the prior approved outputs;
# python-docx exposes the same values as EMU when reading ``.w``.
# The child table lives inside the 8.2 writable value cell (6341 twips).
# Keep a small margin so WPS/Word does not clip the fourth column at the
# parent-cell boundary.  The prior v3.13 geometry overflowed that cell.
GRID_WIDTHS = [2400, 1100, 1100, 1600]
HEADERS = {
    "zh": ["物质", "依据", "类型", "数值"],
    "en": ["Substance", "Basis", "Type", "Value"],
}
S82_MARKERS = ("8.2", "工程控制", "Engineering controls")


def _set_attr(element, name, value):
    element.set(qn(f"w:{name}"), str(value))


def _set_cell_width(cell, width):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.insert(0, tc_w)
    _set_attr(tc_w, "w", width)
    _set_attr(tc_w, "type", "dxa")


def _set_text(cell, text, *, size=12):
    paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    run = paragraph.add_run(text)
    run.font.size = Pt(size)


def _remove_known_en_label_residual(document):
    """Remove the supplied EN template's accidental CN label suffix.

    This is a narrowly identified template defect, not a generic translation
    pass.  The first bold label run and its paragraph properties are retained;
    only the tab and the following placeholder runs are removed.
    """
    section8 = document.tables[7]
    row = section8.rows[3]
    cells = []
    seen = set()
    for cell in row.cells:
        key = hash(cell._tc)
        if key not in seen:
            seen.add(key)
            cells.append(cell)
    if len(cells) != 2:
        raise ValueError("Section 8.1 hand-protection row must keep two physical cells")
    paragraph = cells[0].paragraphs[0]
    if not paragraph.text.startswith("Hand protection"):
        raise ValueError("unexpected EN Section 8.1 hand-protection label")
    runs = paragraph.runs
    if len(runs) < 2:
        return
    runs[0].text = "Hand protection:"
    for run in runs[1:]:
        run._element.getparent().remove(run._element)


def _set_fixed_grid(table):
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.insert(0, tbl_w)
    _set_attr(tbl_w, "w", 0)
    _set_attr(tbl_w, "type", "auto")
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    _set_attr(layout, "type", "fixed")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in GRID_WIDTHS:
        col = OxmlElement("w:gridCol")
        _set_attr(col, "w", width)
        grid.append(col)
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        _set_attr(node, "val", "single")
        _set_attr(node, "sz", 4)
        _set_attr(node, "space", 0)
        _set_attr(node, "color", "auto")


def _set_row_cant_split(row):
    """Keep the 8.2 parent row and its nested child table together."""
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def _find_s82_cell(document):
    section8 = document.tables[7]
    for row in section8.rows:
        text = " ".join(cell.text for cell in row.cells)
        if "8.2" in text and ("工程控制" in text or "Engineering controls" in text):
            _set_row_cant_split(row)
            cells = []
            seen = set()
            for cell in row.cells:
                physical_key = hash(cell._tc)
                if physical_key not in seen:
                    seen.add(physical_key)
                    cells.append(cell)
            if len(cells) == 1:
                return cells[0]
            if len(cells) == 2:
                # The current CN/EN templates keep the sequence/label cell
                # separate from the writable value cell.  Add the child table
                # only to the latter; the locked first cell is never touched.
                return cells[1]
            raise ValueError("Section 8.2 must keep a two-cell parent row")
    raise ValueError("Section 8.2 engineering-controls row not found")


def ensure_child_table(document, language):
    if language not in HEADERS:
        raise ValueError(f"unsupported language: {language}")
    if language == "en":
        _remove_known_en_label_residual(document)
    cell = _find_s82_cell(document)
    if cell.tables:
        child = cell.tables[0]
        if len(child.columns) != 4 or [c.text for c in child.rows[0].cells] != HEADERS[language]:
            raise ValueError("existing Section 8.2 child table does not match approved language baseline")
        _set_fixed_grid(child)
        for row in child.rows:
            for index, item in enumerate(row.cells):
                _set_cell_width(item, GRID_WIDTHS[index])
                item.vertical_alignment = 1
        return child
    child = cell.add_table(rows=2, cols=4)
    child.style = "Table Grid"
    _set_fixed_grid(child)
    for row in child.rows:
        for index, item in enumerate(row.cells):
            _set_cell_width(item, GRID_WIDTHS[index])
            item.vertical_alignment = 1
    for cell_item, header in zip(child.rows[0].cells, HEADERS[language]):
        _set_text(cell_item, header)
    # The second row is a blank, formatted source-data slot.  No example
    # chemical, limit, method or value is copied into the maintained template.
    for cell_item in child.rows[1].cells:
        _set_text(cell_item, "")
    return child


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("language", choices=sorted(HEADERS))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    document = Document(str(args.docx))
    ensure_child_table(document, args.language)
    document.save(str(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
