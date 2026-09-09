"""Source-presence policy for the shared MSDS overwrite pipeline.

The facts model is intentionally small and backwards-compatible: a row keeps
its historical list shape, while the value payload is classified into one of
four states before it is projected into the template.
"""
from __future__ import annotations

from enum import Enum
import re
from typing import Iterable

from section2_hp_policy import is_missing_data_value


class SourceState(str, Enum):
    SUPPORTED = "SUPPORTED"
    EXPLICIT_MISSING = "EXPLICIT_MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ABSENT = "ABSENT"


def classify_source_value(value: object, *, present: bool = True) -> SourceState:
    if not present or value is None or not str(value).strip():
        return SourceState.ABSENT
    text = str(value).strip()
    if is_missing_data_value(text):
        return SourceState.EXPLICIT_MISSING
    if text.casefold() in {"不适用", "not applicable"}:
        return SourceState.NOT_APPLICABLE
    return SourceState.SUPPORTED


def row_state(values: Iterable[object], *, value_start: int = 1) -> SourceState:
    payload = list(values)[value_start:]
    states = [classify_source_value(value) for value in payload]
    if any(state == SourceState.SUPPORTED for state in states):
        return SourceState.SUPPORTED
    if any(state == SourceState.NOT_APPLICABLE for state in states):
        return SourceState.NOT_APPLICABLE
    if any(state == SourceState.EXPLICIT_MISSING for state in states):
        return SourceState.EXPLICIT_MISSING
    return SourceState.ABSENT


def _remove_row(table, row) -> None:
    table._tbl.remove(row._tr)


def _normalized(text: object) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def _source_text(rows: Iterable[object]) -> str:
    return _normalized(" ".join(str(value) for row in rows for value in row))


def _source_backed_note(text: str, rows: Iterable[object]) -> bool:
    candidate = _normalized(text)
    return bool(candidate and candidate in _source_text(rows))


def _payload_cells(cells: list, section: int) -> list:
    """Exclude S11.7's sub-endpoint label from its value test."""
    if len(cells) == 1:
        return cells
    if section == 11 and cells and re.match(r"^\s*11\.7\b", cells[0].text):
        return cells[2:]
    return cells[1:]


def apply_source_absence_policy(document, facts: dict, unique_cells) -> dict:
    """Remove template-only rows and collapse note-only Sections 11/12.

    This is deliberately applied after value projection so the output is
    judged by the actual source payload, not by illustrative template text.
    S2 and S9 keep their dedicated policy modules because both also renumber
    visible coded items.
    """
    audit = {"source_absent_removed": [], "note_only": {"s11": False, "s12": False}}

    for section in (4, 5, 6, 7, 10, 13, 14, 15):
        rows = facts.get(f"s{section}") or []
        table = document.tables[section - 1]
        source_limit = 1 + len(rows)
        for index, row in reversed(list(enumerate(table.rows[1:], 1))):
            cells = unique_cells(row)
            absent = index >= source_limit
            if not absent:
                payload = _payload_cells(cells, section)
                absent = all(not cell.text.strip() for cell in payload)
                if section == 10 and not absent:
                    absent = row_state([cell.text for cell in cells]) == SourceState.EXPLICIT_MISSING
            if absent:
                label = cells[0].text.strip() if cells else f"row {index}"
                _remove_row(table, row)
                audit["source_absent_removed"].append(f"S{section}:{label}")

    for section in (11, 12):
        key = f"s{section}"
        rows = facts.get(key) or []
        has_endpoint = any(
            row_state(row) in (SourceState.SUPPORTED, SourceState.EXPLICIT_MISSING)
            and len(row) > 1
            for row in rows[1:]
        )
        table = document.tables[section - 1]
        if not has_endpoint:
            for row in list(table.rows[2:]):
                _remove_row(table, row)
            audit["note_only"][key] = True
            continue

        source_limit = 1 + len(rows)
        for index, row in reversed(list(enumerate(table.rows[1:], 1))):
            cells = unique_cells(row)
            absent = index >= source_limit
            if not absent:
                payload = _payload_cells(cells, section)
                absent = all(not cell.text.strip() for cell in payload)
                if section == 12 and not absent:
                    absent = row_state([cell.text for cell in cells]) == SourceState.EXPLICIT_MISSING
            if not absent and len(cells) == 1 and section in (11, 12):
                absent = not _source_backed_note(cells[0].text, rows)
            if absent:
                label = cells[0].text.strip() if cells else f"row {index}"
                _remove_row(table, row)
                audit["source_absent_removed"].append(f"S{section}:{label}")

    return audit


__all__ = [
    "SourceState",
    "apply_source_absence_policy",
    "classify_source_value",
    "row_state",
]
