#!/usr/bin/env python3
"""Canonical four-format output matrix for the unified MSDS skill."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Variant:
    language: str
    company: str
    suffix: str

VARIANTS = (
    Variant('CN', 'guanzhi', 'MSDS_CN_冠志.docx'),
    Variant('CN', 'guocai', 'MSDS_CN_国彩.docx'),
    Variant('EN', 'guanzhi', 'MSDS_EN_冠志.docx'),
    Variant('EN', 'guocai', 'MSDS_EN_国彩.docx'),
)

def output_names(model: str, language: str = 'ALL') -> list[str]:
    model = (model or '').strip()
    if not model:
        raise ValueError('model is required')
    lang = language.upper()
    if lang not in {'ALL','CN','EN'}:
        raise ValueError('language must be ALL, CN, or EN')
    return [f'{model}_{v.suffix}' for v in VARIANTS if lang == 'ALL' or v.language == lang]

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('model')
    p.add_argument('--language', default='ALL', choices=['ALL','CN','EN'])
    a=p.parse_args()
    print('\n'.join(output_names(a.model,a.language)))
