from pathlib import Path
from copy import deepcopy
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
