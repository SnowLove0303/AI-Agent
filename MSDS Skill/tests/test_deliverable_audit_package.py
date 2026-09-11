import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_deliverable_package import run_audit  # noqa: E402
from deliverable_audit_framework import MATRIX, write_reports  # noqa: E402


def _package(tmp_path, model="TEST-1"):
    for key, aliases in MATRIX.items():
        suffix = aliases[1]
        language = "en" if key.startswith("en") else "cn"
        brand = "guanzhi" if "guanzhi" in key else "guocai"
        d = tmp_path / f"{brand}_{language}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{model}_{suffix}.docx").write_bytes(b"docx")
        (d / f"{model}_{suffix}.pdf").write_bytes(b"pdf")
    (tmp_path / "matrix-report.json").write_text(json.dumps({
        "product": model, "docx_count": 4, "pdf_count": 4,
        "formal_ready_count": 4, "shared_blocker": None,
    }), encoding="utf-8")


def test_nested_matrix_discovery_and_report(tmp_path):
    _package(tmp_path)
    result = run_audit(tmp_path, "TEST-1", template_cn=tmp_path / "cn.docx", template_en=tmp_path / "en.docx")
    # Template files need to exist for template-control evidence in this
    # contract test; the package matrix itself remains independently checked.
    assert result["package"]["complete"]
    assert len(result["records"]) == 22
    # The deliberately invalid placeholder DOCX proves the auditor fails
    # closed instead of accepting a package whose source documents cannot be
    # parsed.
    assert result["outcome"] == "RELEASE_FAIL"


def test_report_serialization_is_machine_and_human_readable(tmp_path):
    _package(tmp_path)
    result = run_audit(tmp_path, "TEST-1")
    write_reports(result, tmp_path / "audit.json", tmp_path / "audit.txt")
    assert json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))["outcome"] == result["outcome"]
    assert "Outcome:" in (tmp_path / "audit.txt").read_text(encoding="utf-8")


def test_incomplete_duplicate_matrix_short_circuits_expensive_docx_scan(tmp_path, monkeypatch):
    _package(tmp_path)
    original = next(tmp_path.rglob("TEST-1_MSDS_CN_Guanzhi.docx"))
    duplicate = tmp_path / "stale-copy" / original.name
    duplicate.parent.mkdir()
    duplicate.write_bytes(b"stale")

    def fail_if_opened(_path):
        raise AssertionError("incomplete matrix should short-circuit DOCX text scanning")

    monkeypatch.setattr("audit_deliverable_package._docx_text", fail_if_opened)
    result = run_audit(tmp_path, "TEST-1")
    assert result["package"]["complete"] is False
    assert result["outcome"] == "RELEASE_FAIL"
    src_record = next(record for record in result["records"] if record["rule_id"] == "SRC-002")
    assert src_record["status"] == "NOT_CHECKED"
