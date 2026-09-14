"""Small, bounded diagnostics for release-blocking MSDS audits."""
from __future__ import annotations

import re


def _compact(value, limit: int = 240) -> str:
    if value is None:
        return "<absent>"
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text or "<empty>"


def element_signature(element, limit: int = 240) -> str:
    """Return a stable, bounded tag/attribute/child signature for an XML node."""
    if element is None:
        return "<absent>"
    tag = str(getattr(element, "tag", "")).rsplit("}", 1)[-1]
    attrs = getattr(element, "attrib", {}) or {}
    attr_text = ",".join(
        f"{str(key).rsplit('}', 1)[-1]}={value!r}"
        for key, value in sorted(attrs.items(), key=lambda item: str(item[0]))
    )
    children = []
    for child in list(element)[:12]:
        child_tag = str(getattr(child, "tag", "")).rsplit("}", 1)[-1]
        children.append(child_tag)
    child_text = ",".join(children) or "-"
    return _compact(f"<{tag} attrs=[{attr_text}] children=[{child_text}]", limit)


def diagnostic_diff(expected, actual) -> str:
    """Describe the comparison without dumping an entire DOCX XML tree."""
    if expected == actual:
        return "none"
    expected_text = _compact(expected, 100)
    actual_text = _compact(actual, 100)
    return f"expected!=actual ({expected_text} -> {actual_text})"


def format_diagnostic(code: str, *, location: str, expected=None, actual=None,
                      diff: str | None = None, hint: str = "") -> str:
    """Build one Harness-friendly blocker with expected/actual/diff/hint fields."""
    diff = diff if diff is not None else diagnostic_diff(expected, actual)
    return (
        f"[{code}] location={_compact(location, 180)} "
        f"expected={_compact(expected)} actual={_compact(actual)} "
        f"diff={_compact(diff, 220)} hint={_compact(hint, 220)}"
    )


__all__ = ["diagnostic_diff", "element_signature", "format_diagnostic"]
