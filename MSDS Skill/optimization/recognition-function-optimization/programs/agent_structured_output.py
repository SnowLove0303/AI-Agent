#!/usr/bin/env python3
"""Convert GUI recognition evidence into a stable Agent import channel."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "agent-recognition-v1"
SECTION_RE = re.compile(r"(?:第\s*)?(1[0-6]|[1-9])\s*(?:部分|[.．、:：])")


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def section_number(record: dict[str, Any]) -> str | None:
    explicit = record.get("section")
    if isinstance(explicit, str):
        match = re.search(r"第\s*(1[0-6]|[1-9])\s*部分", explicit)
        if match:
            return match.group(1)
    for value in (record.get("label"), record.get("title"), record.get("text")):
        match = SECTION_RE.search(str(value or ""))
        if match:
            return match.group(1)
    if isinstance(explicit, str) and explicit.startswith("第 0 部分"):
        return "0"
    return None


def image_projection(segment: dict[str, Any], locator: str) -> dict[str, Any]:
    image = segment.get("image", {})
    data = image.get("data", "")
    try:
        raw = __import__("base64").b64decode(data)
        image_hash = hashlib.sha256(raw).hexdigest()
        byte_count = len(raw)
    except Exception:
        image_hash = None
        byte_count = None
    return {
        "id": f"{locator}/image",
        "locator": locator,
        "sha256": image_hash,
        "bytes": byte_count,
        "search_text": image.get("search_text", ""),
        "run_format": segment.get("run_format", {}),
        "paragraph_format": segment.get("paragraph_format", {}),
    }


def convert_item(recognition: dict[str, Any], comparison: dict[str, Any], raw_paths: dict[str, str] | None = None) -> dict[str, Any]:
    source = comparison.get("source", {})
    source_meta = comparison.get("source_meta") or {}
    source_hash = source_meta.get("sha256") or source.get("source_sha256") or digest(recognition.get("name"))
    item_id = f"SRC-{source_hash[:16]}"
    sections: dict[str, list[dict[str, Any]]] = {str(index): [] for index in range(17)}
    tables: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    segment_index: dict[str, dict[str, Any]] = {}
    warnings = list(recognition.get("recognition_warnings", []))
    for record_index, record in enumerate(recognition.get("records", [])):
        record_locator = f"{item_id}/record/{record_index}"
        section = section_number(record)
        structured = {
            "id": record_locator,
            "section": section,
            "kind": record.get("kind"),
            "label": record.get("label"),
            "title": record.get("title"),
            "text": record.get("text"),
            "page": record.get("page"),
            "source_locator": record_locator,
            "tables": [],
            "segments": [],
        }
        for segment_index_number, segment in enumerate(record.get("content", [])):
            locator = f"{record_locator}/segment/{segment_index_number}"
            if segment.get("type") == "image":
                image = image_projection(segment, locator)
                images.append(image)
                structured["segments"].append({"id": locator, "type": "image", "image_id": image["id"]})
            else:
                projected = {
                    "id": locator,
                    "type": "text",
                    "text": segment.get("text", ""),
                    "normalized_text": re.sub(r"\s+", " ", str(segment.get("text", ""))).strip(),
                    "run_format": segment.get("run_format", {}),
                    "paragraph_format": segment.get("paragraph_format", {}),
                }
                segment_index[locator] = projected
                structured["segments"].append(projected)
        for row_index, row in enumerate(record.get("rows", [])):
            row_id = f"{record_locator}/row/{row_index}"
            row_out = {"id": row_id, "row": row_index, "cells": []}
            for cell_index, cell in enumerate(row):
                cell_id = f"{row_id}/cell/{cell.get('col', cell_index)}"
                cell_out = {
                    "id": cell_id,
                    "row": cell.get("row", row_index),
                    "column": cell.get("col", cell_index),
                    "colspan": cell.get("colspan", 1),
                    "rowspan": cell.get("rowspan", 1),
                    "text": cell.get("text", ""),
                    "normalized_text": re.sub(r"\s+", " ", str(cell.get("text", ""))).strip(),
                    "format": cell.get("format", {}),
                    "background": cell.get("background"),
                    "segments": [],
                }
                for paragraph_index, paragraph in enumerate(cell.get("paragraphs", [])):
                    for segment_number, segment in enumerate(paragraph.get("content", [])):
                        locator = f"{cell_id}/paragraph/{paragraph_index}/segment/{segment_number}"
                        if segment.get("type") == "image":
                            image = image_projection(segment, locator)
                            images.append(image)
                            cell_out["segments"].append({"id": locator, "type": "image", "image_id": image["id"]})
                        else:
                            projected = {
                                "id": locator,
                                "type": "text",
                                "text": segment.get("text", ""),
                                "normalized_text": re.sub(r"\s+", " ", str(segment.get("text", ""))).strip(),
                                "run_format": segment.get("run_format", {}),
                                "paragraph_format": segment.get("paragraph_format", paragraph.get("paragraph_format", {})),
                            }
                            segment_index[locator] = projected
                            cell_out["segments"].append(projected)
                row_out["cells"].append(cell_out)
            structured["tables"].append(row_out)
        if record.get("kind") == "table":
            table = {
                "id": record_locator,
                "section": section,
                "label": record.get("label"),
                "title": record.get("title"),
                "columns": record.get("columns"),
                "rows": structured["tables"],
                "structure": record.get("structure", {}),
                "source_locator": record_locator,
            }
            tables.append(table)
            structured["tables"] = [table]
        sections.setdefault(section or "unclassified", []).append(structured)

    dimensions = comparison.get("dimensions", {})
    statuses = {name: value.get("status", "UNAVAILABLE") for name, value in dimensions.items()}
    blocking = {"MISMATCH", "BLOCKED", "UNAVAILABLE"}
    overall = "COMPLETE" if not warnings and all(statuses.get(name) == "PASS" for name in ("content", "structure", "images", "package")) else "PARTIAL"
    if any(status == "BLOCKED" for status in statuses.values()):
        overall = "BLOCKED"
    quality = {
        "overall": overall,
        "dimensions": statuses,
        "warnings": warnings,
        "section_counts": {key: len(value) for key, value in sections.items()},
        "table_count": len(tables),
        "image_count": len(images),
        "blocking_dimensions": [name for name, status in statuses.items() if status in blocking],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "item_id": item_id,
        "source": {
            "name": recognition.get("name"),
            "source_type": recognition.get("source_type"),
            "sha256": source_hash,
            "path": source_meta.get("path"),
        },
        "evidence": {"raw_recognition": raw_paths.get("recognition") if raw_paths else None, "raw_comparison": raw_paths.get("comparison") if raw_paths else None},
        "quality": quality,
        "sections": sections,
        "tables": tables,
        "images": images,
        "indexes": {
            "tables": {table["id"]: {"section": table.get("section"), "title": table.get("title")} for table in tables},
            "segments": segment_index,
        },
    }


def convert_workspace(workspace: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    summary = json.loads((workspace / "benchmark-summary.json").read_text(encoding="utf-8"))
    records = []
    for result in summary.get("results", []):
        if result.get("status") != "COMPLETE":
            records.append({"source": result.get("source"), "status": "BLOCKED", "error": result.get("error")})
            continue
        source = result.get("source", {})
        artifact_dir = Path(result["artifact_dir"])
        recognition = json.loads((artifact_dir / "recognition.json").read_text(encoding="utf-8"))
        comparison = json.loads((artifact_dir / "comparison.json").read_text(encoding="utf-8"))
        comparison["source_meta"] = {
            "path": source.get("path"),
            "sha256": source.get("sha256") or comparison.get("source", {}).get("source_sha256"),
            "bytes": source.get("bytes"),
        }
        structured = convert_item(recognition, comparison, {"recognition": str(artifact_dir / "recognition.json"), "comparison": str(artifact_dir / "comparison.json")})
        item_path = output / "items" / f"{structured['item_id']}.json"
        item_path.parent.mkdir(parents=True, exist_ok=True)
        item_path.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append({"item_id": structured["item_id"], "source": structured["source"], "quality": structured["quality"], "path": str(item_path)})
    manifest = {"schema_version": SCHEMA_VERSION, "seed": summary.get("manifest", {}).get("seed"), "source_root": summary.get("manifest", {}).get("source_root"), "items": records, "counts": dict(Counter(item.get("quality", {}).get("overall", item.get("status", "UNKNOWN")) for item in records))}
    (output / "agent-import-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit stable Agent recognition records")
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = convert_workspace(args.workspace, args.output)
    print(json.dumps({"schema_version": SCHEMA_VERSION, "items": len(manifest["items"]), "manifest": str(args.output / "agent-import-manifest.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
