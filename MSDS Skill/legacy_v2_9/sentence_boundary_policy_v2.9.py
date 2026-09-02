#!/usr/bin/env python3
"""Sentence-boundary line-break policy for MSDS body values.

Break after Chinese full stop/semicolon (。；). English semicolon is also a
boundary. ASCII period is deliberately NOT split automatically because it is
ambiguous in decimals, CAS-like tokens, abbreviations, URLs, units, etc.
Existing line breaks are preserved and empty lines are removed.
"""
from __future__ import annotations
import re

BOUNDARY_RE = re.compile(r'([。；;])(?=\s*\S)')


def normalize_semantic_linebreaks(text: str) -> str:
    if not text:
        return text
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Split only after safe punctuation; keep punctuation on previous line.
    text = BOUNDARY_RE.sub(r'\1\n', text)
    # Trim each logical line and suppress blank lines introduced by source artifacts.
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    return '\n'.join(lines)


def audit_semantic_linebreaks(text: str):
    issues = []
    for i, line in enumerate((text or '').splitlines(), 1):
        # A safe boundary followed by more text on same line is a violation.
        if re.search(r'[。；;]\s*\S', line):
            issues.append((i, line))
    return issues

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('text')
    p.add_argument('--audit', action='store_true')
    a = p.parse_args()
    if a.audit:
        problems = audit_semantic_linebreaks(a.text)
        print(problems)
        raise SystemExit(1 if problems else 0)
    print(normalize_semantic_linebreaks(a.text))
