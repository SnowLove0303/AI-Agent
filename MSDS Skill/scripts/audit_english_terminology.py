#!/usr/bin/env python3
"""Release-blocking customer-visible English terminology audit.

Only visible Word parts are scanned. Styles/settings XML is intentionally
excluded so internal style names cannot become false customer-facing issues.
Formatting and locked-structure checks remain in the template mutation audit.
"""
import html
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

BANNED = [
    r'\bdanger chemicals?\b', r'\bpoison information\b', r'\becology toxicity\b',
    r'\bhand protect\b', r'\beye protect\b', r'\bno danger reaction\b',
    r'not satisfy classification standard', r'no data materials?'
]
MISSING = ['无数据', '无数据资料', '暂无数据', '无可用数据', '无适用资料']
CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
FULLWIDTH_COLON_RE = re.compile(r"：")
INVALID_UNIT_RE = re.compile(r"(?:\d\s*[℃％]|[（］）])")
NONCANONICAL_HEADINGS = (
    "firefighting precautions", "measures for accidental leakage",
    "operation and storage", "toxicity information", "transportation information",
)
KNOWN_COMPANY_DRIFT = (
    re.compile(r"Guangzhou Guanzhi New Material Technology", re.I),
    # The canonical legal name is singular "Fine Chemical". Flag only the
    # known pluralized drift so valid Guocai output is not rejected.
    re.compile(r"Yingde Guocai Fine Chemicals\b", re.I),
)


def _visible_docx_parts(path: Path) -> dict[str, str]:
    """Return visible text by Word part, excluding styles/settings."""
    parts: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not re.match(r"^word/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml$", name):
                continue
            raw = archive.read(name)
            try:
                root = ElementTree.fromstring(raw)
            except ElementTree.ParseError:
                parts[name] = raw.decode("utf-8", "ignore")
                continue
            text = []
            for node in root.iter():
                local = node.tag.rsplit("}", 1)[-1]
                if local in {"t", "delText", "instrText"} and node.text:
                    text.append(node.text)
            parts[name] = html.unescape(" ".join(text))
    return parts


def text_from_docx(p):
    return " ".join(_visible_docx_parts(Path(p)).values())


def _scan_part(part: str, text: str, baseline: str = "") -> list[str]:
    issues = []
    low = text.lower()
    base_low = baseline.lower()
    for pat in BANNED:
        if len(re.findall(pat, low)) > len(re.findall(pat, base_low)):
            issues.append(f"BANNED_TRANSLATION: {pat}")
    for marker in MISSING:
        if text.count(marker) > baseline.count(marker):
            issues.append(f"VISIBLE_MISSING_MARKER: {marker}")
    chinese_count = len(CHINESE_RE.findall(text))
    baseline_chinese_count = len(CHINESE_RE.findall(baseline))
    if chinese_count > baseline_chinese_count:
        chinese = CHINESE_RE.search(text)
        start = max(0, chinese.start() - 18)
        issues.append("CHINESE_REMAINDER: " + text[start:chinese.start() + 42].strip())
    if len(FULLWIDTH_COLON_RE.findall(text)) > len(FULLWIDTH_COLON_RE.findall(baseline)):
        issues.append("FULLWIDTH_COLON: customer-visible English text contains '：'")
    if INVALID_UNIT_RE.search(text):
        if len(INVALID_UNIT_RE.findall(text)) > len(INVALID_UNIT_RE.findall(baseline)):
            issues.append("INVALID_UNIT_TYPOGRAPHY: use ASCII parentheses, %, °C and approved units")
    for heading in NONCANONICAL_HEADINGS:
        if low.count(heading) > base_low.count(heading):
            issues.append(f"NONCANONICAL_HEADING: {heading}")
    for pattern in KNOWN_COMPANY_DRIFT:
        if len(pattern.findall(text)) > len(pattern.findall(baseline)):
            issues.append(f"COMPANY_SUFFIX_DRIFT: {pattern.pattern}")
    return [f"{part}: {issue}" for issue in issues]


def run(p, baseline=None):
    """Audit one built file; return release-blocking issue strings."""
    p = Path(p)
    parts = _visible_docx_parts(p) if p.suffix.lower() == '.docx' else {
        "text": p.read_text(encoding='utf-8')
    }
    baseline_parts = _visible_docx_parts(Path(baseline)) if baseline else {}
    issues = []
    for part, text in parts.items():
        issues.extend(_scan_part(part, text, baseline_parts.get(part, "")))
    return issues


def main():
    p = Path(sys.argv[1])
    issues = run(p)
    if issues:
        print('\n'.join(issues)); return 2
    print('PASS: English terminology audit')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
