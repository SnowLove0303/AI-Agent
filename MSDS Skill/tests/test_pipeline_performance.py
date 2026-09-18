"""Regression tests for the V3.24 Harness performance controls."""

import inspect
from pathlib import Path

import pytest

from convert_docx_to_pdf import convert, find_wpscli, preflight, version
from msds_pipeline import (build_matrix, gate_output_matrix, resolve_cache_dir,
                           resolve_pdf_workers)


def test_build_matrix_has_batch_performance_controls():
    params = inspect.signature(build_matrix).parameters
    assert {"pdf_workers", "wpscli", "progress_callback", "docx_preview_dir", "cache_dir"} <= set(params)
    assert "converter_version" in inspect.signature(convert).parameters
    assert "template_path" in inspect.signature(preflight).parameters
    assert hasattr(find_wpscli, "cache_info")
    assert hasattr(version, "cache_info")


def test_invalid_pdf_worker_count_fails_before_source_io(tmp_path):
    with pytest.raises(ValueError, match="pdf_workers"):
        build_matrix(
            source=Path("does-not-exist.docx"),
            facts={"model": "PERF-TEST"},
            out_root=tmp_path / "out",
            model="PERF-TEST",
            do_pdf=True,
            pdf_workers=0,
        )


def test_cache_root_is_explicit_or_deterministic(tmp_path):
    assert resolve_cache_dir(tmp_path / "out") == (tmp_path / "out" / ".msds_cache").resolve()
    explicit = tmp_path / "shared-cache"
    assert resolve_cache_dir(tmp_path / "out", explicit) == explicit.resolve()


def test_pdf_workers_are_bounded_by_variant_count():
    assert resolve_pdf_workers(1, 4) == 1
    assert resolve_pdf_workers(99, 4) == 4
    with pytest.raises(ValueError, match="pdf_workers"):
        resolve_pdf_workers(0, 4)


def test_matrix_gate_rejects_pdf_lineage_hash_drift(tmp_path):
    model = "EFF-TEST"
    from output_matrix import output_names
    import hashlib

    records = []
    for name in output_names(model):
        docx = tmp_path / name
        pdf = docx.with_suffix(".pdf")
        docx.write_bytes((name + "-docx").encode())
        pdf.write_bytes((name + "-pdf").encode())
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({
            "output_path": str(docx),
            "pdf_path": str(pdf),
            "pdf_evidence": {
                "source_sha256": digest(docx),
                "output_sha256": digest(pdf),
                "source_is_final_docx": True,
            },
        })
    gate_output_matrix(tmp_path, model, records, True)
    records[0]["pdf_evidence"]["source_sha256"] = "stale"
    with pytest.raises(Exception, match="not bound"):
        gate_output_matrix(tmp_path, model, records, True)
