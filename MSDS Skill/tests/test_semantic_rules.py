# -*- coding: utf-8 -*-
"""Offline regression tests for deterministic semantic rules."""

import os
import sys

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from semantic_rules import DEFAULT_ROUTER, SemanticRouter


def test_router_has_no_credential_or_network_configuration():
    router = SemanticRouter()
    assert not hasattr(router, "api_key")
    assert not hasattr(router, "endpoint")
    assert not hasattr(router, "model")


def test_explicit_signal_word_fast_paths():
    assert DEFAULT_ROUTER.resolve_signal_word("警告词：警告") == ("警告", "Warning", 1.0)
    assert DEFAULT_ROUTER.resolve_signal_word("信号词：危险") == ("危险", "Danger", 1.0)
    assert DEFAULT_ROUTER.resolve_signal_word("GHS危险性分类：不适用\n无信号词") == ("无信号词", "No signal word", 1.0)


def test_ambiguous_signal_word_uses_safe_local_fallback():
    assert DEFAULT_ROUTER.resolve_signal_word("可能引起轻微呼吸道不适") == ("无信号词", "No signal word", 0.0)


def test_cross_section_route_is_source_pattern_bound():
    raw = "N,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%，特定阈值浓度≥5%"
    routed = DEFAULT_ROUTER.route_cross_section_fact(raw)
    assert routed is not None
    assert "N,N-二甲基乙醇胺" in routed["zh"]
    assert "N,N-Dimethylethanolamine" in routed["en"]
    assert DEFAULT_ROUTER.route_cross_section_fact("普通水性树脂，无中和剂") is None


def test_row_split_and_tds_slot_rules_are_deterministic():
    assert DEFAULT_ROUTER.classify_row_split(
        "该产品无可用的毒理学研究。", "羟基聚丙烯酸酯分散体：毒性：无资料。"
    )[0] == "split_independent_row"
    assert DEFAULT_ROUTER.map_tds_slot("涂-4杯流出时间 (25℃)") == ("viscosity", 1.0)
    assert DEFAULT_ROUTER.map_tds_slot("未知技术参数") == ("unknown", 0.0)


def test_semantic_consistency_gate_has_no_remote_fallback():
    bad = {
        "classification_status": "non_hazardous",
        "precautionary_statements": "P405 存放在上锁的密闭储藏间。",
    }
    passed, reason, risk = DEFAULT_ROUTER.check_semantic_consistency(bad)
    assert passed is False
    assert "P405" in reason
    assert risk == 1.0

    passed2, reason2, risk2 = DEFAULT_ROUTER.check_semantic_consistency(
        {"classification_status": "non_hazardous", "section2": {"2.1": "根据 GHS 标准未分类为危险化学品。"}}
    )
    assert passed2 is True
    assert risk2 == 0.0
