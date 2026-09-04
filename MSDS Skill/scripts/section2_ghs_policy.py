#!/usr/bin/env python3
"""Customer-facing Section 2 policy for the unified MSDS skill.

This module keeps Section 2 source-grounded and readable:

* GHS label elements are written as explicit, line-separated tips.  A reader
  must never be sent to another row with a phrase such as ``See 2.4-2.6``.
* A source pictogram image is treated as an asset, not as text or a missing
  value.  The caller inserts it into the cloned template pictogram cell.
* Whole Section 2 rows whose value is only missing data are removed before
  visible numbering is recalculated.  A value such as ``Eyes: No data`` is
  also a missing row; substantive negatives such as ``No irritation`` are not.

The module does not infer hazard classes, H/P codes, signal words or label
ingredients.  Those inputs must already be present in the verified semantic
model or in the source asset.
"""
from __future__ import annotations

import re
from copy import deepcopy

from docx.oxml.ns import qn

from section2_hp_policy import is_missing_data_value


def format_label_elements(language: str, hazardous_ingredients: list[str] | tuple[str, ...]) -> str:
    """Return the explicit, line-separated GHS label-ingredient tip.

    With no verified ingredients the value stays empty so the existing
    missing-row suppression removes the whole label-elements row instead of
    leaving a bare heading in customer-facing output.
    """
    ingredients = [str(x).strip() for x in hazardous_ingredients if str(x).strip()]
    if not ingredients:
        if language not in ("en", "zh"):
            raise ValueError("language must be zh or en")
        return ""
    if language == "en":
        heading = "Hazardous ingredients required to be listed on the label:"
    elif language == "zh":
        heading = "必须列在标签上的有害成分："
    else:
        raise ValueError("language must be zh or en")
    return "\n".join([heading, *ingredients])


def row_has_visual_content(row) -> bool:
    """Return true when a row contains an embedded drawing/picture."""
    for cell in row.cells:
        if cell._tc.xpath(".//w:drawing") or cell._tc.xpath(".//w:pict"):
            return True
    return False


def _value_text(row) -> str:
    cells = []
    seen = set()
    for cell in row.cells:
        key = hash(cell._tc)
        if key in seen:
            continue
        seen.add(key)
        # Keep empty value cells in the shape calculation.  Dropping them
        # would make a two-cell row look like a merged label-only row.
        cells.append(cell.text.strip())
    # Two-cell rows have a label cell followed by a value cell.  Exclude the
    # label even when the value cell is empty; this is what lets an empty
    # pictogram slot be removed.  A genuinely merged one-cell row contains
    # both label and value and therefore remains self-contained.
    return " ".join(cells[1:]) if len(cells) > 1 else " ".join(cells)


def is_missing_section2_value(value: str) -> bool:
    """Recognize only whole-item missing values, including ``Label: No data``."""
    if is_missing_data_value(value):
        return True
    stripped = re.sub(r"\s+", " ", (value or "").strip())
    if ":" in stripped or "：" in stripped:
        remainder = re.split(r"[:：]", stripped, maxsplit=1)[1].strip()
        return is_missing_data_value(remainder)
    return False


def _replace_prefix(paragraph, section: int, item: int, set_paragraph_text) -> None:
    current = paragraph.text
    updated = re.sub(rf"^(\s*){section}\.\d+(\b)", rf"\g<1>{section}.{item}\g<2>", current, count=1)
    if updated != current:
        # This is the sole approved label-cell content mutation.  Preserve
        # the existing run tree even when Word split ``2.2`` across runs.
        from template_mutation_whitelist import _replace_leading_pattern_in_runs
        _replace_leading_pattern_in_runs(
            paragraph,
            rf"^(\s*){section}\.\d+(\b)",
            rf"\g<1>{section}.{item}\g<2>",
        )


def suppress_missing_section2_rows_and_renumber(document, set_paragraph_text):
    """Remove missing Section 2 rows and renumber unique visible items.

    Repeated child rows such as multiple ``2.8 Health hazards`` rows retain a
    shared number.  The unnumbered GHS pictogram row is retained when it has an
    embedded image, even though its text value is empty.
    """
    table = document.tables[1]
    removed_labels = []
    for row in list(table.rows)[1:]:
        cells = []
        seen = set()
        for cell in row.cells:
            key = hash(cell._tc)
            if key not in seen:
                seen.add(key)
                cells.append(cell)
        label = cells[0].text.strip() if cells else ""
        if not row_has_visual_content(row) and (not _value_text(row) or is_missing_section2_value(_value_text(row))):
            # Keep an unnumbered non-data row only when it is the pictogram slot
            # and the picture is present.  Other empty rows are not customer-facing.
            removed_labels.append(label)
            table._tbl.remove(row._tr)
        else:
            pass

    # Re-read rows after XML removal.  Retaining row proxy objects across
    # deletion can make python-docx resolve a later repeated row to the old
    # physical position, which is unsafe for repeated 2.8 child rows.
    visible_rows = list(table.rows)[1:]

    # Snapshot the original item number before changing any label text.  A
    # vertically merged label cell is returned by python-docx for every child
    # row, so reading its text after the first rewrite would make the next
    # child appear to have a different original number.
    row_info = []
    for row in visible_rows:
        cells = []
        seen = set()
        for cell in row.cells:
            key = hash(cell._tc)
            if key not in seen:
                seen.add(key)
                cells.append(cell)
        if not cells or not cells[0].paragraphs:
            continue
        paragraph = cells[0].paragraphs[0]
        match = re.match(r"^\s*2\.(\d+)\b", paragraph.text)
        if match:
            row_info.append((row, cells, hash(cells[0]._tc), int(match.group(1))))

    old_to_new = {}
    next_item = 1
    labels = []
    rewritten_cells = set()
    for row, cells, label_cell_key, old in row_info:
        if old not in old_to_new:
            old_to_new[old] = next_item
            next_item += 1
        if label_cell_key not in rewritten_cells:
            _replace_prefix(cells[0].paragraphs[0], 2, old_to_new[old], set_paragraph_text)
            rewritten_cells.add(label_cell_key)
        labels.append(cells[0].paragraphs[0].text.strip())

    return {
        "removed_count": len(removed_labels),
        "removed_labels": removed_labels,
        "visible_count": len(labels),
        "visible_labels": labels,
        "number_map": {f"2.{old}": f"2.{new}" for old, new in old_to_new.items()},
    }


__all__ = [
    "format_label_elements",
    "row_has_visual_content",
    "is_missing_section2_value",
    "suppress_missing_section2_rows_and_renumber",
]
