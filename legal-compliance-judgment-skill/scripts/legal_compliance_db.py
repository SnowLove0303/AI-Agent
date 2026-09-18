#!/usr/bin/env python3
"""SQLite catalog, source refresh, condition selection, and audit storage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DATA_ROOT = r"F:\APP Location\Guanzhi Tong\法律法规物质清单"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "regulation_catalog.json"
DB_SCHEMA_VERSION = "1.0"

COMPOSITION_BASELINE_STANDARDS = [
    "REACH SVHC 253项",
    "REACH Annex XVII",
    "RoHS",
    "HSF 001",
    "BSBL",
    "AfPS GS 2019:01 PAK",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS regulations (
  regulation_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  aliases_json TEXT NOT NULL,
  jurisdiction_json TEXT NOT NULL,
  scope_mode TEXT NOT NULL,
  source_key TEXT NOT NULL,
  conditions_json TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS regulation_sources (
  source_key TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  local_path TEXT NOT NULL DEFAULT '',
  reference_uri TEXT NOT NULL DEFAULT '',
  version TEXT NOT NULL DEFAULT '',
  effective_date TEXT NOT NULL DEFAULT '',
  sha256 TEXT NOT NULL DEFAULT '',
  row_count INTEGER NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS regulation_conditions (
  condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
  regulation_id TEXT NOT NULL,
  field TEXT NOT NULL,
  operator TEXT NOT NULL,
  values_json TEXT NOT NULL,
  rationale TEXT NOT NULL DEFAULT '',
  FOREIGN KEY(regulation_id) REFERENCES regulations(regulation_id)
);
CREATE TABLE IF NOT EXISTS restriction_rules (
  rule_id TEXT PRIMARY KEY,
  regulation_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_row INTEGER NOT NULL,
  source_hash TEXT NOT NULL,
  source_version TEXT NOT NULL DEFAULT '',
  cn_name TEXT NOT NULL DEFAULT '',
  en_name TEXT NOT NULL DEFAULT '',
  cas TEXT NOT NULL DEFAULT '',
  ec TEXT NOT NULL DEFAULT '',
  group_flag TEXT NOT NULL DEFAULT '',
  scope TEXT NOT NULL DEFAULT '',
  limit_raw TEXT NOT NULL DEFAULT '',
  unit TEXT NOT NULL DEFAULT '',
  test_method TEXT NOT NULL DEFAULT '',
  raw_json TEXT NOT NULL,
  FOREIGN KEY(regulation_id) REFERENCES regulations(regulation_id)
);
CREATE INDEX IF NOT EXISTS idx_restriction_cas ON restriction_rules(regulation_id, cas);
CREATE INDEX IF NOT EXISTS idx_restriction_ec ON restriction_rules(regulation_id, ec);
CREATE INDEX IF NOT EXISTS idx_restriction_names ON restriction_rules(regulation_id, cn_name, en_name);
CREATE TABLE IF NOT EXISTS judgment_runs (
  run_id TEXT PRIMARY KEY,
  facts_hash TEXT NOT NULL,
  facts_json TEXT NOT NULL,
  mode TEXT NOT NULL,
  selected_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS judgment_results (
  result_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  regulation_id TEXT,
  regulation_name TEXT NOT NULL,
  status TEXT NOT NULL,
  result_json TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES judgment_runs(run_id)
);
CREATE TABLE IF NOT EXISTS feedback (
  feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT,
  regulation_id TEXT,
  regulation_name TEXT NOT NULL,
  feedback_json TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  approved_at TEXT NOT NULL DEFAULT ''
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(value: Any) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


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
    raise UnicodeError(f"无法解码数据文件: {path}")


def metadata_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    values: dict[str, str] = {}
    for row in read_csv(path):
        keys = list(row)
        if len(keys) >= 2:
            key = str(row.get(keys[0]) or "").strip()
            if key:
                values[key] = str(row.get(keys[1]) or "").strip()
    return values


def pick(row: dict[str, Any], *keys: str) -> str:
    return next((str(row.get(key) or "").strip() for key in keys if row.get(key)), "")


def portable_source_path(path: Path | str, data_root: Path) -> str:
    try:
        relative = Path(path).relative_to(data_root)
        return "${GUANZHI_TONG_LEGAL_DATA_ROOT}/" + relative.as_posix()
    except ValueError:
        return str(path)


def public_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): public_metadata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_metadata(item) for item in value]
    text = str(value)
    if "feishu.cn" in text or "chatgpt.com/s/" in text:
        return "[internal source redacted; see canonical metadata file]"
    if text.startswith("F:\\") or text.startswith("C:\\"):
        return Path(text).name
    return value


def open_db(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)", (DB_SCHEMA_VERSION,))
    connection.commit()
    return connection


def load_catalog(path: str | Path) -> dict[str, Any]:
    catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(catalog.get("regulations"), list) or not isinstance(catalog.get("sources"), dict):
        raise ValueError("法规目录必须包含 regulations 数组和 sources 对象")
    ids = [entry.get("id") for entry in catalog["regulations"]]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("法规目录存在空 ID 或重复 ID")
    return catalog


def upsert_catalog(connection: sqlite3.Connection, catalog: dict[str, Any]) -> None:
    timestamp = now()
    for key, source in catalog["sources"].items():
        connection.execute(
            """INSERT INTO regulation_sources(source_key,title,kind,local_path,reference_uri,metadata_json,notes,updated_at)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(source_key) DO UPDATE SET title=excluded.title,kind=excluded.kind,metadata_json=excluded.metadata_json,notes=excluded.notes,updated_at=excluded.updated_at""",
            (key, source.get("title", key), source.get("kind", "catalog"), source.get("csv", source.get("directory", "")), source.get("uri", ""), json.dumps(source, ensure_ascii=False), source.get("notes", ""), timestamp),
        )
    for entry in catalog["regulations"]:
        conditions = entry.get("conditions", [])
        connection.execute(
            """INSERT INTO regulations(regulation_id,name,aliases_json,jurisdiction_json,scope_mode,source_key,conditions_json,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(regulation_id) DO UPDATE SET name=excluded.name,aliases_json=excluded.aliases_json,jurisdiction_json=excluded.jurisdiction_json,scope_mode=excluded.scope_mode,source_key=excluded.source_key,conditions_json=excluded.conditions_json,updated_at=excluded.updated_at""",
            (entry["id"], entry["name"], json.dumps(entry.get("aliases", []), ensure_ascii=False), json.dumps(entry.get("jurisdiction", []), ensure_ascii=False), entry.get("scope_mode", "direct-material"), entry.get("source_key", "catalog_only"), json.dumps(conditions, ensure_ascii=False), timestamp, timestamp),
        )
        connection.execute("DELETE FROM regulation_conditions WHERE regulation_id=?", (entry["id"],))
        for condition in conditions:
            connection.execute("INSERT INTO regulation_conditions(regulation_id,field,operator,values_json,rationale) VALUES(?,?,?,?,?)", (entry["id"], condition.get("field", ""), condition.get("operator", "contains_any"), json.dumps(condition.get("values", []), ensure_ascii=False), condition.get("rationale", "")))
    connection.commit()


def _source_file_for(source: dict[str, Any], csv_root: Path) -> Path | None:
    filename = source.get("csv")
    return csv_root / filename if filename else None


def refresh_restrictions(connection: sqlite3.Connection, data_root: str | Path, catalog: dict[str, Any]) -> dict[str, int]:
    root = Path(data_root)
    csv_root = root / "法律法规物质限制清单_CSV导出"
    if not csv_root.is_dir():
        raise FileNotFoundError(f"法规 CSV 数据目录不存在: {csv_root}")
    connection.execute("DELETE FROM restriction_rules")
    counts: dict[str, int] = {}
    regulation_by_source: dict[str, list[dict[str, Any]]] = {}
    for entry in catalog["regulations"]:
        regulation_by_source.setdefault(entry.get("source_key", "catalog_only"), []).append(entry)
    for source_key, source in catalog["sources"].items():
        path = _source_file_for(source, csv_root)
        if not path:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"法规源文件不存在: {path}")
        rows = read_csv(path)
        file_hash = sha256(path)
        metadata_path = csv_root / source.get("metadata", "") if source.get("metadata") else None
        metadata = metadata_map(metadata_path)
        version = metadata.get("版本") or metadata.get("version") or metadata.get("register") or metadata.get("清单名称") or metadata.get("source_regulation") or ""
        connection.execute("UPDATE regulation_sources SET local_path=?,version=?,effective_date=?,sha256=?,row_count=?,metadata_json=?,updated_at=? WHERE source_key=?", (portable_source_path(path, root), version, metadata.get("生效日期", metadata.get("effective_date", "")), file_hash, len(rows), json.dumps(public_metadata({"catalog": source, "metadata": metadata}), ensure_ascii=False), now(), source_key))
        row_total = 0
        for entry in regulation_by_source.get(source_key, []):
            for row_number, row in enumerate(rows, start=2):
                rule_id = f"{entry['id']}:{file_hash}:{row_number}"
                connection.execute(
                    """INSERT INTO restriction_rules(rule_id,regulation_id,source_key,source_file,source_row,source_hash,source_version,cn_name,en_name,cas,ec,group_flag,scope,limit_raw,unit,test_method,raw_json)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rule_id, entry["id"], source_key, portable_source_path(path, root), row_number, file_hash, version, pick(row, "中文名称"), pick(row, "英文名称"), pick(row, "CAS号", "标准CAS号", "源CAS号"), pick(row, "EC号", "标准EC号", "源EC号"), pick(row, "是否组别/类", "是否物质组成员", "记录类型"), pick(row, "限制条件标题", "适用范围(Scope)", "材料筛查说明", "物质描述"), pick(row, "限值ppm", "限值(Limit)", "Limit", "限值", "Category 1", "Category 2a", "Category 2b", "Category 3a", "Category 3b"), pick(row, "单位(Unit)", "Unit", "单位"), pick(row, "测试方法", "Test Method"), json.dumps(row, ensure_ascii=False)),
                )
                row_total += 1
        counts[source_key] = row_total
    connection.commit()
    return counts


def build_database(db_path: str | Path, data_root: str | Path, catalog_path: str | Path = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog = load_catalog(catalog_path)
    connection = open_db(db_path)
    try:
        upsert_catalog(connection, catalog)
        counts = refresh_restrictions(connection, data_root, catalog)
        connection.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('data_root',?)", ("${GUANZHI_TONG_LEGAL_DATA_ROOT}",))
        connection.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('catalog_path',?)", (str(Path(catalog_path)),))
        connection.commit()
        return {"db": str(db_path), "regulations": len(catalog["regulations"]), "restriction_rows": counts, "catalog": str(catalog_path)}
    finally:
        connection.close()


def register_regulation(db_path: str | Path, entry: dict[str, Any], source: dict[str, Any] | None = None) -> None:
    required = ("id", "name", "scope_mode")
    missing = [field for field in required if not entry.get(field)]
    if missing:
        raise ValueError(f"法规注册缺少字段: {', '.join(missing)}")
    connection = open_db(db_path)
    try:
        source_key = entry.get("source_key", "catalog_only")
        if source:
            connection.execute("INSERT OR REPLACE INTO regulation_sources(source_key,title,kind,local_path,reference_uri,metadata_json,notes,updated_at) VALUES(?,?,?,?,?,?,?,?)", (source_key, source.get("title", entry["name"]), source.get("kind", "catalog"), source.get("csv", source.get("directory", "")), source.get("uri", ""), json.dumps(source, ensure_ascii=False), source.get("notes", ""), now()))
        elif not connection.execute("SELECT 1 FROM regulation_sources WHERE source_key=?", (source_key,)).fetchone():
            connection.execute("INSERT INTO regulation_sources(source_key,title,kind,metadata_json,updated_at) VALUES(?,?,?,?,?)", (source_key, entry["name"], "catalog", "{}", now()))
        timestamp = now()
        conditions = entry.get("conditions", [])
        connection.execute("INSERT OR REPLACE INTO regulations(regulation_id,name,aliases_json,jurisdiction_json,scope_mode,source_key,conditions_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (entry["id"], entry["name"], json.dumps(entry.get("aliases", []), ensure_ascii=False), json.dumps(entry.get("jurisdiction", ["GLOBAL"]), ensure_ascii=False), entry["scope_mode"], source_key, json.dumps(conditions, ensure_ascii=False), timestamp, timestamp))
        connection.execute("DELETE FROM regulation_conditions WHERE regulation_id=?", (entry["id"],))
        for condition in conditions:
            connection.execute("INSERT INTO regulation_conditions(regulation_id,field,operator,values_json,rationale) VALUES(?,?,?,?,?)", (entry["id"], condition.get("field", ""), condition.get("operator", "contains_any"), json.dumps(condition.get("values", []), ensure_ascii=False), condition.get("rationale", "")))
        connection.commit()
    finally:
        connection.close()


def _facts_text(facts: dict[str, Any], fields: tuple[str, ...]) -> str:
    values: list[str] = []
    for field in fields:
        value = facts.get(field, [])
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return norm(" ".join(values))


def _condition_match(condition: dict[str, Any], facts: dict[str, Any]) -> bool:
    field = condition.get("field", "")
    haystack = _facts_text(facts, (field,))
    values = [norm(item) for item in condition.get("values", [])]
    operator = condition.get("operator", "contains_any")
    if operator == "contains_all":
        return all(value in haystack for value in values)
    if operator == "not_contains_any":
        return not any(value in haystack for value in values)
    if operator == "equals_any":
        return haystack in values
    return any(value in haystack for value in values)


def _mode_match(mode: str, facts: dict[str, Any], special: str) -> tuple[bool, str]:
    use = _facts_text(facts, ("final_use", "substrates"))
    special_text = _facts_text(facts, ("special_requirements",))
    if mode == "direct-material":
        return True, "条件单包含配方/物质事实，适用直接物质限制筛查"
    if mode == "toy-only":
        ok = any(term in use for term in ("toy", "玩具", "children", "儿童"))
        return ok, "检测到玩具/儿童用途" if ok else "未检测到玩具/儿童用途"
    if mode == "eee-only":
        ok = any(term in use for term in ("eee", "electronic", "electrical", "电子", "电气"))
        return ok, "检测到电子/电气用途" if ok else "未检测到电子/电气用途"
    if mode == "packaging-only":
        ok = any(term in use for term in ("packaging", "container", "包装"))
        return ok, "检测到包装用途" if ok else "未检测到包装用途"
    if mode == "wood-only":
        ok = any(term in use for term in ("wood", "wooden", "木器", "木材", "家具", "furniture"))
        return ok, "检测到木器/木材/家具用途" if ok else "未检测到木器/木材/家具用途"
    if mode == "wall-only":
        ok = any(term in use for term in ("wall", "architectural", "建筑", "墙面"))
        return ok, "检测到建筑/墙面用途" if ok else "未检测到建筑/墙面用途"
    if mode == "building-only":
        ok = any(term in use for term in ("building", "architectural", "建筑", "墙面", "工程"))
        return ok, "检测到建筑用途" if ok else "未检测到建筑用途"
    if mode == "industrial-coating":
        ok = any(term in use for term in ("industrial", "protective", "工业", "防护", "钢结构"))
        return ok, "检测到工业/防护涂层用途" if ok else "未检测到工业/防护涂层用途"
    if mode == "toy-or-gs":
        ok = any(term in use for term in ("toy", "玩具", "children", "儿童")) or "gs" in special_text
        return ok, "检测到玩具/儿童或 GS 特殊要求" if ok else "未检测到玩具/儿童或 GS 特殊要求"
    if mode == "coating":
        ok = any(term in use for term in ("coating", "paint", "涂料", "涂层"))
        return ok, "检测到涂料/涂层用途" if ok else "未检测到涂料/涂层用途"
    if mode == "opaque":
        haystack = _facts_text(facts, ("special_requirements",))
        ok = norm(special) in haystack or any(norm(term) in haystack for term in (special,))
        return ok, "特殊要求明确引用该标准代码" if ok else "条件单未引用该客户/企业标准代码"
    return True, f"未定义 scope_mode={mode}，保守纳入候选"


def select_regulations(db_path: str | Path, facts: dict[str, Any]) -> list[dict[str, Any]]:
    connection = open_db(db_path)
    try:
        selected: list[dict[str, Any]] = []
        for row in connection.execute("SELECT * FROM regulations WHERE enabled=1 ORDER BY regulation_id"):
            jurisdictions = json.loads(row["jurisdiction_json"])
            markets = _facts_text(facts, ("target_market",))
            jurisdiction_ok = not markets or "GLOBAL" in jurisdictions or any(norm(item) in markets for item in jurisdictions)
            if not jurisdiction_ok:
                selected.append({"regulation_id": row["regulation_id"], "name": row["name"], "applicable": False, "reason": "销售市场与该法规管辖区域不匹配"})
                continue
            conditions = json.loads(row["conditions_json"])
            if conditions:
                applicable = all(_condition_match(condition, facts) for condition in conditions)
                reason = "满足目录条件" if applicable else "未满足目录条件"
            else:
                applicable, reason = _mode_match(row["scope_mode"], facts, row["name"])
            selected.append({"regulation_id": row["regulation_id"], "name": row["name"], "applicable": applicable, "reason": reason, "scope_mode": row["scope_mode"], "source_key": row["source_key"]})
        return selected
    finally:
        connection.close()


def select_composition_baseline_regulations(db_path: str | Path) -> list[dict[str, Any]]:
    """Select the broad substance screen without condition-sheet filtering."""
    connection = open_db(db_path)
    try:
        selected: list[dict[str, Any]] = []
        for name in COMPOSITION_BASELINE_STANDARDS:
            row = connection.execute("SELECT * FROM regulations WHERE name=? AND enabled=1", (name,)).fetchone()
            if not row:
                selected.append({
                    "name": name,
                    "applicable": True,
                    "baseline": True,
                    "screening_tier": "composition-baseline",
                    "source_status": "unregistered",
                    "reason": "基础物质筛查固定纳入；当前数据库尚未登记法规条目",
                })
                continue
            rule_count = connection.execute("SELECT COUNT(*) FROM restriction_rules WHERE regulation_id=?", (row["regulation_id"],)).fetchone()[0]
            selected.append({
                "regulation_id": row["regulation_id"],
                "name": row["name"],
                "applicable": True,
                "baseline": True,
                "screening_tier": "composition-baseline",
                "source_status": "source-backed" if rule_count else "catalog-only",
                "reason": "基础物质成分筛查：不使用销售市场、用途、环境、包装或客户条件",
                "scope_mode": row["scope_mode"],
                "source_key": row["source_key"],
                "restriction_row_count": rule_count,
            })
        return selected
    finally:
        connection.close()


def load_rows_from_db(db_path: str | Path, standards: list[str]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Path]:
    connection = open_db(db_path)
    try:
        rows: dict[str, list[dict[str, Any]]] = {}
        sources: list[dict[str, Any]] = []
        placeholders = ",".join("?" for _ in standards)
        regulation_rows = connection.execute(f"SELECT regulation_id,name FROM regulations WHERE name IN ({placeholders})", standards).fetchall() if standards else []
        id_by_name = {row["name"]: row["regulation_id"] for row in regulation_rows}
        for standard in standards:
            regulation_id = id_by_name.get(standard)
            if not regulation_id:
                continue
            db_rows = connection.execute("SELECT * FROM restriction_rules WHERE regulation_id=? ORDER BY source_row", (regulation_id,)).fetchall()
            converted: list[dict[str, Any]] = []
            for item in db_rows:
                raw = json.loads(item["raw_json"])
                raw.update({"_source_file": item["source_file"], "_source_row": item["source_row"], "_source_version": item["source_version"], "_source_metadata": {"db_source_key": item["source_key"]}})
                converted.append(raw)
            rows[standard] = converted
            source = connection.execute("SELECT * FROM regulation_sources WHERE source_key=(SELECT source_key FROM regulations WHERE regulation_id=?)", (regulation_id,)).fetchone()
            if source:
                sources.append({"standard": standard, "file": source["local_path"], "sha256": source["sha256"], "rows": source["row_count"], "version": source["version"], "metadata": json.loads(source["metadata_json"]) if source["metadata_json"] else {}})
        data_root = connection.execute("SELECT value FROM meta WHERE key='data_root'").fetchone()
        return rows, sources, Path(data_root["value"]) if data_root else Path("")
    finally:
        connection.close()


def record_run(db_path: str | Path, facts: dict[str, Any], selection: list[dict[str, Any]], report: dict[str, Any], mode: str) -> str:
    connection = open_db(db_path)
    try:
        run_id = str(uuid.uuid4())
        facts_json = json.dumps(facts, ensure_ascii=False, sort_keys=True)
        facts_hash = hashlib.sha256(facts_json.encode("utf-8")).hexdigest()
        connection.execute("INSERT INTO judgment_runs(run_id,facts_hash,facts_json,mode,selected_json,created_at) VALUES(?,?,?,?,?,?)", (run_id, facts_hash, facts_json, mode, json.dumps(selection, ensure_ascii=False), now()))
        ids = {row["name"]: row["regulation_id"] for row in connection.execute("SELECT regulation_id,name FROM regulations")}
        for result in report.get("results", []):
            connection.execute("INSERT INTO judgment_results(run_id,regulation_id,regulation_name,status,result_json) VALUES(?,?,?,?,?)", (run_id, ids.get(result["standard"]), result["standard"], result["status"], json.dumps(result, ensure_ascii=False)))
        connection.commit()
        return run_id
    finally:
        connection.close()


def add_feedback(db_path: str | Path, regulation_name: str, feedback: dict[str, Any], run_id: str | None = None) -> int:
    connection = open_db(db_path)
    try:
        row = connection.execute("SELECT regulation_id FROM regulations WHERE name=?", (regulation_name,)).fetchone()
        cursor = connection.execute("INSERT INTO feedback(run_id,regulation_id,regulation_name,feedback_json,created_at) VALUES(?,?,?,?,?)", (run_id, row["regulation_id"] if row else None, regulation_name, json.dumps(feedback, ensure_ascii=False), now()))
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def approve_feedback(db_path: str | Path, feedback_id: int) -> None:
    connection = open_db(db_path)
    try:
        feedback_row = connection.execute("SELECT * FROM feedback WHERE feedback_id=?", (feedback_id,)).fetchone()
        if not feedback_row:
            raise KeyError(f"feedback_id 不存在: {feedback_id}")
        feedback = json.loads(feedback_row["feedback_json"])
        regulation_id = feedback_row["regulation_id"]
        if feedback.get("kind") == "add_alias" and regulation_id:
            row = connection.execute("SELECT aliases_json FROM regulations WHERE regulation_id=?", (regulation_id,)).fetchone()
            aliases = json.loads(row["aliases_json"])
            alias = feedback.get("alias")
            if alias and alias not in aliases:
                aliases.append(alias)
                connection.execute("UPDATE regulations SET aliases_json=?,updated_at=? WHERE regulation_id=?", (json.dumps(aliases, ensure_ascii=False), now(), regulation_id))
        elif feedback.get("kind") == "add_condition" and regulation_id:
            row = connection.execute("SELECT conditions_json FROM regulations WHERE regulation_id=?", (regulation_id,)).fetchone()
            conditions = json.loads(row["conditions_json"])
            conditions.append(feedback.get("condition", {}))
            connection.execute("UPDATE regulations SET conditions_json=?,updated_at=? WHERE regulation_id=?", (json.dumps(conditions, ensure_ascii=False), now(), regulation_id))
        connection.execute("UPDATE feedback SET approved=1,approved_at=? WHERE feedback_id=?", (now(), feedback_id))
        connection.commit()
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "refresh"):
        command = sub.add_parser(name)
        command.add_argument("--db", required=True)
        command.add_argument("--data-root", default=os.environ.get("GUANZHI_TONG_LEGAL_DATA_ROOT", DEFAULT_DATA_ROOT))
        command.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    list_command = sub.add_parser("list")
    list_command.add_argument("--db", required=True)
    select_command = sub.add_parser("select")
    select_command.add_argument("--db", required=True)
    select_command.add_argument("--facts", required=True)
    feedback_command = sub.add_parser("feedback-add")
    feedback_command.add_argument("--db", required=True)
    feedback_command.add_argument("--regulation", required=True)
    feedback_command.add_argument("--feedback-json", required=True)
    feedback_command.add_argument("--run-id")
    register_command = sub.add_parser("register")
    register_command.add_argument("--db", required=True)
    register_command.add_argument("--entry", required=True)
    approve_command = sub.add_parser("feedback-approve")
    approve_command.add_argument("--db", required=True)
    approve_command.add_argument("--feedback-id", required=True, type=int)
    args = parser.parse_args(argv)
    if args.command in {"init", "refresh"}:
        print(json.dumps(build_database(args.db, args.data_root, args.catalog), ensure_ascii=False, indent=2))
        return 0
    if args.command == "list":
        connection = open_db(args.db)
        try:
            print(json.dumps([dict(row) for row in connection.execute("SELECT regulation_id,name,scope_mode,source_key,enabled FROM regulations ORDER BY regulation_id")], ensure_ascii=False, indent=2))
        finally:
            connection.close()
        return 0
    if args.command == "select":
        facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
        print(json.dumps(select_regulations(args.db, facts), ensure_ascii=False, indent=2))
        return 0
    if args.command == "register":
        entry = json.loads(Path(args.entry).read_text(encoding="utf-8"))
        register_regulation(args.db, entry, entry.get("source"))
        return 0
    if args.command == "feedback-add":
        feedback = json.loads(Path(args.feedback_json).read_text(encoding="utf-8")) if Path(args.feedback_json).is_file() else json.loads(args.feedback_json)
        print(add_feedback(args.db, args.regulation, feedback, args.run_id))
        return 0
    approve_feedback(args.db, args.feedback_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
