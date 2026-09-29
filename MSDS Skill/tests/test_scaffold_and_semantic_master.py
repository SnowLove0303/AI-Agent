from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_source_facts import SemanticMaster, extract
from preflight_facts import run as run_preflight
from scaffold_evidence_packet import scaffold_facts


SOURCE = ROOT / "examples" / "regression_HPU-7660_source.docx"


def test_scaffold_facts_passes_preflight_cleanly(tmp_path):
    scaffold = scaffold_facts(SOURCE, model="HPU-7660")
    assert scaffold["model"] == "HPU-7660"
    assert scaffold["source_coverage"]["status"] == "ready"
    assert scaffold["overwrite_sop"]["status"] == "reviewed"
    assert "semantic_master" in scaffold
    assert scaffold["semantic_master"]["status"] == "reviewed"

    scaffold_file = tmp_path / "scaffold_approved.json"
    scaffold_file.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")

    report = run_preflight(SOURCE, scaffold_file, model="HPU-7660")
    assert report["status"] == "ready"
    assert report["errors"] == []
    assert report["blockers"] == []


def test_semantic_master_bilingual_inheritance():
    master = SemanticMaster()
    master.add_entry(
        slot_id="s1.row[1]",
        source_fact_id="FACT-0001",
        source_section="s1",
        zh_value="测试产品",
        en_value="Test Product",
        presence_decision="written",
    )
    master.add_entry(
        slot_id="s2.ghs_classes",
        source_fact_id="FACT-0010",
        source_section="s2",
        zh_value="非GHS危险化学品",
        en_value="Not classified as hazardous",
        presence_decision="written",
    )

    data = master.to_dict()
    assert data["spec_id"] == "MSDS-SEMANTIC-MASTER-001"
    assert data["spec_version"] == "1.0.0"
    assert len(data["items"]) == 2
    assert data["items"][0]["slot_id"] == "s1.row[1]"
    assert data["items"][0]["zh_value"] == "测试产品"
    assert data["items"][0]["en_value"] == "Test Product"

    master.inherit_translations({"s1.row[1]": "Overridden Test Product"})
    data2 = master.to_dict()
    assert data2["items"][0]["en_value"] == "Overridden Test Product"
