from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from section2_fact_router import ROUTER_VERSION, audit, semantic_target  # noqa: E402


def _facts(*, source_locator="s2.h_statements[1]", source_text="H226 flammable liquid"):
    return {
        "fact_ledger": [{
            "fact_id": "FACT-1",
            "source_section": "s2",
            "source_locator": source_locator,
            "source_text": source_text,
            "normalized_value": source_text,
            "source_unit_ids": ["SRC-1"],
            "evidence_type": "explicit",
            "mapping_status": "mapped",
            "line_break_policy": "preserve_logical_lines",
        }],
        "source_mapping": {
            "items": [{
                "fact_id": "FACT-1",
                "source_section": "s2",
                "source_locator": source_locator,
                "source_text": source_text,
                "decision": "mapped",
                "target_section": "s2",
                "target_slot": "s2.h_statements[1]",
            }],
        },
        "output_traceability": {"items": []},
        "section2_routing": {
            "version": ROUTER_VERSION,
            "status": "reviewed",
            "items": [{
                "fact_id": "FACT-1",
                "semantic_target": "hazard_statements",
                "usage": "exclusive",
            }],
        },
        "zh": {"s2": [["2.5 危险性说明：", source_text]]},
        "en": {"s2": [["2.5 Hazard statements:", source_text]]},
    }


def _trace(target, *, zh="H226 flammable liquid", en="H226 flammable liquid"):
    return {
        "target_section": "s2",
        "target_slot": f"s2.{target}",
        "decision": "written",
        "source_fact_ids": ["FACT-1"],
        "line_break_policy": "preserve_logical_lines",
        "output_values": {"zh": zh, "en": en},
    }


def test_semantic_target_rejects_generic_positional_row():
    assert semantic_target("s2.h_statements[1]") == "hazard_statements"
    assert semantic_target("s2.row[1]") is None
    assert semantic_target("2.8 健康危害") == "health_hazards"


def test_emergency_overview_cannot_be_synthesized_from_hazard_statement():
    facts = _facts()
    facts["output_traceability"]["items"] = [_trace("emergency_overview")]
    facts["zh"]["s2"] = [["2.1 紧急情况概述", "H226 flammable liquid"]]
    facts["en"]["s2"] = [["2.1 Emergency overview", "H226 flammable liquid"]]
    report = audit(facts)
    assert report["status"] == "failed"
    assert any("mapping assigns another destination" in error for error in report["errors"])


def test_one_fact_cannot_be_duplicated_across_section2_targets():
    facts = _facts()
    facts["output_traceability"]["items"] = [
        _trace("hazard_statements"),
        _trace("health_hazards"),
    ]
    report = audit(facts)
    assert report["status"] == "failed"
    assert any("duplicated across targets" in error for error in report["errors"])


def test_route_duplicate_in_health_row_is_blocked_only_for_covered_route():
    facts = _facts(source_text="H315 Causes skin irritation.")
    facts["zh"]["s2"] = [
        ["2.5 危险性说明：", "H315 Causes skin irritation."],
        ["2.8 健康危害 [route=skin]", "Skin irritation."],
        ["2.8 健康危害 [route=eyes]", "Eye irritation."],
    ]
    facts["en"]["s2"] = [
        ["2.5 Hazard statements:", "H315 Causes skin irritation."],
        ["2.8 Health hazards [route=skin]", "Skin irritation."],
        ["2.8 Health hazards [route=eyes]", "Eye irritation."],
    ]
    facts["output_traceability"]["items"] = [
        _trace("hazard_statements", zh="H315 Causes skin irritation.", en="H315 Causes skin irritation."),
        _trace("health_hazards.skin", zh="Skin irritation.", en="Skin irritation."),
        _trace("health_hazards.eyes", zh="Eye irritation.", en="Eye irritation."),
    ]
    report = audit(facts)
    assert any(
        "repeats a route already covered" in error and "skin" in error
        for error in report["errors"]
    )
    assert not any(
        "repeats a route already covered" in error and "eyes" in error
        for error in report["errors"]
    )


def test_explicit_source_emergency_overview_and_translation_are_accepted():
    source_text = "吸入后可能引起呼吸道刺激。"
    facts = _facts(
        source_locator="s2.1.emergency_overview[1]",
        source_text=source_text,
    )
    facts["source_mapping"]["items"][0]["target_slot"] = "s2.emergency_overview[1]"
    facts["section2_routing"]["items"][0]["semantic_target"] = "emergency_overview"
    facts["output_traceability"]["items"] = [{
        "target_section": "s2",
        "target_slot": "s2.emergency_overview",
        "decision": "written",
        "source_fact_ids": ["FACT-1"],
        "line_break_policy": "preserve_logical_lines",
        "output_values": {"zh": source_text, "en": "May cause respiratory irritation after inhalation."},
    }]
    facts["zh"]["s2"] = [["2.1 紧急情况概述", source_text]]
    facts["en"]["s2"] = [["2.1 Emergency overview", "May cause respiratory irritation after inhalation."]]
    report = audit(facts)
    assert report["status"] == "passed", report["errors"]


def test_reviewed_component_classification_can_route_to_section2_category():
    facts = _facts(source_locator="s3.component_ghs[1]")
    facts["fact_ledger"][0]["source_section"] = "s3"
    facts["source_mapping"]["items"][0].update({
        "source_section": "s3",
        "source_locator": "s3.component_ghs[1]",
        "target_slot": "s2.ghs_classes",
        "cross_section_route": True,
    })
    facts["section2_routing"]["items"][0].update({
        "fact_id": "FACT-1",
        "semantic_target": "ghs_classes",
        "cross_section_route": True,
        "reason": "Reviewed component GHS classification routes to S2.1.",
    })
    facts["output_traceability"]["items"] = [{
        "target_section": "s2",
        "target_slot": "s2.ghs_classes",
        "decision": "written",
        "source_fact_ids": ["FACT-1"],
        "line_break_policy": "preserve_logical_lines",
        "output_values": {"zh": "易燃液体3 H226", "en": "Flammable liquid 3 H226"},
    }]
    facts["zh"]["s2"] = [["2.2 GHS危险性类别", "易燃液体3 H226"]]
    facts["en"]["s2"] = [["2.2 GHS classification", "Flammable liquid 3 H226"]]
    report = audit(facts)
    assert report["status"] == "passed", report["errors"]


def test_precautionary_group_requires_semantic_route_and_both_language_headings():
    facts = _facts(
        source_locator="s2.line[4]",
        source_text="\u9884\u9632\u63aa\u65bd\uff1a\nP210 \u8fdc\u79bb\u70ed\u6e90\u3002",
    )
    facts["fact_ledger"][0].update({
        "source_kind": "precautionary_group",
        "group_key": "prevention",
        "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a",
        "has_statements": True,
    })
    facts["source_mapping"]["items"][0].update({
        "target_slot": "s2.precautionary_statements.group[prevention]",
        "source_kind": "precautionary_group",
        "group_key": "prevention",
        "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a",
        "has_statements": True,
    })
    facts["section2_routing"]["items"][0] = {
        "fact_id": "FACT-1",
        "semantic_target": "precautionary_statements",
        "usage": "exclusive",
    }
    facts["output_traceability"]["items"] = [{
        "target_section": "s2",
        "target_slot": "s2.precautionary_statements",
        "decision": "written",
        "source_fact_ids": ["FACT-1"],
        "line_break_policy": "preserve_logical_lines",
        "output_values": {
            "zh": "\u9884\u9632\u63aa\u65bd\uff1a\nP210 \u8fdc\u79bb\u70ed\u6e90\u3002",
            "en": "Prevention:\nP210 Keep away from heat.",
        },
    }]
    facts["zh"]["s2"] = [["2.6 \u9632\u8303\u8bf4\u660e\uff1a", facts["output_traceability"]["items"][0]["output_values"]["zh"]]]
    facts["en"]["s2"] = [["2.6 Precautionary statements:", facts["output_traceability"]["items"][0]["output_values"]["en"]]]
    report = audit(facts)
    assert report["status"] == "passed", report["errors"]


def test_precautionary_group_duplicate_decision_is_blocking():
    facts = _facts(source_locator="s2.line[4]", source_text="\u9884\u9632\u63aa\u65bd\uff1a")
    facts["fact_ledger"][0].update({
        "source_kind": "precautionary_group",
        "group_key": "prevention",
        "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a",
        "has_statements": True,
    })
    facts["source_mapping"]["items"][0].update({
        "decision": "duplicate",
        "source_kind": "precautionary_group",
        "group_key": "prevention",
        "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a",
        "has_statements": True,
    })
    report = audit(facts)
    assert report["status"] == "failed"
    assert any("precautionary group fact FACT-1 cannot be silently marked duplicate" in error for error in report["errors"])


def test_reviewed_shared_exception_is_explicit_and_target_limited():
    facts = _facts()
    facts["section2_routing"]["items"][0] = {
        "fact_id": "FACT-1",
        "semantic_target": "hazard_statements",
        "usage": "shared",
        "approved_targets": ["hazard_statements", "health_hazards"],
        "reason": "The reviewed source sentence is intentionally repeated in both controlled destinations.",
    }
    facts["output_traceability"]["items"] = [
        _trace("hazard_statements"),
        _trace("health_hazards"),
    ]
    report = audit(facts)
    assert report["status"] == "passed", report["errors"]
