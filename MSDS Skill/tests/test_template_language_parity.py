from pathlib import Path
import json

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
CN_ROWS = [10, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2]
EN_ROWS = [9, 16, 6, 6, 5, 4, 3, 12, 24, 6, 18, 6, 3, 5, 9, 2]


def _rows(document):
    return [len(table.rows) for table in document.tables]


def test_cn_and_en_templates_keep_independent_language_specific_capacity():
    cn = Document(ROOT / "examples" / "template_reference.docx")
    en = Document(ROOT / "examples" / "template_reference_en.docx")
    assert len(cn.tables) == len(en.tables) == 16
    assert _rows(cn) == CN_ROWS
    assert _rows(en) == EN_ROWS


def test_en_template_is_distinct_and_uses_english_section_labels():
    source = ROOT / "examples" / "template_reference_en_source.docx"
    en = Document(ROOT / "examples" / "template_reference_en.docx")
    assert source.is_file()
    assert source.read_bytes() != (ROOT / "examples" / "template_reference_en.docx").read_bytes()
    assert "Identification" in en.tables[0].rows[0].cells[0].text
    assert "Chemical category" in en.tables[0].rows[2].cells[0].text
    assert "Chinese name:" not in "\n".join(cell.text for row in en.tables[0].rows for cell in row.cells)
    assert "8.2" in "\n".join(cell.text for row in en.tables[7].rows for cell in row.cells)
    assert "11.10" in "\n".join(cell.text for row in en.tables[10].rows for cell in row.cells)
    assert en.tables[7].rows[3].cells[0].text == "Hand protection:"
    child = en.tables[7].rows[11].cells[1].tables[0]
    assert [[cell.text for cell in row.cells] for row in child.rows] == [
        ["Substance", "Basis", "Type", "Value"],
        ["", "", "", ""],
    ]
    assert en.tables[10].cell(3, 1).text == "Oral:"
    assert en.tables[10].cell(4, 1).text == "Inhalation:"
    assert en.tables[10].cell(5, 1).text == "Dermal:"
    # Preserve the punctuation actually present in the user-supplied EN
    # template: ASCII colons in the acute-toxicity labels and full-width
    # colons in the reproductive-toxicity labels.
    assert en.tables[10].cell(12, 1).text == "Fertility："
    assert en.tables[10].cell(13, 1).text == "Teratogenicity："
    assert en.tables[10].cell(14, 1).text == "In vitro genotoxicity："


def test_en_snapshot_pins_the_supplied_template_hash_and_geometry():
    snapshot = json.loads((ROOT / "tests" / "template_snapshot_en.json").read_text(encoding="utf-8"))
    assert snapshot["source_sha256"] == "4ba9475bb211bfa7dae6328243cddb1797ff36afb17875b66d53d782b15216ff"
    import hashlib
    assert hashlib.sha256((ROOT / "examples" / "template_reference_en_source.docx").read_bytes()).hexdigest() == "2f287b544705d0db7ff724610c6f7878a88ff2912bbf074151e107f36a588a0e"
    assert [table["row_count"] for table in snapshot["tables"]] == EN_ROWS
    assert [table["column_count"] for table in snapshot["tables"]] == [2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 1]
    child = snapshot["tables"][7]["rows"][11]["cells"][1]["nested_tables"][0]
    assert [cell["text"] for cell in child["rows"][0]["cells"]] == ["Substance", "Basis", "Type", "Value"]
    assert child["grid_widths_dxa"] == ["2400", "1100", "1100", "1600"]


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
