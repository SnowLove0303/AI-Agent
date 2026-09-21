#!/usr/bin/env python3
"""Fail-closed source/fact/output grounding for the MSDS pipeline.

The template is allowed to contribute structure only. This module checks the
semantic model before a template is cloned, using the reviewed fact ledger and
output traceability as the allow-list for non-empty product values. It also
checks that a ledger source value has an anchor in the original source file;
an Agent cannot make a fabricated value authoritative merely by placing it in
the ledger.

The check intentionally does not use a global keyword blacklist. Common words
such as ``water`` or ``hazard`` are not evidence of leakage by themselves. A
value is accepted only when it is source-backed, trace-backed (including an
approved translation), or explicitly declared as a controlled overlay.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path


_STRUCTURAL_ONLY = re.compile(
    r"^\s*(?:\d+(?:\.\d+)?\s*)?(?:产品名称|供应商信息|成分|化学品名称|"
    r"product name|supplier information|composition|chemical name|"
    r"(?:物质|依据|类型|数值|substance|basis|type|value))\s*[：:]?\s*$",
    re.I,
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _canonical(value: object) -> str:
    """Normalize layout noise but not customer-facing semantics."""
    text = unicodedata.normalize("NFKC", _text(value)).casefold()
    text = text.replace("／", "/").replace("－", "-").replace("：", ":")
    return re.sub(r"[\s\u3000]+", "", text)


def _informative_parts(value: str) -> list[str]:
    parts = []
    for line in re.split(r"[\r\n]+", value):
        compact = _canonical(line)
        if len(compact) >= 4:
            parts.append(compact)
    return parts


@lru_cache(maxsize=16)
def _source_text(source: Path) -> str:
    """Extract a searchable text corpus from the original source DOCX."""
    if source.suffix.lower() not in {".docx", ".docm"}:
        return ""
    try:
        from docx import Document

        document = Document(str(source))
        chunks: list[str] = []

        def visit_table(table) -> None:
            for row in table.rows:
                for cell in row.cells:
                    chunks.append(cell.text)
                    for nested in cell.tables:
                        visit_table(nested)

        chunks.extend(paragraph.text for paragraph in document.paragraphs)
        for table in document.tables:
            visit_table(table)
        # Header/footer content is part of the source inventory too.  It may
        # contain product identifiers, revision data or supplier facts that an
        # output traceability record legitimately references.
        for section in document.sections:
            for container in (section.header, section.footer):
                chunks.extend(paragraph.text for paragraph in container.paragraphs)
                for table in container.tables:
                    visit_table(table)
        return "\n".join(chunks)
    except Exception:
        # The source-interpretation gate reports unsupported/unreadable source
        # formats. This helper remains useful for semantic model tests.
        return ""


def _source_anchor(value: str, corpus: str) -> bool:
    if not _text(value):
        return True
    if not corpus:
        return False
    source = _canonical(corpus)
    candidate = _canonical(value)
    if candidate and candidate in source:
        return True
    chunks = _informative_parts(value)
    return bool(chunks) and all(chunk in source for chunk in chunks)


def _iter_payloads(layer: object, language: str):
    if not isinstance(layer, dict):
        return
    for section in range(1, 17):
        key = f"s{section}"
        rows = layer.get(key)
        if not isinstance(rows, list):
            continue
        for row_index, row in enumerate(rows, start=1):
            if isinstance(row, dict):
                value = row.get("value", "")
            elif isinstance(row, (list, tuple)):
                if section == 3 or len(row) <= 1:
                    values = row
                else:
                    values = row[1:]
                value = "\n".join(_text(item) for item in values if _text(item))
            else:
                value = ""
            text = _text(value)
            if text and not _STRUCTURAL_ONLY.fullmatch(text):
                yield f"{language}.{key}[{row_index}]", text


def _iter_control_payloads(facts: dict, language: str):
    controls = facts.get("s8_control_parameters") or {}
    if not isinstance(controls, dict):
        return
    rows = controls.get(language) or []
    for row_index, row in enumerate(rows, start=1):
        if isinstance(row, (list, tuple)):
            value = "\n".join(_text(item) for item in row if _text(item))
        else:
            value = _text(row)
        if value:
            yield f"{language}.s8_control_parameters[{row_index}]", value


def _iter_output_trace_values(facts: dict):
    """Yield only explicitly reviewed non-source output evidence.

    ``output_values`` is a record of a decision, not a source of truth.  The
    old implementation added every traced value to the allow-list, which let a
    fabricated value pass simply because an Agent copied it into its own
    traceability record.  Exact source values are checked against the source
    corpus below; only reviewed translations/derivations need an explicit
    exception here.
    """
    trace = facts.get("output_traceability") or {}
    items = trace.get("items", []) if isinstance(trace, dict) else []
    for item in items:
        if not isinstance(item, dict) or item.get("decision") not in {"written", "merged"}:
            continue
        values = item.get("output_values") if isinstance(item, dict) else None
        if not isinstance(values, dict):
            continue
        fact_ids = item.get("source_fact_ids") or []
        evidence_type = str(item.get("evidence_type") or "").strip()
        if not fact_ids or evidence_type not in {
            "approved_translation", "approved_derivation", "company_overlay"
        }:
            continue
        if evidence_type == "approved_translation" and item.get("translation_reviewed") is not True:
            continue
        if evidence_type == "approved_derivation" and not str(
            item.get("derivation_rule_id") or ""
        ).strip():
            continue
        for language in ("zh", "en"):
            value = _text(values.get(language))
            if value:
                yield language, value, evidence_type


def audit(facts: dict, source: Path, model: str,
          prepared_source: Path | None = None) -> dict:
    """Return a grounding report without mutating the model or source."""
    errors: list[str] = []
    ledger = facts.get("fact_ledger")
    ledger_by_id = {}
    source_values: list[str] = []
    if not isinstance(ledger, list) or not ledger:
        errors.append("source grounding: fact_ledger is required")
    else:
        search_source = prepared_source or source
        corpus = _source_text(search_source)
        for index, fact in enumerate(ledger, start=1):
            if not isinstance(fact, dict):
                errors.append(f"source grounding: fact {index} is not an object")
                continue
            fact_id = _text(fact.get("fact_id"))
            source_value = _text(fact.get("source_text"))
            normalized = _text(fact.get("normalized_value"))
            if fact_id:
                ledger_by_id[fact_id] = fact
            if source_value and not source_value.startswith("(section present;"):
                if not _source_anchor(source_value, corpus):
                    errors.append(
                        f"source grounding: {fact_id or 'fact ' + str(index)} source_text "
                        "has no anchor in the original source"
                    )
            if normalized:
                source_values.append(normalized)
            if source_value:
                source_values.append(source_value)

    trace_values = {language: [] for language in ("zh", "en")}
    for language, value, _evidence_type in _iter_output_trace_values(facts):
        trace_values[language].append(value)

    grounding = facts.get("source_grounding") or {}
    if grounding and not isinstance(grounding, dict):
        errors.append("source grounding: source_grounding must be an object")
        grounding = {}
    overlay_values = {language: [] for language in ("zh", "en")}
    if isinstance(grounding, dict):
        raw_overlays = grounding.get("overlay_values") or {}
        if not isinstance(raw_overlays, dict):
            errors.append("source grounding: overlay_values must be an object")
        else:
            for language in ("zh", "en"):
                values = raw_overlays.get(language) or []
                if not isinstance(values, list):
                    errors.append(f"source grounding: {language} overlay_values must be a list")
                else:
                    overlay_values[language] = [_text(value) for value in values if _text(value)]
        if grounding.get("status") not in {None, "reviewed"}:
            errors.append(
                f"source grounding: status must be reviewed, found {grounding.get('status')!r}"
            )
        if grounding.get("source_sha256") not in {None, facts.get("source_sha256")}:
            errors.append("source grounding: source_sha256 does not match facts")

    # Source text is the primary allow-list.  Reviewed translations and
    # narrowly approved derivations are the only trace-based exceptions.
    allowed = {
        language: {_canonical(value) for value in trace_values[language]
                   + overlay_values[language] if _text(value)}
        for language in ("zh", "en")
    }
    # These fallback strings are not generally allowed. They become valid
    # only when the original source explicitly concludes that the material is
    # non-hazardous under GHS; this prevents a model from adding them merely to
    # fill an empty pictogram/signal slot.
    search_source = prepared_source or source
    source_corpus = _canonical(_source_text(search_source))
    if re.search(r"不属于(?:危险|危害)|nothazardous|notclassified", source_corpus, re.I):
        allowed["zh"].update({
            _canonical("无信号词"),
            _canonical("无危险的象形图警示性说明"),
        })
        allowed["en"].update({
            _canonical("No signal word"),
            _canonical("No hazard pictograms or precautionary statements"),
        })
    unbound: list[dict] = []
    for language in ("zh", "en"):
        payloads = list(_iter_payloads(facts.get(language), language))
        payloads.extend(_iter_control_payloads(facts, language) or [])
        for location, value in payloads:
            candidate = _canonical(value)
            if not candidate:
                continue
            if _source_anchor(value, _source_text(search_source)):
                continue
            if candidate in allowed[language] or any(
                candidate in item or item in candidate for item in allowed[language]
                if len(item) >= 4
            ):
                continue
            item = {"language": language, "location": location, "value": value}
            unbound.append(item)
            errors.append(
                f"source grounding: {location} value has no reviewed fact/source anchor: {value[:120]}"
            )

    record_count = (
        len(grounding.get("records") or [])
        if isinstance(grounding, dict) and grounding.get("status") == "reviewed"
        else 0
    )
    return {
        "status": "passed" if not errors else "failed",
        "model": model,
        "source": str(source),
        "source_search_path": str(search_source),
        "prepared_source": str(prepared_source) if prepared_source else None,
        "fact_count": len(ledger_by_id),
        "trace_value_count": sum(len(values) for values in trace_values.values()),
        "overlay_value_count": sum(len(values) for values in overlay_values.values()),
        "grounding_record_count": record_count,
        "unbound_values": unbound,
        "errors": errors,
    }


def validate(facts: dict, source: Path, model: str,
             prepared_source: Path | None = None) -> list[str]:
    return audit(facts, source, model, prepared_source=prepared_source).get("errors", [])


__all__ = ["audit", "validate"]
