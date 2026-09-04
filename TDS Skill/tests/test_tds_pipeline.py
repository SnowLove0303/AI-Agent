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


def test_language_specific_template_labels_and_grid_widths_are_registered():
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    en_labels = [
        item["label"]
        for item in registry["variants"]["TDS_EN_冠志模板"]["slots"]
        if item["kind"] == "performance_row"
    ]
    assert en_labels == [
        "Emulsion Appearance",
        "Epoxy Equivalent Weight",
        "Solids Content",
        "pH Value (25°C)",
        "Viscosity (25°C)",
    ]
    assert registry["variants"]["TDS_EN_冠志模板"]["template_sha256"] != "4d602128bd397235e76e48d39a9a02b7862b840063734bc89b67661271d0a216"


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
    assert "zh-CN" not in result["mapped_fields"]["performance.ph_25c"]["values"]
    assert [x["label_values"]["zh-CN"] for x in result["performance_extra_rows"]] == ["PH值（1:10稀释在水中）", "密度(25℃)"]


def test_mapping_keeps_evidence_separate_from_normalized_model(tmp_path):
    facts = tmp_path / "cn.json"
    facts.write_text(json.dumps({
        "language": "zh-CN",
        "title": {"text": "TDS-DEMO"},
        "sections": {"product.description": {"text": "用于水性涂层。", "locations": [3]}},
        "performance_rows": [{"item": "PH值（1:10稀释在水中）", "value": "7.0-9.0", "unit": "", "test_method": "方法A", "source_column_count": 4, "source_location": "table[0].row[4]"}]
    }, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "mapping.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "map_tds_fields.py"), "--cn", str(facts), "--registry", str(ROOT / "mapping" / "template_field_registry.json"), "--output", str(output)], check=True)
    result = json.loads(output.read_text(encoding="utf-8"))
    row = result["normalized_model"]["performance_rows"][0]
    assert row["source_values"]["zh-CN"] == "7.0-9.0"
    assert row["normalized_values"]["zh-CN"] == "7.0-9.0"
    assert result["normalized_model"]["translation"]["source"] == "normalized_model"
    decision = next(item for item in result["decision_ledger"] if item["field_id"] == "performance.row.001")
    assert decision["decision"] == "preserve_as_source_row"
    assert decision["provenance"]["zh-CN"] == ["table[0].row[4]"]


def test_overwrite_reads_normalized_values_not_raw_values(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["schema_version"] = "1.3.0"
    mapping["normalized_model"] = {
        "status": "approved",
        "translation": {"source": "normalized_model"},
        "fields": {
            field_id: {"field_id": field_id, "normalized_values": dict(item.get("values", {}))}
            for field_id, item in mapping["mapped_fields"].items()
        },
        "performance_rows": [
            {
                **row,
                "normalized_label_values": {"zh-CN": "标准化外观"},
                "normalized_values": {"zh-CN": "标准化液体"},
                "normalized_unit_values": {"zh-CN": ""},
                "normalized_test_method_values": {"zh-CN": "标准化方法"},
            }
            for row in [{"field_id": "performance.row.001", "label_values": {"zh-CN": "乳液外观"}, "values": {"zh-CN": "乳白色液体"}}]
        ],
    }
    output = tmp_path / "normalized.docx"
    write_variant(mapping, registry, "TDS_CN_冠志模板", output)
    rows = [[cell.text for cell in row.cells] for row in Document(str(output)).tables[0].rows]
    assert rows[1] == ["标准化外观", "标准化液体", "", "标准化方法"]


def test_numbered_features_do_not_duplicate_template_numbering(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["mapped_fields"]["product.features"]["values"]["zh-CN"] = "1. 成膜柔软；\n2. 耐黄变；"
    output = tmp_path / "numbered.docx"
    write_variant(mapping, registry, "TDS_CN_冠志模板", output)
    text = "\n".join(p.text for p in Document(str(output)).paragraphs)
    assert "1. 1." not in text
    assert "2. 2." not in text


def test_source_led_performance_rows_keep_order_and_conditions(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["performance_rows"] = [
        {"field_id": "performance.row.001", "label_values": {"zh-CN": "外观"}, "values": {"zh-CN": "蓝光透明液体"}, "unit_values": {"zh-CN": ""}, "test_method_values": {"zh-CN": "目测"}},
        {"field_id": "performance.row.002", "label_values": {"zh-CN": "固体份含量"}, "values": {"zh-CN": "22±1"}, "unit_values": {"zh-CN": "%"}, "test_method_values": {"zh-CN": "150℃ 30min，鼓风烘箱"}},
        {"field_id": "performance.row.003", "label_values": {"zh-CN": "粘度(25℃)"}, "values": {"zh-CN": "＜500"}, "unit_values": {"zh-CN": "mPa·S"}, "test_method_values": {"zh-CN": "GB/T 2794-2022"}},
        {"field_id": "performance.row.004", "label_values": {"zh-CN": "PH值（1:10稀释在水中）"}, "values": {"zh-CN": "7.0-9.0"}, "unit_values": {"zh-CN": ""}, "test_method_values": {"zh-CN": "GB 6920-86"}},
        {"field_id": "performance.row.005", "label_values": {"zh-CN": "密度(25℃)"}, "values": {"zh-CN": "约1.06"}, "unit_values": {"zh-CN": "g/cm3"}, "test_method_values": {"zh-CN": "GB/T 4472-2011"}}
    ]
    output = tmp_path / "source-led.docx"
    write_variant(mapping, registry, "TDS_CN_冠志模板", output)
    rows = [[c.text for c in row.cells] for row in Document(str(output)).tables[0].rows]
    assert len(rows) == 6
    assert rows[1:] == [
        ["外观", "蓝光透明液体", "", "目测"],
        ["固体份含量", "22±1", "%", "150℃ 30min，鼓风烘箱"],
        ["粘度(25℃)", "＜500", "mPa·S", "GB/T 2794-2022"],
        ["PH值（1:10稀释在水中）", "7.0-9.0", "", "GB 6920-86"],
        ["密度(25℃)", "约1.06", "g/cm3", "GB/T 4472-2011"]
    ]


def test_source_led_table_trims_unused_template_rows(tmp_path):
    registry = load(ROOT / "mapping" / "template_field_registry.json")
    mapping = deepcopy(load(ROOT / "tests" / "fixtures" / "valid_mapping.json"))
    mapping["performance_rows"] = [{"field_id": "performance.row.001", "label_values": {"zh-CN": "外观"}, "values": {"zh-CN": "液体"}, "unit_values": {"zh-CN": ""}, "test_method_values": {"zh-CN": "目测"}}]
    output = tmp_path / "trimmed.docx"
    write_variant(mapping, registry, "TDS_CN_冠志模板", output)
    assert len(Document(str(output)).tables[0].rows) == 2
