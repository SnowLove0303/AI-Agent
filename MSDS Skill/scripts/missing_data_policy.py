"""Source-presence policy for the shared MSDS overwrite pipeline.

The facts model is intentionally small and backwards-compatible: a row keeps
its historical list shape, while the value payload is classified into one of
four states before it is projected into the template.
"""
from __future__ import annotations

from enum import Enum
import copy
import re
from typing import Iterable

from docx.oxml.ns import qn

from section2_hp_policy import is_missing_data_value
from s8_ppe_policy import split_s8_label_value
from template_mutation_whitelist import is_s15_locked_heading_row


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


def _promote_following_vertical_merges(row) -> None:
    """Keep a surviving vMerge group valid when its restart row is removed."""
    current_tr = row._tr
    next_tr = current_tr.getnext()
    if next_tr is None:
        return
    current_cells = current_tr.findall(qn("w:tc"))
    next_cells = next_tr.findall(qn("w:tc"))
    for current_cell, next_cell in zip(current_cells, next_cells):
        current_pr = current_cell.find(qn("w:tcPr"))
        next_pr = next_cell.find(qn("w:tcPr"))
        current_merge = current_pr.find(qn("w:vMerge")) if current_pr is not None else None
        next_merge = next_pr.find(qn("w:vMerge")) if next_pr is not None else None
        if (
            current_merge is not None
            and current_merge.get(qn("w:val"), "restart") == "restart"
            and next_merge is not None
            and next_merge.get(qn("w:val")) == "continue"
        ):
            promoted = copy.deepcopy(current_cell)
            promoted_pr = promoted.find(qn("w:tcPr"))
            promoted_merge = promoted_pr.find(qn("w:vMerge"))
            promoted_merge.set(qn("w:val"), "restart")
            next_tr.replace(next_cell, promoted)


def _remove_row(table, row) -> None:
    _promote_following_vertical_merges(row)
    table._tbl.remove(row._tr)


def _normalized(text: object) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def _source_text(rows: Iterable[object]) -> str:
    return _normalized(" ".join(str(value) for row in rows for value in row))


def _source_backed_note(text: str, rows: Iterable[object]) -> bool:
    candidate = _normalized(text)
    return bool(candidate and candidate in _source_text(rows))


def _payload_cells(cells: list, section: int) -> list:
    """Return only actual value cells for source-presence evaluation.

    Section 11 has three three-column families: the acute-toxicity route
    rows (11.1), the direct toxicity/irritation subrows (11.2) and the
    reproductive-toxicity child rows (11.7).  Their
    middle cells are locked sublabels, not evidence.  Counting ``吸入：`` or
    ``Dermal:`` as payload leaves an absent endpoint visible and was the cause
    of the empty-row defect.
    """
    if len(cells) == 1:
        return cells
    if section == 11 and cells and re.match(
        r"^\s*11\.(?:1|2|7)\b", cells[0].text, re.I
    ) and len(cells) >= 3:
        return cells[2:]
    return cells[1:]


def _fact_row_state(row: object, section: int) -> SourceState:
    """Classify a fact row without treating a locked sublabel as its value."""
    values = list(row) if isinstance(row, (list, tuple)) else [row]
    value_start = 2 if section == 11 and len(values) >= 3 else 1
    return row_state(values, value_start=value_start)


def apply_source_absence_policy(document, facts: dict, unique_cells) -> dict:
    """Remove template-only rows and collapse note-only Sections 11/12.

    This is deliberately applied after value projection so the output is
    judged by the actual source payload, not by illustrative template text.
    S2 and S9 keep their dedicated policy modules because both also renumber
    visible coded items.
    """
    audit = {"source_absent_removed": [], "note_only": {"s11": False, "s12": False}}

    # S3 component rows and the ordinary S8 PPE rows are source-presence
    # controlled too.  If they are not removed here, clearing a fresh clone
    # leaves template labels with empty values or blank component rows.
    for section in (1, 3, 4, 5, 6, 7, 8, 10, 13, 14, 15):
        rows = facts.get(f"s{section}") or []
        table = document.tables[section - 1]
        source_limit = 1 + len(rows)
        for index, row in reversed(list(enumerate(table.rows[1:], 1))):
            cells = unique_cells(row)
            label = cells[0].text.strip() if cells else ""
            # These are structural rows or explicit maintained blank-value
            # exceptions, not missing customer-facing fields.
            if section == 1 and index in {1, 5}:
                continue
            if section == 3 and index in {2, 3}:
                continue
            if section == 8 and index in {1, 12, 13}:
                continue
            hand_key, _hand_tail, _hand_contaminated = split_s8_label_value(label, "")
            if section == 8 and (
                hand_key == "hand"
                or re.match(r"^\s*(?:手部防护|hand\s+protection)\s*[:：]?\s*$", label, re.I)
            ):
                # Hand protection is a template-owned parent slot.  Its
                # empty value is meaningful when child glove-material rows
                # are present and must not be hidden as missing data.
                continue
            if section == 8 and re.match(r"^\s*(?:建议|recommendation)\b", label, re.I):
                continue
            if section == 15 and is_s15_locked_heading_row(row):
                # These one-cell rows are structural headings, not source
                # values.  A missing legal item must never remove them.
                continue
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
            _fact_row_state(row, section) in (SourceState.SUPPORTED, SourceState.EXPLICIT_MISSING)
            and len(row) > 1
            for row in rows[1:]
        )
        table = document.tables[section - 1]
        if not has_endpoint:
            # Keep only source-backed explanation notes.  A padded canonical
            # skeleton can contain a blank first note slot; it must not leak
            # into the customer-facing document.
            for row in list(table.rows[1:]):
                cells = unique_cells(row)
                keep = (
                    len(cells) == 1
                    and _source_backed_note(cells[0].text, rows)
                )
                if not keep:
                    _remove_row(table, row)
                    label = cells[0].text.strip() if cells else "row"
                    audit["source_absent_removed"].append(f"S{section}:{label}")
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
