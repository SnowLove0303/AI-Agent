#!/usr/bin/env python3
"""OpenSpec release audit for the agent-executed overwrite contract.

This is an additional fail-closed gate over the existing template whitelist.
It catches the practical failures that a visually plausible DOCX can otherwise
hide: empty value rows, empty paragraphs, artificial spacing and numbering
that was not checked after omission.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document

from audit_template_mutation_whitelist import audit as audit_template
from audit_whitespace import run as audit_whitespace
from renumber_visible_items import audit as audit_numbering
from renumber_visible_items import collect as collect_numbered_items
from section2_hp_policy import is_missing_data_value
from template_mutation_whitelist import composite_value_text, is_s28_row, unique_cells
from agent_execution_contract import load_spec


def _label_body(text: str) -> str:
    text = re.sub(r"\t.*$", "", str(text or ""))
    text = re.sub(r"^\s*\d+\.\d+\s*", "", text)
    return re.sub(r"\s+", " ", text).strip().rstrip("：:")


def _is_allowed_blank_value(table_index: int, row_index: int, label: str) -> bool:
    body = _label_body(label).casefold()
    if table_index == 0 and body in {"产品名称", "product name"}:
        return True
    if table_index == 0 and body in {"供应商信息", "supplier information"}:
        return True
    if table_index == 7 and body in {"建议", "recommendation"}:
        return True
    if table_index == 14 and body.startswith(
        ("相关安全、健康和环保法律法规", "relevant safety, health and environmental regulations")
    ):
        return True
    if table_index == 2 and row_index == 2:
        return True
    if table_index == 7 and row_index in {1, 12, 13}:
        return True
    return False


def audit_empty_value_rows(document, context=None) -> list[dict]:
    """Reject visible label rows whose writable value area is empty."""
    problems: list[dict] = []
    if context is None:
        rows = (
            (table_index, row_index, row, unique_cells(row))
            for table_index, table in enumerate(document.tables)
            for row_index, row in enumerate(table.rows)
        )
    else:
        rows = (
            (record.table_index, record.row_index, record.row, record.cells)
            for record in context.rows()
        )
    for table_index, row_index, row, cells in rows:
            if row_index == 0:
                continue
            if not cells:
                problems.append({"type": "row_without_cells", "table": table_index, "row": row_index})
                continue
            label = cells[0].text.strip()
            if len(cells) == 1:
                if not label:
                    problems.append({"type": "empty_structural_row", "table": table_index, "row": row_index})
                continue
            if table_index == 2 and row_index == 3:
                # S3's three-column header is structure, not a value row.
                continue
            if table_index == 1 and is_s28_row(table_index, row):
                # The route prefix is template-owned.  Audit only the value
                # tail so a prefix-only retained row is correctly blocking.
                values = [composite_value_text(row).strip()]
            elif table_index == 7 and row_index >= 12:
                # S8.2 parent/header/data rows are independently handled by
                # write_s82_top_rows; a retained data row must have all values.
                values = [cell.text.strip() for cell in cells]
            elif table_index == 10 and re.match(r"^\s*11\.7\b", label):
                values = [cells[-1].text.strip()]
            else:
                values = [cell.text.strip() for cell in cells[1:]]
            if not any(values) and not _is_allowed_blank_value(table_index, row_index, label):
                problems.append({
                    "type": "empty_value_row_remains",
                    "table": table_index,
                    "row": row_index,
                    "label": label,
                })
                continue
            joined = " ".join(value for value in values if value)
            if joined and is_missing_data_value(joined):
                # S2 other-hazards and source-backed Section 11 endpoints have
                # explicit missing-data exceptions in the maintained spec.
                allow_missing = (
                    table_index == 1 and _label_body(label).casefold() in {"其他危害", "other hazards"}
                ) or table_index == 10
                if not allow_missing:
                    problems.append({
                        "type": "bare_missing_data_value_row",
                        "table": table_index,
                        "row": row_index,
                        "label": label,
                    })
    return problems


def audit_value_whitespace(document, context=None) -> list[dict]:
    """Reject blank lines and fake spacing in non-locked value content."""
    if context is not None:
        return context.value_whitespace()
    problems: list[dict] = []
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            cells = unique_cells(row)
            if len(cells) == 1:
                value_cells = list(enumerate(cells))
            elif table_index == 2 and row_index >= 4:
                value_cells = list(enumerate(cells))
            elif table_index == 7 and row_index >= 14:
                value_cells = list(enumerate(cells))
            elif table_index == 10 and len(cells) >= 3:
                value_cells = [(len(cells) - 1, cells[-1])]
            else:
                value_cells = list(enumerate(cells[1:], start=1))
            for cell_index, cell in value_cells:
                for paragraph_index, paragraph in enumerate(cell.paragraphs):
                    text = paragraph.text
                    if "\n\n" in text or "\r\n\r\n" in text:
                        problems.append({
                            "type": "blank_line_in_value",
                            "table": table_index,
                            "row": row_index,
                            "cell": cell_index,
                            "paragraph": paragraph_index,
                        })
                    if re.search(r" {3,}|\u3000{2,}", text):
                        problems.append({
                            "type": "artificial_spacing_in_value",
                            "table": table_index,
                            "row": row_index,
                            "cell": cell_index,
                            "paragraph": paragraph_index,
                        })
    return problems


def audit(template_path: Path, output_path: Path, *, language: str = "cn",
          template=None, output=None, context=None) -> dict:
    template = template or Document(str(template_path))
    output = output or Document(str(output_path))
    base = audit_template(template_path, output_path, template=template,
                          output=output, language=language, context=context)
    errors = list(base.get("errors", []))
    empty_rows = audit_empty_value_rows(output, context=context)
    value_whitespace = audit_value_whitespace(output, context=context)
    whitespace = audit_whitespace(str(output_path), document=output, context=context)
    whitespace_issues = whitespace.get("issues", [])
    numbering_items = context.numbering_items() if context is not None else collect_numbered_items(output)
    numbering = audit_numbering(numbering_items)
    for item in empty_rows:
        errors.append("OpenSpec: " + json.dumps(item, ensure_ascii=False, sort_keys=True))
    for item in value_whitespace:
        errors.append("OpenSpec: " + json.dumps(item, ensure_ascii=False, sort_keys=True))
    for item in whitespace_issues:
        errors.append("OpenSpec whitespace: " + json.dumps(item, ensure_ascii=False, sort_keys=True))
    errors.extend("OpenSpec numbering: " + item for item in numbering)
    spec = load_spec()
    return {
        "spec_id": spec["spec_id"],
        "spec_version": spec["version"],
        "template": str(template_path),
        "output": str(output_path),
        "language": language,
        "errors": errors,
        "empty_value_rows": empty_rows,
        "value_whitespace": value_whitespace,
        "whitespace": whitespace,
        "numbering": numbering,
        "template_audit": base,
        "status": "passed" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, nargs="+")
    parser.add_argument("--language", choices=("cn", "en"), default="cn")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    results = [audit(args.template, path, language=args.language) for path in args.output]
    rendered = json.dumps(results, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    return 0 if all(item["status"] == "passed" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
