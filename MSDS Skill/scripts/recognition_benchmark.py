#!/usr/bin/env python3
"""Reproducible MSDS recognition sampling, evidence and parity benchmarking.

The corpus is read-only.  Recognition uses ``msds_table_search.read_file``
without loading Tk.  DOCX source evidence is independently inspected from the
OOXML package so the normalized recognition record is not its own oracle.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import hashlib
import json
import os
import random
import re
import shutil
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from msds_table_search import SUPPORTED, read_file  # noqa: E402


SCHEMA_VERSION = "recognition-benchmark-v1"
COMPARATOR_VERSION = "recognition-comparator-v1"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
VOLATILE_PARTS = {"docProps/core.xml", "docProps/app.xml"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [canonical(item) for item in value]
    if isinstance(value, float):
        return round(value, 8)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def normalize_text(text: Any) -> str:
    text = str(text or "").replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def text_from_xml(xml: bytes) -> str:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return ""
    parts: list[str] = []
    for node in root.iter():
        local = node.tag.rsplit("}", 1)[-1]
        if local == "t":
            parts.append(node.text or "")
        elif local in {"tab", "br", "cr"}:
            parts.append("\n" if local != "tab" else "\t")
    return normalize_text("".join(parts))


def raw_docx_evidence(path: Path) -> dict[str, Any]:
    """Read source package bytes and independent OOXML geometry evidence."""
    with zipfile.ZipFile(path) as archive:
        names = sorted(name for name in archive.namelist() if not name.endswith("/"))
        part_hashes = {
            name: sha256_bytes(archive.read(name))
            for name in names
            if name not in VOLATILE_PARTS
        }
        media = [
            {"name": name, "sha256": sha256_bytes(archive.read(name)), "bytes": len(archive.read(name))}
            for name in names
            if name.startswith("word/media/")
        ]
        xml_parts = {
            name: archive.read(name)
            for name in names
            if name.startswith("word/") and name.endswith(".xml") and "/_rels/" not in name
        }
    header_parts = [
        ("页眉：" if "/header" in name else "页脚：") + text_from_xml(xml_parts[name])
        for name in sorted(xml_parts)
        if re.search(r"/(?:header|footer)\d+\.xml$", name)
    ]
    document_xml = xml_parts.get("word/document.xml", b"")
    tables: list[dict[str, Any]] = []
    body_paragraphs: list[str] = []
    body_tables: list[str] = []
    try:
        root = ET.fromstring(document_xml)
        body = root.find(".//w:body", NS)
        if body is not None:
            body_paragraphs = [text_from_xml(ET.tostring(node, encoding="utf-8")) for node in body.findall("./w:p", NS)]
            body_tables = [text_from_xml(ET.tostring(node, encoding="utf-8")) for node in body.findall("./w:tbl", NS)]
        for index, table in enumerate(root.findall(".//w:tbl", NS), 1):
            grid = [col.get(f"{{{W_NS}}}w") for col in table.findall("./w:tblGrid/w:gridCol", NS)]
            rows = []
            for row_index, row in enumerate(table.findall("./w:tr", NS)):
                cells = []
                for col_index, cell in enumerate(row.findall("./w:tc", NS)):
                    tcpr = cell.find("./w:tcPr", NS)
                    gridspan = tcpr.find("./w:gridSpan", NS) if tcpr is not None else None
                    vmerge = tcpr.find("./w:vMerge", NS) if tcpr is not None else None
                    cells.append({
                        "row": row_index,
                        "col": col_index,
                        "grid_span": gridspan.get(f"{{{W_NS}}}val") if gridspan is not None else None,
                        "v_merge": vmerge.get(f"{{{W_NS}}}val") if vmerge is not None else None,
                        "text": text_from_xml(ET.tostring(cell, encoding="utf-8")),
                    })
                rows.append(cells)
            tables.append({"table": index, "grid": grid, "rows": rows})
    except ET.ParseError:
        tables = []
    return {
        "source_sha256": sha256_file(path),
        "source_bytes": path.stat().st_size,
        "package_hash": digest_json(part_hashes),
        "part_hashes": part_hashes,
        # Match the reader's record order: header/footer furniture, body
        # paragraphs, then body tables.  The raw XML still remains available
        # for order-sensitive audits when a source has nested structures.
        "text": "\n".join(part for part in [*header_parts, *body_paragraphs, *body_tables] if part),
        "tables": tables,
        "images": media,
        "image_hash": digest_json(media),
    }


def recognition_projection(document: dict[str, Any]) -> dict[str, Any]:
    records = document.get("records", [])
    tables = [record for record in records if record.get("kind") == "table"]
    content = []
    structure = []
    formatting = []
    images = []
    for record in records:
        if record.get("kind") == "text":
            content.append({"label": record.get("label"), "text": normalize_text(record.get("text"))})
            for segment in record.get("content", []):
                if segment.get("type") == "image":
                    raw = base64.b64decode(segment.get("image", {}).get("data", ""))
                    images.append({"sha256": sha256_bytes(raw), "search_text": segment.get("image", {}).get("search_text", "")})
                elif segment.get("type") == "text":
                    formatting.append({
                        "text": segment.get("text", ""),
                        "run_format": segment.get("run_format", {}),
                        "paragraph_format": segment.get("paragraph_format", {}),
                    })
            continue
        content.append({
            "label": record.get("label"),
            "title": normalize_text(record.get("title")),
            "rows": [[normalize_text(cell.get("text")) for cell in row] for row in record.get("rows", [])],
        })
        structure.append({
            "label": record.get("label"),
            "columns": record.get("columns"),
            "rows": [[{
                "row": cell.get("row"), "col": cell.get("col"),
                "colspan": cell.get("colspan"), "rowspan": cell.get("rowspan"),
                "format": cell.get("format"),
            } for cell in row] for row in record.get("rows", [])],
            "structure": record.get("structure", {}),
        })
        for row in record.get("rows", []):
            for cell in row:
                for segment in cell.get("content", []):
                    if segment.get("type") == "image":
                        raw = base64.b64decode(segment.get("image", {}).get("data", ""))
                        images.append({"sha256": sha256_bytes(raw), "search_text": segment.get("image", {}).get("search_text", "")})
                    elif segment.get("type") == "text":
                        formatting.append({
                            "text": segment.get("text", ""),
                            "run_format": segment.get("run_format", {}),
                            "paragraph_format": segment.get("paragraph_format", {}),
                        })
    return {
        "content": content,
        "structure": structure,
        "formatting": formatting,
        "images": images,
        "warnings": document.get("recognition_warnings", []),
        "coverage": document.get("coverage", {}),
    }


def compare_docx(source: Path, document: dict[str, Any]) -> dict[str, Any]:
    raw = raw_docx_evidence(source)
    projection = recognition_projection(document)
    source_content = normalize_text(raw["text"])
    recognized_content = normalize_text("\n".join(
        item.get("text", "") if "text" in item else "\n".join("\n".join(row) for row in item.get("rows", []))
        for item in projection["content"]
    ))
    content_ratio = difflib.SequenceMatcher(None, source_content, recognized_content).ratio()
    source_semantic = re.sub(r"\s+", " ", source_content).strip()
    recognized_semantic = re.sub(r"\s+", " ", recognized_content).strip()
    semantic_equal = source_semantic == recognized_semantic
    content_status = "PASS" if source_content == recognized_content else ("PARTIAL" if semantic_equal or content_ratio >= 0.98 else "MISMATCH")
    source_geometry = raw["tables"]
    recognized_geometry = [
        item for item in projection["structure"]
        if not str(item.get("label", "")).startswith("第 0 部分")
    ]
    structure_status = "PASS" if len(source_geometry) == len(recognized_geometry) and all(
        len(item["rows"]) == len(recognized_geometry[index]["rows"])
        for index, item in enumerate(source_geometry) if index < len(recognized_geometry)
    ) else "MISMATCH"
    source_images = [{"sha256": item["sha256"], "bytes": item["bytes"]} for item in raw["images"]]
    recognized_images = [{"sha256": item["sha256"]} for item in projection["images"]]
    image_status = "PASS" if [item["sha256"] for item in source_images] == [item["sha256"] for item in recognized_images] else "MISMATCH"
    package_status = "PASS" if document.get("source_ooxml") and raw["part_hashes"] else "PARTIAL"
    formatting_status = "PARTIAL" if projection["formatting"] else "UNAVAILABLE"
    render_status = "PASS" if document.get("render_pdf") else "UNAVAILABLE"
    dimensions = {
        "content": {
            "status": content_status,
            "source_hash": sha256_bytes(source_content.encode()),
            "recognized_hash": digest_json(projection["content"]),
            "source_semantic_hash": sha256_bytes(source_semantic.encode()),
            "recognized_semantic_hash": sha256_bytes(recognized_semantic.encode()),
            "ordered_similarity": round(content_ratio, 6),
            "semantic_equal": semantic_equal,
            "diff_note": "only logical line/segment boundaries differ" if semantic_equal and content_status == "PARTIAL" else None,
        },
        "structure": {"status": structure_status, "source_hash": digest_json(source_geometry), "recognized_hash": digest_json(recognized_geometry)},
        "formatting": {"status": formatting_status, "source_hash": digest_json(raw["part_hashes"]), "recognized_hash": digest_json(projection["formatting"])},
        "images": {"status": image_status, "source_hash": raw["image_hash"], "recognized_hash": digest_json(recognized_images)},
        "package": {"status": package_status, "source_hash": raw["package_hash"], "recognized_hash": digest_json(document.get("source_ooxml", {}))},
        "render": {"status": render_status, "reason": "native render not requested" if render_status == "UNAVAILABLE" else None},
    }
    required = ["content", "structure", "images"]
    overall = "PASS" if all(dimensions[name]["status"] == "PASS" for name in required) and all(
        dimensions[name]["status"] in {"PASS", "UNAVAILABLE"} for name in dimensions
    ) else ("PARTIAL" if any(dimensions[name]["status"] == "PASS" for name in required) else "MISMATCH")
    return {"overall": overall, "dimensions": dimensions, "source": raw, "recognition": projection}


def discover(root: Path, extensions: set[str]) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and not path.name.startswith("~$")
        and path.suffix.lower() in extensions
    )


def family_key(path: Path) -> str:
    match = re.search(r"([A-Za-z]{1,8})[-_ ]?\d", path.stem)
    return match.group(1).upper() if match else path.parent.name[:32]


def sample_paths(paths: list[Path], size: int, seed: int) -> list[Path]:
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path in paths:
        size_bucket = "small" if path.stat().st_size < 100_000 else "medium" if path.stat().st_size < 1_000_000 else "large"
        strata[(path.suffix.lower(), family_key(path), size_bucket)].append(path)
    candidates = list(paths)
    rng.shuffle(candidates)
    chosen: list[Path] = []
    # Guarantee extension coverage before filling the remaining slots.
    by_extension: dict[str, list[Path]] = defaultdict(list)
    for path in candidates:
        by_extension[path.suffix.lower()].append(path)
    for extension in sorted(by_extension):
        if len(chosen) >= size:
            break
        chosen.append(by_extension[extension][0])
    # Fill in round-robin extension order so a small smoke sample does not
    # become all legacy DOC merely because DOC is lexicographically first.
    extension_candidates = {
        extension: [item for item in candidates if item.suffix.lower() == extension]
        for extension in sorted(by_extension)
    }
    cursor = {extension: 0 for extension in extension_candidates}
    while len(chosen) < size and extension_candidates:
        progressed = False
        for extension in sorted(extension_candidates):
            items = extension_candidates[extension]
            while cursor[extension] < len(items) and items[cursor[extension]] in chosen:
                cursor[extension] += 1
            if cursor[extension] < len(items):
                chosen.append(items[cursor[extension]])
                cursor[extension] += 1
                progressed = True
                if len(chosen) >= size:
                    break
        if not progressed:
            break
    return sorted(chosen)


def build_manifest(root: Path, selected: list[Path], seed: int, extensions: set[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "source_root": str(root),
        "extensions": sorted(extensions),
        "selected": [
            {
                "path": str(path),
                "relative_path": path.relative_to(root).as_posix(),
                "extension": path.suffix.lower(),
                "family": family_key(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in selected
        ],
    }


def read_file_worker(source: Path) -> dict[str, Any]:
    """Read one item with COM initialized when the host provides pywin32."""
    pythoncom = None
    try:
        import pythoncom as _pythoncom
        pythoncom = _pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass
    try:
        return read_file(source)
    finally:
        if pythoncom is not None:
            pythoncom.CoUninitialize()


def update_regression_ledger(path: Path, summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Append dimension outcomes and classify changes against the prior run."""
    prior: dict[str, str] = {}
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            for item in previous.get("entries", []):
                prior[item["key"]] = item.get("status")
        except (OSError, json.JSONDecodeError):
            prior = {}
    changes = []
    entries = []
    for result in summary.get("results", []):
        source = result.get("source", {})
        source_hash = source.get("sha256")
        for dimension, status in (result.get("dimensions") or {}).items():
            key = f"{source_hash}|{summary.get('manifest', {}).get('seed')}|{summary.get('comparator_version')}|{dimension}"
            previous_status = prior.get(key)
            if previous_status is None:
                classification = "new"
            elif previous_status == status:
                classification = "unchanged"
            elif previous_status not in {"PASS", "PARTIAL"} and status in {"PASS", "PARTIAL"}:
                classification = "fixed"
            elif previous_status in {"PASS", "PARTIAL"} and status not in {"PASS", "PARTIAL"}:
                classification = "regressed"
            else:
                classification = "changed"
            entry = {"key": key, "source": source, "dimension": dimension, "status": status, "classification": classification}
            entries.append(entry)
            changes.append(entry)
    path.write_text(json.dumps({"schema_version": "recognition-regression-ledger-v1", "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    return changes


def run(args: argparse.Namespace) -> int:
    source_path = Path(args.source).resolve() if args.source else None
    root = Path(args.source_root).resolve() if args.source_root else (source_path.parent if source_path else None)
    if root is None:
        raise ValueError("--source-root or --source is required")
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    extensions = {f".{item.strip().lower().lstrip('.')}" for item in args.extensions.split(",") if item.strip()}
    paths = [source_path] if source_path else discover(root, extensions)
    if source_path is not None and (not source_path.exists() or source_path.suffix.lower() not in extensions):
        raise ValueError(f"Selected source is missing or unsupported: {source_path}")
    selected = [source_path] if source_path is not None else sample_paths(paths, args.sample_size, args.seed)
    manifest = build_manifest(root, selected, args.seed, extensions)
    (workspace / "sample-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "DRY_RUN", "selected": len(selected), "manifest": str(workspace / "sample-manifest.json")}, ensure_ascii=False))
        return 0
    results = []
    artifacts = workspace / "items"
    artifacts.mkdir(exist_ok=True)
    for index, item in enumerate(manifest["selected"], 1):
        source = Path(item["path"])
        item_dir = artifacts / f"{index:04d}_{item['sha256'][:12]}"
        item_dir.mkdir(exist_ok=True)
        started = time.perf_counter()
        try:
            # Keep the default batch path serial and bounded.  A per-item
            # future prevents a hung converter from blocking the whole run;
            # cancelled conversion work remains isolated from the corpus.
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="msds-recognition")
            future = executor.submit(read_file_worker, source)
            try:
                document = future.result(timeout=args.timeout_seconds)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
            if source.suffix.lower() == ".docx":
                comparison = compare_docx(source, document)
            else:
                projection = recognition_projection(document)
                comparison = {"overall": "PARTIAL", "dimensions": {"content": {"status": "PARTIAL", "recognized_hash": digest_json(projection["content"])}, "structure": {"status": "PARTIAL"}, "formatting": {"status": "UNAVAILABLE"}, "images": {"status": "PARTIAL"}, "package": {"status": "UNAVAILABLE"}, "render": {"status": "UNAVAILABLE"}}, "recognition": projection}
            document.pop("render_pdf", None)
            (item_dir / "recognition.json").write_text(json.dumps(canonical(document), ensure_ascii=False, indent=2), encoding="utf-8")
            (item_dir / "comparison.json").write_text(json.dumps(canonical(comparison), ensure_ascii=False, indent=2), encoding="utf-8")
            results.append({"source": item, "status": "COMPLETE", "overall": comparison["overall"], "dimensions": {key: value.get("status") for key, value in comparison["dimensions"].items()}, "artifact_dir": str(item_dir), "elapsed_seconds": round(time.perf_counter() - started, 4)})
        except Exception as exc:
            results.append({"source": item, "status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}", "artifact_dir": str(item_dir), "elapsed_seconds": round(time.perf_counter() - started, 4)})
    summary = {"schema_version": SCHEMA_VERSION, "comparator_version": COMPARATOR_VERSION, "manifest": manifest, "results": results, "counts": dict(Counter(result["status"] for result in results))}
    ledger_path = workspace / "regression-ledger.json"
    summary["regressions"] = update_regression_ledger(ledger_path, summary)
    summary["ledger"] = str(ledger_path)
    (workspace / "benchmark-summary.json").write_text(json.dumps(canonical(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "selected": len(selected), "summary": str(workspace / "benchmark-summary.json")}, ensure_ascii=False))
    return 0 if all(result["status"] == "COMPLETE" for result in results) else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark GUI-backed MSDS recognition without modifying sources")
    parser.add_argument("--source-root")
    parser.add_argument("--source")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--sample-size", type=int, default=6)
    parser.add_argument("--extensions", default="docx,doc,pdf")
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--dry-run", action="store_true")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
