from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from docx import Document
from overwrite_tds import write_variant
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
