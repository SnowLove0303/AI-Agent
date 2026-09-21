"""Semantic alignment for the fixed Section 11 toxicology skeleton.

Section 11 is not a free-form list.  Its physical rows contain repeated
acute-toxicity routes and three reproductive-toxicity children, so a compacted
facts list cannot be written by list position without risking a catastrophic
label/value shift.  This module maps approved facts to the existing template
row keys, pads absent slots, and rejects endpoint names that cannot be mapped.
It never edits the template labels or row geometry.
"""
from __future__ import annotations

import re

from template_mutation_whitelist import normalize_value_text, set_sequence_prefix, unique_cells


class Section11AlignmentError(ValueError):
    """The approved Section 11 payload cannot be safely mapped to the template."""


_ROUTE_ALIASES = {
    "经口": "oral",
    "口服": "oral",
    "急性经口毒性": "oral",
    "oral": "oral",
    "acute oral toxicity": "oral",
    "吸入": "inhalation",
    "吸入性": "inhalation",
    "急性吸入毒性": "inhalation",
    "inhalation": "inhalation",
    "acute inhalation toxicity": "inhalation",
    "经皮": "dermal",
    "皮肤": "dermal",
    "急性经皮毒性": "dermal",
    "dermal": "dermal",
    "acute dermal toxicity": "dermal",
}

_CHILD_ALIASES = {
    "生育力": "fertility",
    "fertility": "fertility",
    "致畸形": "teratogenicity",
    "致畸": "teratogenicity",
    "胚胎": "teratogenicity",
    "teratogenicity": "teratogenicity",
    "体外遗传毒性": "in_vitro_genotoxicity",
    "体外基因毒性": "in_vitro_genotoxicity",
    "invitrogenotoxicity": "in_vitro_genotoxicity",
}


def _compact(text: object) -> str:
    text = str(text or "").casefold()
    return re.sub(r"[\s:：;；,，。./／()（）\[\]【】_-]+", "", text)


def _number(text: object) -> int | None:
    match = re.match(r"^\s*11\.(\d+)\b", str(text or ""))
    return int(match.group(1)) if match else None


def _route(text: object) -> str | None:
    compact = _compact(text)
    for alias, key in _ROUTE_ALIASES.items():
        if _compact(alias) == compact:
            return key
    return None


def _child(text: object) -> str | None:
    compact = _compact(text)
    for alias, key in _CHILD_ALIASES.items():
        if _compact(alias) == compact:
            return key
    return None


def _endpoint_number(label: object) -> int | None:
    numbered = _number(label)
    if numbered is not None:
        return numbered
    text = _compact(label)
    # Order matters: specific labels must be resolved before generic toxicity.
    aliases = (
        (1, ("急性毒性", "急性经口毒性", "急性吸入毒性", "急性经皮毒性",
             "acutetoxicity", "acute oral toxicity", "acute inhalation toxicity",
             "acute dermal toxicity")),
        (2, ("主要皮肤刺激性", "皮肤刺激", "primaryskinirritation")),
        (3, ("主要眼睛刺激性", "主要粘膜刺激性", "原发性粘膜刺激", "眼睛刺激", "primaryeyeirritation")),
        (4, ("致敏性", "sensitization")),
        (5, ("致突变性", "mutagenicity", "genotoxicity")),
        (6, ("致癌性", "carcinogenicity")),
        (7, ("生殖毒性", "reproductivetoxicity")),
        (8, ("特异性靶器官", "特异性靶器官系统毒性", "specifictargetorgantoxicity")),
        (9, ("吸入危险", "aspirationhazard")),
        (10, ("附加信息", "其他信息", "additionalinformation")),
    )
    for endpoint, candidates in aliases:
        if any(_compact(candidate) in text for candidate in candidates):
            return endpoint
    return None


def _row_key(row: list | tuple) -> tuple:
    """Return a semantic key for one facts row."""
    if not isinstance(row, (list, tuple)) or not row:
        raise Section11AlignmentError("every Section 11 fact row must be a non-empty list/tuple")
    if len(row) > 3:
        raise Section11AlignmentError("Section 11 rows may contain at most label/sublabel/value")
    if len(row) == 1:
        return ("note",)
    label = row[0]
    endpoint = _endpoint_number(label)
    if endpoint is None:
        raise Section11AlignmentError(f"cannot map Section 11 endpoint label: {label!r}")
    sublabel = row[1] if len(row) == 3 else ""
    if endpoint == 1:
        route = _route(sublabel)
        if route is None:
            label_text = _compact(label)
            route = next(
                (key for alias, key in _ROUTE_ALIASES.items() if _compact(alias) in label_text),
                None,
            )
        if route is not None:
            return ("endpoint", endpoint, route)
        if len(row) == 3 and _compact(sublabel) not in {"", "总结", "overall", "summary"}:
            raise Section11AlignmentError(
                f"cannot map Section 11.1 sublabel: {sublabel!r}"
            )
        # The fixed template represents the aggregate 11.1 row with no route
        # key (None).  Keep the semantic key identical to the template so an
        # omitted route cannot become a phantom unmatched endpoint.
        return ("endpoint", endpoint, None)
    if endpoint == 7:
        child = _child(sublabel)
        if child is None:
            label_text = _compact(label)
            child = next(
                (key for alias, key in _CHILD_ALIASES.items() if _compact(alias) in label_text),
                None,
            )
        if child is None:
            raise Section11AlignmentError(
                "Section 11.7 requires an explicit fertility, teratogenicity or "
                f"in-vitro-genotoxicity sublabel: {sublabel!r}"
            )
        return ("endpoint", endpoint, child)
    return ("endpoint", endpoint, None)


def _template_key(row) -> tuple:
    cells = unique_cells(row)
    if len(cells) == 1:
        return ("note",)
    label = cells[0].text
    endpoint = _endpoint_number(label)
    if endpoint is None:
        return ("unknown", label)
    if endpoint == 1 and len(cells) >= 3:
        return ("endpoint", endpoint, _route(cells[1].text))
    if endpoint == 7 and len(cells) >= 3:
        return ("endpoint", endpoint, _child(cells[1].text))
    return ("endpoint", endpoint, None)


def _normalized_row(row: list | tuple, target_cells: list) -> list:
    """Fit a source row to the target row shape without changing labels."""
    source = [str(value or "") for value in row]
    if len(target_cells) == 1:
        return [normalize_value_text("\n".join(source))]
    if len(target_cells) == 3:
        sublabel = target_cells[1].text
        value = normalize_value_text(source[-1])
        return [source[0], sublabel if not source[1].strip() else source[1], value]
    return [source[0], normalize_value_text(source[-1])]


def align_s11_rows(values, table) -> list:
    """Map Section 11 facts to the physical template skeleton.

    The returned list has exactly one item for every template data row.  Notes
    occupy only the leading one-cell note slots, while absent endpoint slots
    receive shape-preserving blank rows.  Duplicate facts for one endpoint are
    merged as semantic value lines instead of being allowed to shift later
    rows.
    """
    source_rows = list(values or [])
    template_rows = list(table.rows)[1:]
    if not template_rows:
        raise Section11AlignmentError("Section 11 template has no data rows")
    target_keys = [_template_key(row) for row in template_rows]
    if any(key[0] == "unknown" for key in target_keys):
        raise Section11AlignmentError("Section 11 template contains an unmappable endpoint label")
    note_slots = [index for index, key in enumerate(target_keys) if key == ("note",)]
    endpoint_slots = {
        key: index for index, key in enumerate(target_keys) if key != ("note",)
    }
    aligned = []
    for row in template_rows:
        cells = unique_cells(row)
        if len(cells) == 1:
            aligned.append([""])
        elif len(cells) == 3:
            aligned.append([cells[0].text, cells[1].text, ""])
        else:
            aligned.append([cells[0].text, ""])

    next_note = 0
    for source_row in source_rows:
        key = _row_key(source_row)
        if key == ("note",):
            if not str(source_row[0] or "").strip():
                continue
            if next_note >= len(note_slots):
                raise Section11AlignmentError(
                    "Section 11 contains more source notes than the template note slots"
                )
            slot = note_slots[next_note]
            aligned[slot] = [normalize_value_text(source_row[0])]
            next_note += 1
            continue
        slot = endpoint_slots.get(key)
        if slot is None:
            raise Section11AlignmentError(
                f"Section 11 endpoint has no matching template row: {source_row[0]!r}"
            )
        normalized = _normalized_row(source_row, unique_cells(template_rows[slot]))
        existing = aligned[slot]
        if not any(str(value).strip() for value in existing[1:]):
            aligned[slot] = normalized
            continue
        old_value = existing[-1].strip()
        new_value = normalized[-1].strip()
        if new_value and new_value != old_value:
            existing[-1] = normalize_value_text(f"{old_value}\n{new_value}")
    return aligned


def renumber_visible_s11_rows(table) -> dict:
    """Compact surviving S11 endpoint groups to continuous visible numbers."""
    next_number = 1
    old_to_new: dict[int, int] = {}
    labels = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        if not cells:
            continue
        match = re.match(r"^\s*11\.(\d+)\b", cells[0].text)
        if not match:
            continue
        old = int(match.group(1))
        if old not in old_to_new:
            old_to_new[old] = next_number
            next_number += 1
        set_sequence_prefix(cells[0], 11, old_to_new[old])
        labels.append(cells[0].text.strip())
    return {
        "renumbered": bool(old_to_new),
        "number_map": {f"11.{old}": f"11.{new}" for old, new in old_to_new.items()},
        "visible_labels": labels,
    }


__all__ = ["Section11AlignmentError", "align_s11_rows", "renumber_visible_s11_rows"]
