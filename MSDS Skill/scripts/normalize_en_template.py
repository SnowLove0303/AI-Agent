#!/usr/bin/env python3
"""Historical EN-template migration utility.

This utility is retained for v3.10-era rollback and audit reproduction. It is
not part of the active v3.13 generation path. The active EN baseline is the
user-supplied template used byte-for-byte; it must not be normalized to the CN
geometry or have a Chinese-name row added. It does not translate or invent
product facts.
"""

from __future__ import annotations

import argparse
import copy
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}
W = "{" + W_NS + "}"


def _text(paragraph) -> str:
    return "".join(t.text or "" for t in paragraph.findall(".//w:t", NS))


def _set_paragraph_text(paragraph, value: str) -> None:
    ppr = paragraph.find("w:pPr", NS)
    first_run = paragraph.find("w:r", NS)
    run_pr = None
    if first_run is not None:
        existing_run_pr = first_run.find("w:rPr", NS)
        if existing_run_pr is not None:
            run_pr = copy.deepcopy(existing_run_pr)
    for child in list(paragraph):
        if child is not ppr:
            paragraph.remove(child)

    if not value:
        return

    run = ET.SubElement(paragraph, W + "r")
    if run_pr is not None:
        run.append(run_pr)
    t = ET.SubElement(run, W + "t")
    t.text = value
    if value[:1].isspace() or value[-1:].isspace():
        t.set("{" + XML_NS + "space}", "preserve")


def _set_cell_text(cell, value: str) -> None:
    paragraphs = cell.findall("./w:p", NS)
    if not paragraphs:
        paragraphs = [ET.SubElement(cell, W + "p")]
    _set_paragraph_text(paragraphs[0], value)
    for paragraph in paragraphs[1:]:
        cell.remove(paragraph)


def normalize(source: Path, output: Path) -> None:
    with zipfile.ZipFile(source, "r") as zin:
        document = ET.fromstring(zin.read("word/document.xml"))
        tables = document.findall(".//w:body/w:tbl", NS)
        if len(tables) != 16:
            raise ValueError(f"expected 16 body tables, found {len(tables)}")

        table1 = tables[0]
        rows = table1.findall("w:tr", NS)
        if len(rows) == 10:
            pass
        elif len(rows) == 9:
            # Row 2 is the existing 1.1 product-name row.  Its formatting is
            # the closest EN anchor; the CN baseline places the extra row at
            # the same position with an at-least height of 245 twips.
            inserted = copy.deepcopy(rows[1])
            tr_pr = inserted.find("w:trPr", NS)
            if tr_pr is None:
                tr_pr = ET.Element(W + "trPr")
                inserted.insert(0, tr_pr)
            tr_height = tr_pr.find("w:trHeight", NS)
            if tr_height is None:
                tr_height = ET.SubElement(tr_pr, W + "trHeight")
            tr_height.set(W + "val", "245")
            tr_height.set(W + "hRule", "atLeast")
            cells = inserted.findall("w:tc", NS)
            if len(cells) != 2:
                raise ValueError(f"Section 1.1 anchor row has {len(cells)} cells")
            _set_cell_text(cells[0], "Chinese name:")
            _set_cell_text(cells[1], "")
            # ``tblPr`` and ``tblGrid`` precede the row children, so the
            # Python list index is not the XML child insertion index.  Insert
            # immediately after the existing product-name row by locating the
            # row among the table's direct children.
            insert_at = list(table1).index(rows[1]) + 1
            table1.insert(insert_at, inserted)
        else:
            raise ValueError(f"unexpected Section 1 table row count: {len(rows)}")

        # Keep the output deterministic and validate the normalized geometry.
        normalized_rows = table1.findall("w:tr", NS)
        if len(normalized_rows) != 10:
            raise AssertionError("EN template normalization did not produce 10 Section 1 rows")

        # The supplied EN source has one accidental CN factual placeholder
        # appended to the locked ``Hand protection:`` label in Section 8.1.
        # Remove only that residual text from the maintained copy.  The source
        # file remains archived byte-for-byte; sequence/label formatting and
        # all other source geometry are preserved.
        section8 = tables[7]
        section8_rows = section8.findall("w:tr", NS)
        hand_row = section8_rows[3]
        hand_cells = hand_row.findall("w:tc", NS)
        if len(hand_cells) != 2:
            raise ValueError(f"Section 8.1 hand-protection row has {len(hand_cells)} cells")
        _set_cell_text(hand_cells[0], "Hand protection:")

        xml_bytes = ET.tostring(document, encoding="utf-8", xml_declaration=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=output.stem + ".", suffix=".docx", dir=output.parent, delete=False) as tmp:
            temp_path = Path(tmp.name)
        try:
            with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    payload = xml_bytes if item.filename == "word/document.xml" else zin.read(item.filename)
                    zout.writestr(item, payload)
            temp_path.replace(output)
        finally:
            if temp_path.exists():
                temp_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    normalize(args.source, args.output)
    print(output_summary(args.output))


def output_summary(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        tables = root.findall(".//w:body/w:tbl", NS)
        return f"normalized={path} tables={len(tables)} section1_rows={len(tables[0].findall('w:tr', NS))}"


if __name__ == "__main__":
    main()
