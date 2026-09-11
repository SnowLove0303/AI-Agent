"""Regression tests for the 3.21.0 Harness performance controls."""

import inspect
from pathlib import Path

import pytest

from convert_docx_to_pdf import convert, find_wpscli, preflight, version
from msds_pipeline import build_matrix


def test_build_matrix_has_batch_performance_controls():
    params = inspect.signature(build_matrix).parameters
    assert {"pdf_workers", "wpscli", "progress_callback", "docx_preview_dir"} <= set(params)
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
