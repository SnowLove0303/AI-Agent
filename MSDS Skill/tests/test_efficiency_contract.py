"""Regression tests for the V3.24 four-stage efficiency contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from diagnostics import format_diagnostic  # noqa: E402
from efficiency_contract import (  # noqa: E402
    BUSINESS_STAGES,
    StageTimer,
    load_efficiency_spec,
    validate_efficiency_spec,
)


def test_efficiency_openspec_is_active_and_ordered():
    spec = load_efficiency_spec()
    assert spec["spec_id"] == "MSDS-EFFICIENCY-001"
    assert validate_efficiency_spec(spec) == []
    assert tuple(stage["id"] for stage in spec["business_stages"]) == BUSINESS_STAGES
    assert [target["id"] for target in spec["target_points"]] == [
        "EFF-01", "EFF-02", "EFF-03", "EFF-04", "EFF-05", "EFF-06"
    ]


def test_stage_timer_aggregates_without_changing_failure_semantics():
    timer = StageTimer()
    with timer.stage("extract_all_source_information", adapter="direct-docx"):
        pass
    timer.add("extract_all_source_information", 0.25, source_format="docx")
    snapshot = timer.snapshot()
    assert len(snapshot["events"]) == 2
    assert snapshot["totals"]["extract_all_source_information"] >= 0.25
    assert all(event["status"] == "ok" for event in snapshot["events"])


def test_diagnostic_has_actionable_expected_actual_diff_and_hint():
    message = format_diagnostic(
        "FORMAT_MISMATCH", location="table=2 row=4",
        expected="tcPr=A", actual="tcPr=B", hint="restore the template anchor",
    )
    assert "[FORMAT_MISMATCH]" in message
    assert "location=table=2 row=4" in message
    assert "expected=tcPr=A" in message
    assert "actual=tcPr=B" in message
    assert "diff=expected!=actual" in message
    assert "hint=restore the template anchor" in message
