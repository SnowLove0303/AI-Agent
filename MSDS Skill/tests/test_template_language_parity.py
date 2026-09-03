from pathlib import Path
import json

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROWS = [10, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2]


def _rows(document):
    return [len(table.rows) for table in document.tables]


def test_cn_and_en_templates_have_same_section_capacity():
    cn = Document(ROOT / "examples" / "template_reference.docx")
    en = Document(ROOT / "examples" / "template_reference_en.docx")
    assert len(cn.tables) == len(en.tables) == 16
    assert _rows(cn) == EXPECTED_ROWS
    assert _rows(en) == EXPECTED_ROWS


def test_en_template_is_distinct_and_uses_english_section_labels():
    source = ROOT / "examples" / "template_reference_en_source.docx"
    en = Document(ROOT / "examples" / "template_reference_en.docx")
    assert source.is_file()
    assert "Identification" in en.tables[0].rows[0].cells[0].text
    assert "Chinese name:" in en.tables[0].rows[2].cells[0].text
    assert "8.2" in "\n".join(cell.text for row in en.tables[7].rows for cell in row.cells)
    assert "11.10" in "\n".join(cell.text for row in en.tables[10].rows for cell in row.cells)


def test_en_snapshot_pins_normalized_template_hash_and_geometry():
    snapshot = json.loads((ROOT / "tests" / "template_snapshot_en.json").read_text(encoding="utf-8"))
    assert snapshot["source_sha256"] == "b36d542e7e000c7fa979875f127459505dc9f7d9e0b9180ecb1f3856fd74103f"
    assert [table["row_count"] for table in snapshot["tables"]] == EXPECTED_ROWS
    assert [table["column_count"] for table in snapshot["tables"]] == [2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 1]


def test_generator_selects_language_specific_template():
    import importlib.util
    import sys

    task_root = next(path for path in (ROOT / "_task_work", ROOT.parent / "_task_work") if (path / "generate_pu2345_eight.py").exists())
    sys.path.insert(0, str(task_root))
    spec = importlib.util.spec_from_file_location("generate_pu2345_eight_parity_test", task_root / "generate_pu2345_eight.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    assert generator.template_for("zh") == ROOT / "examples" / "template_reference.docx"
    assert generator.template_for("en") == ROOT / "examples" / "template_reference_en.docx"
