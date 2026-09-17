#!/usr/bin/env python3
"""Deterministic, closed-world legal restriction check for complete MSDS/TDS facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
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
SCRIPT_VERSION = "1.0.0"

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
        loaded = None
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                with path.open("r", encoding=encoding, newline="") as handle:
                    loaded = list(csv.DictReader(handle))
                break
            except UnicodeDecodeError:
                continue
        if loaded is None:
            raise UnicodeError(f"无法解码法规数据文件: {path}")
        rows[standard] = [dict(row, _source_file=str(path), _source_row=index) for index, row in enumerate(loaded, start=2)]
        sources.append({"standard": standard, "file": str(path), "sha256": sha256(path), "rows": len(loaded)})
    toy_root = root / "欧盟玩具"
    if toy_root.is_dir() and any(standard in standards for standard in {"2009/48/EC", "EN71-3", "ISO8124-3", "ASTM F963", "16 CFR 1303", "CPSIA/HR4040"}):
        toy_files = sorted(p for p in toy_root.iterdir() if p.is_file())
        sources.append({"standard": "EU Toy source set", "directory": str(toy_root), "files": len(toy_files), "file_names": [p.name for p in toy_files]})
    return rows, sources, root


def component_match(component: dict[str, Any], row: dict[str, Any]) -> bool:
    c_cas = tokens(component.get("cas"), CAS_RE)
    c_ec = tokens(component.get("ec"), EC_RE)
    row_text = " | ".join(str(value or "") for value in row.values())
    if c_cas and c_cas & tokens(row_text, CAS_RE):
        return True
    if c_ec and c_ec & tokens(row_text, EC_RE):
        return True
    c_name = norm(component.get("name"))
    if not c_name:
        return False
    row_names = [norm(row.get(key)) for key in ("中文名称", "英文名称", "物质描述", "限制条件标题", "类别", "物质类别")]
    if any(c_name == name or (len(c_name) >= 4 and c_name in name) or (len(name) >= 4 and name in c_name) for name in row_names if name):
        return True
    component_aliases = next((aliases for key, aliases in ALIASES.items() if norm(key) == c_name or c_name in aliases), {c_name})
    return bool(component_aliases & set(row_names))


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


def evaluate_standard(standard: str, facts: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    applicable, reason = applies(standard, facts)
    result: dict[str, Any] = {"standard": standard, "status": None, "applicable": applicable, "scope_reason": reason, "matches": [], "evidence": []}
    if not applicable:
        result["status"] = NA
        return result
    if standard in OPAQUE_STANDARDS:
        result["status"] = EVIDENCE
        result["evidence"] = ["需要该客户/企业标准的现行限值、适用范围和测试方法"]
        return result
    if standard not in rows:
        result["status"] = EVIDENCE
        result["evidence"] = ["适用范围已确定，但当前数据包没有该标准的结构化限值规则"]
        return result
    for component in facts.get("components", []):
        for row in rows[standard]:
            if component_match(component, row):
                result["matches"].append({"component": component, "rule": row})
    if not result["matches"]:
        result["status"] = PASS
        return result
    measurements = facts.get("measurements", {})
    unresolved = False
    for match in result["matches"]:
        component = match["component"]
        key = str(component.get("cas") or component.get("name") or "")
        value = measurements.get(key, component.get("concentration"))
        limit = next((match["rule"].get(field) for field in ("限值ppm", "限值(Limit)", "Limit", "限值", "Category 1", "Category 2a", "Category 2b", "Category 3a", "Category 3b") if match["rule"].get(field)), None)
        measured = numeric(value)
        threshold = numeric(limit)
        match["measured"] = value
        match["limit"] = limit
        if measured is None:
            unresolved = True
        elif threshold is not None and measured > threshold:
            result["status"] = FAIL
            return result
    result["status"] = EVIDENCE if unresolved else PASS
    if unresolved:
        result["evidence"] = ["命中受限物质，但输入未提供可与限值比较的成品含量/迁移量"]
    return result


def judge(facts: dict[str, Any], standards: list[str], data_root: str | Path) -> dict[str, Any]:
    if facts.get("assume_complete") is not True:
        raise ValueError("闭世界模式要求 facts.assume_complete=true")
    rows, sources, root = load_rows(data_root, standards)
    results = [evaluate_standard(standard, facts, rows) for standard in standards]
    counts = {status: sum(result["status"] == status for result in results) for status in (PASS, FAIL, NA, EVIDENCE)}
    return {
        "report_schema": "legal-compliance-judgment/1.0",
        "script_version": SCRIPT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_name": facts.get("product_name", "未命名产品"),
        "assumptions": ["MSDS/TDS 提供的配方、CAS/EC、含量和用途事实完整且确定", "未列入完整事实的物质在本次闭世界判断中视为不存在"],
        "facts": facts,
        "data_root": str(root),
        "sources": sources,
        "results": results,
        "counts": counts,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [f"# 法律法规合格性检查报告：{report['product_name']}", "", f"- 生成时间：{report['generated_at']}", f"- 数据根目录：`{report['data_root']}`", "- 判断模式：完整事实、闭世界", "", "## 输入事实与假设", "", "```json", json.dumps(report["facts"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["## 逐项判断", "", "| 法律法规/标准 | 结果 | 适用性理由 | 命中物质 | 证据 |", "|---|---|---|---|---|"]
    for result in report["results"]:
        matches = "; ".join(str(item["component"].get("name", "")) for item in result["matches"]) or "—"
        evidence = "; ".join(result["evidence"]) or "—"
        reason = result["scope_reason"].replace("|", "\\|")
        lines.append(f"| {result['standard']} | {result['status']} | {reason} | {matches} | {evidence} |")
    lines += ["", "## 汇总", "", json.dumps(report["counts"], ensure_ascii=False, indent=2), "", "## 数据源", ""]
    for source in report["sources"]:
        lines.append(f"- `{source.get('standard')}`: `{source.get('file', source.get('directory'))}`，行数/文件数 `{source.get('rows', source.get('files', '—'))}`，SHA-256 `{source.get('sha256', '目录登记')}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", required=True, help="完整事实 JSON 文件")
    parser.add_argument("--standards", required=True, help="标准 JSON 数组文件，或逗号分隔标准名")
    parser.add_argument("--data-root", default=None, help="法规数据根目录")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", required=True, help="输出文件")
    args = parser.parse_args(argv)
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
    standards_path = Path(args.standards)
    if standards_path.is_file():
        standards = json.loads(standards_path.read_text(encoding="utf-8"))
    else:
        standards = [item.strip() for item in args.standards.split(",") if item.strip()]
    data_root = args.data_root or __import__("os").environ.get("GUANZHI_TONG_LEGAL_DATA_ROOT", DEFAULT_DATA_ROOT)
    report = judge(facts, standards, data_root)
    output = markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2)
    Path(args.output).write_text(output + ("" if output.endswith("\n") else "\n"), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
