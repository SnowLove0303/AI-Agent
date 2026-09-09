import importlib.util
import json
import hashlib
import sys
from pathlib import Path

import pytest
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from msds_pipeline import ReleaseBlocked, build_matrix, gate_output_matrix, sha256
from output_matrix import output_names


def _os9015_facts():
    from docx import Document  # noqa: F401  (ensures python-docx present)
    spec = importlib.util.spec_from_file_location(
        "os9015_facts_probe", ROOT / "_task_work" / "generate_os9015_eight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    zh = module.source_facts("zh", "guanzhi")
    en = module.source_facts("en", "guanzhi")
    source = ROOT / "examples" / "regression_HPU-7660_source.docx"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    return {
        "model": "OS-9015",
        "revision": "2025/2/22",
        "source_sha256": source_hash,
        "zh": {f"s{sec}": zh[f"s{sec}"] for sec in range(1, 17)},
        "en": {f"s{sec}": en[f"s{sec}"] for sec in range(1, 17)},
        "s8_control_parameters": {"zh": [], "en": []},
        "source_mapping": {
            "model": "OS-9015",
            "source_sha256": source_hash,
            "status": "reviewed",
            "unresolved": [],
            "items": [{
                "source_locator": f"s{section}.table",
                "source_section": f"s{section}",
                "source_text": f"verified source section {section}",
                "decision": "mapped",
                "target_section": f"s{section}",
            } for section in range(1, 17)],
        },
        "translation_review": [],
    }


def test_pipeline_builds_matrix_docx_only(tmp_path):
    facts = _os9015_facts()
    source = ROOT / "examples" / "regression_HPU-7660_source.docx"
    report = build_matrix(source=source, facts=facts,
                          out_root=tmp_path / "matrix", do_pdf=False)
    records = report["records"]
    assert report["docx_count"] == 4
    assert report["pdf_count"] == 0
    assert (tmp_path / "matrix" / "matrix-report.json").is_file()
    for record in records:
        assert record["status"] == "ready"
        assert record["blockers"] == []
        assert Path(record["output_path"]).is_file()
    zh_rows = records[0]["output_geometry"]["rows"]
    assert zh_rows[7] == 12  # absent S8.2 workplace block is hidden
    output = Document(records[0]["output_path"])
    assert "掬泉路3号" in output.tables[0].rows[7].cells[1].text


def test_pipeline_blocks_wrong_s2_slot_projection_before_output(tmp_path):
    facts = _os9015_facts()
    facts["zh"]["s2"][0] = ["2.1 GHS危险性类别：", "错误位置"]
    source = ROOT / "examples" / "regression_HPU-7660_source.docx"
    with pytest.raises(ReleaseBlocked, match="Section 2 slot 1"):
        build_matrix(source=source, facts=facts,
                     out_root=tmp_path / "blocked", do_pdf=False)


def test_pipeline_blocks_facts_from_a_different_source(tmp_path):
    facts = _os9015_facts()
    facts["source_sha256"] = "0" * 64
    source = ROOT / "examples" / "regression_HPU-7660_source.docx"
    with pytest.raises(ReleaseBlocked, match="source_sha256"):
        build_matrix(source=source, facts=facts,
                     out_root=tmp_path / "blocked", do_pdf=False)


def test_pipeline_blocks_unreviewed_source_mapping_before_output(tmp_path):
    facts = _os9015_facts()
    facts.pop("source_mapping")
    source = ROOT / "examples" / "regression_HPU-7660_source.docx"
    with pytest.raises(ReleaseBlocked, match="source_mapping"):
        build_matrix(source=source, facts=facts,
                     out_root=tmp_path / "blocked", do_pdf=False)


def test_pdf_matrix_gate_requires_all_files_and_lineage(tmp_path):
    model = "TEST-1000"
    records = []
    for name in output_names(model):
        docx = tmp_path / name
        pdf = docx.with_suffix(".pdf")
        docx.write_bytes(name.encode())
        pdf.write_bytes((name + ".pdf").encode())
        records.append({
            "output_path": str(docx),
            "pdf_path": str(pdf),
            "pdf_evidence": {
                "source_sha256": sha256(docx),
                "output_sha256": sha256(pdf),
                "source_is_final_docx": True,
            },
        })
    gate_output_matrix(tmp_path, model, records, do_pdf=True)
    (tmp_path / f"{model}_MSDS_EN_国彩.pdf").unlink()
    with pytest.raises(ReleaseBlocked, match="missing PDF"):
        gate_output_matrix(tmp_path, model, records, do_pdf=True)
