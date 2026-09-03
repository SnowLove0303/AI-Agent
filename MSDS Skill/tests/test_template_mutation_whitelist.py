from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from template_mutation_whitelist import (
    compare_locked_skeleton,
    set_sequence_prefix,
    write_row_values,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples" / "template_reference.docx"


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
