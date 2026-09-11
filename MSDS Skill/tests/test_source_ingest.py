from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_ingest import (  # noqa: E402
    SourceSelectionError,
    discover_source,
    prepare_source,
    require_section_extraction,
)


def test_pdf_is_publication_only_and_cannot_be_a_source(tmp_path):
    source = tmp_path / "PU-2411.pdf"
    source.write_bytes(b"source")
    with pytest.raises(SourceSelectionError, match="publication-only"):
        discover_source(source)


def test_directory_discovery_requires_one_unambiguous_candidate(tmp_path):
    (tmp_path / "~$PU-2411.docx").write_bytes(b"lock")
    source = tmp_path / "PU-2411.docx"
    source.write_bytes(b"docx")
    selected = discover_source(tmp_path, model="PU-2411")
    assert selected.original_path == source.resolve()

    (tmp_path / "PU-2411.xlsx").write_bytes(b"spreadsheet")
    with pytest.raises(SourceSelectionError, match="ambiguous"):
        discover_source(tmp_path, model="PU-2411")


def test_direct_docx_source_is_the_only_extraction_path_without_conversion(tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"docx")
    selected = discover_source(source)
    with prepare_source(selected) as prepared:
        assert prepared.adapter == "direct-docx"
        assert prepared.extraction_path == source.resolve()
        assert require_section_extraction(prepared) == source.resolve()


def test_formal_output_cannot_be_reused_as_source(tmp_path):
    output = tmp_path / "PU-2411_MSDS_CN_冠志.docx"
    output.write_bytes(b"formal output")
    with pytest.raises(SourceSelectionError, match="formal MSDS output"):
        discover_source(output)


def test_renamed_generated_file_in_output_directory_cannot_be_reused(tmp_path):
    output_dir = tmp_path / "覆写产出"
    output_dir.mkdir()
    renamed = output_dir / "reviewed_source.docx"
    renamed.write_bytes(b"renamed generated output")
    with pytest.raises(SourceSelectionError, match="generated/output directory"):
        discover_source(renamed)


def test_docx_preview_checkpoint_cannot_be_reused_as_source(tmp_path):
    preview_dir = tmp_path / "_docx_preview"
    preview_dir.mkdir()
    preview = preview_dir / "reviewed_source.docx"
    preview.write_bytes(b"audited DOCX checkpoint")
    with pytest.raises(SourceSelectionError, match="generated/output directory"):
        discover_source(preview)
