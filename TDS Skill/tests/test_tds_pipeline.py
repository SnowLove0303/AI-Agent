from pathlib import Path
from copy import deepcopy
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from docx import Document
from overwrite_tds import write_variant
from audit_tds_eight import audit_shape
from tds_common import load, package_inventory


def test_all_four_variants_are_fresh_clones(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = load(ROOT / "tests" / "fixtures" / "valid_mapping.json")
    for variant_id, variant in registry["variants"].items():
        output = tmp_path / f"TDS-DEMO_{variant_id}.docx"
        write_variant(mapping, registry, variant_id, output)
        assert output.is_file()
        doc = Document(str(output))
        assert len(doc.tables) == 1
        assert len(doc.tables[0].rows) == 6
        assert "EP-1704" not in "\n".join(p.text for p in doc.paragraphs)
        original = package_inventory(ROOT / variant["template"])
        generated = package_inventory(output)
        assert {k: v for k, v in generated.items() if k != "word/document.xml"} == {k: v for k, v in original.items() if k != "word/document.xml"}


def test_performance_and_feature_extensions_clone_template_styles(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["mapped_fields"]["product.features"]["values"]["zh-CN"] += "\n低气味。"
    mapping["mapped_fields"]["product.features"]["values"]["en-US"] += "\nLow odor."
    mapping["performance_extra_rows"] = [{
        "field_id": "performance.extra.001",
        "label_values": {"zh-CN": "粒径", "en-US": "Particle size"},
        "values": {"zh-CN": "≤ 100 nm", "en-US": "≤ 100 nm"},
        "unit": "nm",
        "test_method": "Laser diffraction"
    }]
    for variant_id in registry["variants"]:
        output = tmp_path / f"extended_{variant_id}.docx"
        write_variant(mapping, registry, variant_id, output)
        doc = Document(str(output))
        assert len(doc.tables[0].rows) == 7
        text = "\n".join(c.text for r in doc.tables[0].rows for c in r.cells)
        paragraphs = "\n".join(p.text for p in doc.paragraphs)
        assert ("粒径" if registry["variants"][variant_id]["language"] == "zh-CN" else "Particle size") in text
        assert ("低气味。" if registry["variants"][variant_id]["language"] == "zh-CN" else "Low odor.") in paragraphs
        base = Document(str(ROOT / registry["variants"][variant_id]["template"]))
        assert audit_shape(base, doc, registry["variants"][variant_id], mapping)


def test_unknown_bilingual_metric_is_paired_by_source_order(tmp_path):
    sources = {
        "zh-CN": {"language": "zh-CN", "title": {"text": "TDS-DEMO", "paragraph_index": 0}, "sections": {}, "performance_rows": [{"item": "粒径", "value": "≤ 100 nm", "unit": "nm", "test_method": "方法A", "source_column_count": 4, "source_location": "table[0].row[6]"}]},
        "en-US": {"language": "en-US", "title": {"text": "TDS-DEMO", "paragraph_index": 0}, "sections": {}, "performance_rows": [{"item": "Particle size", "value": "≤ 100 nm", "unit": "nm", "test_method": "Method A", "source_column_count": 4, "source_location": "table[0].row[6]"}]}
    }
    facts = []
    for language, payload in sources.items():
        path = tmp_path / f"{language}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        facts.append(path)
    output = tmp_path / "mapping.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "map_tds_fields.py"), "--cn", str(facts[0]), "--en", str(facts[1]), "--registry", str(ROOT / "mapping" / "template_field_registry.json"), "--output", str(output)], check=True)
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "ready"
    assert len(result["performance_extra_rows"]) == 1
    assert set(result["performance_extra_rows"][0]["label_values"]) == {"zh-CN", "en-US"}


def test_common_cn_performance_labels_map_to_fixed_slots(tmp_path):
    facts = tmp_path / "cn.json"
    facts.write_text(json.dumps({
        "language": "zh-CN",
        "title": {"text": "PU-1001"},
        "sections": {},
        "performance_rows": [
            {"item": "外观", "value": "蓝光透明液体", "unit": "", "test_method": "目测", "source_column_count": 4, "source_location": "table[0].row[1]"},
            {"item": "固体份含量", "value": "22±1", "unit": "%", "test_method": "方法", "source_column_count": 4, "source_location": "table[0].row[2]"},
            {"item": "粘度(25℃)", "value": "＜500", "unit": "mPa·s", "test_method": "方法", "source_column_count": 4, "source_location": "table[0].row[3]"},
            {"item": "PH值（1:10稀释在水中）", "value": "7.0-9.0", "unit": "", "test_method": "方法", "source_column_count": 4, "source_location": "table[0].row[4]"},
            {"item": "密度(25℃)", "value": "约1.06", "unit": "g/cm3", "test_method": "方法", "source_column_count": 4, "source_location": "table[0].row[5]"}
        ]
    }, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "mapping.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "map_tds_fields.py"), "--cn", str(facts), "--registry", str(ROOT / "mapping" / "template_field_registry.json"), "--output", str(output)], check=True)
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["mapped_fields"]["performance.appearance"]["values"]["zh-CN"] == "蓝光透明液体"
    assert result["mapped_fields"]["performance.solid_content"]["values"]["zh-CN"] == "22±1"
    assert result["mapped_fields"]["performance.viscosity_25c"]["values"]["zh-CN"] == "＜500"
    assert result["mapped_fields"]["performance.ph_25c"]["values"]["zh-CN"] == "7.0-9.0"
    assert result["performance_extra_rows"][0]["label_values"]["zh-CN"] == "密度(25℃)"


def test_numbered_features_do_not_duplicate_template_numbering(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["mapped_fields"]["product.features"]["values"]["zh-CN"] = "1. 成膜柔软；\n2. 耐黄变；"
    output = tmp_path / "numbered.docx"
    write_variant(mapping, registry, "TDS_CN_冠志模板", output)
    text = "\n".join(p.text for p in Document(str(output)).paragraphs)
    assert "1. 1." not in text
    assert "2. 2." not in text
