#!/usr/bin/env python3
"""Create the reviewed active English MSDS template baseline.

The supplied English template is kept as an immutable source record.  This
tool makes only maintainer-approved text corrections in a copy; it does not
change table geometry, merges, widths, row counts, or locked formatting
boundaries.  Runtime overwrite code must continue to use the active copy as
its structure authority.
"""
from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


HEADING_REPLACEMENTS = {
    "Identification": "Identification of the substance/mixture and of the company/undertaking",
    "6.Measures for accidental leakage": "6. Accidental release measures",
    "7.Operation and storage": "7. Handling and storage",
    "11.Toxicity information": "11. Toxicological information",
    "14.Transportation information": "14. Transport information",
}

PARAGRAPH_REPLACEMENTS = {
    " 物料安全数据表": " SAFETY DATA SHEET",
    "Version：V1.0": "Version: 1.0",
}

CELL_REPLACEMENTS = {
    "6.1  Firefighting precautions\nprotective equipment：": (
        "Personal precautions, protective equipment and",
        "emergency procedures:",
    ),
}

HEALTH_HAZARD_PREFIX_REPLACEMENTS = {
    "吸入：": "Inhalation:",
    "食入：": "Ingestion:",
    "皮肤：": "Skin:",
    "眼睛：": "Eyes:",
    "症状和体征：": "Signs and symptoms:",
}


def _write_text_preserving_first_run(paragraph, text: str) -> None:
    first_rpr = None
    for run in paragraph.runs:
        if run._r.rPr is not None:
            first_rpr = copy.deepcopy(run._r.rPr)
            break
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    run = paragraph._p.makeelement(qn("w:r"), {})
    if first_rpr is not None:
        run.append(first_rpr)
    for index, line in enumerate(str(text).split("\n")):
        if index:
            run.append(paragraph._p.makeelement(qn("w:br"), {}))
        text_node = paragraph._p.makeelement(qn("w:t"), {})
        text_node.text = line
        if line and (line[0].isspace() or line[-1].isspace()):
            text_node.set(qn("xml:space"), "preserve")
        run.append(text_node)
    paragraph._p.append(run)


def _unique_cells(row):
    seen = set()
    cells = []
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            cells.append(cell)
    return cells


def _set_bold(run) -> None:
    """Make a maintainer-controlled route prefix use the bold prototype."""
    r_pr = run._r.get_or_add_rPr()
    for tag in (qn("w:b"), qn("w:bCs")):
        for node in list(r_pr.iter(tag)):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
    r_pr.append(OxmlElement("w:b"))


def _rewrite_paragraph(paragraph, *, is_heading: bool = False) -> bool:
    text = paragraph.text
    replacement = PARAGRAPH_REPLACEMENTS.get(text)
    if replacement is not None and replacement != text:
        _write_text_preserving_first_run(paragraph, replacement)
        return True
    if is_heading and text in HEADING_REPLACEMENTS:
        replacement = HEADING_REPLACEMENTS[text]
        runs = [run for run in paragraph.runs if run.text]
        if not runs:
            _write_text_preserving_first_run(paragraph, replacement)
            return True
        prefix = re.match(r"^(\s*\d+\.)", text)
        if prefix and len(runs) > 1:
            runs[0].text = prefix.group(1)
            runs[-1].text = replacement[len(prefix.group(1)):]
            for run in runs[1:-1]:
                run.text = ""
        else:
            runs[0].text = replacement
            for run in runs[1:]:
                run.text = ""
        return True
    changed = False
    for run in paragraph.runs:
        if "：" in run.text and not re.search(r"[\u4e00-\u9fff]", run.text):
            run.text = run.text.replace("：", ": ")
            changed = True
    return changed


def _rewrite_cell(cell) -> int:
    full_text = "\n".join(paragraph.text for paragraph in cell.paragraphs)
    route_replacement = HEALTH_HAZARD_PREFIX_REPLACEMENTS.get(full_text)
    if route_replacement is not None:
        paragraph = cell.paragraphs[0]
        runs = [run for run in paragraph.runs if run.text]
        if runs:
            runs[0].text = route_replacement
            _set_bold(runs[0])
            for run in runs[1:]:
                run.text = ""
        else:
            _write_text_preserving_first_run(paragraph, route_replacement)
            _set_bold(paragraph.runs[0])
        return 1
    replacement = CELL_REPLACEMENTS.get(full_text)
    if replacement is not None:
        for paragraph, text in zip(cell.paragraphs, replacement):
            runs = [run for run in paragraph.runs if run.text]
            if runs:
                runs[-1].text = text
                for run in runs[:-1]:
                    run.text = run.text if re.match(r"^\s*\d", run.text) else run.text
            else:
                _write_text_preserving_first_run(paragraph, text)
        return 1
    if full_text == "Hand protection：\t喷涂过程中要求有呼吸防护设备。":
        paragraph = cell.paragraphs[0]
        runs = [run for run in paragraph.runs if run.text]
        if runs:
            runs[0].text = "Hand protection:"
            for run in runs[1:]:
                run.text = ""
        else:
            _write_text_preserving_first_run(paragraph, "Hand protection:")
        return 1
    return 0


def _rewrite_document(document: Document) -> int:
    changed = 0
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            for cell in _unique_cells(row):
                cell_changed = _rewrite_cell(cell)
                changed += cell_changed
                if cell_changed:
                    # The cell-level replacement owns all of its paragraphs.
                    continue
                for paragraph in cell.paragraphs:
                    changed += _rewrite_paragraph(
                        paragraph,
                        is_heading=(row_index == 0 and len(cell.paragraphs) == 1),
                    )
    for section in document.sections:
        for container in (section.header, section.footer):
            for paragraph in container.paragraphs:
                changed += _rewrite_paragraph(paragraph)
            for table in container.tables:
                for row in table.rows:
                    for cell in _unique_cells(row):
                        for paragraph in cell.paragraphs:
                            changed += _rewrite_paragraph(paragraph)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = Document(str(args.source))
    changed = _rewrite_document(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(args.output))
    print(f"remediated_paragraphs={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
