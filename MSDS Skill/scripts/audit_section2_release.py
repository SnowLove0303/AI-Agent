#!/usr/bin/env python3
"""Release audit for customer-facing Section 2 output."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document

from section2_ghs_policy import is_missing_section2_value, row_has_visual_content


def unique_cells(row):
    seen = set()
    out = []
    for cell in row.cells:
        key = hash(cell._tc)
        if key not in seen:
            seen.add(key)
            out.append(cell)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", type=Path)
    ap.add_argument("--require-pictogram", action="store_true")
    args = ap.parse_args()
    doc = Document(str(args.docx))
    table = doc.tables[1]
    errors = []
    all_text = "\n".join(cell.text for row in table.rows for cell in unique_cells(row))
    if "见2.4-2.6" in all_text or "See 2.4-2.6" in all_text:
        errors.append("customer-facing cross-reference remains in Section 2")

    labels = []
    pictogram_present = False
    old_to_new = {}
    next_item = 1
    for row in table.rows[1:]:
        cells = unique_cells(row)
        label = cells[0].text.strip() if cells else ""
        value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        if "GHS象形图" in label or re.search(r"ghs\s+pictogram", label, flags=re.IGNORECASE):
            pictogram_present = pictogram_present or row_has_visual_content(row)
        if not row_has_visual_content(row) and (not value or is_missing_section2_value(value)):
            errors.append(f"missing-data row remains: {label}")
        match = re.match(r"^\s*2\.(\d+)\b", label)
        if match:
            old = int(match.group(1))
            if old not in old_to_new:
                old_to_new[old] = next_item
                next_item += 1
            labels.append(f"2.{old_to_new[old]}")
    if args.require_pictogram and not pictogram_present:
        errors.append("required source pictogram is absent")
    # Compare unique transitions, while allowing repeated child rows.
    unique_labels = []
    for label in labels:
        if not unique_labels or unique_labels[-1] != label:
            unique_labels.append(label)
    if unique_labels != [f"2.{i}" for i in range(1, len(unique_labels) + 1)]:
        errors.append(f"Section 2 numbering is not continuous: {unique_labels}")
    print({"pass": not errors, "pictogram_present": pictogram_present, "labels": labels, "errors": errors})
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
