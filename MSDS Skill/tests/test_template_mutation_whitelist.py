from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from template_mutation_whitelist import (
    audit_cross_page_contract,
    MutationViolation,
    compare_format_anchors,
    compare_locked_skeleton,
    set_sequence_prefix,
    write_s82_top_rows,
    write_row_values,
)
from template_runtime import ensure_source_data_rows, sanitize_template_artifacts


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


def test_value_format_change_is_blocked():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    value = output.tables[0].rows[1].cells[1].paragraphs[0]
    value.paragraph_format.space_after = 123
    errors = compare_format_anchors(template, output)
    assert any("format anchor changed" in error for error in errors)


def test_cross_page_contract_preserves_template_table_and_row_settings():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    report = audit_cross_page_contract(template, output)
    assert report["errors"] == []
    assert len(report["tables"]) == 16
    assert all(item["template_allows_cross_page"] for item in report["tables"])
    assert all(item["output_allows_cross_page"] for item in report["tables"])
    assert all(item["template_row_cant_split"] == item["output_row_cant_split"] for item in report["tables"])
    assert all(item["template_all_rows_breakable"] == item["output_all_rows_breakable"] for item in report["tables"])


def test_cross_page_contract_blocks_row_split_setting_drift():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    tr_pr = output.tables[0].rows[1]._tr.get_or_add_trPr()
    tr_pr.append(tr_pr.makeelement(qn("w:cantSplit"), {}))
    report = audit_cross_page_contract(template, output)
    assert any("cross-page row settings changed" in error for error in report["errors"])


def test_blank_s117_value_inherits_template_body_run_format():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    row = output.tables[10].rows[12]
    write_row_values(
        row,
        ["11.7 生殖毒性：", "生育力", "无数据"],
        table_index=10, row_index=12,
    )
    value_run = row.cells[-1].paragraphs[0].runs[0]
    assert value_run._r.rPr is not None
    assert value_run._r.rPr.find(qn("w:sz")).get(qn("w:val")) == "24"
    assert not compare_format_anchors(template, output)


def test_template_label_artifacts_are_preserved_exactly():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    original_label = template.tables[7].rows[3].cells[0].text
    sanitize_template_artifacts(output)
    assert output.tables[7].rows[3].cells[0].text == original_label
    assert len(output.tables[7].rows) == len(template.tables[7].rows)
    assert not compare_locked_skeleton(template, output)
    assert not compare_format_anchors(template, output)


def test_one_cell_write_does_not_append_an_empty_line():
    output = Document(str(TEMPLATE))
    row = output.tables[14].rows[1]
    write_row_values(row, ["法规文本", ""], table_index=14, row_index=1)
    assert row.cells[0].text == "法规文本"


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


def test_extra_s9_source_row_uses_cloned_style_and_source_label_only_on_insert():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    ensure_source_data_rows(output, 9, 24)
    row = output.tables[8].rows[24]
    write_row_values(
        row, ["9.24  New physical property:", "source value"],
        table_index=8, row_index=24, inserted_data_row=True,
    )
    assert row.cells[0].text == "9.24  New physical property:"
    assert row.cells[1].text == "source value"
    assert not compare_locked_skeleton(template, output)


def test_section9_sequence_renumber_can_rebalance_prefix_spacing():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    cell = output.tables[8].rows[12].cells[0]  # template 9.12 has one separator space
    updated = set_sequence_prefix(cell, 9, 5, prefix_width=5)
    assert updated.startswith("9.5  ")
    assert not compare_locked_skeleton(template, output)
    assert not compare_format_anchors(template, output)


def test_extra_s15_regulation_row_uses_cloned_note_style():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    ensure_source_data_rows(output, 15, 9)
    row = output.tables[14].rows[9]
    write_row_values(
        row, ["Source-backed additional regulation"],
        table_index=14, row_index=9, inserted_data_row=True,
    )
    assert row.cells[0].text == "Source-backed additional regulation"
    assert not compare_locked_skeleton(template, output)
    assert not compare_format_anchors(template, output)


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


def test_s82_empty_records_hide_workplace_component_block():
    template = Document(str(TEMPLATE))
    output = Document(str(TEMPLATE))
    table = output.tables[7]
    audit = write_s82_top_rows(table, [], "zh")
    assert audit == {"record_count": 0, "row_count": 0, "placeholder": False, "hidden": True}
    assert len(table.rows) == 12
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
