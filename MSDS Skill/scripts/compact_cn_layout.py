#!/usr/bin/env python3
"""Apply the CN PDF-compatible compact layout after content is written.

The uploaded reference PDF was produced by a WPS/Word-compatible layout
engine.  LibreOffice interprets the template's inherited 12 pt / 1.25-line
body formatting more loosely, causing CN exports to grow from roughly 9 pages
to 16-17 pages.  This controlled post-write pass changes only CN table-body
layout; it does not rebuild tables, change cell geometry, or alter facts.
"""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


def unique_cells(row):
    seen = set()
    cells = []
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            cells.append(cell)
    return cells


def compact_table_body(document) -> None:
    """Compact table paragraphs while retaining template indentation and runs."""
    for table in document.tables:
        for row in table.rows:
            for cell in unique_cells(row):
                for paragraph in cell.paragraphs:
                    locked_label = any(
                        run.bold and run.text.strip() for run in paragraph.runs
                    )
                    # Locked template label paragraphs retain their original
                    # pPr.  Their adjacent value paragraphs receive the
                    # compact spacing that controls the visual density.
                    if not locked_label:
                        paragraph.paragraph_format.space_before = Pt(0)
                        paragraph.paragraph_format.space_after = Pt(0)
                        paragraph.paragraph_format.line_spacing = 1.0
                    for run in paragraph.runs:
                        run.font.size = Pt(10)


def normalize_footer(document) -> None:
    """Keep the revision date on one footer line under LibreOffice.

    The inherited character-based indent affects both language variants, so
    this footer-only normalization is safe for CN and EN outputs alike.
    """
    for section in document.sections:
        for table in section.footer.tables:
            if not table.rows:
                continue
            cells = unique_cells(table.rows[0])
            if len(cells) < 2:
                continue
            paragraph = cells[1].paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            paragraph.paragraph_format.left_indent = Pt(0)
            paragraph.paragraph_format.right_indent = Pt(0)
            paragraph.paragraph_format.first_line_indent = Pt(0)
            # python-docx writes firstLine=0 but does not remove the
            # inherited firstLineChars attribute. LibreOffice still honors
            # that character-based indent and renders the first character of
            # the date on a separate line, so remove both legacy attributes.
            p_pr = paragraph._p.get_or_add_pPr()
            ind = p_pr.find(qn("w:ind"))
            if ind is not None:
                ind.attrib.pop(qn("w:firstLineChars"), None)
                ind.attrib.pop(qn("w:firstLine"), None)
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0


def keep_final_information_block_together(document) -> None:
    """Avoid an orphaned final line in Section 16 after compaction."""
    if len(document.tables) < 16 or len(document.tables[15].rows) < 2:
        return
    tr_pr = document.tables[15].rows[1]._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def compact_cn_document(document) -> None:
    compact_table_body(document)
    normalize_footer(document)
    keep_final_information_block_together(document)


__all__ = ["compact_cn_document", "normalize_footer"]
