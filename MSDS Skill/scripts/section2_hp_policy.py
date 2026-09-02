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
