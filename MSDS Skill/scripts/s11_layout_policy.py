#!/usr/bin/env python3
"""Narrow, auditable Section 11.4 output-layout compatibility policy.

The formal templates remain byte-identical. One maintained template contains a
known 1169-twip ``atLeast`` height on S11.4, which creates a large blank block
for a short source value. The policy adjusts only the cloned output row to the
normal short-row height (285 twips), only when a source-backed S11.4 value is
present and is short enough. Any other row-height drift is a release blocker.
"""
from __future__ import annotations

import re

from docx.oxml.ns import qn

from template_mutation_whitelist import unique_cells


KNOWN_OVERSIZED_TWIPS = 1169
SHORT_ROW_TWIPS = 285
MAX_SHORT_LINES = 2
MAX_SHORT_CHARS = 240


def _height(row) -> tuple[int | None, str | None]:
    tr_pr = row._tr.trPr
    node = tr_pr.find(qn("w:trHeight")) if tr_pr is not None else None
    if node is None:
        return None, None
    try:
        value = int(node.get(qn("w:val")))
    except (TypeError, ValueError):
        value = None
    return value, node.get(qn("w:hRule"))


def _set_height(row, value: int) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    node = tr_pr.find(qn("w:trHeight"))
    if node is None:
        node = tr_pr.makeelement(qn("w:trHeight"), {})
        tr_pr.append(node)
    node.set(qn("w:val"), str(value))
    node.set(qn("w:hRule"), "atLeast")


def _label(row) -> str:
    cells = unique_cells(row)
    return cells[0].text.strip() if cells else ""


def _value(row) -> str:
    cells = unique_cells(row)
    if not cells:
        return ""
    return cells[-1].text.strip() if len(cells) > 1 else ""


def _source_has_s114(source_rows) -> bool:
    for row in list(source_rows or []):
        if isinstance(row, dict):
            label = str(row.get("label") or row.get("field") or "")
            value = str(row.get("value") or "")
        elif isinstance(row, (list, tuple)):
            label = str(row[0] if row else "")
            value = str(row[-1] if len(row) > 1 else "")
        else:
            continue
        if re.search(r"11\.4|致敏性|sensitization", label, re.I) and value.strip():
            return True
    return False


def normalize(document, source_rows) -> dict:
    """Apply the one approved output-only S11.4 height normalization."""
    table = document.tables[10]
    for row in table.rows[1:]:
        label = _label(row)
        if not re.match(r"^\s*11\.4\b", label):
            continue
        value = _value(row)
        lines = [line for line in value.splitlines() if line.strip()]
        current, rule = _height(row)
        eligible = (
            current == KNOWN_OVERSIZED_TWIPS
            and _source_has_s114(source_rows)
            and bool(value)
            and len(lines) <= MAX_SHORT_LINES
            and len(value) <= MAX_SHORT_CHARS
        )
        if eligible:
            _set_height(row, SHORT_ROW_TWIPS)
            return {
                "applied": True,
                "section": "s11",
                "field": "11.4",
                "from_twips": current,
                "to_twips": SHORT_ROW_TWIPS,
                "rule": rule or "atLeast",
                "reason": "short source-backed S11.4 value",
            }
        return {
            "applied": False,
            "section": "s11",
            "field": "11.4",
            "from_twips": current,
            "to_twips": current,
            "reason": "not eligible for the narrow short-value exception",
        }
    return {"applied": False, "section": "s11", "field": "11.4", "reason": "row absent"}


def _semantic_key(row) -> tuple[str, ...]:
    cells = unique_cells(row)
    return tuple(cell.text.strip() for cell in cells[:-1]) if len(cells) > 1 else (cells[0].text.strip(),) if cells else ()


def audit(template, output, exception: dict | None = None) -> dict:
    """Check S11 row heights and allow only the recorded S11.4 exception."""
    errors: list[str] = []
    expected = {}
    for row in template.tables[10].rows[1:]:
        expected.setdefault(_semantic_key(row), []).append(_height(row))
    seen = {}
    for row in output.tables[10].rows[1:]:
        key = _semantic_key(row)
        heights = expected.get(key)
        if not heights:
            continue
        position = seen.get(key, 0)
        seen[key] = position + 1
        expected_height = heights[min(position, len(heights) - 1)]
        actual_height = _height(row)
        if re.match(r"^\s*11\.4\b", _label(row)) and exception and exception.get("applied"):
            if actual_height != (SHORT_ROW_TWIPS, "atLeast"):
                errors.append(f"S11.4 controlled height mismatch: {actual_height}")
            continue
        if actual_height != expected_height:
            errors.append(
                f"S11 row height changed for {_label(row)!r}: "
                f"{expected_height} -> {actual_height}"
            )
    return {"status": "passed" if not errors else "failed", "errors": errors}


__all__ = [
    "KNOWN_OVERSIZED_TWIPS", "SHORT_ROW_TWIPS", "audit", "normalize",
]
