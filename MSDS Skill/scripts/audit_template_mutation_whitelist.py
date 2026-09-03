#!/usr/bin/env python3
"""Release-blocking audit for the template mutation whitelist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx import Document

from template_mutation_whitelist import compare_locked_skeleton


def audit(template_path: Path, output_path: Path) -> dict:
    template = Document(str(template_path))
    output = Document(str(output_path))
    errors = compare_locked_skeleton(template, output)
    result = {
        "template": str(template_path),
        "output": str(output_path),
        "table_count": len(output.tables),
        "errors": errors,
        "status": "passed" if not errors else "failed",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, nargs="+")
    args = parser.parse_args()
    results = [audit(args.template, output) for output in args.output]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "passed" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
