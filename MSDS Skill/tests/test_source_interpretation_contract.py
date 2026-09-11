from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_source_facts import extract  # noqa: E402
from source_interpretation_contract import validate_source_interpretation  # noqa: E402


SOURCE = ROOT / "examples" / "regression_HPU-7660_source.docx"


def reviewed_facts():
    facts = extract(SOURCE)
    facts["source_mapping"]["status"] = "reviewed"
    facts["source_mapping"]["unresolved"] = []
    for item in facts["source_mapping"]["items"]:
        if item.get("fact_id"):
            item["review_status"] = "reviewed"
            item["decision"] = "mapped"
    facts["output_traceability"] = {
        "spec_id": "MSDS-SOURCE-INTERPRETATION-001",
        "spec_version": "1.0.0",
        "status": "reviewed",
        "source_sha256": facts["source_sha256"],
        "items": [
            {
                "target_section": item["target_section"],
                "target_slot": item["target_slot"],
                "decision": "written",
                "source_fact_ids": [item["fact_id"]],
                "line_break_policy": item["line_break_policy"],
                "output_values": {"zh": item["source_text"], "en": item["source_text"]},
            }
            for item in facts["source_mapping"]["items"]
            if item.get("fact_id")
        ],
        "empty_decisions": [],
    }
    return facts


def test_extractor_emits_coverage_ledger_and_traceability_draft():
    facts = extract(SOURCE)
    coverage = facts["source_coverage"]
    assert coverage["status"] == "ready"
    assert coverage["unmapped"] == []
    assert coverage["unreadable"] == []
    assert coverage["counts"]["source_unit_count"] == len(coverage["source_units"])
    assert facts["fact_ledger"]
    assert len({item["fact_id"] for item in facts["fact_ledger"]}) == len(facts["fact_ledger"])
    assert all(item["source_unit_ids"] for item in facts["fact_ledger"])
    assert facts["output_traceability"]["status"] == "needs-review"


def test_reviewed_source_interpretation_is_accepted():
    facts = reviewed_facts()
    assert validate_source_interpretation(facts, SOURCE, facts["model"]) == []


def test_unreadable_source_unit_blocks_even_when_mapping_is_reviewed():
    facts = reviewed_facts()
    facts["source_coverage"]["unreadable"] = [{"unit_id": "SRC-T01-R001-C001-L01"}]
    facts["source_coverage"]["status"] = "needs-review"
    facts["source_coverage"]["counts"]["unreadable_count"] = 1
    errors = validate_source_interpretation(facts, SOURCE, facts["model"])
    assert any("source_coverage status must be ready" in error for error in errors)
    assert any("unreadable" in error for error in errors)


def test_missing_fact_traceability_blocks_before_overwrite():
    facts = reviewed_facts()
    facts["output_traceability"]["items"].pop()
    errors = validate_source_interpretation(facts, SOURCE, facts["model"])
    assert any("has no output trace" in error for error in errors)


def test_source_only_disposition_requires_reason_and_no_target():
    facts = reviewed_facts()
    item = next(item for item in facts["source_mapping"]["items"] if item.get("fact_id"))
    item["decision"] = "source_only"
    item.pop("target_section", None)
    item.pop("target_slot", None)
    item["reason"] = "The formal template has no corresponding field."
    facts["output_traceability"]["items"] = [
        entry for entry in facts["output_traceability"]["items"]
        if item["fact_id"] not in entry["source_fact_ids"]
    ]
    assert validate_source_interpretation(facts, SOURCE, facts["model"]) == []


def test_mapping_conflict_is_a_hard_blocker():
    facts = reviewed_facts()
    item = next(item for item in facts["source_mapping"]["items"] if item.get("fact_id"))
    item["decision"] = "conflict"
    item["reason"] = "Two source locations disagree."
    facts["output_traceability"]["items"] = [
        entry for entry in facts["output_traceability"]["items"]
        if item["fact_id"] not in entry["source_fact_ids"]
    ]
    errors = validate_source_interpretation(facts, SOURCE, facts["model"])
    assert any("remains conflict" in error for error in errors)
