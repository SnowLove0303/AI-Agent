"""Semantic Section 8 PPE labels shared by extraction and projection.

The source and maintained template may number Section 8 differently, may omit
an intermediate subsection heading, or may contain a stale value after a label
in the same cell.  This module resolves only the approved PPE vocabulary.  It
does not invent a destination for an unknown source row.
"""
from __future__ import annotations

import re
import unicodedata


S8_PPE_ORDER = (
    "respiratory",
    "hand",
    "glove_material",
    "fkm",
    "iir",
    "nbr",
    "recommendation",
    "eye",
    "body",
)

S8_PPE_ALIASES = {
    "respiratory": (
        "呼吸系统防护", "呼吸防护", "呼吸器官防护", "respiratory protection",
    ),
    "hand": ("手部防护", "hand protection"),
    "glove_material": (
        "防护手套的合适材料", "防护手套合适材料", "适合防护手套的材料",
        "suitable material for protective gloves", "suitable material for gloves",
    ),
    "fkm": ("氟化橡胶-fkm", "氟化橡胶–fkm", "fluororubber-fkm", "fluororubber – fkm"),
    "iir": ("丁基橡胶-iir", "丁基橡胶–iir", "butyl rubber-iir", "butyl rubber – iir"),
    "nbr": ("丁腈橡胶-nbr", "丁腈橡胶–nbr", "nitrile rubber-nbr", "nitrile rubber – nbr"),
    "recommendation": ("建议", "recommendation"),
    "eye": ("眼睛防护", "眼部防护", "eye protection"),
    "body": ("身体防护", "身体保护", "body protection"),
}

S8_PPE_LABELS = {
    "zh": {
        "respiratory": "呼吸系统防护：",
        "hand": "手部防护：",
        "glove_material": "防护手套的合适材料：",
        "fkm": "氟化橡胶 – FKM:",
        "iir": "丁基橡胶 – IIR:",
        "nbr": "丁腈橡胶 – NBR:",
        "recommendation": "建议：",
        "eye": "眼睛防护：",
        "body": "身体防护：",
    },
    "en": {
        "respiratory": "Respiratory protection:",
        "hand": "Hand protection:",
        "glove_material": "Suitable material for protective gloves:",
        "fkm": "Fluororubber – FKM:",
        "iir": "Butyl rubber – IIR:",
        "nbr": "Nitrile rubber – NBR:",
        "recommendation": "Recommendation:",
        "eye": "Eye protection:",
        "body": "Body protection:",
    },
}


def _compact(text: object) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    value = value.replace("：", ":")
    value = re.sub(r"[\s:;,，；。]+", "", value)
    value = value.replace("–", "-").replace("—", "-")
    return value


def s8_ppe_key(label: object) -> str | None:
    """Return the approved semantic key for an exact PPE label."""
    candidate = _compact(label)
    if not candidate:
        return None
    for key in S8_PPE_ORDER:
        if any(candidate == _compact(alias) for alias in S8_PPE_ALIASES[key]):
            return key
    return None


def split_s8_label_value(label: object, value: object = "") -> tuple[str | None, str, bool]:
    """Recover a known label/value pair from a source row.

    The third return value is true when the label cell also contained a tail
    after a tab/newline while a separate value cell was present.  That tail is
    reported as contamination by the caller and is not allowed to overwrite
    the authoritative value cell.
    """
    raw_label = str(label or "").replace("\r\n", "\n").replace("\r", "\n")
    raw_value = str(value or "").strip()
    if raw_value == raw_label.strip():
        raw_value = ""

    chunks = re.split(r"[\t\n]+", raw_label, maxsplit=1)
    head = chunks[0].strip()
    key = s8_ppe_key(head)
    if key is not None:
        tail = chunks[1].strip() if len(chunks) > 1 else ""
        return key, raw_value or tail, bool(tail and raw_value)

    # Some sources flatten ``Label: value`` into one physical cell.  Match a
    # known label prefix only; free prose is never split by a generic colon.
    match = re.match(r"^\s*(.+?)\s*[:：]\s*(.+?)\s*$", raw_label, re.S)
    if match:
        key = s8_ppe_key(match.group(1))
        if key is not None:
            return key, raw_value or match.group(2).strip(), False

    return None, raw_value, False


def canonical_s8_label(key: str, language: str = "zh") -> str:
    try:
        return S8_PPE_LABELS[language][key]
    except KeyError as exc:
        raise ValueError(f"unsupported Section 8 PPE key/language: {key}/{language}") from exc


def align_s8_rows(rows, language: str = "zh") -> list[list[str]]:
    """Align sparse semantic PPE rows to the fixed template order.

    Empty placeholders are intentional at this stage.  They keep later values
    in their semantic rows while the source-presence pass removes the empty
    physical rows after writing.  Section 8.2 remains the final top-level row.
    """
    if language not in S8_PPE_LABELS:
        raise ValueError(f"unsupported Section 8 language: {language}")
    records: dict[str, str] = {}
    engineering_value = ""
    for row in list(rows or []):
        if not isinstance(row, (list, tuple)) or not row:
            continue
        label = str(row[0] or "").strip()
        value = "\n".join(str(item or "").strip() for item in row[1:] if str(item or "").strip())
        if re.match(r"^\s*8\.2\b", label, re.I):
            engineering_value = value
            continue
        if re.match(r"^\s*8\.1\b", label, re.I):
            continue
        key, split_value, _ = split_s8_label_value(label, value)
        if key is None:
            if label or value:
                raise ValueError(f"unmapped Section 8 PPE row: {label!r}")
            continue
        # A source often leaves a stale prose tail after the hand-protection
        # label while the actual value cell is empty.  That tail is not a
        # hand-protection fact and must not duplicate respiratory protection.
        if key == "hand" and not value:
            split_value = ""
        if key in records and records[key] and split_value:
            records[key] = f"{records[key]}\n{split_value}".strip()
        else:
            records[key] = split_value

    if records.get("hand") and records.get("hand") == records.get("respiratory"):
        records["hand"] = ""

    heading = "8.1 暴露控制：" if language == "zh" else "8.1 Exposure controls:"
    engineering = "8.2 工程控制：" if language == "zh" else "8.2 Engineering controls:"
    output = [[heading, ""]]
    output.extend([
        [canonical_s8_label(key, language), records.get(key, "")]
        for key in S8_PPE_ORDER
    ])
    output.append([engineering, engineering_value])
    return output


def audit_s8_ppe_label_boundaries(rows) -> list[str]:
    """Review a source PPE row whose label contains a value tail.

    Source documents sometimes contain ``Label<TAB>value`` in one cell while
    also carrying an independent value cell.  The extractor must retain the
    independent value as authoritative and expose the stale tail for review.
    This helper is source-side only. Output labels are validated by comparing
    the cloned document with the fresh template skeleton; an output audit must
    not infer a template defect by inspecting the baseline in isolation.
    """
    errors = []
    for index, row in enumerate(list(rows or []), start=1):
        if hasattr(row, "cells"):
            # python-docx repeats horizontally/vertically merged cells in
            # ``row.cells``; use the physical-cell view so a merged label is
            # not mistaken for the independent value cell.
            from template_mutation_whitelist import unique_cells
            cells = unique_cells(row)
            label = cells[0].text if cells else ""
            value = cells[1].text if len(cells) > 1 else ""
        elif isinstance(row, (list, tuple)):
            label = str(row[0] or "") if row else ""
            value = "\n".join(str(item or "") for item in row[1:])
        else:
            continue
        key, _recovered, contaminated = split_s8_label_value(label, value)
        if key is not None and contaminated:
            errors.append(
                f"S8 source PPE row {index} has value text in the {key} label cell; "
                "the independent value cell is authoritative and the tail requires review"
            )
    return errors


__all__ = [
    "S8_PPE_ALIASES", "S8_PPE_LABELS", "S8_PPE_ORDER", "align_s8_rows",
    "audit_s8_ppe_label_boundaries", "canonical_s8_label", "s8_ppe_key",
    "split_s8_label_value",
]
