import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from deliverable_audit_framework import (  # noqa: E402
    CATEGORY_WEIGHTS,
    RULES,
    evidence,
    rule_map,
    score_and_decide,
    validate_evidence,
)


def _complete(status="PASS"):
    return [evidence(r.rule_id, status, method="fixture", observed={"fixture": True},
                     evidence_paths=["fixture.json"], message="fixture result") for r in RULES]


def test_registry_is_unique_and_weights_total_100():
    assert len(rule_map()) == len(RULES)
    assert sum(CATEGORY_WEIGHTS.values()) == 100
    assert sum(r.points for r in RULES) == 100


def test_release_pass_requires_95_and_complete_evidence():
    result = score_and_decide(_complete())
    assert result["score"] == 100
    assert result["outcome"] == "RELEASE_PASS"
    assert result["evidence_errors"] == []


def test_high_score_does_not_override_b1():
    records = _complete()
    records[0] = evidence("ID-001", "FAIL", method="fixture", observed={"duplicate": True},
                          evidence_paths=["fixture.json"], message="duplicate matrix slot")
    result = score_and_decide(records)
    assert result["score"] < 100
    assert result["outcome"] == "RELEASE_FAIL"
    assert result["blockers"][0]["severity"] == "B0"


def test_missing_or_error_evidence_fails_closed():
    records = _complete()
    records[1] = evidence("ID-002", "NOT_CHECKED", method="missing source", observed=None,
                          evidence_paths=["missing.json"], message="source was not supplied")
    result = score_and_decide(records)
    assert result["outcome"] == "NOT_READY"
    assert result["incomplete"]


def test_observation_mode_is_not_a_release_claim():
    result = score_and_decide(_complete(), observation_only=True)
    assert result["outcome"] == "OBSERVATION_ONLY"


def test_evidence_requires_all_registered_rules():
    errors = validate_evidence(_complete()[:-1])
    assert any("missing required rule" in error for error in errors)
