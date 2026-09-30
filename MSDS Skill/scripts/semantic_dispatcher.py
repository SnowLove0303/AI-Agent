# -*- coding: utf-8 -*-
"""Deterministic Section 2 semantic dispatch helpers."""
from __future__ import annotations

from typing import Optional, Tuple

try:
    from semantic_rules import DEFAULT_ROUTER
except ImportError:
    from .semantic_rules import DEFAULT_ROUTER


def resolve_signal_word(raw_text: str) -> Tuple[str, str]:
    """Resolve an explicit signal word locally; unknown prose is safe fallback."""
    zh, en, _ = DEFAULT_ROUTER.resolve_signal_word(raw_text)
    return zh, en


def route_s3_to_s2(s3_text: str) -> Optional[dict]:
    """Route only verified neutralized-amine/SCL evidence to Section 2."""
    return DEFAULT_ROUTER.route_cross_section_fact(s3_text)


__all__ = ["resolve_signal_word", "route_s3_to_s2"]
