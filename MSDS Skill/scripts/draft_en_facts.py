#!/usr/bin/env python3
"""Draft English facts from an approved standardized Chinese model (v3.26.0).

Business role: EN is a professional translation OF the standardized model,
never of a rendered DOCX and never an independent derivation.  This module
does the mechanical part only:

* locked tokens (CAS numbers, measurements, H/EUH/P codes, standard codes,
  model codes) are copied verbatim and never substituted;
* `resources/professional_translation_glossary.tsv` is applied longest-match;
* every residual Chinese segment is kept in place and recorded in
  ``translation_review``.

Any non-empty ``translation_review`` forces ``formal_ready=false``
downstream; a human/agent must clear each entry by hand-editing ``en``.
Re-running the drafter overwrites ``en`` — it is a one-shot step.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from section2_hp_policy import translate_precautionary_group_headings

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
CAS_RE = re.compile(r"\d{2,7}-\d{2}-\d")
CODE_RE = re.compile(r"(?:EUH|H)\d{3}[A-Za-z]{0,3}|P\d{3}(?:\+P\d{3})*")
MEASURE_RE = re.compile(
    r"[<>＜＞≥≤≧≦~～\-–—]?\s*\d[\d\s.,~～\-–—]*\s*"
    r"(?:%|％|mg\/kg|mg\/L|mg\/l|g\/cm3|mPa\.?s|hPa|ppm|ppb|mg|g\b|kg\b|ml\b|mL\b|L\b|"
    r"°C|℃|mm\b|cm\b|min\b|\bh\b|\bd\b|h\/| zone)?",
    re.IGNORECASE,
)
STANDARD_RE = re.compile(
    r"\b(?:GB\/T|GB|ISO|OECD|EN|ASTM|EWC|ADR|RID|IMDG|IATA|MARPOL|IBC)\b[\s\d.\-–/]*\d[\d.\-–/]*",
    re.IGNORECASE,
)
MODEL_RE = re.compile(r"\b[A-Z]{1,4}-\d{3,4}[A-Z0-9]*\b")
LOCKED_RES = (CAS_RE, CODE_RE, MEASURE_RE, STANDARD_RE, MODEL_RE)


def load_glossary(path: Path) -> list[tuple[str, str]]:
    rows = []
    with path.open(encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            source = (row.get("Chinese") or "").strip()
            target = (row.get("Canonical English") or "").strip()
            if source and target:
                rows.append((source, target))
    rows.sort(key=lambda item: len(item[0]), reverse=True)
    return rows


def protect_locked(text: str) -> tuple[str, dict[str, str]]:
    """Replace locked spans with placeholders; return (masked, table)."""
    table: dict[str, str] = {}
    counter = 0

    def stash(match: re.Match) -> str:
        nonlocal counter
        key = f"\ue000{counter}\ue001"
        counter += 1
        table[key] = match.group(0)
        return key

    masked = text
    for pattern in LOCKED_RES:
        masked = pattern.sub(stash, masked)
    return masked, table


def draft_value(text: str, glossary: list[tuple[str, str]]) -> tuple[str, bool]:
    """Return (draft, needs_review). Locked spans are restored verbatim."""
    if not text or not text.strip():
        return text, False
    masked, table = protect_locked(text)
    for source, target in glossary:
        if source in masked:
            masked = masked.replace(source, target)
    for key, original in table.items():
        masked = masked.replace(key, original)
    return masked, bool(CJK_RE.search(masked))


def draft_section(rows: list, glossary, section: str, review: list) -> list:
    out = []
    for row_index, row in enumerate(rows):
        if isinstance(row, dict):
            # s9-style {label, value, ...} entries.
            value = row.get("value", "")
            draft, flagged = draft_value(str(value), glossary)
            entry = dict(row)
            entry["value"] = draft
            if flagged:
                review.append({"section": section, "row": row_index,
                               "cell": "value", "value": str(value)})
            out.append(entry)
            continue
        drafted = []
        for cell_index, cell in enumerate(row):
            source_cell = str(cell)
            if section == "s2" and cell_index > 0:
                # Convert controlled group headings before the general
                # glossary runs.  Otherwise a broad glossary entry such as
                # "预防措施" could consume the exact heading and make the
                # group-level EN contract impossible to verify.
                source_cell = translate_precautionary_group_headings(source_cell)
            draft, flagged = draft_value(source_cell, glossary)
            if section == "s2" and cell_index > 0:
                draft = translate_precautionary_group_headings(draft)
                flagged = bool(CJK_RE.search(draft))
            drafted.append(draft)
            if flagged and not (section == "s3" and cell_index == 1):
                # S3 CAS cells are locked verbatim; nothing to review there.
                review.append({"section": section, "row": row_index,
                               "cell": cell_index, "value": str(cell)})
        out.append(drafted)
    return out


def draft(model: dict, glossary) -> dict:
    review: list[dict] = []
    zh = model.get("zh") or {}
    en: dict = {}
    for section in sorted(zh):
        rows = zh[section]
        if section == "s2" and isinstance(rows, dict):
            # Extractor-shape S2 is normalized by the reviewer into the
            # generator row shape before drafting; flag it loudly.
            review.append({"section": "s2", "row": -1, "cell": -1,
                           "value": "s2 must be reviewed into generator rows first"})
            en[section] = rows
            continue
        en[section] = draft_section(rows, glossary, section, review)
    records = {}
    for language in ("zh", "en"):
        controls = (model.get("s8_control_parameters") or {}).get(language) or []
        records[language] = controls
    if records["zh"] and not records["en"]:
        drafted_records = []
        for record in records["zh"]:
            cells = []
            for cell in record:
                draft, flagged = draft_value(str(cell), glossary)
                cells.append(draft)
                if flagged:
                    review.append({"section": "s8_control_parameters",
                                   "row": len(drafted_records),
                                   "cell": len(cells) - 1, "value": str(cell)})
            drafted_records.append(cells)
        records["en"] = drafted_records
    model["en"] = en
    model["s8_control_parameters"] = records
    model["translation_review"] = review
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_json")
    parser.add_argument("--glossary", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    model_path = Path(args.model_json)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    glossary_path = Path(args.glossary) if args.glossary else (
        Path(__file__).resolve().parent.parent / "resources" / "professional_translation_glossary.tsv")
    glossary = load_glossary(glossary_path)
    draft(model, glossary)
    target = Path(args.out) if args.out else model_path
    target.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"model": model.get("model"), "review_count": len(model["translation_review"]),
                      "out": str(target)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
