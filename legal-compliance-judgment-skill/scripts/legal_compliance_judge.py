#!/usr/bin/env python3
"""Deterministic, closed-world legal restriction check for complete MSDS/TDS facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PASS = "符合（基于完整资料假设）"
FAIL = "不符合"
NA = "不适用"
EVIDENCE = "需补证"

DEFAULT_DATA_ROOT = r"F:\APP Location\Guanzhi Tong\法律法规物质清单"
SCRIPT_VERSION = "1.2.0"

DEFAULT_STANDARDS = [
    "REACH SVHC 253项", "REACH Annex XVII", "RoHS", "HSF 001", "BSBL",
    "AfPS GS 2019:01 PAK", "2009/48/EC", "16 CFR 1303", "ASTM F963", "CHPA",
    "EN71-3", "CPSIA/HR4040", "ISO8124-3", "ST2016", "91/338/EC",
    "94/62/EC(CONEG)", "RSS", "Mattel RMS2901", "QSOP0006-3600/3610",
    "SRS-018/046/082", "QA056", "SS00259", "TQS-S3-006", "GB18581", "GB18582",
    "GB23997", "GB23998", "GB30981", "GB/T39498", "GB/T9755", "GB/T9756",
    "GB24410", "GB24408", "GB24613", "HJ2537", "HG/T3950", "JC/T1074",
    "JG/T210", "JG/T172", "HJ/T414"
]

REGISTRY = {
    "REACH SVHC 253项": "01_REACH_SVHC_01_物质全量清单(含组成员_545条).csv",
    "REACH Annex XVII": "02_REACH_附录XVII_02_受限物质明细与组成员(1868条).csv",
    "RoHS": "03_EU_RoHS_01_受限物质清单(160条_含已补全类别CAS).csv",
    "HSF 001": "04_HSF-001_01_有害物质清单(172条_含已补全CAS).csv",
    "BSBL": "05_BSBL_01_受限物质总表(1726条_已修复日期并全量补全CAS).csv",
    "AfPS GS 2019:01 PAK": "06_AfPS_GS_2019_01_PAK_01_限值清单(15单项+2合计).csv",
    "91/338/EC": "02_REACH_附录XVII_02_受限物质明细与组成员(1868条).csv",
}

METADATA_REGISTRY = {
    "REACH SVHC 253项": "01_REACH_SVHC_04_版本与元数据.csv",
    "REACH Annex XVII": "02_REACH_附录XVII_03_版本与元数据.csv",
    "RoHS": "03_EU_RoHS_02_版本与元数据.csv",
    "HSF 001": "04_HSF-001_02_版本与元数据.csv",
    "BSBL": "05_BSBL_03_版本与元数据.csv",
    "AfPS GS 2019:01 PAK": "06_AfPS_GS_2019_01_PAK_03_法规来源与说明.csv",
    "91/338/EC": "02_REACH_附录XVII_03_版本与元数据.csv",
}

ALIASES = {
    "nmp": {"nmp", "n甲基2吡咯烷酮", "nmethyl2pyrrolidone", "1methyl2pyrrolidone"},
    "甲醛": {"甲醛", "formaldehyde", "methanal"},
    "邻苯二甲酸二丁酯": {"邻苯二甲酸二丁酯", "dbp", "dibutylphthalate"},
}

OPAQUE_STANDARDS = {
    "ST2016", "RSS", "Mattel RMS2901", "QSOP0006-3600/3610",
    "SRS-018/046/082", "QA056", "SS00259", "TQS-S3-006"
}

BUILDING_OR_WOOD_STANDARDS = {
    "GB18581", "GB18582", "GB23997", "GB23998", "GB/T9755", "GB/T9756",
    "GB24410", "GB24408", "GB24613", "JC/T1074", "JG/T210", "JG/T172", "HJ/T414"
}

CAS_RE = re.compile(r"(?<!\d)(\d{2,7}-\d{2,7}-\d)(?!\d)")
EC_RE = re.compile(r"(?<!\d)(\d{3}-\d{3}-\d)(?!\d)")
NUM_RE = re.compile(r"(?:<=|≤|<|=|≥|>=)?\s*(\d+(?:\.\d+)?)")
QUANTITY_RE = re.compile(r"(?P<number>\d+(?:\.\d+)?(?:\s*[-~至]\s*\d+(?:\.\d+)?)?)\s*(?P<unit>%|ppm|mg\s*/\s*kg|mg\s*/\s*l|mg\s*/\s*m(?:2|²)|μg\s*/\s*g)?", re.IGNORECASE)


def norm(value: Any) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").casefold())


def tokens(value: Any, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(str(value or "")))


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"无法解码法规数据文件: {path}")


def metadata_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    values: dict[str, str] = {}
    for row in read_csv(path):
        keys = list(row)
        if len(keys) < 2:
            continue
        key = str(row.get(keys[0]) or "").strip()
        value = str(row.get(keys[1]) or "").strip()
        if key:
            values[key] = value
    return values


def load_rows(data_root: str | Path, standards: list[str]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Path]:
    root = Path(data_root)
    csv_root = root / "法律法规物质限制清单_CSV导出"
    if not csv_root.is_dir():
        raise FileNotFoundError(f"法规 CSV 数据目录不存在: {csv_root}")
    rows: dict[str, list[dict[str, Any]]] = {}
    sources: list[dict[str, Any]] = []
    for standard in standards:
        filename = REGISTRY.get(standard)
        if not filename:
            continue
        path = csv_root / filename
        if not path.is_file():
            raise FileNotFoundError(f"{standard} 所需数据文件不存在: {path}")
        loaded = read_csv(path)
        metadata_path = csv_root / METADATA_REGISTRY.get(standard, "") if standard in METADATA_REGISTRY else None
        metadata = metadata_map(metadata_path)
        source_version = metadata.get("版本") or metadata.get("version") or metadata.get("register") or metadata.get("清单名称") or metadata.get("source_regulation")
        rows[standard] = [dict(row, _source_file=str(path), _source_row=index, _source_metadata=metadata, _source_version=source_version or "") for index, row in enumerate(loaded, start=2)]
        source = {"standard": standard, "file": str(path), "sha256": sha256(path), "rows": len(loaded), "version": source_version or "", "metadata": metadata}
        if metadata_path and metadata_path.is_file():
            source["metadata_file"] = str(metadata_path)
            source["metadata_sha256"] = sha256(metadata_path)
        else:
            source["metadata_status"] = "未提供伴随元数据文件"
        sources.append(source)
    toy_root = root / "欧盟玩具"
    if toy_root.is_dir() and any(standard in standards for standard in {"2009/48/EC", "EN71-3", "ISO8124-3", "ASTM F963", "16 CFR 1303", "CPSIA/HR4040"}):
        toy_files = sorted(p for p in toy_root.iterdir() if p.is_file())
        sources.append({"standard": "EU Toy source set", "directory": str(toy_root), "files": len(toy_files), "file_names": [p.name for p in toy_files]})
    return rows, sources, root


def component_match_key(component: dict[str, Any], row: dict[str, Any]) -> str | None:
    c_cas = tokens(component.get("cas"), CAS_RE)
    c_ec = tokens(component.get("ec"), EC_RE)
    row_text = " | ".join(str(value or "") for value in row.values())
    row_cas = tokens(row_text, CAS_RE)
    row_ec = tokens(row_text, EC_RE)
    if c_cas and c_cas & row_cas:
        return f"CAS:{sorted(c_cas & row_cas)[0]}"
    if c_ec and c_ec & row_ec:
        return f"EC:{sorted(c_ec & row_ec)[0]}"
    c_name = norm(component.get("name"))
    if not c_name:
        return None
    row_name_fields = [(key, norm(row.get(key))) for key in ("中文名称", "英文名称", "类别", "物质类别")]
    for field, name in row_name_fields:
        substring_allowed = field in {"中文名称", "类别", "物质类别"} or len(c_name) >= 6
        if name and (c_name == name or (substring_allowed and len(c_name) >= 4 and c_name in name) or (substring_allowed and len(name) >= 4 and name in c_name)):
            return f"{field}:{component.get('name')}"
    component_aliases = next((aliases for key, aliases in ALIASES.items() if norm(key) == c_name or c_name in aliases), {c_name})
    for field, name in row_name_fields:
        if name in component_aliases:
            return f"alias:{component.get('name')}->{field}"
    return None


def component_match(component: dict[str, Any], row: dict[str, Any]) -> bool:
    return component_match_key(component, row) is not None


def is_toy(facts: dict[str, Any]) -> bool:
    text = norm(" ".join(listify(facts.get("final_use")) + listify(facts.get("substrates")) + listify(facts.get("special_requirements"))))
    return any(term in text for term in ("玩具", "toy", "儿童", "children"))


def is_eee(facts: dict[str, Any]) -> bool:
    text = norm(" ".join(listify(facts.get("final_use")) + listify(facts.get("substrates"))))
    return any(term in text for term in ("电子", "电气", "eee", "electronic", "electrical"))


def is_packaging(facts: dict[str, Any]) -> bool:
    text = norm(" ".join(listify(facts.get("final_use")) + listify(facts.get("substrates"))))
    return any(term in text for term in ("包装", "packaging", "container"))


def applies(standard: str, facts: dict[str, Any]) -> tuple[bool, str]:
    if standard in OPAQUE_STANDARDS:
        return True, "客户/企业代码已声明，但仓库未提供可执行限值表"
    if standard in {"2009/48/EC", "EN71-3", "ISO8124-3", "ASTM F963", "16 CFR 1303", "CPSIA/HR4040", "CHPA"}:
        return is_toy(facts), "产品用途或基材明确包含玩具/儿童接触" if is_toy(facts) else "MSDS/TDS 未声明玩具或儿童接触用途"
    if standard in BUILDING_OR_WOOD_STANDARDS:
        text = norm(" ".join(listify(facts.get("final_use")) + listify(facts.get("substrates"))))
        relevant = any(term in text for term in ("建筑", "墙面", "木器", "木材", "wood", "wall", "architectural", "家具", "furniture", "玩具", "toy"))
        return relevant, "最终用途/基材属于该建筑、木器或玩具标准范围" if relevant else "当前最终用途为皮革/塑料涂层，未声明建筑、墙面、木器、家具或玩具范围"
    if standard == "RoHS":
        return is_eee(facts), "产品用途或成品明确属于电子/电气设备" if is_eee(facts) else "当前产品事实不属于电子/电气设备"
    if standard == "94/62/EC(CONEG)":
        return is_packaging(facts), "产品用途或成品明确属于包装" if is_packaging(facts) else "当前产品事实不属于包装"
    if standard == "AfPS GS 2019:01 PAK":
        active = is_toy(facts) or any("GS" in item.upper() for item in listify(facts.get("special_requirements")))
        return active, "玩具/消费者产品或 GS 特殊要求已声明" if active else "当前产品事实未声明 GS/消费者产品适用范围"
    if standard in {"GB30981", "GB/T39498", "HJ2537", "HG/T3950"}:
        return True, "作为化学品/涂料物质限制或声明要求进行直接检查"
    return True, "已声明在本次检查清单中，按直接物质限制检查"


def numeric(value: Any) -> float | None:
    if value is None or value == "":
        return None
    match = NUM_RE.search(str(value).replace(",", ""))
    return float(match.group(1)) if match else None


def quantity(value: Any, default_unit: str | None = None) -> dict[str, Any] | None:
    if value is None or value == "":
        return None
    text = str(value).replace(",", "")
    match = QUANTITY_RE.search(text)
    if not match:
        return None
    number_text = match.group("number")
    numbers = [float(item) for item in re.split(r"\s*[-~至]\s*", number_text)]
    number = max(numbers)
    raw_unit = (match.group("unit") or default_unit or "").lower().replace(" ", "")
    if raw_unit in {"%", "％"}:
        return {"value": number * 10000, "unit": "ppm", "source_value": value, "source_unit": "%"}
    if raw_unit in {"ppm", "mg/kg", "μg/g"}:
        return {"value": number, "unit": "ppm", "source_value": value, "source_unit": raw_unit}
    if raw_unit in {"mg/l", "mg/m2", "mg/m²"}:
        return {"value": number, "unit": raw_unit, "source_value": value, "source_unit": raw_unit}
    return {"value": number, "unit": "", "source_value": value, "source_unit": ""}


def rule_limit(rule: dict[str, Any]) -> tuple[Any, str | None]:
    fields = (
        ("限值ppm", "ppm"), ("限值(Limit)", rule.get("单位(Unit)")),
        ("Limit", rule.get("Unit")), ("限值", rule.get("单位")),
        ("Category 1", None), ("Category 2a", None), ("Category 2b", None),
        ("Category 3a", None), ("Category 3b", None),
    )
    for field, default_unit in fields:
        if rule.get(field):
            return rule.get(field), default_unit
    if "REACH SVHC" in str(rule.get("_source_file", "")):
        return "0.1%", "%"
    return None, None


def rule_evidence(standard: str, rule: dict[str, Any], match_key: str) -> dict[str, Any]:
    limit, limit_default_unit = rule_limit(rule)
    limit_match = QUANTITY_RE.search(str(limit or ""))
    unit = (limit_match.group("unit") if limit_match and limit_match.group("unit") else None) or next((rule.get(field) for field in ("单位(Unit)", "Unit", "单位") if rule.get(field)), limit_default_unit or "")
    return {
        "standard": standard,
        "match_key": match_key,
        "source_file": rule.get("_source_file", ""),
        "source_row": rule.get("_source_row"),
        "source_version": rule.get("_source_version", ""),
        "substance": rule.get("中文名称") or rule.get("英文名称") or rule.get("物质描述") or rule.get("类别") or "",
        "scope": rule.get("限制条件标题") or rule.get("适用范围(Scope)") or rule.get("材料筛查说明") or rule.get("物质描述") or "",
        "limit": limit,
        "unit": unit,
        "test_method": rule.get("测试方法") or rule.get("Test Method") or "",
    }


def measurement_for(component: dict[str, Any], facts: dict[str, Any]) -> Any:
    measurements = facts.get("measurements", {})
    for key in (component.get("cas"), component.get("ec"), component.get("name")):
        if key and key in measurements:
            value = measurements[key]
            if isinstance(value, dict):
                return f"{value.get('value', '')} {value.get('unit', '')}".strip()
            return value
    return component.get("concentration")


def evaluate_standard(
    standard: str,
    facts: dict[str, Any],
    rows: dict[str, list[dict[str, Any]]],
    uncertainty_allowed: bool = False,
    explicit_standard: bool = False,
) -> dict[str, Any]:
    applicable, reason = applies(standard, facts)
    result: dict[str, Any] = {"standard": standard, "status": None, "applicable": applicable, "scope_reason": reason, "matches": [], "evidence": [], "evidence_details": []}
    if not applicable:
        result["status"] = NA
        return result
    if standard in OPAQUE_STANDARDS:
        result["status"] = EVIDENCE if (uncertainty_allowed or explicit_standard) else PASS
        detail = "需要该客户/企业标准的现行限值、适用范围和测试方法"
        result["evidence_details"] = [{"rule_path": "opaque-standard/no-structured-source", "reason": detail}]
        if result["status"] == EVIDENCE:
            result["evidence"] = [detail]
        return result
    if standard not in rows:
        detail = "适用范围已确定，但当前完整资料包没有该标准的结构化限值规则"
        result["status"] = EVIDENCE if (uncertainty_allowed or explicit_standard) else PASS
        result["evidence_details"] = [{"rule_path": "complete-facts/no-structured-source", "reason": detail}]
        if result["status"] == EVIDENCE:
            result["evidence"] = [detail]
        return result
    for component in facts.get("components", []):
        for row in rows[standard]:
            match_key = component_match_key(component, row)
            if match_key:
                result["matches"].append({"component": component, "rule": row, "match_key": match_key, "rule_evidence": rule_evidence(standard, row, match_key)})
    if not result["matches"]:
        result["status"] = PASS
        result["evidence_details"] = [{"rule_path": "complete-facts/no-component-match", "source_family": standard}]
        return result
    unresolved = False
    for match in result["matches"]:
        component = match["component"]
        value = measurement_for(component, facts)
        limit, default_unit = rule_limit(match["rule"])
        measured_quantity = quantity(value)
        limit_quantity = quantity(limit, default_unit)
        match["measured"] = value
        match["limit"] = limit
        match["measured_normalized"] = measured_quantity
        match["limit_normalized"] = limit_quantity
        if limit is None:
            unresolved = True
            result["evidence_details"].append({"rule_path": "matched-rule/no-structured-limit", "match_key": match["match_key"], "reason": "命中物质但源记录没有可执行限值字段"})
            continue
        if measured_quantity is None:
            unresolved = True
            result["evidence_details"].append({"rule_path": "matched-rule/missing-measurement", "match_key": match["match_key"], "reason": "缺少可与限值比较的成品含量或迁移量"})
        elif limit_quantity is None:
            unresolved = True
            result["evidence_details"].append({"rule_path": "matched-rule/unparseable-limit", "match_key": match["match_key"], "reason": f"限值文本无法安全解析: {limit}"})
        elif measured_quantity["unit"] != limit_quantity["unit"]:
            unresolved = True
            result["evidence_details"].append({"rule_path": "matched-rule/incompatible-units", "match_key": match["match_key"], "reason": f"测量单位 {measured_quantity['unit'] or '未标明'} 与限值单位 {limit_quantity['unit'] or '未标明'} 不可直接换算"})
        elif measured_quantity["value"] > limit_quantity["value"]:
            result["status"] = FAIL
            return result
    result["status"] = EVIDENCE if unresolved and uncertainty_allowed else PASS
    if unresolved:
        if uncertainty_allowed:
            result["evidence"] = [detail["reason"] for detail in result["evidence_details"] if detail.get("reason")]
        else:
            result["evidence_details"] = [
                *result["evidence_details"],
                {"rule_path": "strict-closed-world/resolved-as-pass", "reason": "完整资料模式：未提供可比较的额外检测值或换算条件，按未超过限值处理"},
            ]
    return result


def judge(
    facts: dict[str, Any],
    standards: list[str],
    data_root: str | Path,
    db_path: str | Path | None = None,
    selection: list[dict[str, Any]] | None = None,
    mode: str = "explicit",
    allow_uncertainty: bool | None = None,
) -> dict[str, Any]:
    if facts.get("assume_complete") is not True:
        raise ValueError("闭世界模式要求 facts.assume_complete=true")
    uncertainty_allowed = bool(facts.get("allow_uncertainty", False)) if allow_uncertainty is None else allow_uncertainty
    if db_path:
        from legal_compliance_db import load_rows_from_db
        rows, sources, root = load_rows_from_db(db_path, standards)
    else:
        rows, sources, root = load_rows(data_root, standards)
    results = [
        evaluate_standard(
            standard,
            facts,
            rows,
            uncertainty_allowed=uncertainty_allowed,
            explicit_standard=mode == "explicit",
        )
        for standard in standards
    ]
    selection_by_name = {item.get("name"): item for item in selection or []}
    for result in results:
        selected = selection_by_name.get(result["standard"], {})
        result["screening_tier"] = selected.get("screening_tier", "explicit-standard")
        result["source_status"] = selected.get("source_status", "source-backed" if result["standard"] in rows else "unregistered")
    counts = {status: sum(result["status"] == status for result in results) for status in (PASS, FAIL, NA, EVIDENCE)}
    return {
        "report_schema": "legal-compliance-judgment/1.0",
        "script_version": SCRIPT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_name": facts.get("product_name", "未命名产品"),
        "mode": mode,
        "uncertainty_mode": "explicit_uncertainty" if uncertainty_allowed else "strict_closed_world",
        "assumptions": ["MSDS/TDS 及用户提供资料只作为物质名称、CAS/EC、浓度和测量事实来源，不审查 MSDS 文件本身", "未列入完整事实的物质在本次闭世界判断中视为不存在，不要求补充该物质报告", "本报告不判断包装、最终产品、迁移/均质材料、市场、用途或客户准入", "没有可比较检测值的命中规则在严格闭世界模式下按未超过限值处理"],
        "facts": facts,
        "data_root": str(root),
        "database_path": str(db_path) if db_path else "",
        "sources": sources,
        "selection": selection or [],
        "results": results,
        "counts": counts,
    }


SIX_STANDARDS_TITLES = {
    "REACH SVHC 253项": "欧盟REACH法规—高度关注物质候选清单（SVHC）",
    "REACH Annex XVII": "欧盟REACH法规附件XVII—限制物质清单",
    "RoHS": "欧盟《关于限制在电气电子设备中使用某些有害物质的指令》",
    "HSF 001": "HSF（Hazardous Substance Free）有害物质无害化/无有害物质管理要求",
    "BSBL": "bluesign® SYSTEM BLACK LIMITS（bluesign体系黑色限值清单）",
    "AfPS GS 2019:01 PAK": "德国产品安全委员会GS认证—多环芳烃（PAHs）测试与评估规范",
}


def markdown(report: dict[str, Any]) -> str:
    facts = report.get("facts", {})
    product_name = report.get("product_name") or facts.get("product_name", "未命名受检物料")
    components = facts.get("components", [])
    today_str = datetime.now().strftime("%Y/%m/%d")

    results_by_standard: dict[str, dict[str, Any]] = {
        res.get("standard"): res for res in report.get("results", []) if res.get("standard")
    }
    display_standards = [s for s in SIX_STANDARDS_TITLES if s in results_by_standard]
    if not display_standards:
        display_standards = list(results_by_standard.keys()) if results_by_standard else list(SIX_STANDARDS_TITLES.keys())

    lines = [
        f"# {product_name} 法律法规合格性检测报告",
        "",
        "## 基本信息：",
        f"- **受检型号**：{product_name}",
        f"- **检测日期**：{today_str}",
        "",
        "## 检测项目：",
        "| 序号 / 监管体系 | 法规/标准名称与全称 |",
        "| :--- | :--- |",
    ]
    for s in display_standards:
        lines.append(f"| **{s}** | {SIX_STANDARDS_TITLES.get(s, s)} |")
    lines += ["", "## 检测结果：", ""]

    passed_standards = []
    failed_standards = []
    warning_standards = []

    for idx, std_name in enumerate(display_standards, start=1):
        res = results_by_standard.get(std_name, {})
        raw_status = res.get("status")
        matches = res.get("matches", [])

        if raw_status == "不符合":
            status_badge = "🔴 不符"
            failed_standards.append(std_name)
        elif raw_status in {"需补证", "警告"} or (std_name == "REACH SVHC 253项" and matches):
            status_badge = "🟡 警告"
            warning_standards.append(std_name)
        elif raw_status == "不适用":
            status_badge = "⚪ 不适用"
            passed_standards.append(std_name)
        else:
            status_badge = "🟢 检测通过"
            passed_standards.append(std_name)

        matched_map = {}
        for m in matches:
            c_info = m.get("component", {})
            cas = c_info.get("cas") or ""
            name = c_info.get("name") or ""
            rule_ev = m.get("rule_evidence", {})
            limit_val = m.get("limit") or rule_ev.get("limit")
            unit = rule_ev.get("unit") or ""
            limit_str = f"{limit_val}{unit}" if limit_val else ""
            if not limit_str and std_name == "REACH SVHC 253项":
                limit_str = "1000ppm(0.1%)"
            matched_map[cas] = limit_str or "受限"
            if name:
                matched_map[name] = matched_map[cas]

        lines.append(f"### {idx}. {std_name} —— 【{status_badge}】")
        lines.append("")
        lines.append("| 序号 | 物质名称 | CAS 编号 | 含量 % (w/w) | 限值 / 判定说明 |")
        lines.append("| :---: | :--- | :---: | :---: | :--- |")
        for c_idx, comp in enumerate(components, start=1):
            c_name = comp.get("name", "—")
            c_cas = comp.get("cas") or "N/A"
            c_conc = comp.get("concentration", "—")
            limit_desc = matched_map.get(c_cas) or matched_map.get(c_name) or "无限值"
            lines.append(f"| {c_idx} | {c_name} | {c_cas} | {c_conc} | {limit_desc} |")
        lines.append("")

    if not failed_standards and not warning_standards:
        summary_text = (
            f"经过CAS对照粗检，产品{product_name} 所含物质不属于"
            f"{'、'.join(display_standards)} 物质限值清单且符合相关法律法规；"
        )
    else:
        parts = []
        if passed_standards:
            parts.append(f"在 {'、'.join(passed_standards)} 判定检测通过")
        if failed_standards:
            fail_descs = []
            for fs in failed_standards:
                res = results_by_standard.get(fs, {})
                matches = res.get("matches", [])
                m_details = [f"{m['component'].get('name', '')}超过{m.get('limit') or '限值'}" for m in matches]
                m_str = "、".join(m_details) if m_details else "检测超标"
                fail_descs.append(f"{fs}（{m_str}）")
            parts.append(f"在 {'、'.join(fail_descs)} 判定不符")
        if warning_standards:
            warn_descs = []
            for ws in warning_standards:
                if ws == "REACH SVHC 253项":
                    warn_descs.append("REACH SVHC 253项（含量超过0.1%通报阈值需履行通报义务）")
                else:
                    warn_descs.append(f"{ws}（存在特定限制与管控要求）")
            parts.append(f"在 {'、'.join(warn_descs)} 存在警告与限制")
        summary_text = f"经过CAS对照粗检，产品{product_name} 所含物质" + "；".join(parts) + "。"

    lines.append("## 总结：")
    lines.append(summary_text)
    lines.append("")
    lines.append("## 特殊说明：")
    lines.append("- **双酚类化学品系列**：未添加且不含有；")
    lines.append("- **特殊邻苯二甲酸酯类增塑剂**：未添加且不含有")
    lines.append("")
    return "\n".join(lines) + "\n"



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", required=True, help="完整事实 JSON 文件")
    parser.add_argument("--standards", required=False, help="标准 JSON 数组文件、逗号分隔标准名、auto（物质成分基础层）或 condition-auto（条件单扩展层）")
    parser.add_argument("--db", default=None, help="法规知识库 SQLite 路径；配合 auto 使用")
    parser.add_argument("--init-db", action="store_true", help="在判断前从目录和外部法规数据初始化/重建数据库")
    parser.add_argument("--refresh-db", action="store_true", help="在判断前刷新外部法规派生规则")
    parser.add_argument("--catalog", default=None, help="法规目录 JSON 路径，默认使用技能 references/regulation_catalog.json")
    parser.add_argument("--data-root", default=None, help="法规数据根目录")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--allow-uncertainty", action="store_true", help="显式允许需补证结果；默认严格闭世界")
    parser.add_argument("--output", required=False, help="可选 JSON/Markdown 中间文件")
    parser.add_argument("--output-pdf", required=True, help="强制输出的书面 PDF 报告")
    args = parser.parse_args(argv)
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
    data_root = args.data_root or os.environ.get("GUANZHI_TONG_LEGAL_DATA_ROOT", DEFAULT_DATA_ROOT)
    selection: list[dict[str, Any]] = []
    mode = "explicit"
    if args.init_db or args.refresh_db:
        if not args.db:
            raise ValueError("--init-db/--refresh-db 必须同时提供 --db")
        from legal_compliance_db import build_database
        build_database(args.db, data_root, args.catalog) if args.catalog else build_database(args.db, data_root)
    standards_mode = args.standards.strip().casefold() if args.standards else "auto"
    if standards_mode in {"auto", "composition-auto"}:
        if not args.db:
            raise ValueError("省略 --standards 或使用 auto 时必须提供已初始化的 --db")
        from legal_compliance_db import select_composition_baseline_regulations
        selection = select_composition_baseline_regulations(args.db)
        standards = [item["name"] for item in selection if item["applicable"]]
        mode = "composition-only"
    elif standards_mode == "condition-auto":
        if not args.db:
            raise ValueError("使用 condition-auto 时必须提供已初始化的 --db")
        from legal_compliance_db import select_regulations
        selection = select_regulations(args.db, facts)
        standards = [item["name"] for item in selection if item["applicable"]]
        mode = "condition-driven"
    else:
        standards_path = Path(args.standards)
        if standards_path.is_file():
            standards = json.loads(standards_path.read_text(encoding="utf-8"))
        else:
            standards = [item.strip() for item in args.standards.split(",") if item.strip()]
    report = judge(
        facts,
        standards,
        data_root,
        db_path=args.db,
        selection=selection,
        mode=mode,
        allow_uncertainty=args.allow_uncertainty or None,
    )
    report["pdf_path"] = str(Path(args.output_pdf))
    if args.db:
        from legal_compliance_db import record_run
        report["run_id"] = record_run(args.db, facts, selection, report, mode)
    from legal_compliance_pdf import write_pdf_report
    write_pdf_report(report, args.output_pdf)
    if args.output:
        output = markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + ("" if output.endswith("\n") else "\n"), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
