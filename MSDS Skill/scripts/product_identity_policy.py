#!/usr/bin/env python3
"""Guanzhi MSDS product identity policy helper.

Policy:
- header/title product code: model
- Section 1 `产品名称` value: blank
- Section 1 `中文名称` value: Chinese name + single ASCII space + model
- footer/MSDS identifier: model-based

This module deliberately exposes pure functions so Agents/tests can validate mapping
before editing DOCX XML.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class IdentityExpected:
    product_name_value: str
    chinese_name_value: str
    model: str


def expected_identity(chinese_name: str, model: str) -> IdentityExpected:
    chinese_name = " ".join((chinese_name or "").split())
    model = " ".join((model or "").split())
    if not chinese_name:
        raise ValueError("Chinese product name is required")
    if not model:
        raise ValueError("Product model/code is required")
    # Avoid accidental duplicate model if the source Chinese name already
    # carries it either with a separator or compactly (for example
    # ``接着树脂PU-1001``).  Compare the suffix after removing whitespace and
    # ignoring case; retain the source spelling/spacing in the display value.
    chinese_compact = re.sub(r"\s+", "", chinese_name).casefold()
    model_compact = re.sub(r"\s+", "", model).casefold()
    if chinese_compact.endswith(model_compact):
        combined = chinese_name
    else:
        combined = f"{chinese_name} {model}"
    return IdentityExpected(product_name_value="", chinese_name_value=combined, model=model)


def audit_identity(*, chinese_name: str, model: str, product_name_value: str,
                   chinese_name_value: str, header_text: str = "", footer_text: str = "") -> list[str]:
    exp = expected_identity(chinese_name, model)
    errors: list[str] = []
    if (product_name_value or "").strip():
        errors.append("Section 1 产品名称 value must be blank")
    if " ".join((chinese_name_value or "").split()) != exp.chinese_name_value:
        errors.append(f"中文名称 must equal: {exp.chinese_name_value}")
    if header_text and model not in header_text:
        errors.append("Header/title does not contain the product model")
    if footer_text and model not in footer_text:
        errors.append("Footer/MSDS identifier does not contain the product model")
    return errors
