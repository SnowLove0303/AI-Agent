#!/usr/bin/env python3
"""Audit a DOCX against the pinned template geometry snapshot."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def geometry_view(data):
    def table_view(t):
        return {
            "row_count": t["row_count"],
            "column_count": t["column_count"],
            "unique_cell_counts": t["unique_cell_counts"],
            "tblPr_hash": t["tblPr_hash"],
            "tblGrid_hash": t["tblGrid_hash"],
            "grid_widths_dxa": t["grid_widths_dxa"],
            "rows": [
                {
                    "trPr_hash": r["trPr_hash"],
                    "cell_count": r["cell_count"],
                    "cells": [
                        {
                            "tcPr_hash": c["tcPr_hash"],
                            "tcW": c["tcW"],
                            "tcW_type": c["tcW_type"],
                            "gridSpan": c["gridSpan"],
                            "vMerge": c["vMerge"],
                            "paragraphs": [
                                {
                                    "pPr_hash": p["pPr_hash"],
                                    "runs": [r["rPr_hash"] for r in p["runs"]],
                                }
                                for p in c["paragraphs"]
                            ],
                        }
                        for c in r["cells"]
                    ],
                }
                for r in t["rows"]
            ],
        }

    return {
        "tables": [table_view(t) for t in data["tables"]],
        "section_count": len(data["sections"]),
        "header_footer_table_geometry": [
            {
                role: [table_view(t) for t in section[role]["tables"]]
                for role in ("header", "footer")
            }
            for section in data["sections"]
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    script = Path(__file__).with_name("snapshot_template_geometry.py")
    with tempfile.TemporaryDirectory() as tmp:
        generated = Path(tmp) / "snapshot.json"
        subprocess.run([sys.executable, str(script), str(args.docx), str(generated)], check=True)
        actual = json.loads(generated.read_text(encoding="utf-8"))
    expected = json.loads(args.snapshot.read_text(encoding="utf-8"))
    passed = geometry_view(actual) == geometry_view(expected)
    print(json.dumps({"pass": passed, "template_sha256": actual["source_sha256"], "snapshot": str(args.snapshot)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
