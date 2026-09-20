# -*- coding: utf-8 -*-
"""Unit tests for Jev System One Engine and Domain Adjudicator."""

import os
import sys
import tempfile
import pytest

# Add scripts directory to path
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from jev_engine import DEFAULT_ENGINE, DecisionLedger, GLOBAL_LEDGER, JevEngine
from jev_domain_adjudicator import DEFAULT_ADJUDICATOR, JevDomainAdjudicator


def test_jev_engine_initialization():
    engine = JevEngine()
    assert engine.api_key.startswith("sk-")
    assert "systemone" in engine.endpoint
    assert engine.model == "jev-1.13-free"


def test_jev_engine_fallback_on_invalid_endpoint():
    """Verify that network errors trigger graceful fallback and record into ledger."""
    bad_engine = JevEngine(endpoint="http://127.0.0.1:59999/invalid", timeout=1.0, max_retries=0)
    choice, conf = bad_engine.decide_choice(
        state="测试状态",
        instructions="测试指令",
        criteria={"a": "选项A", "b": "选项B"},
        fallback_choice="a",
        scenario="fallback_test",
    )
    assert choice == "a"
    assert conf == 0.0

    noul = bad_engine.decide_noul(
        state="测试状态",
        instructions="测试指令",
        fallback_noul=0.5,
        scenario="fallback_test",
    )
    assert noul == 0.5


def test_adjudicate_ghs_signal_word_fast_path():
    adjudicator = JevDomainAdjudicator()
    # Explicit Warning
    zh, en, conf = adjudicator.adjudicate_ghs_signal_word("化学品安全说明书\n警告词：警告\n防范说明：...")
    assert zh == "警告"
    assert en == "Warning"
    assert conf == 1.0

    # Explicit Danger
    zh, en, conf = adjudicator.adjudicate_ghs_signal_word("化学品安全说明书\n信号词：危险\n危险性说明：极度易燃")
    assert zh == "危险"
    assert en == "Danger"
    assert conf == 1.0

    # Explicit Non-hazard
    zh, en, conf = adjudicator.adjudicate_ghs_signal_word("GHS危险性分类：不适用\n无信号词")
    assert zh == "无信号词"
    assert en == "No signal word"
    assert conf == 1.0


def test_adjudicate_ghs_signal_word_live_jev():
    """Test live Jev arbitration on ambiguous text."""
    adjudicator = JevDomainAdjudicator()
    ambiguous_text = "本水性树脂产品未列入危险化学品名录，但在喷涂操作时如果产生气溶胶可能引起轻微呼吸道不适，建议操作人员佩戴防护口罩。"
    zh, en, conf = adjudicator.adjudicate_ghs_signal_word(ambiguous_text)
    assert zh in ["无信号词", "警告"]
    assert en in ["No signal word", "Warning"]
    assert conf >= 0.0


def test_adjudicate_cross_section_fact():
    adjudicator = JevDomainAdjudicator()
    s3_text = "本品含有中和剂 N,N-二甲基乙醇胺，在体系中已键合为盐，质量浓度低于特定浓度限值SCL，不引发分类。"
    res = adjudicator.adjudicate_cross_section_fact(s3_text)
    assert res is not None
    assert "羟基丙烯酸酯聚合物GHS危险性分类：不适用" in res["zh"]
    assert "N,N-二甲基乙醇胺，中和剂，已键合为盐" in res["zh"]
    assert "GHS classification of hydroxyacrylate polymer: Not applicable" in res["en"]

    # Non-applicable S3 text
    res_none = adjudicator.adjudicate_cross_section_fact("纯水 99%，氯化钠 1%")
    assert res_none is None


def test_adjudicate_row_splitting():
    adjudicator = JevDomainAdjudicator()
    # Subject-Object Law: Product vs Polymer
    stmt_a = "该产品无可用的毒理学研究。"
    stmt_b = "羟基聚丙烯酸酯分散体：毒性：无资料；刺激性：无资料。"
    choice, conf = adjudicator.adjudicate_row_splitting(stmt_a, stmt_b)
    assert choice == "split_independent_row"
    assert conf >= 0.9

    # Qualitative vs Quantitative metric
    stmt_c = "未开展针对成品的动物急性毒性试验"
    stmt_d = "二丙二醇丁醚组分：大鼠口服 LD50 > 2000 mg/kg"
    choice2, conf2 = adjudicator.adjudicate_row_splitting(stmt_c, stmt_d)
    assert choice2 == "split_independent_row"


def test_adjudicate_tds_slot_mapping():
    adjudicator = JevDomainAdjudicator()
    # Fast path
    slot1, conf1 = adjudicator.adjudicate_tds_slot_mapping("不挥发份 (120℃/30min)")
    assert slot1 == "solid_content"
    assert conf1 == 1.0

    slot2, conf2 = adjudicator.adjudicate_tds_slot_mapping("羟值")
    assert slot2 == "hydroxyl_content"
    assert conf2 == 1.0

    slot3, conf3 = adjudicator.adjudicate_tds_slot_mapping("涂-4杯流出时间 (25℃)")
    assert slot3 == "viscosity"
    assert conf3 == 1.0


def test_audit_semantic_consistency():
    adjudicator = JevDomainAdjudicator()
    # Contradiction: non-hazard with P405
    bad_facts = {
        "classification_status": "non_hazardous",
        "precautionary_statements": "P405 存放在上锁的密闭储藏间。",
    }
    passed, reason, risk = adjudicator.audit_semantic_consistency(bad_facts)
    assert passed is False
    assert "P405" in reason

    # Clean non-hazard
    good_facts = {
        "classification_status": "non_hazardous",
        "section2": {
            "2.1": "根据 GHS 标准未分类为危险化学品。",
            "2.2": "不适用",
        },
        "precautionary_statements": "P403 存放在通风良好的地方。",
    }
    passed2, reason2, risk2 = adjudicator.audit_semantic_consistency(good_facts)
    assert passed2 is True


def test_decision_ledger_recording_and_export():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tmp_path = tf.name

    try:
        GLOBAL_LEDGER.export(tmp_path)
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = f.read()
            assert "total_decisions" in data
            assert "ledger" in data
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
