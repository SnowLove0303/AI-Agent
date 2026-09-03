"""Source-grounded Section 11 endpoint aliases.

The mapping changes only the destination standard field.  It never fabricates
the source result, method, species, classification or numeric value.
"""

from __future__ import annotations

import re


ALIASES = {
    "主要粘膜刺激性": "11.3 主要眼睛刺激性",
    "主要眼睛刺激性": "11.3 主要眼睛刺激性",
    "眼睛刺激性": "11.3 主要眼睛刺激性",
    "眼部刺激性": "11.3 主要眼睛刺激性",
}


def normalize_endpoint(text: str) -> str:
    value = re.sub(r"\s+", "", str(text or "")).rstrip("：:")
    return value


def map_section11_endpoint(source_endpoint: str) -> str | None:
    """Return an existing standard endpoint, or ``None`` for no match."""
    return ALIASES.get(normalize_endpoint(source_endpoint))


def move_source_value_to_standard_endpoint(source_endpoint: str, source_value: str) -> tuple[str, str] | None:
    """Return ``(standard endpoint, unchanged source value)`` for a match."""
    target = map_section11_endpoint(source_endpoint)
    if target is None:
        return None
    return target, str(source_value)


__all__ = ["ALIASES", "map_section11_endpoint", "move_source_value_to_standard_endpoint"]
