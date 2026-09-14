#!/usr/bin/env python3
"""One-command eight-format build for the unified MSDS skill (v3.24.0).

Business flow::

    source.[docx/doc/odt/rtf/xlsx/xls/txt] --extract--> draft --review--> approved model JSON
        --build_eight--> 4 DOCX + gates + 4 PDF + matrix-report.json

The approved model JSON holds the *standardized* facts; ``en`` must be a
reviewed translation OF that model (see ``draft_en_facts.py``).  Any gate
failure stops the whole release before any PDF is converted. The four DOCX
masters are completed first; PDFs are then converted as a bounded batch with
visible progress checkpoints.

Usage::

    python scripts/build_eight.py --source SRC.docx --facts MODEL.json
    --out DIR [--model MODEL] [--revision DATE] [--no-pdf] [--timeout S]
    [--pdf-workers N] [--wpscli PATH] [--progress-file PATH]
    [--docx-preview-dir DIR] [--preflight-only] [--preflight-report PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msds_pipeline import ReleaseBlocked, build_matrix  # noqa: E402
from preflight_facts import run as run_preflight  # noqa: E402
from source_ingest import SourceSelectionError, discover_source  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", type=Path)
    source_group.add_argument("--source-dir", type=Path,
                              help="recursively discover exactly one supported source file")
    parser.add_argument("--facts", required=True, type=Path)
    parser.add_argument("--out", required=False, type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--pdf-workers", type=int, default=2,
        help="parallel PDF conversion workers; use 1 for conservative serial WPS conversion",
    )
    parser.add_argument(
        "--wpscli", default=None,
        help="explicit WPS CLI path; resolved once before DOCX construction when omitted",
    )
    parser.add_argument(
        "--progress-file", type=Path, default=None,
        help="optional JSON checkpoint file updated at each build milestone",
    )
    parser.add_argument(
        "--docx-preview-dir", type=Path, default=None,
        help="optional directory receiving the four audited DOCX before PDF conversion",
    )
    parser.add_argument(
        "--preflight-only", action="store_true",
        help="report every facts/OpenSpec blocker without cloning templates or starting WPS",
    )
    parser.add_argument(
        "--preflight-report", type=Path, default=None,
        help="optional JSON path for the non-mutating preflight report",
    )
    args = parser.parse_args()
    if not args.preflight_only and args.out is None:
        parser.error("--out is required unless --preflight-only is used")

    def publish_progress(event: dict) -> None:
        payload = {"timestamp": time.time(), **event}
        print("MSDS_PROGRESS " + json.dumps(payload, ensure_ascii=False), flush=True)
        if args.progress_file is not None:
            args.progress_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.progress_file.with_name(
                args.progress_file.name + ".tmp"
            )
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, args.progress_file)

    try:
        selected = discover_source(args.source or args.source_dir, model=args.model)
        facts = json.loads(args.facts.read_text(encoding="utf-8"))
        if args.preflight_only:
            result = run_preflight(selected.original_path, args.facts, args.model)
            if args.preflight_report is not None:
                args.preflight_report.parent.mkdir(parents=True, exist_ok=True)
                temporary = args.preflight_report.with_name(
                    args.preflight_report.name + ".tmp"
                )
                temporary.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                os.replace(temporary, args.preflight_report)
            outcome = "PREFLIGHT_PASS" if result.get("status") == "ready" else "PREFLIGHT_BLOCKED"
            print(json.dumps({"outcome": outcome, **result},
                             ensure_ascii=False, indent=2))
            return 0 if result.get("status") == "ready" else 1
        report = build_matrix(source=selected.original_path, facts=facts, out_root=args.out,
                              model=args.model, revision=args.revision,
                              do_pdf=not args.no_pdf, timeout=args.timeout,
                              pdf_workers=args.pdf_workers, wpscli=args.wpscli,
                              progress_callback=publish_progress,
                              docx_preview_dir=args.docx_preview_dir)
    except (ReleaseBlocked, SourceSelectionError, FileNotFoundError, ValueError, RuntimeError) as blocked:
        print(json.dumps({"outcome": "RELEASE_FAIL", "blocker": str(blocked)},
                         ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"outcome": "RELEASE_PASS", "product": report["product"],
                      "docx": report["docx_count"], "pdf": report["pdf_count"],
                      "timing": report.get("timing"),
                      "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
