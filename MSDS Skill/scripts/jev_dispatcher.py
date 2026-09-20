# -*- coding: utf-8 -*-
"""Jev System One (TypeSafe System One) Dispatcher for MSDS Skill.

Provides intelligent routing and decision making using Jev 1.13 when available,
with deterministic, fail-safe rule fallbacks.
Delegates to JevDomainAdjudicator and JevEngine for unified architecture.
"""
from __future__ import annotations

import sys
from typing import Optional, Tuple

try:
    from jev_domain_adjudicator import DEFAULT_ADJUDICATOR, JevDomainAdjudicator
    from jev_engine import DEFAULT_ENGINE, DecisionLedger, GLOBAL_LEDGER, JevEngine
except ImportError:
    try:
        from .jev_domain_adjudicator import DEFAULT_ADJUDICATOR, JevDomainAdjudicator
        from .jev_engine import DEFAULT_ENGINE, DecisionLedger, GLOBAL_LEDGER, JevEngine
    except ImportError:
        DEFAULT_ADJUDICATOR = None
        DEFAULT_ENGINE = None
        GLOBAL_LEDGER = None


def resolve_signal_word(raw_text: str) -> Tuple[str, str]:
    """Resolve signal word from Section 2 raw text. Returns (zh_word, en_word)."""
    if DEFAULT_ADJUDICATOR:
        zh, en, _ = DEFAULT_ADJUDICATOR.adjudicate_ghs_signal_word(raw_text)
        return zh, en
    return ("无信号词", "No signal word")


def route_s3_to_s2(s3_text: str) -> Optional[dict]:
    """Route Section 3 amine salt neutralization / threshold notes to Section 2 label elements.
    Returns dict with 'zh' and 'en' verbatim text blocks from source, or None if not applicable.
    """
    if DEFAULT_ADJUDICATOR:
        return DEFAULT_ADJUDICATOR.adjudicate_cross_section_fact(s3_text)
    return None
