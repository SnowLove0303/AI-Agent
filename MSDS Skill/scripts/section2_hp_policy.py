#!/usr/bin/env python3
"""Utilities for MSDS Section 2 display policy.

This module is intentionally conservative. It does not locate or overwrite template
labels. It provides two safe primitives for an Agent/editor:
  1) classify missing-data placeholders before DOCX writing;
  2) split Section 2 H/EUH/P coded statements into semantic lines.

The caller must still preserve locked template labels and apply body formatting.
"""
from __future__ import annotations

import re
from typing import List

MISSING_DATA_SENTINELS = {
    "无数据", "无数据资料", "暂无数据", "暂无资料", "无可用数据", "无可用资料",
    "无适用资料", "无相关数据", "无相关资料", "数据不可用", "资料不可用",
    "no data", "no data available", "not available",
}

# Do not add "无", "不适用", "N/A" blindly: they may carry substantive applicability meaning.

def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def is_missing_data_value(text: str) -> bool:
    """Return True only for pure missing-data placeholders.

    Punctuation is ignored. Substantive strings such as "无刺激" or "非危险品"
    return False.
    """
    s = _norm_space(text).lower()
    s = re.sub(r"[。；;，,:：.!！?？]+$", "", s).strip()
    return s in {x.lower() for x in MISSING_DATA_SENTINELS}


# Codes supported:
# H200, H315, H360Df, EUH066, P210, P301+P310, P370+P378, etc.
_CODE_RE = re.compile(r"(?<![A-Za-z0-9])((?:EUH|H)\d{3}[A-Za-z]{0,3}|P\d{3}(?:\+P\d{3})*)\b", re.I)
_GROUP_HEADING_RE = re.compile(r"^(预防措施|事故响应|安全储存|废弃处置|预防|响应|储存|处置)\s*[：:]\s*$")


_PRECAUTIONARY_GROUP_ALIASES = {
    "prevention": ("预防措施", "预防", "Prevention"),
    "response": ("事故响应", "响应", "Response"),
    "storage": ("安全储存", "储存", "Storage"),
    "disposal": ("废弃处置", "处置", "Disposal"),
}
_PRECAUTIONARY_GROUP_CN = {
    "prevention": "预防措施：",
    "response": "事故响应：",
    "storage": "安全储存：",
    "disposal": "废弃处置：",
}
_PRECAUTIONARY_GROUP_EN = {
    "prevention": "Prevention:",
    "response": "Response:",
    "storage": "Storage:",
    "disposal": "Disposal:",
}
_GROUP_HEADING_INLINE_RE = re.compile(
    r"(?:预防措施|事故响应|安全储存|废弃处置|预防|响应|储存|处置|"
    r"Prevention|Response|Storage|Disposal)\s*[：:]",
    re.I,
)
_PRECAUTIONARY_SECTION_HEADING_RE = re.compile(
    r"^\s*(?:2\.\d+\s*)?(?:防范说明|precautionary\s+statements)\s*[：:]?\s*$",
    re.I,
)


def precautionary_group_key(text: str) -> str | None:
    """Return the controlled group key for an explicit heading line."""
    candidate = re.sub(r"[\t\u3000]+", " ", str(text or "")).strip()
    for key, aliases in _PRECAUTIONARY_GROUP_ALIASES.items():
        pattern = r"^(?:" + "|".join(re.escape(alias) for alias in aliases) + r")\s*[：:]\s*$"
        if re.fullmatch(pattern, candidate, flags=re.IGNORECASE):
            return key
    return None


def is_precautionary_group_heading(text: str) -> bool:
    return precautionary_group_key(text) is not None


def is_precautionary_section_heading(text: str) -> bool:
    """Return true for the outer S2 precautionary heading, not a group."""
    return bool(_PRECAUTIONARY_SECTION_HEADING_RE.fullmatch(str(text or "").strip()))


def _heading_boundary(line: str, start: int) -> bool:
    """Accept an inline group heading only at a semantic boundary."""
    prefix = line[:start].rstrip()
    if not prefix:
        return True
    if prefix[-1] in "。.!?！？；;":
        return True
    return bool(_CODE_RE.search(prefix))


def tokenize_precautionary_line(line: str) -> list[dict]:
    """Tokenize headings and complete P-statements in one source line."""
    normalized = re.sub(r"[\t\u3000]+", " ", str(line or "")).strip()
    if not normalized:
        return []

    events: list[tuple[str, re.Match]] = []
    for match in _GROUP_HEADING_INLINE_RE.finditer(normalized):
        if _heading_boundary(normalized, match.start()):
            events.append(("group_heading", match))
    for match in _CODE_RE.finditer(normalized):
        code = match.group(1).upper()
        if code.startswith("P"):
            events.append(("p_statement", match))
    events.sort(key=lambda item: (item[1].start(), 0 if item[0] == "group_heading" else 1))

    if not events:
        if is_precautionary_group_heading(normalized):
            return [{
                "kind": "group_heading",
                "group_key": precautionary_group_key(normalized),
                "source_heading": normalized,
            }]
        return []

    tokens: list[dict] = []
    for index, (kind, match) in enumerate(events):
        if kind == "group_heading":
            heading = match.group(0).strip()
            tokens.append({
                "kind": "group_heading",
                "group_key": precautionary_group_key(heading),
                "source_heading": heading,
            })
            continue
        end = events[index + 1][1].start() if index + 1 < len(events) else len(normalized)
        statement = normalized[match.start():end].strip()
        if statement:
            tokens.append({
                "kind": "p_statement",
                "code": match.group(1).upper(),
                "text": statement,
            })
    return tokens


def split_precautionary_statements(text: str) -> list[dict]:
    """Return an ordered heading/P token stream, joining wrapped P lines."""
    tokens: list[dict] = []
    for raw_line in re.split(r"\r\n|\r|\n", str(text or "")):
        line = re.sub(r"[\t\u3000]+", " ", raw_line).strip()
        if not line:
            continue
        line_tokens = tokenize_precautionary_line(line)
        if line_tokens:
            tokens.extend(line_tokens)
            continue
        if tokens and tokens[-1].get("kind") == "p_statement":
            previous = str(tokens[-1].get("text") or "").rstrip()
            if previous and previous[-1] not in "。.!?！？；;":
                tokens[-1]["text"] = f"{previous} {line}"
                continue
        tokens.append({"kind": "unclassified", "text": line})
    return tokens


def render_precautionary_groups(groups: object, language: str = "zh") -> str:
    """Render reviewed non-empty groups as semantic lines in a value cell."""
    if not isinstance(groups, list):
        return ""
    if language not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    lines: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        statements = group.get("statements") or []
        rendered_statements: list[str] = []
        for statement in statements:
            if isinstance(statement, dict):
                value = str(statement.get("text") or "").strip()
            else:
                value = str(statement or "").strip()
            if value:
                rendered_statements.append(value)
        if not rendered_statements:
            continue
        key = str(group.get("group_key") or "").strip()
        source_heading = str(
            group.get("source_heading") or group.get("heading") or ""
        ).strip()
        if language == "en":
            heading = _PRECAUTIONARY_GROUP_EN.get(key, source_heading)
        else:
            heading = source_heading or _PRECAUTIONARY_GROUP_CN.get(key, "")
        if heading:
            lines.append(heading)
        lines.extend(rendered_statements)
    return "\n".join(lines)


def translate_precautionary_group_headings(text: str) -> str:
    """Translate only complete controlled group-heading lines to English."""
    translated: list[str] = []
    for line in str(text or "").splitlines():
        key = precautionary_group_key(line)
        translated.append(_PRECAUTIONARY_GROUP_EN.get(key, line) if key else line)
    return "\n".join(translated)


def split_coded_statements(text: str, allowed_prefixes=("H", "EUH", "P")) -> List[str]:
    """Split coded H/EUH/P statements into logical lines.

    The split occurs only at a new recognized code boundary. Any text before the
    first code is preserved as a leading logical line (useful for group headings).
    Existing hard line breaks are normalized but remain semantic separators if they
    contain a group heading.
    """
    if not text or not text.strip():
        return []

    # Normalize line endings and remove extraction-only repeated whitespace.
    raw_lines = [re.sub(r"[\t\u3000]+", " ", x).strip() for x in re.split(r"\r\n|\r|\n", text)]
    raw_lines = [x for x in raw_lines if x]
    joined = " ".join(raw_lines)

    matches = list(_CODE_RE.finditer(joined))
    if not matches:
        return raw_lines or [joined]

    allowed = tuple(x.upper() for x in allowed_prefixes)
    usable = []
    for m in matches:
        code = m.group(1).upper()
        prefix = "EUH" if code.startswith("EUH") else code[0]
        if prefix in allowed:
            usable.append(m)
    if not usable:
        return raw_lines or [joined]

    out: List[str] = []
    lead = joined[: usable[0].start()].strip(" ;；")
    if lead:
        # Keep recognized group headings distinct. Other lead text is preserved too.
        out.append(lead)

    for i, m in enumerate(usable):
        end = usable[i + 1].start() if i + 1 < len(usable) else len(joined)
        seg = joined[m.start():end].strip(" ;；")
        if seg:
            out.append(seg)
    return out


def split_h_statements(text: str) -> List[str]:
    return split_coded_statements(text, allowed_prefixes=("H", "EUH"))


def split_p_statements(text: str) -> List[str]:
    return split_coded_statements(text, allowed_prefixes=("P",))


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--kind", choices=["h", "p", "all"], default="all")
    args = ap.parse_args()
    fn = {"h": split_h_statements, "p": split_p_statements, "all": split_coded_statements}[args.kind]
    print(json.dumps({"missing_data": is_missing_data_value(args.text), "lines": fn(args.text)}, ensure_ascii=False, indent=2))
