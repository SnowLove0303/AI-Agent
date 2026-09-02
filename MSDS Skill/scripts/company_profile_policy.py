#!/usr/bin/env python3
"""Company-profile constants and lightweight text-level audits for dual MSDS outputs."""
from dataclasses import dataclass
from typing import Dict, Iterable, List

@dataclass(frozen=True)
class CompanyProfile:
    key: str
    supplier_name: str
    supplier_address: str | None
    phone: str | None
    fax: str | None
    footer_company_name: str

PROFILES: Dict[str, CompanyProfile] = {
    "冠志": CompanyProfile(
        key="冠志",
        supplier_name="广州冠志新材料科技有限公司",
        supplier_address=None,  # resolve from authoritative source/template, not memory
        phone=None,
        fax=None,
        footer_company_name="广州冠志新材料科技有限公司",
    ),
    "国彩": CompanyProfile(
        key="国彩",
        supplier_name="英德市国彩精细化工有限公司",
        supplier_address="广东省英德市白沙镇太平村更古坑凯迪工业园区",
        phone="86-763-2811205",
        fax="86-763-2811024",
        footer_company_name="英德市国彩精细化工有限公司",
    ),
}

GUOCAI_REQUIRED = [
    "英德市国彩精细化工有限公司",
    "广东省英德市白沙镇太平村更古坑凯迪工业园区",
    "86-763-2811205",
    "86-763-2811024",
]

GUOCAI_FORBIDDEN_IDENTITY = ["广州冠志新材料科技有限公司"]


def audit_guocai_text(full_text: str) -> List[str]:
    errors=[]
    for value in GUOCAI_REQUIRED:
        if value not in full_text:
            errors.append(f"missing Guocai profile value: {value}")
    for value in GUOCAI_FORBIDDEN_IDENTITY:
        if value in full_text:
            errors.append(f"Guanzhi company identity leaked into Guocai output: {value}")
    return errors


def expected_footer(company_key: str, product_code: str) -> str:
    p=PROFILES[company_key]
    return f"{p.footer_company_name} {product_code}-MSDS"


def output_filename(product_code: str, company_key: str) -> str:
    return f"{product_code}_MSDS_CN_{company_key}.docx"


def normalize_company_overlay(text: str) -> str:
    """Normalize only approved company-profile literals for cross-variant text parity checks."""
    replacements = {
        "广州冠志新材料科技有限公司": "<COMPANY_NAME>",
        "英德市国彩精细化工有限公司": "<COMPANY_NAME>",
        "广东省英德市白沙镇太平村更古坑凯迪工业园区": "<SUPPLIER_ADDRESS>",
        "86-763-2811205": "<PHONE>",
        "86-763-2811024": "<FAX>",
    }
    for a,b in replacements.items():
        text=text.replace(a,b)
    return text
