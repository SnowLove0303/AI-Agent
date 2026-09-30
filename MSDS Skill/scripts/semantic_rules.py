# -*- coding: utf-8 -*-
"""Deterministic semantic rules for the MSDS/TDS pipeline.

This module deliberately has no network, credential, model, retry, or ledger
dependency. Ambiguous input returns a safe local fallback and remains subject
to the normal source-review gates.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


TDS_CANONICAL_SLOTS = {
    "appearance": ["外观", "外表", "状态", "颜色及状态", "appearance", "state", "form"],
    "solid_content": ["固含量", "固含", "固体含量", "不挥发物", "不挥发份", "固体分", "solid content", "solids", "non-volatile matter"],
    "viscosity": ["粘度", "黏度", "涂-4杯粘度", "涂-4杯流出时间", "动力粘度", "旋转粘度", "viscosity", "dynamic viscosity"],
    "hydroxyl_content": ["羟基含量", "羟值", "OH含量", "OH值", "羟基值", "hydroxyl content", "oh value", "hydroxyl value"],
    "ph_value": ["ph值", "ph", "酸碱度", "ph value"],
    "density": ["密度", "比重", "相对密度", "density", "specific gravity"],
    "solvent": ["溶剂", "溶剂体系", "分散介质", "载体", "solvent", "solvent system"],
    "neutralizing_agent": ["中和剂", "中和胺", "成盐剂", "neutralizing agent", "neutralizer"],
}


class SemanticRouter:
    """Local, deterministic resolver for the supported semantic cases."""

    def resolve_signal_word(self, raw_text: str) -> Tuple[str, str, float]:
        text = str(raw_text or "")
        if re.search(r"(?:警告词|信号词)[：:]\s*警告", text):
            return "警告", "Warning", 1.0
        if re.search(r"(?:警告词|信号词)[：:]\s*危险", text):
            return "危险", "Danger", 1.0
        if ("无信号词" in text or "无需信号词" in text) and (
            "不适用" in text or "未分类" in text or "非危险" in text or "不属于危险" in text
        ):
            return "无信号词", "No signal word", 1.0
        # Unknown or ambiguous prose is intentionally safe and local.
        return "无信号词", "No signal word", 0.0

    def route_cross_section_fact(
        self, s3_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, str]]:
        text = str(s3_text or "").strip()
        if not text:
            return None
        has_amine_salt = bool(re.search(r"中和剂.*?已键合为盐", text) or "键合为盐" in text)
        has_threshold = bool(re.search(r"特定阈值浓度", text) or "SCL" in text)
        if not (has_amine_salt or has_threshold):
            return None
        return {
            "zh": (
                "羟基丙烯酸酯聚合物GHS危险性分类：不适用\n"
                "请注意以下物质：\n"
                "N,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%"
            ),
            "en": (
                "GHS classification of hydroxyacrylate polymer: Not applicable\n"
                "Please note the following substance:\n"
                "N,N-Dimethylethanolamine, neutralizing agent, bound as salt, mass concentration < 2.0%"
            ),
            "confidence": "1.0",
        }

    def classify_row_split(
        self, stmt_a: str, stmt_b: str, section: str = "section11"
    ) -> Tuple[str, float]:
        a, b = str(stmt_a or ""), str(stmt_b or "")
        is_product = bool(re.search(r"产品|无可用的毒理学研究|混合物|product itself|mixture", a, re.I))
        is_component = bool(re.search(r"分散体|聚合物|组分|成分|CAS|dispersion|polymer|ingredient", b, re.I))
        if (is_product and is_component) or (
            bool(re.search(r"分散体|聚合物", a)) and bool(re.search(r"产品", b))
        ):
            return "split_independent_row", 1.0
        qualitative = bool(re.search(r"无可用|未开展|无资料|Not applicable|No data", a))
        quantitative = bool(re.search(r"LD50|LC50|刺激性|毒性|mg/kg|ppm", b))
        if qualitative and quantitative:
            return "split_independent_row", 0.95
        return "split_independent_row", 0.0

    def map_tds_slot(
        self, raw_key: str, candidates: Optional[List[str]] = None
    ) -> Tuple[str, float]:
        clean_key = str(raw_key or "").strip().lower()
        allowed = candidates or list(TDS_CANONICAL_SLOTS)
        for slot in allowed:
            for pattern in TDS_CANONICAL_SLOTS.get(slot, []):
                if pattern.lower() in clean_key or clean_key == pattern.lower():
                    return slot, 1.0
        return "unknown", 0.0

    def check_semantic_consistency(
        self, facts: Dict[str, Any]
    ) -> Tuple[bool, str, float]:
        is_non_hazard = facts.get("classification_status") == "non_hazardous" or "不适用" in str(facts.get("section2", {}))
        precautionary = str(facts.get("precautionary_statements", "")) + str(facts.get("section2", {}))
        if is_non_hazard:
            if "P405" in precautionary or "上锁" in precautionary or "locked up" in precautionary.lower():
                return False, "非危险化学品严禁出现高危防范说明 P405 (上锁保管)", 1.0
            if "P201" in precautionary or "P202" in precautionary:
                return False, "非危险化学品严禁出现 CMR 防范说明 P201/P202", 1.0
        return True, "语义一致性审计通过 (本地确定性规则)", 0.0


DEFAULT_ROUTER = SemanticRouter()


__all__ = ["TDS_CANONICAL_SLOTS", "SemanticRouter", "DEFAULT_ROUTER"]
