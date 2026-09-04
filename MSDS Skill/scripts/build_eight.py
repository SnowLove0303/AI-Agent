#!/usr/bin/env python3
"""One-command eight-format build for the unified MSDS skill (v3.14.2).

Business flow::

    source.docx --extract--> draft --review--> approved model JSON
        --build_eight--> 4 DOCX + gates + 4 PDF + matrix-report.json

The approved model JSON holds the *standardized* facts; ``en`` must be a
reviewed translation OF that model (see ``draft_en_facts.py``).  Any gate
failure stops the whole release before any PDF is converted.

Usage::

    python scripts/build_eight.py --source SRC.docx --facts MODEL.json
        --out DIR [--model MODEL] [--revision DATE] [--no-pdf] [--timeout S]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msds_pipeline import ReleaseBlocked, build_matrix  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--facts", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not args.source.is_file():
        raise FileNotFoundError(args.source)
    facts = json.loads(args.facts.read_text(encoding="utf-8"))
    try:
        report = build_matrix(source=args.source, facts=facts, out_root=args.out,
                              model=args.model, revision=args.revision,
                              do_pdf=not args.no_pdf, timeout=args.timeout)
    except ReleaseBlocked as blocked:
        print(json.dumps({"outcome": "RELEASE_FAIL", "blocker": str(blocked)},
                         ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"outcome": "RELEASE_PASS", "product": report["product"],
                      "docx": report["docx_count"], "pdf": report["pdf_count"],
                      "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
