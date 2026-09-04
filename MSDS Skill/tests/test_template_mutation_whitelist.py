from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from template_mutation_whitelist import (
    MutationViolation,
    compare_locked_skeleton,
    set_sequence_prefix,
    write_s82_top_rows,
    write_row_values,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples" / "template_reference.docx"
TEMPLATE_EN = ROOT / "examples" / "template_reference_en.docx"


def _unique_texts(row):
    seen = set()
    texts = []
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            texts.append(cell.text)
    return texts


def test_value_write_preserves_locked_label_and_skeleton():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    row = output.tables[0].rows[1]
    original_label = row.cells[0].text
    write_row_values(row, ["unused source label", "new value"], table_index=0, row_index=1)
    assert row.cells[0].text == original_label
    assert not compare_locked_skeleton(template, output)


def test_label_text_change_is_blocked():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    row = output.tables[0].rows[1]
    paragraph = row.cells[0].paragraphs[0]
    for run in paragraph.runs:
        if run.text.strip():
            run.text = "tampered label"
            break
    errors = compare_locked_skeleton(template, output)
    assert any("locked label text changed" in error for error in errors)


def test_label_format_change_is_blocked():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    paragraph = output.tables[0].rows[1].cells[0].paragraphs[0]
    paragraph.paragraph_format.left_indent = 999000
    errors = compare_locked_skeleton(template, output)
    assert any("paragraph properties changed" in error for error in errors)


def test_sequence_renumber_is_content_only():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    cell = output.tables[1].rows[1].cells[0]
    set_sequence_prefix(cell, 2, 9)
    assert not compare_locked_skeleton(template, output)


def test_s3_component_row_writes_all_three_data_cells():
    output = Document(str(TEMPLATE))
    row = output.tables[2].rows[4]
    write_row_values(row, ["Component", "123-45-6", "10"], table_index=2, row_index=4)
    assert [cell.text for cell in row.cells] == ["Component", "123-45-6", "10"]


def test_s81_parent_node_is_not_a_writable_note_slot():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    original = output.tables[7].rows[1].cells[0].text
    write_row_values(
        output.tables[7].rows[1],
        ["8.1 source label", "source value must not enter the parent node"],
        table_index=7,
        row_index=1,
    )
    assert output.tables[7].rows[1].cells[0].text == original
    assert not compare_locked_skeleton(template, output)


def test_s82_top_data_write_preserves_locked_header_and_parent_label():
    template = Document(str(TEMPLATE_EN))
    output = Document(str(TEMPLATE_EN))
    table = output.tables[7]
    original_parent = table.rows[12].cells[0].text
    audit = write_s82_top_rows(
        table,
        [["Substance A", "CN OEL", "TWA", "0.03 mg/m3"]],
        "en",
    )
    assert audit == {"record_count": 1, "row_count": 1, "placeholder": False}
    assert _unique_texts(table.rows[13]) == ["Substance", "Basis", "Type", "Value"]
    assert _unique_texts(table.rows[14]) == ["Substance A", "CN OEL", "TWA", "0.03 mg/m3"]
    assert len(table.rows) == 15
    assert table.rows[12].cells[0].text == original_parent
    assert not compare_locked_skeleton(template, output)


def test_s82_empty_records_keep_single_placeholder_row():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    table = output.tables[7]
    audit = write_s82_top_rows(table, [], "zh")
    assert audit == {"record_count": 0, "row_count": 1, "placeholder": True}
    assert _unique_texts(table.rows[13]) == ["物质", "依据", "类型", "数值"]
    assert _unique_texts(table.rows[14]) == ["", "", "", "无数据"]
    assert len(table.rows) == 15
    assert not compare_locked_skeleton(template, output)


def test_s82_extra_records_clone_styled_data_row():
    template = Document(str(TEMPLATE_EN))
    output = Document(str(TEMPLATE_EN))
    table = output.tables[7]
    records = [
        ["Substance A", "CN OEL", "TWA", "0.03 mg/m3"],
        ["Substance B", "CN OEL", "STEL", "0.06 mg/m3"],
        ["Substance C", "CN OEL", "TWA", "100 mg/m3"],
    ]
    write_s82_top_rows(table, records, "en")
    assert len(table.rows) == 17
    assert _unique_texts(table.rows[16]) == ["Substance C", "CN OEL", "TWA", "100 mg/m3"]
    assert not compare_locked_skeleton(template, output)


def test_s82_top_header_mutation_is_blocked():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    output.tables[7].rows[13].cells[1].paragraphs[0].runs[0].text = "Regulation"
    errors = compare_locked_skeleton(template, output)
    assert any("locked S8.2 header text changed" in error for error in errors)


def test_s82_generic_row_write_is_blocked():
    output = Document(str(TEMPLATE))
    try:
        write_row_values(
            output.tables[7].rows[13],
            ["header", "Substance", "Basis", "Type", "Value"],
            table_index=7,
            row_index=13,
        )
    except MutationViolation:
        pass
    else:
        raise AssertionError("expected MutationViolation for S8.2 header write")
