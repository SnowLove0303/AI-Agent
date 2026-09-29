from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_structured_output import convert_item  # noqa: E402


def test_structured_output_keeps_sections_locators_and_quality():
    recognition = {
        "schema_version": "1.0",
        "name": "sample.docx",
        "source_type": "docx",
        "recognition_warnings": [],
        "records": [{
            "kind": "table",
            "label": "第 1 部分 · 表格 1",
            "title": "1 Identification",
            "section": "第 1 部分",
            "columns": 2,
            "structure": {"row_count": 1},
            "rows": [[{
                "row": 0, "col": 0, "colspan": 1, "rowspan": 1,
                "text": "Product name:", "format": {},
                "paragraphs": [{"index": 0, "content": [{"type": "text", "text": "Product name:", "run_format": {}, "paragraph_format": {}}]}],
            }, {
                "row": 0, "col": 1, "colspan": 1, "rowspan": 1,
                "text": "Sample resin", "format": {},
                "paragraphs": [{"index": 0, "content": [{"type": "text", "text": "Sample resin", "run_format": {}, "paragraph_format": {}}]}],
            }]],
        }],
    }
    comparison = {"source": {"source_sha256": "abc"}, "dimensions": {"content": {"status": "PASS"}, "structure": {"status": "PASS"}, "images": {"status": "PASS"}, "package": {"status": "PASS"}},}
    out = convert_item(recognition, comparison, {"recognition": "recognition.json", "comparison": "comparison.json"})
    assert out["schema_version"] == "agent-recognition-v1"
    assert out["quality"]["overall"] == "COMPLETE"
    assert out["sections"]["1"][0]["tables"][0]["rows"][0]["cells"][1]["normalized_text"] == "Sample resin"
    assert out["tables"][0]["id"].startswith("SRC-abc/")


def test_partial_dimension_blocks_complete_status():
    recognition = {"name": "sample.pdf", "source_type": "pdf", "records": [], "recognition_warnings": []}
    comparison = {"source": {"source_sha256": "def"}, "dimensions": {"content": {"status": "PARTIAL"}, "structure": {"status": "PASS"}, "images": {"status": "UNAVAILABLE"}, "package": {"status": "UNAVAILABLE"}}}
    out = convert_item(recognition, comparison)
    assert out["quality"]["overall"] == "PARTIAL"
    assert "images" in out["quality"]["blocking_dimensions"]
