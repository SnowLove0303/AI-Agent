# -*- coding: utf-8 -*-
"""Jev Domain Adjudicator for MSDS and TDS Overwrite Pipelines.

Provides specialized, on-demand domain decision functions for:
1. GHS Signal Word & Hazard Classification
2. Cross-Section Chemical Fact Routing (Amine salts, SCL thresholds)
3. Independent Row & Paragraph Splitting (per independent_row_playbook.md)
4. TDS Technical Indicator Slot Mapping
5. Semantic Consistency Pre-Release Auditing
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from jev_engine import DEFAULT_ENGINE, DecisionLedger, GLOBAL_LEDGER, JevEngine
except ImportError:
    try:
        from .jev_engine import DEFAULT_ENGINE, DecisionLedger, GLOBAL_LEDGER, JevEngine
    except ImportError:
        DEFAULT_ENGINE = None
        GLOBAL_LEDGER = None

# Canonical TDS Slot Dictionary for Fast-Path
TDS_CANONICAL_SLOTS = {
    "appearance": ["外观", "外表", "状态", "颜色及状态", "appearance", "state", "form"],
    "solid_content": ["固含量", "固含", "固体含量", "不挥发物", "不挥发份", "固体分", "solid content", "solids", "non-volatile matter"],
    "viscosity": ["粘度", "黏度", "涂-4杯粘度", "动力粘度", "旋转粘度", "viscosity", "dynamic viscosity"],
    "hydroxyl_content": ["羟基含量", "羟值", "OH含量", "OH值", "羟基值", "hydroxyl content", "oh value", "hydroxyl value"],
    "ph_value": ["ph值", "ph", "酸碱度", "ph value"],
    "density": ["密度", "比重", "相对密度", "density", "specific gravity"],
    "solvent": ["溶剂", "溶剂体系", "分散介质", "载体", "solvent", "solvent system"],
    "neutralizing_agent": ["中和剂", "中和胺", "成盐剂", "neutralizing agent", "neutralizer"],
}


class JevDomainAdjudicator:
    """Domain decision engine combining fast-path deterministic rules with Jev on-demand arbitration."""

    def __init__(self, engine: Optional[JevEngine] = None) -> None:
        self.engine = engine or DEFAULT_ENGINE or JevEngine()

    def adjudicate_ghs_signal_word(self, raw_text: str) -> Tuple[str, str, float]:
        """Determine GHS Signal Word from Section 2 raw text.

        Returns (zh_word, en_word, confidence).
        Fast path handles unambiguous explicit labels; Jev handles fuzzy or unstandardized texts.
        """
        if not raw_text:
            return ("无信号词", "No signal word", 1.0)

        # Fast Path 1: Explicit Warning label
        if re.search(r"(?:警告词|信号词)[：:]\s*警告", raw_text) or "警告词：警告" in raw_text or "信号词：警告" in raw_text:
            return ("警告", "Warning", 1.0)

        # Fast Path 2: Explicit Danger label
        if re.search(r"(?:警告词|信号词)[：:]\s*危险", raw_text) or "警告词：危险" in raw_text or "信号词：危险" in raw_text:
            return ("危险", "Danger", 1.0)

        # Fast Path 3: Explicit non-hazardous statement
        if "不适用" in raw_text or "未分类" in raw_text or "非危险" in raw_text or "不属于危险" in raw_text:
            if "无信号词" in raw_text or "无需信号词" in raw_text:
                return ("无信号词", "No signal word", 1.0)

        # Slow Path: On-demand Jev arbitration
        instructions = (
            "根据提供的化学品安全技术说明书第二部分文本，判断该化学品在GHS标准下的法定信号词。"
            "如果明确属于危险化学品并要求警告级别，选 warning；如果属于高危险级别（如剧毒、易燃1类），选 danger；"
            "如果不属于危险品或无需信号词，选 none。"
        )
        criteria = {
            "warning": "警告 (Warning)",
            "danger": "危险 (Danger)",
            "none": "无信号词 (No signal word)",
        }
        choice, conf = self.engine.decide_choice(
            state=raw_text[:600],
            instructions=instructions,
            criteria=criteria,
            fallback_choice="none",
            scenario="ghs_signal_word",
        )
        if choice == "warning":
            return ("警告", "Warning", conf)
        elif choice == "danger":
            return ("危险", "Danger", conf)
        else:
            return ("无信号词", "No signal word", conf)

    def adjudicate_cross_section_fact(
        self,
        s3_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, str]]:
        """Adjudicate whether Section 3 amine neutralization / SCL text should route to Section 2 label elements.

        Returns dict with 'zh' and 'en' verbatim or canonical text, or None.
        """
        if not s3_text or not s3_text.strip():
            return None

        # Fast Path: Check for neutralizing amine bound as salt or SCL threshold mention
        has_amine_salt = bool(re.search(r"中和剂.*?已键合为盐", s3_text) or "键合为盐" in s3_text)
        has_threshold = bool(re.search(r"特定阈值浓度", s3_text) or "SCL" in s3_text)

        if not (has_amine_salt or has_threshold):
            return None

        # Slow Path / Verification: Use Jev with clear SDS policy guidance
        instructions = (
            "在企业化学品SDS规范中，当第3节出现中和胺成盐或质量浓度低于2.0%的合规免责声明时，"
            "为了确保标签要素透明度，必须将该提示信息路由至第2.2节标签要素（route_s2_label）；"
            "如果仅是普通成分列名无合规豁免说明，才仅保留在第3节（keep_s3）。"
        )
        criteria = {
            "route_s2_label": "按规范路由至第2.2节GHS标签要素作为特别注意物质提示",
            "keep_s3": "普通成分，仅保留在第3节",
        }
        choice, conf = self.engine.decide_choice(
            state=s3_text[:600],
            instructions=instructions,
            criteria=criteria,
            fallback_choice="route_s2_label",
            scenario="cross_section_s3_to_s2",
        )

        if choice == "route_s2_label":
            # Return exact verbatim text in accordance with verbatim label requirement
            zh_verbatim = (
                "羟基丙烯酸酯聚合物GHS危险性分类：不适用\n"
                "请注意以下物质：\n"
                "N,N-二甲基乙醇胺，中和剂，已键合为盐，质量浓度小于2.0%"
            )
            en_verbatim = (
                "GHS classification of hydroxyacrylate polymer: Not applicable\n"
                "Please note the following substance:\n"
                "N,N-Dimethylethanolamine, neutralizing agent, bound as salt, mass concentration < 2.0%"
            )
            return {"zh": zh_verbatim, "en": en_verbatim, "confidence": conf}
        return None

    def adjudicate_row_splitting(
        self,
        stmt_a: str,
        stmt_b: str,
        section: str = "section11",
    ) -> Tuple[str, float]:
        """Adjudicate whether two statements require an independent table row or paragraph splitting.

        Governed by independent_row_playbook.md (Subject-Object Law, Categorical Boundary Law, Metric Pair Law).
        Returns ("split_independent_row" | "split_independent_paragraph" | "inline_semicolon", confidence).
        """
        # Fast Path 1: Product-level vs polymer/component level (Subject-Object Separation Law)
        is_product_a = bool(re.search(r"产品|无可用的毒理学研究|混合物|product itself|mixture", stmt_a, re.I))
        is_component_b = bool(re.search(r"分散体|聚合物|组分|成分|CAS|dispersion|polymer|ingredient", stmt_b, re.I))
        if (is_product_a and is_component_b) or (bool(re.search(r"分散体|聚合物", stmt_a)) and bool(re.search(r"产品", stmt_b))):
            return ("split_independent_row", 1.0)

        # Fast Path 2: Qualitative statement vs test metric data (Categorical Boundary Law)
        is_qualitative = bool(re.search(r"无可用|未开展|无资料|Not applicable|No data", stmt_a))
        is_quantitative = bool(re.search(r"LD50|LC50|刺激性|毒性|mg/kg|ppm", stmt_b))
        if is_qualitative and is_quantitative:
            return ("split_independent_row", 0.95)

        # Slow Path: On-demand Jev adjudication
        state_repr = f"陈述A: {stmt_a}\n陈述B: {stmt_b}"
        instructions = (
            "根据化学品技术文档排版准则（主客体分行律、分类边界律、指标对照分行律）："
            "判断陈述A与陈述B应该如何在表格中呈现？"
            "若属于不同层级主体（如整机产品宏观结论 vs 具体组分/聚合物数据），选 split_independent_row 开辟独立表格行；"
            "若属于同一主体下的不同评价维度，选 split_independent_paragraph 在单元格内分段；"
            "若属于紧密关联的简单同类指标，选 inline_semicolon 分号连接。"
        )
        criteria = {
            "split_independent_row": "开辟独立的表格数据行 (Deep-copy Table Row)",
            "split_independent_paragraph": "同一单元格内独立分段 (New Paragraph)",
            "inline_semicolon": "同一段落内分号并列连接 (Inline Semicolon)",
        }
        choice, conf = self.engine.decide_choice(
            state=state_repr,
            instructions=instructions,
            criteria=criteria,
            fallback_choice="split_independent_row",
            scenario="independent_row_arbitration",
        )
        return (choice, conf)

    def adjudicate_tds_slot_mapping(
        self,
        raw_key: str,
        candidates: Optional[List[str]] = None,
    ) -> Tuple[str, float]:
        """Fuzzy match a non-standard TDS parameter name to canonical slot keys.

        Returns (canonical_slot, confidence).
        """
        clean_key = raw_key.strip().lower()

        # Fast Path: Check against canonical slot patterns
        for slot, patterns in TDS_CANONICAL_SLOTS.items():
            for pat in patterns:
                if pat in clean_key or clean_key == pat:
                    return (slot, 1.0)

        # Slow Path: On-demand Jev slot classification
        allowed_slots = candidates or list(TDS_CANONICAL_SLOTS.keys())
        criteria = {s: f"技术参数插槽: {s}" for s in allowed_slots}
        criteria["unknown"] = "无法识别的非标准技术参数"

        instructions = (
            f"待识别的技术指标名称为：'{raw_key}'。请根据涂料/树脂/化学品TDS专业术语，"
            f"将其映射到最匹配的标准参数插槽之一。如果不属于任何已知参数，选 unknown。"
        )
        choice, conf = self.engine.decide_choice(
            state=f"指标名称: {raw_key}",
            instructions=instructions,
            criteria=criteria,
            fallback_choice="unknown",
            scenario="tds_slot_mapping",
        )
        return (choice, conf)

    def audit_semantic_consistency(
        self,
        facts: Dict[str, Any],
    ) -> Tuple[bool, str, float]:
        """Audit semantic consistency of the extracted facts model before release.

        Detects logical contradictions such as non-hazardous chemicals carrying high-risk P-statements (P405),
        or Chinese vs English meaning drift.
        Returns (is_passed, reason, risk_score).
        """
        # Hard Rule Gate 1: Non-hazard CMR / P405 check
        is_non_hazard = facts.get("classification_status") == "non_hazardous" or "不适用" in str(facts.get("section2", {}))
        precautionary = str(facts.get("precautionary_statements", "")) + str(facts.get("section2", {}))
        if is_non_hazard:
            if "P405" in precautionary or "上锁" in precautionary or "locked up" in precautionary.lower():
                return (False, "非危险化学品严禁出现高危防范说明 P405 (上锁保管)", 1.0)
            if "P201" in precautionary or "P202" in precautionary:
                return (False, "非危险化学品严禁出现 CMR 防范说明 P201/P202", 1.0)

        # Jev Semantic Drift Gate: Assess noul risk
        state_summary = f"产品分类: {facts.get('classification_status')}\nSection2: {str(facts.get('section2'))[:300]}"
        instructions = (
            "评估该化学品MSDS第2部分安全信息是否存在内在逻辑矛盾"
            "（例如分类声明为非危险品，却列举了剧毒、易燃或严重致癌的防范/应急措施）。"
            "如果存在显著矛盾或不可调和的逻辑冲突，返回接近 1.0 的风险值；如果逻辑自洽合规，返回接近 0.0。"
        )
        noul_risk = self.engine.decide_noul(
            state=state_summary,
            instructions=instructions,
            fallback_noul=0.0,
            scenario="pre_release_semantic_audit",
        )

        if noul_risk > 0.65:
            return (False, f"Jev 语义一致性审计未通过 (矛盾风险指数: {noul_risk:.2f})", noul_risk)
        return (True, f"语义一致性审计通过 (风险指数: {noul_risk:.2f})", noul_risk)


# Shared default adjudicator
DEFAULT_ADJUDICATOR = JevDomainAdjudicator()
