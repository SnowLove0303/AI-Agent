#!/usr/bin/env python3
"""Release policy helpers for the CN/EN x Guanzhi/Guocai matrix."""
from __future__ import annotations

COMPANY_WHITELIST={'supplier_name','supplier_address','telephone','fax','footer_company'}
LANGUAGE_FIELDS={'section_labels','body_values','product_display_name','regulatory_wording'}

def allowed_difference(a_lang,a_company,b_lang,b_company,field):
    if a_lang==b_lang and a_company!=b_company:
        return field in COMPANY_WHITELIST
    if a_company==b_company and a_lang!=b_lang:
        return field in LANGUAGE_FIELDS or field in COMPANY_WHITELIST
    if a_lang!=b_lang and a_company!=b_company:
        return field in LANGUAGE_FIELDS or field in COMPANY_WHITELIST
    return False
