from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_efficiency_workflow as workflow  # noqa: E402


SOURCE = ROOT / "examples" / "regression_HPU-7660_source.docx"


def test_first_invocation_stops_at_review_checkpoint(tmp_path):
    result = workflow.run_workflow(
        source=SOURCE, workspace=tmp_path / "run", model="HPU-7660"
    )

    assert result["outcome"] == "EVIDENCE_PACKET_READY"
    state = json.loads((tmp_path / "run" / "workflow-state.json").read_text(encoding='utf-8'))
    assert state["status"] == "awaiting_review"
    assert state["stages"]["review"]["status"] == "required"
    assert state["stages"]["preflight"]["status"] == "pending"
    assert not (tmp_path / "run" / "output").exists()


def test_blocked_preflight_never_starts_build(tmp_path, monkeypatch):
    calls = []

    def fake_preflight(*args, **kwargs):
        return {"status": "blocked", "errors": ["source mapping unresolved"]}

    def fail_build(*args, **kwargs):
        calls.append("build")
        raise AssertionError("formal build must not start after blocked preflight")

    monkeypatch.setattr(workflow, "run_preflight", fake_preflight)
    monkeypatch.setattr(workflow, "build_matrix", fail_build)
    facts = tmp_path / "approved.json"
    facts.write_text(json.dumps({"model": "HPU-7660"}), encoding="utf-8")

    result = workflow.run_workflow(
        source=SOURCE, workspace=tmp_path / "run", model="HPU-7660", facts=facts
    )

    assert result["outcome"] == "PREFLIGHT_BLOCKED"
    assert calls == []
    state = json.loads((tmp_path / "run" / "workflow-state.json").read_text(encoding='utf-8'))
    assert state["status"] == "preflight_blocked"
    assert state["stages"]["build"]["status"] == "not_started"


def test_passed_preflight_calls_formal_build_once(tmp_path, monkeypatch):
    calls = []

    monkeypatch.setattr(workflow, "run_preflight", lambda *a, **k: {"status": "ready", "errors": []})

    def fake_build(**kwargs):
        calls.append(kwargs)
        return {
            "output_root": str(tmp_path / "run" / "output" / "HPU-7660"),
            "docx_count": 4,
            "pdf_count": 0,
            "timing": {"total_seconds": 1.0},
        }

    monkeypatch.setattr(workflow, "build_matrix", fake_build)
    facts = tmp_path / "approved.json"
    facts.write_text(json.dumps({"model": "HPU-7660"}), encoding="utf-8")

    result = workflow.run_workflow(
        source=SOURCE, workspace=tmp_path / "run", model="HPU-7660",
        facts=facts, no_pdf=True,
    )

    assert result["outcome"] == "RELEASE_PASS"
    assert len(calls) == 1
    assert calls[0]["do_pdf"] is False
    state = json.loads((tmp_path / "run" / "workflow-state.json").read_text(encoding='utf-8'))
    assert state["status"] == "release_pass"
    assert state["stages"]["build"]["status"] == "passed"


def test_runtime_environment_shield_catches_embedded(monkeypatch):
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\LibreOffice\program\python.exe")
    with pytest.raises(RuntimeError, match="Detected embedded office interpreter"):
        workflow.check_runtime_environment()

    # When allow_embedded=True, it reports warning instead of raising
    report = workflow.check_runtime_environment(allow_embedded=True)
    assert report["status"] == "warning"
    assert any("embedded office" in issue for issue in report["issues"])


def test_stage_timing_ledger_emission(tmp_path):
    result = workflow.run_workflow(
        source=SOURCE, workspace=tmp_path / "run", model="HPU-7660"
    )
    ledger_file = tmp_path / "run" / "timing-stage-ledger.json"
    assert ledger_file.exists()
    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
    assert ledger["version"] == "1.0.0"
    assert any(s["stage"] == "evidence" for s in ledger["stages"])
    assert any(s["stage"] == "review" for s in ledger["stages"])
