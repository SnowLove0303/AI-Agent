from pathlib import Path
import json

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
CN_ROWS = [10, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]
EN_ROWS = [9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]


def _rows(document):
    return [len(table.rows) for table in document.tables]


def _unique_texts(row):
    seen = set()
    texts = []
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            texts.append(cell.text)
    return texts


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
    import hashlib
    import re
    # The source record stays byte-identical to the user-supplied formal
    # template; the active baseline carries the approved Hand protection label
    # and row-break corrections, so the two files intentionally differ.
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416"
    assert hashlib.sha256((ROOT / "examples" / "template_reference_en.docx").read_bytes()).hexdigest() == "003ff6bac27bf3bc99f0426ea8ed596487b0399f30428c406227d8f7c1b3dd46"
    assert "Identification" in en.tables[0].rows[0].cells[0].text
    assert "Chemical category" in en.tables[0].rows[2].cells[0].text
    assert "Chinese name:" not in "\n".join(cell.text for row in en.tables[0].rows for cell in row.cells)
    assert "8.2" in "\n".join(cell.text for row in en.tables[7].rows for cell in row.cells)
    assert "11.10" in "\n".join(cell.text for row in en.tables[10].rows for cell in row.cells)
    # v3.15.1: the accidental Chinese suffix was removed from the
    # Hand-protection label cell (formatting retained); generation never
    # rewrites label cells.
    hand_protection = en.tables[7].rows[3].cells[0].text
    assert hand_protection.startswith("Hand protection")
    assert "喷涂过程中要求有呼吸防护设备。" not in hand_protection
    assert not re.search(r"[一-鿿]", hand_protection)
    assert en.tables[7].rows[12].cells[0].text == "Control parameters for workplace components"
    assert _unique_texts(en.tables[7].rows[13]) == ["Substance", "Basis", "Type", "Value"]
    assert _unique_texts(en.tables[7].rows[14]) == ["六亚甲基-1,6-二异氰酸酯", "CN OEL", "TWA", "0.03 mg/m3"]
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
    assert snapshot["source_sha256"] == "003ff6bac27bf3bc99f0426ea8ed596487b0399f30428c406227d8f7c1b3dd46"
    import hashlib
    assert hashlib.sha256((ROOT / "examples" / "template_reference_en_source.docx").read_bytes()).hexdigest() == "59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416"
    assert [table["row_count"] for table in snapshot["tables"]] == EN_ROWS
    assert [table["column_count"] for table in snapshot["tables"]] == [2, 2, 3, 2, 2, 2, 2, 5, 2, 2, 4, 2, 2, 2, 1, 1]
    top_rows = snapshot["tables"][7]["rows"]
    assert top_rows[12]["cells"][0]["text"].strip() == "Control parameters for workplace components"
    assert [cell["text"] for cell in top_rows[13]["cells"]] == ["Substance", "Basis", "Type", "Value"]
    assert [cell["text"] for cell in top_rows[14]["cells"]] == ["六亚甲基-1,6-二异氰酸酯", "CN OEL", "TWA", "0.03 mg/m3"]


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
