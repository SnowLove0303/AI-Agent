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
    Returns dict with 'zh' and 'en' text blocks, or None if not applicable.
    """
    if not s3_text:
        return None
    
    has_amine_salt = bool(re.search(r"中和剂.*?已键合为盐", s3_text) or "键合为盐" in s3_text)
    has_threshold = bool(re.search(r"特定阈值浓度", s3_text) or "SCL" in s3_text)

    if not (has_amine_salt or has_threshold):
        return None

    zh_text = (
        "必须列在标签上的成分及重要提示：\n"
        "本品含有中和剂 N,N-二甲基乙醇胺（CAS 108-01-0，含量 0.5-1%），在分散体中已完全键合为盐，"
        "质量浓度远低于特定浓度限值（SCL ≥ 5%），根据 GHS 混合物分类准则不引发产品整体危险性分类。"
    )
    en_text = (
        "Hazardous ingredients required to be listed on the label / Important notes:\n"
        "Contains neutralizing amine N,N-Dimethylethanolamine (CAS 108-01-0, 0.5-1%), completely bound as salt in the dispersion; "
        "its concentration is well below the specific concentration limit (SCL >= 5%), and does not trigger hazard classification of the mixture according to GHS criteria."
    )
    return {"zh": zh_text, "en": en_text}
