from pathlib import Path
import re
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
    # The supplied EN template remains the immutable source record; the active
    # baseline is a versioned maintainer remediation with unchanged geometry.
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497"
    assert hashlib.sha256((ROOT / "examples" / "template_reference_en.docx").read_bytes()).hexdigest() == "49a279aa8c7a50f38ee6929ca2f030cf13b01ee0d1e476d790a2352a316bfa2b"
    assert source.read_bytes() != (ROOT / "examples" / "template_reference_en.docx").read_bytes()
    assert "Identification" in en.tables[0].rows[0].cells[0].text
    assert "Chemical category" in en.tables[0].rows[2].cells[0].text
    assert "Chinese name:" not in "\n".join(cell.text for row in en.tables[0].rows for cell in row.cells)
    assert "8.2" in "\n".join(cell.text for row in en.tables[7].rows for cell in row.cells)
    assert "11.10" in "\n".join(cell.text for row in en.tables[10].rows for cell in row.cells)
    hand_protection = en.tables[7].rows[3].cells[0].text
    assert hand_protection == "Hand protection:"
    assert en.tables[5].rows[1].cells[0].text == (
        "6.1  Personal precautions, protective equipment and\n"
        "emergency procedures:"
    )
    assert en.tables[0].rows[0].cells[0].text == (
        "Identification of the substance/mixture and of the company/undertaking"
    )
    assert en.tables[13].rows[0].cells[0].text == "14. Transport information"
    assert all(
        "：" not in _unique_texts(row)[0]
        for table in en.tables
        for row in table.rows
        if not re.search(r"[\u4e00-\u9fff]", _unique_texts(row)[0])
    )
    assert all("物料安全数据表" not in p.text for p in en.sections[0].header.paragraphs)
    assert en.sections[0].header.paragraphs[0].text.strip() == "SAFETY DATA SHEET"
    assert en.sections[0].header.paragraphs[1].text == "Version: 1.0"
    assert en.tables[7].rows[12].cells[0].text == "Control parameters for workplace components"
    assert _unique_texts(en.tables[7].rows[13]) == ["Substance", "Basis", "Type", "Value"]
    assert _unique_texts(en.tables[7].rows[14]) == ["六亚甲基-1,6-二异氰酸酯", "CN OEL", "TWA", "0.03 mg/m3"]
    assert en.tables[10].cell(3, 1).text == "Oral:"
    assert en.tables[10].cell(4, 1).text == "Inhalation:"
    assert en.tables[10].cell(5, 1).text == "Dermal:"
    assert en.tables[10].cell(12, 1).text == "Fertility: "
    assert en.tables[10].cell(13, 1).text == "Teratogenicity: "
    assert en.tables[10].cell(14, 1).text == "In vitro genotoxicity: "


def test_en_snapshot_pins_the_supplied_template_hash_and_geometry():
    snapshot = json.loads((ROOT / "tests" / "template_snapshot_en.json").read_text(encoding="utf-8"))
    assert snapshot["source_sha256"] == "49a279aa8c7a50f38ee6929ca2f030cf13b01ee0d1e476d790a2352a316bfa2b"
    import hashlib
    assert hashlib.sha256((ROOT / "examples" / "template_reference_en_source.docx").read_bytes()).hexdigest() == "34a259eed50d2e78b4609c66453fa9baab610a623dcc7ee531db359b1a988497"
    assert [table["row_count"] for table in snapshot["tables"]] == EN_ROWS
    assert [table["column_count"] for table in snapshot["tables"]] == [2, 2, 3, 2, 2, 2, 2, 5, 2, 2, 4, 2, 2, 2, 1, 1]
    top_rows = snapshot["tables"][7]["rows"]
    assert top_rows[12]["cells"][0]["text"].strip() == "Control parameters for workplace components"
    assert [cell["text"] for cell in top_rows[13]["cells"]] == ["Substance", "Basis", "Type", "Value"]
    assert [cell["text"] for cell in top_rows[14]["cells"]] == ["六亚甲基-1,6-二异氰酸酯", "CN OEL", "TWA", "0.03 mg/m3"]


def test_generator_selects_language_specific_template():
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import msds_pipeline

    assert msds_pipeline.template_for(
        ROOT / "examples" / "template_reference.docx",
        ROOT / "examples" / "template_reference_en.docx",
        "zh",
    ) == ROOT / "examples" / "template_reference.docx"
    assert msds_pipeline.template_for(
        ROOT / "examples" / "template_reference.docx",
        ROOT / "examples" / "template_reference_en.docx",
        "en",
    ) == ROOT / "examples" / "template_reference_en.docx"
