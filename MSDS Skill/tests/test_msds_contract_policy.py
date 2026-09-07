from pathlib import Path
import sys

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from missing_data_policy import (  # noqa: E402
    SourceState,
    apply_source_absence_policy,
    classify_source_value,
)
from msds_pipeline import write_header_footer  # noqa: E402
from template_mutation_whitelist import (  # noqa: E402
    TemplateSlotRegistry,
    write_row_values,
    unique_cells,
)


TEMPLATE = ROOT / "examples" / "template_reference.docx"


def test_source_states_are_distinct():
    assert classify_source_value("厚度≧0.4mm；穿透时间≧480min.") == SourceState.SUPPORTED
    assert classify_source_value("无数据。") == SourceState.EXPLICIT_MISSING
    assert classify_source_value("不适用") == SourceState.NOT_APPLICABLE
    assert classify_source_value("") == SourceState.ABSENT


def test_blank_s8_recommendation_is_not_a_writable_slot_but_gloves_are():
    document = Document(str(TEMPLATE))
    registry = TemplateSlotRegistry.from_document(document)
    table = document.tables[7]

    write_row_values(
        table.rows[8], ["建议：", "污染的手套应废弃。"],
        table_index=7, row_index=8, registry=registry,
    )
    write_row_values(
        table.rows[5], ["氟化橡胶 –FKM:", "厚度≧0.4mm；穿透时间≧480min."],
        table_index=7, row_index=5, registry=registry,
    )

    assert unique_cells(table.rows[8])[1].text == ""
    assert unique_cells(table.rows[5])[1].text == "厚度≧0.4mm；穿透时间≧480min."


def test_pu1001_source_text_is_written_without_summary_loss():
    document = Document(str(TEMPLATE))
    registry = TemplateSlotRegistry.from_document(document)
    ingestion = "正常使用时只有轻微的摄入危害，可能引起胃不适导致呕吐引起胃损伤"
    write_row_values(
        document.tables[1].rows[10], ["2.8  健康危害", ingestion],
        table_index=1, row_index=10, registry=registry,
    )
    assert unique_cells(document.tables[1].rows[10])[1].text == ingestion


def test_absent_and_explicit_missing_rows_follow_different_policies():
    document = Document(str(TEMPLATE))
    table = document.tables[9]  # Section 10
    unique_cells(table.rows[4])[1].text = ""
    unique_cells(table.rows[5])[1].text = "无数据"
    facts = {"s10": [
        ["10.1", "稳定"], ["10.2", "分解"], ["10.3", "无反应"],
        ["10.4", ""], ["10.5", "无数据"],
    ]}

    audit = apply_source_absence_policy(document, facts, unique_cells)
    labels = [unique_cells(row)[0].text for row in table.rows[1:]]
    assert any("10.4" in label for label in audit["source_absent_removed"])
    assert not any("10.4" in label for label in labels)
    assert any("10.5" in label for label in labels)


def test_note_only_sections_keep_only_the_explanation_row():
    document = Document(str(TEMPLATE))
    facts = {
        "s11": [["该产品无可用的毒理学研究。"]],
        "s12": [["该产品无可用的生态毒理学研究。"]],
    }
    audit = apply_source_absence_policy(document, facts, unique_cells)
    assert audit["note_only"] == {"s11": True, "s12": True}
    assert len(document.tables[10].rows) == 2
    assert len(document.tables[11].rows) == 2


def test_header_version_is_inherited_from_template():
    document = Document(str(TEMPLATE))
    version_before = next(
        paragraph.text for paragraph in document.sections[0].header.paragraphs
        if "Version" in paragraph.text
    )
    write_header_footer(document, "zh", "guanzhi", "PU-1001", "2025/2/22")
    version_after = next(
        paragraph.text for paragraph in document.sections[0].header.paragraphs
        if "Version" in paragraph.text
    )
    assert version_after == version_before == "Version：V1.0"
