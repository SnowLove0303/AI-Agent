import base64
from pathlib import Path

from docx import Document

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ghs_pictogram_policy import insert_source_pictogram
from section2_ghs_policy import (
    format_label_elements,
    is_missing_section2_value,
    suppress_missing_section2_rows_and_renumber,
)


ROOT = Path(__file__).resolve().parents[1]


def test_label_elements_are_explicit_and_line_separated():
    assert format_label_elements("zh", ["亲水脂肪族聚异氰酸酯"]) == "必须列在标签上的有害成分：\n亲水脂肪族聚异氰酸酯"
    assert format_label_elements("en", ["Hydrophilic aliphatic polyisocyanate"]) == "Hazardous ingredients required to be listed on the label:\nHydrophilic aliphatic polyisocyanate"


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
