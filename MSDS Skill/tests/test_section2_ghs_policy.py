import base64
from pathlib import Path

from docx import Document

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ghs_pictogram_policy import insert_source_pictogram
from section2_ghs_policy import (
    format_label_elements,
    is_missing_section2_value,
    is_explicit_other_hazards_row,
    validate_s2_semantics,
    project_source_cn_facts,
    project_source_cn_headings,
    suppress_missing_section2_rows_and_renumber,
)


ROOT = Path(__file__).resolve().parents[1]


def test_label_elements_are_explicit_and_line_separated():
    assert format_label_elements("zh", ["亲水脂肪族聚异氰酸酯"]) == "必须列在标签上的有害成分：\n亲水脂肪族聚异氰酸酯"
    assert format_label_elements("en", ["Hydrophilic aliphatic polyisocyanate"]) == "Hazardous ingredients required to be listed on the label:\nHydrophilic aliphatic polyisocyanate"


def test_label_elements_without_ingredients_leave_empty_value_for_suppression():
    assert format_label_elements("zh", []) == ""
    assert format_label_elements("en", []) == ""
    document = Document(ROOT / "examples" / "template_reference.docx")
    table = document.tables[1]
    table.rows[3].cells[-1].text = format_label_elements("zh", [])
    result = suppress_missing_section2_rows_and_renumber(document, lambda p, text: setattr(p, "text", text))
    labels = [row.cells[0].text.strip() for row in document.tables[1].rows[1:]]
    assert not any("标签要素" in label for label in labels)
    assert result["removed_count"] >= 1


def test_section2_missing_rows_are_removed_and_unique_items_renumbered():
    document = Document(ROOT / "examples" / "template_reference.docx")
    table = document.tables[1]
    values = {
        1: "无数据",
        2: "易燃液体，类别3（H226）",
        3: format_label_elements("zh", ["亲水脂肪族聚异氰酸酯"]),
        4: "",
        5: "警告",
        6: "H226 易燃液体和蒸气。",
        7: "P210 远离热源。",
        8: "无数据",
        9: "吸入：吸入有害。",
        10: "食入：无数据",
        11: "皮肤：可能致敏。",
        12: "眼睛：无数据",
        13: "症状和体征：无数据",
        14: "无数据",
        15: "存在风险。",
    }
    for row_index, value in values.items():
        table.rows[row_index].cells[-1].text = value

    result = suppress_missing_section2_rows_and_renumber(document, lambda p, text: setattr(p, "text", text))
    labels = [row.cells[0].text.strip() for row in document.tables[1].rows[1:]]
    assert result["removed_count"] == 7
    assert labels == [
        "2.1  GHS危险性类别：",
        "2.2  GHS标签要素：",
        "2.3  信号词：",
        "2.4  危险性说明：",
        "2.5  防范说明：",
        "2.6  健康危害",
        "2.6  健康危害",
        "2.7  其他危害",
    ]
    assert is_missing_section2_value("眼睛：无数据")
    assert not is_missing_section2_value("眼睛：无刺激")


def test_section2_explicit_number_map_keeps_source_requested_numbers():
    document = Document(ROOT / "examples" / "template_reference.docx")
    table = document.tables[1]
    for row in table.rows[1:]:
        row.cells[-1].text = ""
    table.rows[2].cells[-1].text = ""
    table.rows[3].cells[-1].text = "根据GHS不属于危害化学品"
    table.rows[15].cells[-1].text = "无适用资料。"
    result = suppress_missing_section2_rows_and_renumber(
        document, lambda p, text: setattr(p, "text", text), number_map={3: 2, 10: 3}
    )
    labels = [row.cells[0].text.strip() for row in document.tables[1].rows[1:]]
    assert labels == ["2.2  GHS标签要素：", "2.3  其他危害"]
    assert result["number_map"] == {"2.3": "2.2", "2.10": "2.3"}


def test_blank_other_hazards_exception_is_suppressed_but_explicit_missing_is_kept():
    document = Document(ROOT / "examples" / "template_reference.docx")
    table = document.tables[1]
    other_row = table.rows[15]
    other_row.cells[-1].text = ""
    assert not is_explicit_other_hazards_row(other_row)
    result = suppress_missing_section2_rows_and_renumber(
        document, lambda p, text: setattr(p, "text", text), number_map={3: 2, 10: 3}
    )
    assert "2.10  其他危害" in result["removed_labels"] or "2.10 其他危害" in result["removed_labels"]

    explicit = Document(ROOT / "examples" / "template_reference.docx")
    explicit_row = explicit.tables[1].rows[15]
    explicit_row.cells[-1].text = "无适用资料。"
    assert is_explicit_other_hazards_row(explicit_row)


def test_source_cn_s2_projects_by_semantic_slot_not_list_position():
    rows, number_map = project_source_cn_facts({
        "ghs_classes": ["根据 GHS 不属于危害化学品"],
        "label_elements": ["根据 GHS 不属于危害化学品"],
        "other_hazards": "无适用资料。",
    })
    assert rows[1] == ["2.2 GHS危险性类别：", "根据 GHS 不属于危害化学品"]
    assert rows[2] == ["2.3 GHS标签要素：", "根据 GHS 不属于危害化学品"]
    assert rows[14] == ["2.10 其他危害：", "无适用资料。"]
    assert number_map == {2: 1, 3: 2, 10: 3}


def test_s2_semantic_contract_separates_label_ingredients_and_signal_word():
    rows = [
        ["2.1 紧急情况概述", ""],
        ["2.2 GHS危险性类别：", "类别 3"],
        ["2.3 GHS标签要素：", "必须列在标签上的有害成分：\n基于HDI的亲水脂肪族聚异氰酸酯"],
        [" GHS象形图", ""],
        ["2.4 信号词：", "警告"],
    ]
    assert validate_s2_semantics(rows, "zh") == []

    misplaced = [list(row) for row in rows]
    misplaced[2][1] = "警告"
    misplaced[4][1] = "必须列在标签上的有害成分：\n基于HDI的亲水脂肪族聚异氰酸酯"
    errors = validate_s2_semantics(misplaced, "zh")
    assert any("label-elements slot contains only a signal word" in error for error in errors)
    assert any("signal-word slot contains label-ingredient prose" in error for error in errors)


def test_source_pictogram_is_inserted_as_picture(tmp_path):
    image_path = tmp_path / "source.png"
    # A tiny valid PNG keeps this regression test independent of Pillow.
    image_path.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    ))
    source = tmp_path / "source.docx"
    source_doc = Document()
    source_doc.add_paragraph().add_run().add_picture(str(image_path))
    source_doc.save(source)

    output = Document(ROOT / "examples" / "template_reference.docx")
    insert_source_pictogram(output, source)
    assert output.tables[1].rows[4].cells[-1]._tc.xpath(".//w:drawing")


def test_cn_source_headings_are_projected_without_layout_drift():
    template = Document(ROOT / "examples" / "template_reference.docx")
    output = Document(ROOT / "examples" / "template_reference.docx")
    try:
        project_source_cn_headings(output)
    except Exception as exc:
        assert "locked Section 2 labels are immutable" in str(exc)
    else:
        raise AssertionError("legacy Section 2 label-rewrite path was not blocked")
    assert [row.cells[0].text for row in output.tables[1].rows] == [
        row.cells[0].text for row in template.tables[1].rows
    ]
