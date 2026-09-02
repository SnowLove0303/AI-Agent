#!/usr/bin/env python3
"""Semantic line-break policy for ordinary MSDS prose.

IMPORTANT: Section 11 is excluded from punctuation-first processing. It must be
parsed with structured_toxicology_policy.py first. H/P statements use their own
Section 2 policy. For ordinary prose only, Chinese full stop/semicolon and ASCII
semicolon may form safe semantic boundaries. ASCII period is not auto-split.
"""
from __future__ import annotations
import re
BOUNDARY_RE=re.compile(r'([。；;])(?=\s*\S)')

def normalize_semantic_linebreaks(text: str, section: int|None=None) -> str:
    if not text: return text
    if section == 11:
        return '\n'.join(x.strip() for x in text.replace('\r','\n').split('\n') if x.strip())
    text=text.replace('\r\n','\n').replace('\r','\n')
    text=BOUNDARY_RE.sub(r'\1\n',text)
    return '\n'.join(x.strip() for x in text.split('\n') if x.strip())

def audit_semantic_linebreaks(text: str, section: int|None=None):
    if section == 11: return []
    return [(i,line) for i,line in enumerate((text or '').splitlines(),1) if re.search(r'[。；;]\s*\S',line)]
