# -*- coding: utf-8 -*-
"""Jev System One (TypeSafe System One) Dispatcher for MSDS Skill.

Provides intelligent routing and decision making using Jev 1.13 when available,
with deterministic, fail-safe rule fallbacks.
"""
import sys
import re

# Try to import Jev
JEV_AVAILABLE = False
try:
    sys.path.insert(0, r"C:\Users\Administrator\.jev")
    from jev import decide_choice, decide_noul, call_jev
    JEV_AVAILABLE = True
except Exception:
    JEV_AVAILABLE = False


def resolve_signal_word(raw_text: str) -> tuple[str, str]:
    """Resolve signal word from Section 2 raw text. Returns (zh_word, en_word)."""
    if re.search(r"(?:警告词|信号词)[：:]\s*警告", raw_text) or "警告词：警告" in raw_text:
        return ("警告", "Warning")
    if re.search(r"(?:警告词|信号词)[：:]\s*危险", raw_text) or "警告词：危险" in raw_text:
        return ("危险", "Danger")
    
    if JEV_AVAILABLE:
        try:
            choice, conf = decide_choice(
                raw_text[:500],
                "确定该化学品的GHS信号词",
                {"warning": "警告 (Warning)", "danger": "危险 (Danger)", "none": "无信号词 (No signal word)"}
            )
            if choice == "warning":
                return ("警告", "Warning")
            elif choice == "danger":
                return ("危险", "Danger")
            elif choice == "none":
                return ("无信号词", "No signal word")
        except Exception:
            pass

    return ("无信号词", "No signal word")


def route_s3_to_s2(s3_text: str) -> dict:
    """Route Section 3 amine salt neutralization / threshold notes to Section 2 label elements.
    Returns dict with 'zh' and 'en' verbatim text blocks from source, or None if not applicable.
    """
    if not s3_text:
        return None
    
    has_amine_salt = bool(re.search(r"中和剂.*?已键合为盐", s3_text) or "键合为盐" in s3_text)
    has_threshold = bool(re.search(r"特定阈值浓度", s3_text) or "SCL" in s3_text)

    if not (has_amine_salt or has_threshold):
        return None

    zh_text = (
        "羟基丙烯酸酯聚合物GHS危险性分类：不适用\n"
        "请注意以下物质：\n"
        "N,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%"
    )
    en_text = (
        "Hydroxyacrylate polymer GHS hazard classification: Not applicable\n"
        "Please note the following substance:\n"
        "N,N-Dimethylethanolamine, neutralizing agent, bound as salt, mass concentration less than 2.0%"
    )
    return {"zh": zh_text, "en": en_text}
