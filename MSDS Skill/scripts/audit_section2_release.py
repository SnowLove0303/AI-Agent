#!/usr/bin/env python3
"""Release audit for customer-facing Section 2 output."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from section2_ghs_policy import (
    has_component_ghs_context,
    is_explicit_other_hazards_row,
    is_missing_section2_value,
    row_has_visual_content,
)
from section2_hp_policy import (
    precautionary_group_key,
)


def unique_cells(row):
    seen = set()
    out = []
    for cell in row.cells:
        key = hash(cell._tc)
        if key not in seen:
            seen.add(key)
            out.append(cell)
    return out


def _precautionary_value(table) -> str:
    for row in table.rows[1:]:
        cells = unique_cells(row)
        label = cells[0].text.strip() if cells else ""
        if re.search(r"(?:防范说明|precautionary\s+statements)", label, re.I):
            return "\n".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
    return ""


def audit_value_cell_typography(docx, language: str = "zh") -> list[str]:
    """Audit every value cell across Section 2 to guarantee 12.0 pt typography and consistent fonts."""
    doc = Document(str(docx)) if not hasattr(docx, "tables") else docx
    table = doc.tables[1]
    errors = []
    for r_idx, row in enumerate(table.rows[1:], start=1):
        cells = unique_cells(row)
        if len(cells) < 2:
            continue
        val_cell = cells[-1]
        for p in val_cell.paragraphs:
            for r in p.runs:
                txt = r.text.strip()
                if not txt:
                    continue
                rPr = r._r.find(qn("w:rPr"))
                if rPr is None:
                    errors.append(f"Section 2 row {r_idx} cell run '{txt[:15]}' missing rPr formatting")
                    continue
                sz = rPr.find(qn("w:sz"))
                val = sz.get(qn("w:val")) if sz is not None else None
                if val != "24":
                    errors.append(f"Section 2 row {r_idx} cell run '{txt[:15]}' size {val} != 24 (12pt)")
                b = rPr.find(qn("w:b"))
                if b is not None and b.get(qn("w:val")) not in ("0", "false"):
                    errors.append(f"Section 2 row {r_idx} cell run '{txt[:15]}' is unexpectedly bold")
    return errors


def run(docx, require_pictogram=False, document=None, expected_precautionary_groups=None,
        check_typography=False, source_s3_rows=None):
    """Audit one built DOCX; return (errors, info). Import-safe core of main()."""
    doc = document or Document(str(docx))
    table = doc.tables[1]
    errors = []
    all_text = "\n".join(cell.text for row in table.rows for cell in unique_cells(row))
    if "见2.4-2.6" in all_text or "See 2.4-2.6" in all_text:
        errors.append("customer-facing cross-reference remains in Section 2")

    for row in table.rows[1:]:
        cells = unique_cells(row)
        label = cells[0].text.strip() if cells else ""
        if "GHS标签要素" not in re.sub(r"\s+", "", label):
            continue
        value = "\n".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        if re.search(
            r"(?:GHS|危险性)\s*(?:危险性)?\s*(?:分类|类别|classification|category)|\bH\d{3}\b",
            value, re.I,
        ):
            errors.append(
                "Section 2 label-elements slot contains component GHS classification/H-code text; "
                "retain only the special-substance note"
            )
        break

    if has_component_ghs_context(source_s3_rows):
        for row in table.rows[1:]:
            cells = unique_cells(row)
            label = cells[0].text.strip() if cells else ""
            if "GHS危险性类别" not in re.sub(r"\s+", "", label):
                continue
            value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
            if value == "根据 GHS 不属于危险物":
                errors.append(
                    "Section 2 category uses the non-hazard fallback even though "
                    "Section 3 contains component GHS classification evidence"
                )
            break

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
        normalized_label = re.sub(r"\s+", "", label)
        explicit_no_is_data = (
            re.sub(r"[\s；;，,:：.!！？?。]+$", "", value.strip()) == "无"
            and (
                normalized_label.startswith("2.1")
                or normalized_label.startswith("2.2")
                or "GHS象形图" in normalized_label
            )
        )
        if (
            not is_explicit_other_hazards_row(row)
            and not row_has_visual_content(row)
            and not explicit_no_is_data
            and (not value or is_missing_section2_value(value))
        ):
            errors.append(f"missing-data row remains: {label}")
        match = re.match(r"^\s*2\.(\d+)\b", label)
        if match:
            old = int(match.group(1))
            if old not in old_to_new:
                old_to_new[old] = next_item
                next_item += 1
            labels.append(f"2.{old_to_new[old]}")
    if require_pictogram and not pictogram_present:
        errors.append("required source pictogram is absent")
    expected_groups = list(expected_precautionary_groups or [])
    if expected_precautionary_groups is not None:
        value = _precautionary_value(table)
        actual_groups = [
            precautionary_group_key(line)
            for line in value.splitlines()
            if precautionary_group_key(line)
        ]
        if actual_groups != expected_groups:
            errors.append(
                "precautionary group headings are missing or out of order: "
                f"expected {expected_groups}, found {actual_groups}"
            )
    # Compare unique transitions, while allowing repeated child rows.
    unique_labels = []
    for label in labels:
        if not unique_labels or unique_labels[-1] != label:
            unique_labels.append(label)
    if unique_labels != [f"2.{i}" for i in range(1, len(unique_labels) + 1)]:
        errors.append(f"Section 2 numbering is not continuous: {unique_labels}")

    # Non-hazard validation: if classified as non-hazardous, verify that no
    # CMR/toxic precautionary statements (e.g. P201, P202, P405) or phantom/illogical health
    # routes (e.g. "吸入：可能引起轻微的皮肤刺激") are present.
    is_non_hazard = bool(
        re.search(r"未被分类|不属于(?:危险|危害)|not\s+classified|not\s+hazardous", all_text, re.I)
    )
    if is_non_hazard:
        if re.search(r"P405|储存处须加锁|store\s+locked\s+up", all_text, re.I):
            errors.append("non-hazardous substance must not contain P405 (Store locked up)")
        if re.search(r"P201|P202|获取特别指示|obtain\s+special\s+instructions", all_text, re.I):
            errors.append("non-hazardous substance must not contain CMR precautionary statements (P201/P202)")
        if "吸入：可能引起轻微的皮肤刺激" in all_text or "Inhalation: May cause mild skin irritation" in all_text:
            errors.append("Section 2 contains illogical health hazard route (inhalation causing skin irritation)")

    # Value cell typography check
    if check_typography:
        errors.extend(audit_value_cell_typography(doc))

    # Duplicate label wording check (e.g. "其他危害其他危害" or "Other HazardsOther Hazards")
    for label in labels:
        if re.search(r"(其他危害|Other\s+Hazards)", label, re.I):
            errors.append(f"Section 2 label has duplicated wording: {label}")

    return errors, {"pass": not errors, "pictogram_present": pictogram_present, "labels": labels}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", type=Path)
    ap.add_argument("--require-pictogram", action="store_true")
    args = ap.parse_args()
    errors, info = run(args.docx, require_pictogram=args.require_pictogram)
    print(info)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
