from __future__ import annotations

import argparse
from pathlib import Path

from tds_common import dump, infer_performance_topology, load, norm, source_fidelity_contract


# These are candidate signals only. The decision ledger records whether the
# source row was safely preserved or merely offered as a semantic candidate.
ALIASES = {
    norm(key): value
    for key, value in {
        "乳液外观": "performance.appearance",
        "外观": "performance.appearance",
        "appearance": "performance.appearance",
        "环氧当量（EEW）": "performance.eew",
        "epoxy equivalent weight (eew)": "performance.eew",
        "固含量": "performance.solid_content",
        "固体份含量": "performance.solid_content",
        "solid content": "performance.solid_content",
        "solids content": "performance.solid_content",
        "ph值（25℃）": "performance.ph_25c",
        "ph value (25°c)": "performance.ph_25c",
        "ph value (25℃)": "performance.ph_25c",
        "粘度（25℃）": "performance.viscosity_25c",
        "viscosity (25°c)": "performance.viscosity_25c",
        "viscosity (25℃)": "performance.viscosity_25c",
        "emulsion appearance": "performance.appearance",
        "epoxy equivalent weight": "performance.eew",
    }.items()
}
TEXT = [
    "product.description",
    "product.supply_form",
    "product.features",
    "product.application",
    "product.storage",
]


def field(field_id: str) -> dict:
    return {"field_id": field_id, "values": {}, "source_values": {}, "sources": {}}


def copy_language_value(target: dict, language: str, value: str, source: dict) -> None:
    target["values"][language] = value
    target["source_values"][language] = value
    target["sources"][language] = source


def source_row_decision(item: dict) -> dict:
    canonical = item["canonical_field_ids"]
    if canonical:
        return {
            "field_id": item["field_id"],
            "kind": "performance_row",
            "source_labels": item["source_label_values"],
            "source_values": item["source_values"],
            "provenance": {language: [row["source_location"]] for language, row in item["sources"].items()},
            "canonical_field_ids": canonical,
            "decision": "candidate_semantic_mapping_preserve_source_row",
            "confidence": "medium",
            "needs_judgment": True,
            "reason": "别名只提供候选归类；Agent 仍需结合限定条件和上下文确认，输出保留源行标签。",
        }
    return {
        "field_id": item["field_id"],
        "kind": "performance_row",
        "source_labels": item["source_label_values"],
        "source_values": item["source_values"],
        "provenance": {language: [row["source_location"]] for language, row in item["sources"].items()},
        "canonical_field_ids": {},
        "decision": "preserve_as_source_row",
        "confidence": "high",
        "needs_judgment": False,
        "reason": "没有安全的固定字段候选；保留原始标签、限定条件和源顺序，避免被模板示例牵引。",
    }


def text_decisions(fields: dict) -> list[dict]:
    out = [
        {
            "field_id": field_id,
            "kind": "text",
            "source_values": item.get("source_values", {}),
            "normalized_values": item.get("values", {}),
            "provenance": {language: source.get("locations", []) for language, source in item.get("sources", {}).items()},
            "decision": "candidate_source_preservation",
            "confidence": "medium",
            "needs_judgment": True,
            "reason": "文本边界、事实归纳、列表结构和英文专业表达必须由 Agent 根据源文上下文确认。",
        }
        for field_id, item in fields.items()
        if item.get("values")
    ]
    out.extend(
        {
            "field_id": field_id,
            "kind": "text",
            "source_values": {},
            "normalized_values": {},
            "provenance": {},
            "decision": "hide_no_source_candidate",
            "confidence": "high",
            "needs_judgment": True,
            "reason": "源文件无本章节证据；Agent 确认后整节隐藏（标题+内容删除，不写无数据），确认前不得发布。",
        }
        for field_id in TEXT
        if field_id in fields and not fields[field_id].get("values")
    )
    return out


def normalized_model(fields: dict, performance_rows: list[dict], decisions: list[dict], table_topology: dict) -> dict:
    return {
        "schema_version": "1.3.0",
        "status": "candidate",
        "fields": {
            field_id: {
                "field_id": field_id,
                "source_values": item.get("source_values", {}),
                "normalized_values": item.get("values", {}),
                "provenance": item.get("sources", {}),
            }
            for field_id, item in fields.items()
        },
        "performance_rows": [
            {
                "field_id": item["field_id"],
                "source_label_values": item["source_label_values"],
                "source_values": item["source_values"],
                "source_unit_values": item["source_unit_values"],
                "source_test_method_values": item["source_test_method_values"],
                "normalized_label_values": item["normalized_label_values"],
                "normalized_values": item["normalized_values"],
                "normalized_unit_values": item["normalized_unit_values"],
                "normalized_test_method_values": item["normalized_test_method_values"],
                "provenance": {language: [row["source_location"]] for language, row in item["sources"].items()},
            }
            for item in performance_rows
        ],
        "performance_table_topology": table_topology,
        "decision_ledger": decisions,
        "translation": {
            "source": "normalized_model",
            "method": "agent-guided-professional-technical-translation",
            "requires_agent_judgment": True,
            "english_source_role": "evidence_and_cross_check_only",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cn", type=Path)
    ap.add_argument("--en", type=Path)
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    paths = [path for path in (args.cn, args.en) if path]
    if not paths:
        raise SystemExit("one source facts file is required")

    fields: dict = {}
    blockers: list[dict] = []
    source_rows_by_lang: dict[str, list[dict]] = {}
    for path in paths:
        source = load(path)
        language = source["language"]
        title = source.get("title", {})
        if title.get("text"):
            item = fields.setdefault("product.title", field("product.title"))
            if language in item["source_values"]:
                blockers.append({"kind": "conflict", "field_id": "product.title", "language": language})
            else:
                copy_language_value(item, language, title["text"], title)
        for field_id in TEXT:
            section = source.get("sections", {}).get(field_id, {})
            value = section.get("text", "")
            if not value:
                continue
            item = fields.setdefault(field_id, field(field_id))
            if language in item["source_values"]:
                blockers.append({"kind": "conflict", "field_id": field_id, "language": language})
            else:
                copy_language_value(item, language, value, section)

        source_rows: list[dict] = []
        for row in source.get("performance_rows", []):
            if row.get("source_column_count", 4) > 4:
                blockers.append(
                    {
                        "kind": "template_capacity",
                        "source_location": row["source_location"],
                        "reason": "source performance row has more columns than the maintained four-column TDS table",
                    }
                )
                continue
            source_rows.append(row)
            canonical = ALIASES.get(norm(row["item"]))
            if not canonical:
                continue
            item = fields.setdefault(canonical, field(canonical))
            if language in item["source_values"]:
                blockers.append({"kind": "conflict", "field_id": canonical, "language": language, "source_location": row["source_location"]})
                continue
            copy_language_value(item, language, row["value"], row)
            item["unit"] = row.get("unit", "")
            item["test_method"] = row.get("test_method", "")
        source_rows_by_lang[language] = source_rows

    row_count = max((len(rows) for rows in source_rows_by_lang.values()), default=0)
    if len({len(rows) for rows in source_rows_by_lang.values()}) > 1:
        blockers.append({"kind": "source_row_count_mismatch", "reason": "CN and EN performance tables do not have the same number of rows"})

    performance_rows: list[dict] = []
    extra_rows: list[dict] = []
    for index in range(row_count):
        item = {
            "field_id": f"performance.row.{index + 1:03d}",
            "label_values": {},
            "values": {},
            "unit_values": {},
            "test_method_values": {},
            "source_label_values": {},
            "source_values": {},
            "source_unit_values": {},
            "source_test_method_values": {},
            "normalized_label_values": {},
            "normalized_values": {},
            "normalized_unit_values": {},
            "normalized_test_method_values": {},
            "sources": {},
            "canonical_field_ids": {},
        }
        for language, rows in source_rows_by_lang.items():
            if index >= len(rows):
                continue
            row = rows[index]
            label = row["item"]
            value = row.get("value", "")
            unit = row.get("unit", "")
            method = row.get("test_method", "")
            item["label_values"][language] = label
            item["values"][language] = value
            item["unit_values"][language] = unit
            item["test_method_values"][language] = method
            item["source_label_values"][language] = label
            item["source_values"][language] = value
            item["source_unit_values"][language] = unit
            item["source_test_method_values"][language] = method
            item["normalized_label_values"][language] = label
            item["normalized_values"][language] = value
            item["normalized_unit_values"][language] = unit
            item["normalized_test_method_values"][language] = method
            item["sources"][language] = row
            canonical = ALIASES.get(norm(label))
            if canonical:
                item["canonical_field_ids"][language] = canonical
        performance_rows.append(item)
        if not item["canonical_field_ids"]:
            extra_rows.append({key: value for key, value in item.items() if key != "canonical_field_ids"})

    registry = load(args.registry)
    required = {
        slot["field_id"]
        for variant in registry["variants"].values()
        for slot in variant["slots"]
    }
    for field_id in required:
        fields.setdefault(field_id, field(field_id))

    table_topology = {language: infer_performance_topology(rows, fields, language) for language, rows in source_rows_by_lang.items()}
    decisions = [source_row_decision(item) for item in performance_rows]
    decisions.extend(text_decisions(fields))
    model = normalized_model(fields, performance_rows, decisions, table_topology)
    fidelity = source_fidelity_contract(fields, performance_rows, paths)
    dump(
        args.output,
        {
            "schema_version": "1.3.0",
            "source_facts": [str(path.resolve()) for path in paths],
            "mapped_fields": fields,
            "normalized_model": model,
            "performance_rows": performance_rows,
            "performance_table_topology": table_topology,
            "performance_extra_rows": extra_rows,
            "decision_ledger": decisions,
            "source_fidelity": fidelity,
            "blockers": blockers,
            "status": "blocked" if blockers else "ready",
        },
    )
    print(
        f"mapping={args.output} fields={len(fields)} rows={len(performance_rows)} "
        f"extra_rows={len(extra_rows)} decisions={len(decisions)} blockers={len(blockers)}"
    )
    raise SystemExit(1 if blockers else 0)


if __name__ == "__main__":
    main()
