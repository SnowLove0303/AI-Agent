import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from msds_pipeline import build_matrix


def _os9015_facts():
    from docx import Document  # noqa: F401  (ensures python-docx present)
    spec = importlib.util.spec_from_file_location(
        "os9015_facts_probe", ROOT / "_task_work" / "generate_os9015_eight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    zh = module.source_facts("zh", "guanzhi")
    en = module.source_facts("en", "guanzhi")
    return {
        "model": "OS-9015",
        "revision": "2025/2/22",
        "zh": {f"s{sec}": zh[f"s{sec}"] for sec in range(1, 17)},
        "en": {f"s{sec}": en[f"s{sec}"] for sec in range(1, 17)},
        "s8_control_parameters": {"zh": [], "en": []},
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
    assert zh_rows[7] == 15  # S8.2 example row removed, placeholder kept
