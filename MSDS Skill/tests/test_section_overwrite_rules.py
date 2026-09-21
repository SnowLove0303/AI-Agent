from pathlib import Path
import sys

import pytest
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from msds_pipeline import ReleaseBlocked, validate_template_baselines  # noqa: E402
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
    assert local_policy_for(9)["match_basis"] == "property_alias"
    assert local_policy_for(11)["match_basis"] == "endpoint_study_field"


def test_section_11_2_three_column_middle_label_is_not_a_value():
    class Cell:
        def __init__(self, text):
            self.text = text

    cells = [Cell("11.2 毒性："), Cell("经口："), Cell("LD50 > 5000 mg/kg")]
    assert [cell.text for cell in _payload_cells(cells, 11)] == ["LD50 > 5000 mg/kg"]
