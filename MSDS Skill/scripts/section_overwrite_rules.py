"""Executable S1-S16 overwrite contract for the maintained templates."""
from __future__ import annotations

from dataclasses import dataclass

class SectionRuleViolation(ValueError):
    """A semantic payload or active template violates a section contract."""


@dataclass(frozen=True)
class SectionRule:
    section: int
    template_table: int
    source_rule: str
    write_mode: str
    value_scope: str
    empty_policy: str
    structural_policy: str
    source_text_policy: str = "verbatim_or_reviewed_translation"


SECTION_RULES = {
    1: SectionRule(1, 1, "source identification", "field_rows", "value cells; identity overlay", "1.1 blank", "no row rebuild"),
    2: SectionRule(2, 2, "semantic hazard slots with product/component scope", "semantic_slots", "value cells; approved numeric prefix only", "omit missing except source 2.3 other hazards", "omit whole rows then prefix-only renumber", "source-scoped; never collapse Section 3 component GHS evidence into product slots"),
    3: SectionRule(3, 3, "name/CAS/content", "component_rows", "all three data cells", "source-only", "clone styled component rows only", "verbatim source component values; all three writable cells centered"),
    4: SectionRule(4, 4, "first-aid endpoints", "field_rows", "value cells", "hide unsupported item", "no row rebuild"),
    5: SectionRule(5, 5, "fire-fighting endpoints", "field_rows", "value cells", "hide unsupported item", "no row rebuild"),
    6: SectionRule(6, 6, "accidental-release endpoints", "field_rows", "value cells", "hide unsupported item", "no row rebuild"),
    7: SectionRule(7, 7, "handling/storage endpoints", "field_rows", "value cells", "hide unsupported item", "no row rebuild"),
    8: SectionRule(8, 8, "PPE plus engineering controls by meaning", "dedicated_ppe_engineering", "PPE value cells; S8.2 four data columns", "suggestion blank; empty engineering row/block hidden", "dedicated S8 writers only"),
    9: SectionRule(9, 9, "physical/chemical properties", "field_rows", "value cells", "omit missing-data row", "omit whole rows then prefix-only renumber"),
    10: SectionRule(10, 10, "stability/reactivity endpoints", "field_rows", "value cells", "omit unsupported or missing item", "smallest safe row omission", "verbatim endpoint value; sequence and label geometry remain template-owned"),
    11: SectionRule(11, 11, "toxicology notes/endpoints", "endpoint_notes", "note slots or endpoint value cells; final cell only in 11.1/11.2/11.7 three-column rows", "preserve explicit availability sentence; omit absent endpoints; 11.7 no-data only when source-present", "no invented endpoint or generic renumber", "verbatim structured source fields; first two columns of 11.1/11.2/11.7 are locked labels"),
    12: SectionRule(12, 12, "ecotoxicity/persistence/adverse effects", "endpoint_rows", "source-backed endpoint value cells", "template-only note rows hidden", "remove note rows only; retain mapped 12.1-12.3"),
    13: SectionRule(13, 13, "disposal endpoints", "field_rows", "value cells", "source-only", "no row rebuild"),
    14: SectionRule(14, 14, "transport endpoints", "field_rows", "value cells", "source-only", "no row rebuild"),
    15: SectionRule(15, 15, "laws/regulations", "field_rows", "value cells", "empty legal rows hidden", "remove only empty row; preserve source order"),
    16: SectionRule(16, 16, "disclaimer", "field_rows", "value cells", "source-only", "no row rebuild"),
}

# Local rules are deliberately data, not scattered writer-side exceptions.
# They refine semantic routing after the global source/template/value gates.
LOCAL_SECTION_POLICIES = {
    2: {"match_basis": "semantic_route_with_product_component_scope", "source_text_policy": "verbatim_product_s2_facts plus explicit reviewed cross-section route of component GHS classification/H-code evidence into S2.1; one classification/H-code pair per line; reviewed H226 typo correction only when evidence-bound; S2.2/S2.3 only special-substance attention note in title-plus-explanation shape; retain threshold on explanation line; no-pictogram=>无象形图; S2.5 H and S2.6 P logical lines with heading plus hanging detail paragraphs", "empty_policy": "hide_then_renumber"},
    3: {"match_basis": "component_name_cas_content_plus_component_evidence", "source_text_policy": "verbatim_source_component_values; component GHS evidence remains routed evidence and is never copied into S2 label-elements prose", "layout_policy": "all three component data cells horizontal and vertical center", "empty_policy": "source-only"},
    8: {"match_basis": "ppe_and_control_meaning", "source_text_policy": "verbatim_source_control_or_ppe; preserve the template hand-protection parent even when its value is blank; never duplicate another PPE value", "empty_policy": "hide_absent_ppe_and_engineering_block"},
    9: {"match_basis": "property_alias", "source_text_policy": "match source properties to template labels by semantic alias; preserve explicit not-applicable values and omit only approved missing rows", "empty_policy": "hide_missing_property_row"},
    10: {"match_basis": "endpoint_semantics", "source_text_policy": "verbatim_endpoint_value; sequence prefix and label text/format/indent/spacing remain locked", "empty_policy": "reviewed_absence_declaration_or_hide"},
    11: {"match_basis": "endpoint_study_field", "source_text_policy": "verbatim_structured_source_fields; in 11.1/11.2/11.7 three-column rows write only the final value cell; renumber surviving endpoint groups continuously after omission", "layout_policy": "first two columns are locked bold labels; every value is explicit language font/12pt, vertical center, left align", "empty_policy": "align_skeleton_then_hide_absent_endpoint"},
    12: {"match_basis": "endpoint_and_explanatory_note", "source_text_policy": "verbatim_endpoint_value", "empty_policy": "hide_unmatched_explanatory_row"},
    13: {"match_basis": "disposal_endpoint", "source_text_policy": "verbatim_source_instruction; combine source explanation lines into the template one-cell note slot, retain the final two-column treatment row", "empty_policy": "source_only"},
    14: {"match_basis": "transport_field", "source_text_policy": "verbatim_source_instruction", "empty_policy": "source_only"},
}


def local_policy_for(section: int) -> dict:
    """Return the local semantic rule without weakening global gates."""
    return dict(LOCAL_SECTION_POLICIES.get(section, {
        "match_basis": "registered_semantic_field",
        "source_text_policy": "verbatim_or_reviewed_translation",
        "empty_policy": rule_for(section).empty_policy,
    }))


def rule_for(section: int) -> SectionRule:
    try:
        return SECTION_RULES[section]
    except KeyError as exc:
        raise SectionRuleViolation(f"no overwrite rule registered for S{section}") from exc


def _unique_cell_count(row) -> int:
    return len({id(cell._tc) for cell in row.cells})


def validate_section_template(document, language: str) -> None:
    """Validate the physical table contract before any value is written."""
    if language not in {"zh", "en"}:
        raise SectionRuleViolation(f"unsupported language: {language}")
    if len(document.tables) != 16:
        raise SectionRuleViolation(f"template must contain 16 section tables, found {len(document.tables)}")
    if set(SECTION_RULES) != set(range(1, 17)):
        raise SectionRuleViolation("S1-S16 overwrite rule registry is incomplete")
    for section, rule in SECTION_RULES.items():
        if rule.template_table != section:
            raise SectionRuleViolation(f"S{section} rule points to table {rule.template_table}")
        if not document.tables[rule.template_table - 1].rows:
            raise SectionRuleViolation(f"S{section} template table is empty")
    s3 = document.tables[2]
    if len(s3.rows) < 4 or _unique_cell_count(s3.rows[3]) != 3:
        raise SectionRuleViolation("S3 requires a three-column component data row")
    s8 = document.tables[7]
    if len(s8.rows) >= 16:
        if _unique_cell_count(s8.rows[12]) != 1:
            raise SectionRuleViolation("S8 requires its one-cell engineering-control parent row")
        expected_header = ("物质", "依据", "类型", "数值") if language == "zh" else ("Substance", "Basis", "Type", "Value")
        header = tuple(cell.text.strip() for cell in {
            id(cell._tc): cell for cell in s8.rows[13].cells
        }.values())
        if header != expected_header:
            raise SectionRuleViolation(f"S8.2 header mismatch: expected {expected_header}, found {header}")
    elif len(s8.rows) == 12:
        pass
    else:
        raise SectionRuleViolation(f"S8 requires either 12 or at least 16 rows, found {len(s8.rows)}")


def validate_section_payload(section: int, rows, table, *, check_capacity: bool = True) -> None:
    """Reject positional/scalar payloads before they reach a template row."""
    rule = rule_for(section)
    if not isinstance(rows, list):
        raise SectionRuleViolation(f"S{rule.section} requires a list of semantic rows")
    if check_capacity and section not in {3, 8} and len(rows) > len(table.rows) - 1:
        raise SectionRuleViolation(
            f"S{section} payload exceeds template capacity: {len(rows)} > {len(table.rows) - 1}"
        )
    for row_number, row in enumerate(rows, 1):
        if not isinstance(row, (list, tuple)) or not row:
            raise SectionRuleViolation(f"S{section} row {row_number} must be a non-empty list/tuple")
    if section == 3 and any(len(row) != 3 for row in rows):
        raise SectionRuleViolation("S3 every row must contain exactly name/CAS/content columns")
    if section in {11, 12} and any(len(row) > 3 for row in rows):
        raise SectionRuleViolation(f"S{section} rows may contain at most label/sublabel/value")


def sanitize_section_payload(section: int, rows) -> list:
    """Remove only empty intermediate rows before capacity/shape validation.

    This is deliberately conservative. A one-cell row is itself a possible
    source value (especially S15/S16); rows with explicit missing wording are
    retained for the section policy to decide. Rows with no payload at all are
    removed so later values cannot be shifted by an empty source row.
    """
    # Section 1 is a positional identity/supplier skeleton.  Its blank
    # product-name and supplier-heading rows are structural slots; removing
    # them shifts every following value into the wrong locked label.
    if section == 1:
        return [list(row) for row in list(rows or [])
                if isinstance(row, (list, tuple)) and row]
    if section == 9:
        return [dict(row) if isinstance(row, dict) else list(row)
                for row in list(rows or [])
                if isinstance(row, dict) or (isinstance(row, (list, tuple)) and row)]
    cleaned = []
    for row in list(rows or []):
        if isinstance(row, dict):
            value = str(row.get("value") or "").strip()
            if value or row.get("state") in {"EXPLICIT_MISSING", "NOT_APPLICABLE"}:
                cleaned.append(row)
            continue
        if not isinstance(row, (list, tuple)):
            continue
        values = [str(value or "").strip() for value in row]
        if not any(values):
            continue
        if section in {2, 8}:
            # S2/S8 are semantic fixed-slot projections. Keep their headings
            # and sparse rows until the value writer has used the physical
            # template positions; the later source-presence pass is the only
            # stage allowed to remove empty rows. Compacting either payload
            # here would move a later value into an earlier locked label.
            cleaned.append(list(row))
            continue
        if len(values) > 1 and not any(values[1:]) and section not in {3, 11, 12, 13, 15, 16}:
            continue
        # A common one-cell draft shape is [label, label + value]. Keep the
        # row here; the mutation whitelist performs the value-only de-dup.
        cleaned.append(list(row))
    return cleaned


__all__ = ["LOCAL_SECTION_POLICIES", "SECTION_RULES", "SectionRule", "SectionRuleViolation",
           "local_policy_for", "rule_for", "sanitize_section_payload",
           "validate_section_payload", "validate_section_template"]
