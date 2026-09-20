# -*- coding: utf-8 -*-
"""Unit tests for GHS code resolver and Jev dispatcher."""
from pathlib import Path
import sys

# Ensure MSDS Skill/scripts is on sys.path
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ghs_code_resolver import resolve_precautionary_statements, format_precautionary_text
from jev_dispatcher import resolve_signal_word, route_s3_to_s2
from section2_ghs_policy import format_label_elements


def test_resolve_precautionary_statements_full():
    raw_lines = [
        "穿戴防护用品（手套、防护镜、工作服等）。",
        "作业后彻底清洗身体接触部位。",
        "使用本品时不得进食、饮水或吸烟。",
        "只能在室外或通风良好处操作。",
        "如吸入：将受害人转移到空气新鲜处，如有不适，就医。",
        "如眼睛接触：用清水清洗数分钟，如有不适，就医。",
        "如皮肤接触：用肥皂和水清洗，如有不适，就医。",
        "如误服：漱口，禁止催吐，立即就医。",
        "收集泄漏物。",
        "火灾时使用干粉、泡沫、二氧化碳灭火。",
        "避光、阴凉、通风干燥处储存，存储温度5-35℃，避免霜冻。",
        "空桶及包装物按照环保法规处置。",
    ]
    groups = resolve_precautionary_statements(raw_lines)
    
    # Check prevention
    prev_codes = [s["code"] for s in groups["prevention"]["statements"]]
    assert "P280" in prev_codes
    assert "P264" in prev_codes
    assert "P270" in prev_codes
    assert "P271" in prev_codes

    # Check response
    resp_codes = [s["code"] for s in groups["response"]["statements"]]
    assert "P304+P340" in resp_codes
    assert "P305+P351+P338" in resp_codes
    assert "P302+P352" in resp_codes
    assert "P301+P330+P331" in resp_codes
    assert "P391" in resp_codes
    assert "P370+P378" in resp_codes

    # Check storage
    stor_codes = [s["code"] for s in groups["storage"]["statements"]]
    assert "P403+P235" in stor_codes

    # Check disposal
    disp_codes = [s["code"] for s in groups["disposal"]["statements"]]
    assert "P501" in disp_codes

    # Test formatting
    zh_text = format_precautionary_text(groups, "zh")
    assert "预防措施：" in zh_text
    assert "P280" in zh_text
    assert "事故响应：" in zh_text
    assert "P304+P340" in zh_text
    assert "安全储存：" in zh_text
    assert "P403+P235" in zh_text
    assert "废弃处置：" in zh_text
    assert "P501" in zh_text

    en_text = format_precautionary_text(groups, "en")
    assert "Prevention:" in en_text
    assert "P280 Wear protective gloves" in en_text
    assert "Response:" in en_text
    assert "Storage:" in en_text
    assert "Disposal:" in en_text


def test_resolve_signal_word():
    assert resolve_signal_word("2.4 警告词：警告") == ("警告", "Warning")
    assert resolve_signal_word("信号词：危险") == ("危险", "Danger")
    assert resolve_signal_word("无特别提示") == ("无信号词", "No signal word")


def test_route_s3_to_s2():
    s3_raw = (
        "N,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%，"
        "特定阈值浓度≥5% 特异性靶器官系统毒性3 H335"
    )
    routed = route_s3_to_s2(s3_raw)
    assert routed is not None
    assert "N,N-二甲基乙醇胺" in routed["zh"]
    assert "已完全键合为盐" in routed["zh"]
    assert "SCL >= 5%" in routed["en"]

    assert route_s3_to_s2("普通水性树脂，无中和剂") is None


def test_format_label_elements_with_extra_note():
    # Only extra note
    res_zh = format_label_elements("zh", [], extra_note="重要提示：已键合为盐")
    assert res_zh == "重要提示：已键合为盐"

    # Ingredients + extra note
    res_en = format_label_elements("en", ["Component A (10%)"], extra_note="Note: neutralized")
    assert "Hazardous ingredients required to be listed on the label:" in res_en
    assert "Component A (10%)" in res_en
    assert "Note: neutralized" in res_en
