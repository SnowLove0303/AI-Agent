from pathlib import Path
import sys

import pytest
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from msds_pipeline import (  # noqa: E402
    ReleaseBlocked,
    align_note_section_rows,
    align_s9_rows,
    validate_template_baselines,
)
from section2_ghs_policy import (  # noqa: E402
    normalize_non_hazard_category,
    normalize_ghs_classification_text,
    normalize_s2_projected_rows,
    sanitize_label_elements_text,
)
from section_overwrite_rules import (  # noqa: E402
    LOCAL_SECTION_POLICIES,
    SECTION_RULES,
    local_policy_for,
    SectionRuleViolation,
    validate_section_payload,
    validate_section_template,
)
from missing_data_policy import _payload_cells  # noqa: E402


def test_active_templates_match_all_sixteen_section_rules():
    assert set(SECTION_RULES) == set(range(1, 17))
    for language, filename in (("zh", "template_reference.docx"),
                               ("en", "template_reference_en.docx")):
        validate_section_template(Document(str(ROOT / "examples" / filename)), language)


def test_component_payload_cannot_use_positional_two_column_rows():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    with pytest.raises(SectionRuleViolation, match="exactly name/CAS/content"):
        validate_section_payload(3, [["name", "CAS"]], template.tables[2])


def test_modified_active_template_cannot_become_the_audit_baseline(tmp_path):
    cn = ROOT / "examples" / "template_reference.docx"
    en = ROOT / "examples" / "template_reference_en.docx"
    en_source = ROOT / "examples" / "template_reference_en_source.docx"
    tampered = tmp_path / "template_reference.docx"
    tampered.write_bytes(cn.read_bytes() + b"tampered")
    with pytest.raises(ReleaseBlocked, match="template baseline"):
        validate_template_baselines(tampered, en, en_source)


def test_local_rules_are_semantic_and_cover_known_high_risk_sections():
    assert {2, 8, 9, 10, 11, 12, 13, 14} <= set(LOCAL_SECTION_POLICIES)
    assert local_policy_for(8)["match_basis"] == "ppe_and_control_meaning"
    assert local_policy_for(9)["match_basis"] == "property_alias_one_fact_per_property_row"
    assert local_policy_for(11)["match_basis"] == "endpoint_study_field"


def test_section_11_2_three_column_middle_label_is_not_a_value():
    class Cell:
        def __init__(self, text):
            self.text = text

    cells = [Cell("11.2 毒性："), Cell("经口："), Cell("LD50 > 5000 mg/kg")]
    assert [cell.text for cell in _payload_cells(cells, 11)] == ["LD50 > 5000 mg/kg"]


def test_section2_keeps_explicit_category_and_line_breaks_special_note():
    assert normalize_non_hazard_category("GHS危险性类别: 无") == "无"
    assert sanitize_label_elements_text("请注意以下物质：，N,N-二甲基乙醇胺\n特定阈值浓度≥5%") == (
        "请注意以下物质：\nN,N-二甲基乙醇胺，特定阈值浓度≥5%"
    )


def test_section2_classification_keeps_h_code_with_class_and_corrects_reviewed_typo():
    assert normalize_ghs_classification_text(
        "依然液体3 H226；急性毒性4 吸入性 H332；皮肤腐蚀1B H314"
    ) == (
        "易燃液体3 H226\n急性毒性4 吸入性 H332\n皮肤腐蚀1B H314"
    )


def test_section2_h_and_p_values_split_before_the_guarded_writer():
    rows = normalize_s2_projected_rows([
        ["2.5 危险性说明：", "H226 易燃液体。 H332 吸入有害。"],
        ["2.6 防范说明：", "预防措施： P280 戴防护手套。 P270 操作时不得进食。"],
    ])
    assert rows == [
        ["2.5 危险性说明：", "H226 易燃液体。\nH332 吸入有害。"],
        ["2.6 防范说明：", "预防措施：\nP280 戴防护手套。\nP270 操作时不得进食。"],
    ]


def test_section2_english_classification_uses_the_same_line_policy():
    rows = normalize_s2_projected_rows([
        ["2.2 GHS classification", "Flammable liquid 3 H226; Skin corrosion 1B H314"],
        ["2.3 GHS label elements", "Please note the following substance:\nN,N-dimethylethanolamine\nspecific concentration limit >=5%"],
    ])
    assert rows == [
        ["2.2 GHS classification", "Flammable liquid 3 H226\nSkin corrosion 1B H314"],
        ["2.3 GHS label elements", "Please note the following substance:\nN,N-dimethylethanolamine, specific concentration limit >=5%"],
    ]


def test_section9_matches_properties_by_label_not_source_position():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    rows = align_s9_rows([
        {"label": "9.3 pH值：", "value": "7-9"},
        {"label": "外 观：", "value": "透明装液体"},
    ], template.tables[8])
    assert rows[0][1] == "透明装液体"
    assert next(value for label, value in rows if "ph" in label.casefold()) == "7-9"


def test_section9_preserves_conditions_and_keeps_each_property_independent():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    rows = align_s9_rows([
        {"label": "9.3 pH值（5%水溶液）：", "value": "10-12"},
        {"label": "9.4 离子性：", "value": "不适用"},
        {"label": "9.6 表面张力（10%水溶液）：", "value": "55dynes/cm"},
        {"label": "9.9 水溶性：", "value": "完全混溶"},
        {"label": "9.10 粘度/25℃：", "value": "<500mPa.S"},
        {"label": "9.22 其他信息：", "value": "上述数据非产品指标。"},
    ], template.tables[8])
    by_label = {label.strip(): value for label, value in rows}
    assert by_label["9.3  pH值（5%水溶液）："] == "10-12"
    assert by_label["9.4  离子性："] == "不适用"
    assert by_label["9.14 表面张力（10%水溶液）："] == "55dynes/cm"
    assert by_label["9.13 水溶性："] == "完全混溶"
    assert by_label["9.19 动力粘度（25℃）："] == "<500mPa.S"
    assert by_label["9.24 其他信息："] == "上述数据非产品指标。"
    assert "<500mPa.S" not in by_label["9.13 水溶性："]
    assert "离子性" not in by_label["9.24 其他信息："]

    en_template = Document(str(ROOT / "examples" / "template_reference_en.docx"))
    en_rows = align_s9_rows([
        {"label": "9.3 pH value (5% aqueous solution):", "value": "10-12"},
        {"label": "9.4 Ionicity:", "value": "Not applicable"},
        {"label": "9.6 Surface tension (10% aqueous solution):", "value": "55dynes/cm"},
        {"label": "9.9 Solubility in water:", "value": "Completely miscible"},
        {"label": "9.10 Viscosity/25°C:", "value": "<500mPa.S"},
        {"label": "9.22 Other information:", "value": "These data are not product specifications."},
    ], en_template.tables[8])
    en_by_label = {label.strip(): value for label, value in en_rows}
    assert any("pH value (5% aqueous solution)" in label for label in en_by_label)
    assert any("Surface tension (10% aqueous solution)" in label for label in en_by_label)
    assert any("Dynamic viscosity (25°C)" in label for label in en_by_label)
    assert en_by_label["9.4  Ionicity:"] == "Not applicable"
    assert en_by_label["9.13 Solubility in water:"] == "Completely miscible"


def test_section9_rejects_a_property_embedded_in_another_property_value():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    with pytest.raises(ValueError, match="each property to its own row"):
        align_s9_rows([
            {"label": "水溶性：", "value": "完全混溶\n粘度/25℃：\n<500mPa.S"},
        ], template.tables[8])
    with pytest.raises(ValueError, match="each property to its own row"):
        align_s9_rows([
            {"label": "其他信息：", "value": "离子性：不适用"},
        ], template.tables[8])


def test_section13_combines_two_notes_into_one_note_slot():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    rows = align_note_section_rows([
        ["第一条说明", ""],
        ["第二条说明", ""],
        ["处理方法：", "处置值"],
    ], template.tables[12])
    assert rows == [["第一条说明\n第二条说明"], ["处理方法：", "处置值"]]


def test_section12_never_discards_explanation_lines_when_notes_exceed_slots():
    template = Document(str(ROOT / "examples" / "template_reference.docx"))
    rows = align_note_section_rows([
        ["产品无可用生态毒理学研究。"],
        ["以下结果属于组分 A："],
        ["测试条件：96 小时。"],
        ["12.1 生态毒性：", "LC50：1,500mg/l"],
    ], template.tables[11])
    note_text = "\n".join(row[0] for row in rows if len(row) == 1)
    assert "产品无可用生态毒理学研究。" in note_text
    assert "以下结果属于组分 A：" in note_text
    assert "测试条件：96 小时。" in note_text
    assert rows[-1] == ["12.1 生态毒性：", "LC50：1,500mg/l"]


def test_source_note_without_a_template_note_slot_blocks_instead_of_dropping():
    table = Document().add_table(rows=1, cols=2)
    row = table.add_row()
    row.cells[0].text = "12.1 生态毒性："
    row.cells[1].text = "LC50：1,500mg/l"
    with pytest.raises(ReleaseBlocked, match="no template note slot"):
        align_note_section_rows([["来源说明必须保留。"], ["12.1 生态毒性：", "LC50"]], table)
