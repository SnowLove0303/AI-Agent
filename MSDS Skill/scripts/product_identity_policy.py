#!/usr/bin/env python3
"""Guanzhi MSDS product identity policy helper.

Policy:
- header/title product code: model
- Chinese Section 1 `产品名称` value: blank
- Chinese Section 1 `中文名称` value: Chinese name + single ASCII space + model
- English Section 1 `Product name` value: reviewed professional English name +
  single ASCII space + model
- footer/MSDS identifier: model-based

This module deliberately exposes pure functions so Agents/tests can validate mapping
before editing DOCX XML.  It never translates, invents, or derives a professional
English name from a model code; the English name must already be present in the
reviewed English facts layer.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class IdentityExpected:
    product_name_value: str
    chinese_name_value: str
    model: str
    english_product_name_value: str = ""


def _normalize_display_text(value: str) -> str:
    """Collapse extraction whitespace without changing words or punctuation."""
    return " ".join(str(value or "").split())


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def expected_english_product_name(english_name: str, model: str) -> str:
    """Return the reviewed English product name in its canonical display form.

    ``english_name`` is intentionally required.  The helper may normalize
    whitespace and append the already-reviewed model code, but it may not use
    the model as a substitute for a missing professional name.
    """
    english_name = _normalize_display_text(english_name)
    model = _normalize_display_text(model)
    if not english_name:
        raise ValueError("reviewed English product name is required")
    if not model:
        raise ValueError("Product model/code is required")
    if _compact(english_name) == _compact(model):
        raise ValueError("English product name must not be only the product model/code")
    if re.search(r"[\u4e00-\u9fff]", english_name):
        raise ValueError("English product name must not contain Chinese characters")
    if _compact(english_name).endswith(_compact(model)):
        return english_name
    return f"{english_name} {model}"


def english_product_name_errors(english_name: str, model: str) -> list[str]:
    """Validate the reviewed EN S1.1 fact before any template is cloned."""
    try:
        expected_english_product_name(english_name, model)
    except ValueError as exc:
        return [f"English Section 1.1 product name: {exc}"]
    return []


def expected_identity(chinese_name: str, model: str) -> IdentityExpected:
    chinese_name = _normalize_display_text(chinese_name)
    model = _normalize_display_text(model)
    if not chinese_name:
        raise ValueError("Chinese product name is required")
    if not model:
        raise ValueError("Product model/code is required")
    # Avoid accidental duplicate model if the source Chinese name already
    # carries it either with a separator or compactly (for example
    # ``接着树脂PU-1001``).  Compare the suffix after removing whitespace and
    # ignoring case; retain the source spelling/spacing in the display value.
    chinese_compact = _compact(chinese_name)
    model_compact = _compact(model)
    if chinese_compact.endswith(model_compact):
        combined = chinese_name
    else:
        combined = f"{chinese_name} {model}"
    return IdentityExpected(product_name_value="", chinese_name_value=combined, model=model)


def audit_english_identity(*, product_name_value: str, model: str) -> list[str]:
    """Audit the rendered English S1.1 value against reviewed facts."""
    errors = english_product_name_errors(product_name_value, model)
    if errors:
        return errors
    expected = expected_english_product_name(product_name_value, model)
    actual = _normalize_display_text(product_name_value)
    if actual != expected:
        errors.append(f"English Section 1.1 product name must equal: {expected}")
    return errors


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
