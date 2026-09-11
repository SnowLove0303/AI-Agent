"""Fail-closed source interpretation and output traceability contract.

The MSDS overwrite pipeline must not jump directly from a source document to a
template value cell.  This module validates the intermediate evidence records:

* ``source_coverage`` inventories what the extractor actually saw;
* ``fact_ledger`` gives every extracted fact a stable ID and source locator;
* ``source_mapping`` disposes every fact and every S1-S16 section; and
* ``output_traceability`` connects written/hidden targets back to the facts.

The module deliberately has no DOCX mutation code.  It is a pre-clone gate and
therefore cannot be bypassed by a formatting or value-writing helper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = SKILL_ROOT / "openspec" / "source_interpretation_contract.json"
SECTION_KEYS = {f"s{i}" for i in range(1, 17)}
MAPPING_DECISIONS = {
    "mapped",
    "omitted",
    "not_applicable",
    "source_only",
    "duplicate",
    "conflict",
    "unresolved",
}
BLOCKING_DECISIONS = {"conflict", "unresolved"}
TRACE_DECISIONS = {"written", "hidden", "not_written", "merged"}
LINE_BREAK_POLICIES = {
    "preserve_logical_lines",
    "field_value_lines",
    "structured_field_lines",
    "transport_field_lines",
    "verbatim_single_line",
    "not_written",
}


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: object) -> str:
    return str(value or "").strip()


def _key(value: object) -> str:
    return "".join(_text(value).replace("：", ":").split())


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_source_coverage(coverage: object, source_hash: str) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    unit_ids: set[str] = set()
    if not isinstance(coverage, dict):
        return ["source interpretation: source_coverage is missing"], unit_ids

    for field in load_spec().get("required_source_coverage_fields", []):
        if field not in coverage:
            _error(errors, f"source interpretation: source_coverage missing {field}")
    if coverage.get("source_sha256") != source_hash:
        _error(errors, "source interpretation: source_coverage source_sha256 does not match original source")
    if coverage.get("status") != "ready":
        _error(errors, f"source interpretation: source_coverage status must be ready, found {coverage.get('status')!r}")

    units = coverage.get("source_units")
    if not isinstance(units, list) or not units:
        _error(errors, "source interpretation: source_coverage source_units must be a non-empty list")
        units = []
    for index, unit in enumerate(units, start=1):
        if not isinstance(unit, dict):
            _error(errors, f"source interpretation: source unit {index} is not an object")
            continue
        unit_id = _text(unit.get("unit_id"))
        if not unit_id:
            _error(errors, f"source interpretation: source unit {index} has no unit_id")
        elif unit_id in unit_ids:
            _error(errors, f"source interpretation: duplicate source unit {unit_id}")
        else:
            unit_ids.add(unit_id)
        if not _text(unit.get("source_locator")):
            _error(errors, f"source interpretation: source unit {index} has no source_locator")
        if not _text(unit.get("text")) and not _text(unit.get("image_name")):
            _error(errors, f"source interpretation: source unit {index} has no text or image_name")
        if unit.get("processing_status") not in {"extracted", "reviewed", "reviewed_structural"}:
            _error(errors, f"source interpretation: source unit {index} has invalid processing_status")

    for key in ("unmapped", "unreadable"):
        value = coverage.get(key)
        if not isinstance(value, list):
            _error(errors, f"source interpretation: source_coverage {key} must be a list")
        elif value:
            _error(errors, f"source interpretation: source_coverage has {len(value)} {key} item(s)")

    counts = coverage.get("counts")
    if not isinstance(counts, dict):
        _error(errors, "source interpretation: source_coverage counts is missing")
    else:
        expected_counts = {
            "source_unit_count": len(unit_ids),
            "processed_unit_count": len(unit_ids),
            "unmapped_count": len(coverage.get("unmapped") or []),
            "unreadable_count": len(coverage.get("unreadable") or []),
        }
        for key, expected in expected_counts.items():
            if counts.get(key) != expected:
                _error(errors, f"source interpretation: source_coverage counts.{key} must be {expected}")
        image_count = counts.get("image_count")
        reviewed_image_count = counts.get("reviewed_image_count")
        if not isinstance(image_count, int) or not isinstance(reviewed_image_count, int):
            _error(errors, "source interpretation: image_count and reviewed_image_count are required integers")
        elif reviewed_image_count != image_count:
            _error(errors, "source interpretation: every discovered image must be reviewed")
    return errors, unit_ids


def _validate_fact_ledger(ledger: object, unit_ids: set[str]) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    fact_ids: set[str] = set()
    locators: set[str] = set()
    if not isinstance(ledger, list) or not ledger:
        return ["source interpretation: fact_ledger must be a non-empty list"], fact_ids
    required = load_spec().get("required_fact_fields", [])
    allowed_evidence = set(load_spec().get("evidence_types", []))
    allowed_status = set(load_spec().get("fact_mapping_statuses", []))
    for index, fact in enumerate(ledger, start=1):
        if not isinstance(fact, dict):
            _error(errors, f"source interpretation: fact {index} is not an object")
            continue
        for field in required:
            if field not in fact:
                _error(errors, f"source interpretation: fact {index} missing {field}")
        fact_id = _text(fact.get("fact_id"))
        if not fact_id:
            _error(errors, f"source interpretation: fact {index} has no fact_id")
        elif fact_id in fact_ids:
            _error(errors, f"source interpretation: duplicate fact_id {fact_id}")
        else:
            fact_ids.add(fact_id)
        locator = _text(fact.get("source_locator"))
        if locator in locators and locator:
            _error(errors, f"source interpretation: duplicate fact source_locator {locator}")
        elif locator:
            locators.add(locator)
        if fact.get("source_section") not in SECTION_KEYS:
            _error(errors, f"source interpretation: fact {index} has invalid source_section")
        if not _text(fact.get("source_text")):
            _error(errors, f"source interpretation: fact {index} has no source_text")
        if not _text(fact.get("normalized_value")):
            _error(errors, f"source interpretation: fact {index} has no normalized_value")
        source_unit_ids = fact.get("source_unit_ids")
        if not isinstance(source_unit_ids, list) or not source_unit_ids:
            _error(errors, f"source interpretation: fact {index} has no source_unit_ids")
        else:
            unknown = [item for item in source_unit_ids if item not in unit_ids]
            if unknown:
                _error(errors, f"source interpretation: fact {index} references unknown source units: {unknown}")
        if fact.get("evidence_type") not in allowed_evidence:
            _error(errors, f"source interpretation: fact {index} has invalid evidence_type")
        if fact.get("mapping_status") not in allowed_status:
            _error(errors, f"source interpretation: fact {index} has invalid mapping_status")
        if fact.get("line_break_policy") not in LINE_BREAK_POLICIES:
            _error(errors, f"source interpretation: fact {index} has invalid line_break_policy")
    return errors, fact_ids


def _validate_mapping(mapping: object, fact_ids: set[str], model: str,
                      source_hash: str) -> tuple[list[str], dict[str, dict]]:
    errors: list[str] = []
    by_fact: dict[str, dict] = {}
    if not isinstance(mapping, dict):
        return ["source interpretation: source_mapping is missing"], by_fact
    if mapping.get("model") != model:
        _error(errors, "source interpretation: source_mapping model does not match requested model")
    if mapping.get("source_sha256") != source_hash:
        _error(errors, "source interpretation: source_mapping source_sha256 does not match original source")
    if mapping.get("status") != "reviewed":
        _error(errors, "source interpretation: source_mapping status must be reviewed")
    if mapping.get("unresolved") != []:
        _error(errors, "source interpretation: source_mapping unresolved must be empty")
    items = mapping.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["source interpretation: source_mapping items are missing"], by_fact
    target_keys: set[tuple[str, str]] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            _error(errors, f"source interpretation: mapping item {index} is not an object")
            continue
        source_kind = item.get("source_kind", "fact")
        if source_kind == "section_presence":
            if item.get("decision") not in {"omitted", "not_applicable"}:
                _error(errors, f"source interpretation: section-presence item {index} must be omitted/not_applicable")
            if not _text(item.get("reason")):
                _error(errors, f"source interpretation: section-presence item {index} needs a reason")
            continue
        fact_id = _text(item.get("fact_id"))
        if not fact_id:
            _error(errors, f"source interpretation: mapping item {index} has no fact_id")
            continue
        if fact_id not in fact_ids:
            _error(errors, f"source interpretation: mapping item {index} references unknown fact_id {fact_id}")
        if fact_id in by_fact:
            _error(errors, f"source interpretation: fact_id {fact_id} is disposed more than once")
        else:
            by_fact[fact_id] = item
        decision = item.get("decision")
        if decision not in MAPPING_DECISIONS:
            _error(errors, f"source interpretation: mapping item {index} has invalid decision")
        elif decision in BLOCKING_DECISIONS:
            _error(errors, f"source interpretation: mapping item {index} remains {decision}")
        if decision == "mapped":
            target_section = item.get("target_section")
            target_slot = _text(item.get("target_slot"))
            if target_section not in SECTION_KEYS or not target_slot:
                _error(errors, f"source interpretation: mapped item {index} needs target_section and target_slot")
            elif not target_slot.casefold().startswith(target_section.casefold() + "."):
                _error(errors, f"source interpretation: mapping item {index} target_slot is outside target_section")
            else:
                key = (target_section, target_slot)
                if key in target_keys:
                    _error(errors, f"source interpretation: duplicate mapped target_slot {target_slot}")
                target_keys.add(key)
        elif decision in {"omitted", "not_applicable", "source_only", "duplicate"}:
            if not _text(item.get("reason")) and decision != "duplicate":
                _error(errors, f"source interpretation: {decision} item {index} needs a reason")
            if decision == "duplicate" and not _text(item.get("canonical_fact_id")):
                _error(errors, f"source interpretation: duplicate item {index} needs canonical_fact_id")
            if decision == "source_only" and any(_text(item.get(key)) for key in ("target_section", "target_slot")):
                _error(errors, f"source interpretation: source_only item {index} cannot claim an output target")
        if decision in {"mapped", "omitted", "not_applicable", "source_only", "duplicate"}:
            policy = item.get("line_break_policy")
            if policy not in LINE_BREAK_POLICIES:
                _error(errors, f"source interpretation: mapping item {index} has invalid line_break_policy")
    missing = sorted(fact_ids - set(by_fact))
    if missing:
        _error(errors, "source interpretation: facts without a reviewed disposition: " + ", ".join(missing))
    return errors, by_fact


def _validate_traceability(trace: object, fact_ids: set[str], mapping_by_fact: dict[str, dict],
                           source_hash: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["source interpretation: output_traceability is missing"]
    spec = load_spec()
    if trace.get("spec_id") != spec["spec_id"]:
        _error(errors, "source interpretation: output_traceability spec_id does not match active contract")
    if trace.get("spec_version") != spec["version"]:
        _error(errors, "source interpretation: output_traceability spec_version does not match active contract")
    if trace.get("status") != "reviewed":
        _error(errors, "source interpretation: output_traceability status must be reviewed")
    if trace.get("source_sha256") != source_hash:
        _error(errors, "source interpretation: output_traceability source_sha256 does not match original source")
    items = trace.get("items")
    if not isinstance(items, list):
        _error(errors, "source interpretation: output_traceability items must be a list")
        items = []
    seen_targets: set[tuple[str, str]] = set()
    traced_facts: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            _error(errors, f"source interpretation: trace item {index} is not an object")
            continue
        target_section = item.get("target_section")
        target_slot = _text(item.get("target_slot"))
        if target_section not in SECTION_KEYS or not target_slot:
            _error(errors, f"source interpretation: trace item {index} needs target_section and target_slot")
        else:
            key = (target_section, target_slot)
            if key in seen_targets:
                _error(errors, f"source interpretation: duplicate output target {target_slot}")
            seen_targets.add(key)
        decision = item.get("decision")
        if decision not in TRACE_DECISIONS:
            _error(errors, f"source interpretation: trace item {index} has invalid decision")
        policy = item.get("line_break_policy")
        if policy not in LINE_BREAK_POLICIES:
            _error(errors, f"source interpretation: trace item {index} has invalid line_break_policy")
        source_fact_ids = item.get("source_fact_ids", [])
        if not isinstance(source_fact_ids, list):
            _error(errors, f"source interpretation: trace item {index} source_fact_ids must be a list")
            source_fact_ids = []
        unknown = [fact_id for fact_id in source_fact_ids if fact_id not in fact_ids]
        if unknown:
            _error(errors, f"source interpretation: trace item {index} references unknown facts: {unknown}")
        traced_facts.update(source_fact_ids)
        if decision in {"written", "merged"} and not source_fact_ids:
            _error(errors, f"source interpretation: written trace item {index} has no source_fact_ids")
        if decision in {"written", "merged"}:
            output_values = item.get("output_values")
            if not isinstance(output_values, dict):
                _error(errors, f"source interpretation: written trace item {index} needs output_values")
            else:
                for language in ("zh", "en"):
                    if not isinstance(output_values.get(language), str) or not output_values[language].strip():
                        _error(errors, f"source interpretation: written trace item {index} needs non-empty {language} output_value")
        if decision in {"hidden", "not_written"}:
            if not _text(item.get("reason")):
                _error(errors, f"source interpretation: hidden/not_written trace item {index} needs a reason")
            if item.get("presence_status") not in {
                "source_absent", "explicit_missing", "unsupported", "not_applicable", "source_only", "duplicate"
            }:
                _error(errors, f"source interpretation: trace item {index} has invalid presence_status")
    empty_decisions = trace.get("empty_decisions")
    if not isinstance(empty_decisions, list):
        _error(errors, "source interpretation: output_traceability empty_decisions must be a list")
    for fact_id, mapping in mapping_by_fact.items():
        decision = mapping.get("decision")
        if decision == "mapped" and fact_id not in traced_facts:
            _error(errors, f"source interpretation: mapped fact {fact_id} has no output trace")
    return errors


def validate_source_interpretation(facts: dict, source: Path, model: str) -> list[str]:
    """Return all source interpretation blockers before template cloning."""
    errors: list[str] = []
    if not source.is_file():
        return [f"source interpretation: original source is missing: {source}"]
    source_hash = sha256(source)
    coverage_errors, unit_ids = _validate_source_coverage(facts.get("source_coverage"), source_hash)
    errors.extend(coverage_errors)
    ledger_errors, fact_ids = _validate_fact_ledger(facts.get("fact_ledger"), unit_ids)
    errors.extend(ledger_errors)
    mapping_errors, mapping_by_fact = _validate_mapping(
        facts.get("source_mapping"), fact_ids, model, source_hash
    )
    errors.extend(mapping_errors)
    errors.extend(_validate_traceability(
        facts.get("output_traceability"), fact_ids, mapping_by_fact, source_hash
    ))
    return errors


def blank_output_traceability(source_hash: str) -> dict:
    """Return the review-required output trace record for extraction drafts."""
    return {
        "spec_id": load_spec()["spec_id"],
        "spec_version": load_spec()["version"],
        "status": "needs-review",
        "source_sha256": source_hash,
        "items": [],
        "empty_decisions": [],
    }


__all__ = [
    "LINE_BREAK_POLICIES",
    "SECTION_KEYS",
    "SPEC_PATH",
    "blank_output_traceability",
    "load_spec",
    "sha256",
    "validate_source_interpretation",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit source coverage, fact provenance, mapping and output traceability"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("facts", type=Path)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    try:
        facts = json.loads(args.facts.read_text(encoding="utf-8"))
        errors = validate_source_interpretation(facts, args.source, args.model)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "errors": [str(exc)]}, ensure_ascii=False))
        return 1
    result = {"status": "ready" if not errors else "blocked", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
