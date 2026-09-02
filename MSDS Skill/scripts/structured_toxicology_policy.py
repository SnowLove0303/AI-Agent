#!/usr/bin/env python3
"""Section 11 structural policy shared by CN and EN outputs.

Punctuation is not the primary parser. Toxicology is modeled as
endpoint -> study block -> field:value. This module provides conservative
field recognition/auditing helpers; product facts remain source-controlled.
"""
from __future__ import annotations
import re

FIELD_ALIASES = {
    'test_type': ('测试种类：','Test type:'),
    'species': ('物种：','Species:'),
    'test_atmosphere': ('试验环境：','Test atmosphere:'),
    'metabolic_activation': ('代谢活化：','Metabolic activation:'),
    'result': ('结果：','Result:'),
    'assessment': ('评估：','Assessment:'),
    'classification': ('分类：','Classification:'),
    'method': ('方法：','Method:'),
}

STUDY_MARKERS = ('Buehler','LLNA','Ames','染色体畸变','chromosome aberration')

def split_structured_lines(text: str) -> list[str]:
    """Preserve existing semantic lines; split concatenated recognized fields only.
    Never split a field from its value and never use punctuation alone as structure.
    """
    if not text:
        return []
    s=text.replace('\r\n','\n').replace('\r','\n')
    labels=[]
    for vals in FIELD_ALIASES.values(): labels.extend(vals)
    # Insert a line break before a recognized field label only when it is not at
    # the start of a line. This fixes flattened source records conservatively.
    for label in sorted(labels, key=len, reverse=True):
        s=re.sub(r'(?<!^)(?<!\n)\s*'+re.escape(label), '\n'+label, s)
    return [x.strip() for x in s.split('\n') if x.strip()]

def audit_field_value_integrity(lines: list[str]) -> list[str]:
    issues=[]
    labels=[x for vals in FIELD_ALIASES.values() for x in vals]
    for i,line in enumerate(lines):
        for label in labels:
            if line.strip()==label:
                issues.append(f'BROKEN_FIELD_VALUE line {i+1}: {label}')
    return issues

def audit_study_separation(lines: list[str]) -> list[str]:
    issues=[]
    for i,line in enumerate(lines,1):
        hits=[m for m in STUDY_MARKERS if m.lower() in line.lower()]
        if len(hits)>1:
            issues.append(f'MERGED_STUDIES line {i}: {hits}')
    return issues
