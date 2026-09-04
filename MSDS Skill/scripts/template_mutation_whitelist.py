"""Controlled mutation boundary for the unified MSDS templates.

The template is an executable document skeleton.  This module centralizes the
small set of mutations that generation is allowed to make:

* ordinary fields write only to value cells;
* S3 data rows write name/CAS/concentration to the three data cells;
* S8.2 top-level data rows write substance/basis/type/value to the four data
  cells, with the template example rows cleared per the data/placeholder rule;
* one-cell note slots may be replaced as a whole slot;
* S2/S9 may remove an explicitly missing row and change only the visible
  sequence prefix afterwards;
* no operation may rewrite a sequence/label cell as a generic value write.

The functions intentionally operate on the existing OOXML nodes.  They do not
rebuild tables or normalize the formatting of locked cells.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from docx.oxml.ns import qn


S82_TOP_HEADERS = {
    "zh": ("物质", "依据", "类型", "数值"),
    "en": ("Substance", "Basis", "Type", "Value"),
}

S82_CHILD_HEADERS = S82_TOP_HEADERS

S82_MISSING = {
    "zh": "无数据",
    "en": "No data available",
}


class MutationViolation(RuntimeError):
    """Raised when a generator attempts to mutate outside the whitelist."""


def unique_cells(row) -> list:
    """Return physical cells once, including stable handling of merged cells."""
    seen: set[int] = set()
    result = []
    for cell in row.cells:
        key = hash(cell._tc)
        if key not in seen:
            seen.add(key)
            result.append(cell)
    return result


def _clear_paragraph_content(paragraph) -> None:
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _write_paragraph_content(paragraph, text: str) -> None:
    """Replace text while retaining the paragraph and first run properties."""
    old_rpr = None
    for run in paragraph.runs:
        if run._r.rPr is not None:
            old_rpr = copy.deepcopy(run._r.rPr)
            break
    _clear_paragraph_content(paragraph)
    run = paragraph._p.makeelement(qn("w:r"), {})
    if old_rpr is not None:
        run.append(old_rpr)
    for index, line in enumerate(str(text).split("\n")):
        if index:
            run.append(paragraph._p.makeelement(qn("w:br"), {}))
        text_node = paragraph._p.makeelement(qn("w:t"), {})
        text_node.text = line
        if line and (line[0].isspace() or line[-1].isspace()):
            text_node.set(qn("xml:space"), "preserve")
        run.append(text_node)
    paragraph._p.append(run)


def _replace_leading_pattern_in_runs(paragraph, pattern: str, replacement: str) -> str:
    """Replace a leading pattern without collapsing the existing run tree."""
    current = paragraph.text
    match = re.match(pattern, current)
    if not match:
        return current
    old_prefix = match.group(0)
    new_prefix = re.sub(pattern, replacement, old_prefix, count=1)
    start, end = match.span()
    spans = []
    cursor = 0
    for run in paragraph.runs:
        spans.append((run, cursor, cursor + len(run.text)))
        cursor += len(run.text)
    overlapping = [item for item in spans if item[2] > start and item[1] < end]
    if not overlapping:
        return current
    first_run, first_start, _ = overlapping[0]
    last_run, _, last_end = overlapping[-1]
    if first_run is last_run:
        local_start = start - first_start
        local_end = end - first_start
        first_run.text = first_run.text[:local_start] + new_prefix + first_run.text[local_end:]
    else:
        first_local_start = start - first_start
        first_run.text = first_run.text[:first_local_start] + new_prefix
        for run, _, _ in overlapping[1:-1]:
            run.text = ""
        last_local_end = end - (last_end - len(last_run.text))
        last_run.text = last_run.text[last_local_end:]
    return paragraph.text


def set_value_cell_text(cell, text: str) -> None:
    """Write only a pre-authorized value/note cell."""
    if not cell.paragraphs:
        raise MutationViolation("value cell has no template paragraph")
    _write_paragraph_content(cell.paragraphs[0], text)
    for paragraph in cell.paragraphs[1:]:
        paragraph._element.getparent().remove(paragraph._element)


def set_sequence_prefix(cell, section: int, item: int) -> str:
    """Change only an approved visible sequence prefix in an existing cell."""
    if not cell.paragraphs:
        return ""
    paragraph = cell.paragraphs[0]
    current = paragraph.text
    pattern = rf"^(\s*){section}\.\d+(\b)"
    return _replace_leading_pattern_in_runs(
        paragraph, pattern, rf"\g<1>{section}.{item}\g<2>"
    )


def _payload_for_field_row(cells: list, values: Sequence[object]) -> list[str]:
    values = [str(value) for value in values]
    if len(cells) == 2 and len(values) > 2:
        return ["\n".join(value for value in values[1:] if value.strip())]
    return values[1:]


def write_row_values(row, values: Sequence[object], *, table_index: int | None = None, row_index: int | None = None) -> None:
    """Write a semantic row through the mutation whitelist.

    ``values`` keeps the historical source-fact shape, where the first item is
    a source label.  For normal field rows that first item is deliberately
    ignored: the label already belongs to the template.  Subtable data rows
    are the explicit exception because every cell is data, not a label.
    """
    cells = unique_cells(row)
    if not cells:
        raise MutationViolation("attempted to write a row without cells")
    values = [str(value) for value in values]

    if table_index == 2 and row_index in {2, 3}:
        # S3 parent row and the three-column table header are template-owned.
        return

    if table_index == 7 and row_index == 1:
        # Feishu S8.1 is a section parent node.  The supplied template uses a
        # single merged cell here, so it must not be mistaken for a writable
        # one-cell note slot.
        return

    if table_index == 7 and row_index is not None and row_index >= 12:
        # The formal S8.2 parent/header/data rows are owned by
        # write_s82_top_rows; generic row writes must not touch them.
        raise MutationViolation("S8.2 top-level rows must be written through write_s82_top_rows")

    # S3 component data rows: name, CAS, concentration are all writable.
    if table_index == 2 and row_index is not None and row_index >= 4:
        if len(cells) != 3 or len(values) < 3:
            raise MutationViolation("S3 data row must contain exactly name/CAS/concentration")
        for cell, value in zip(cells, values[:3]):
            set_value_cell_text(cell, value)
        return

    # One-cell fixed semantic note slots are expressly writable as a slot.
    if len(cells) == 1:
        set_value_cell_text(cells[0], "\n".join(values))
        return

    payload = _payload_for_field_row(cells, values)
    for offset, value in enumerate(payload, start=1):
        if offset >= len(cells):
            break
        set_value_cell_text(cells[offset], value)


def write_s82_top_rows(table, records: Iterable[Sequence[object]], language: str) -> dict:
    """Write verified S8.2 control-parameter records into the formal top-level rows.

    The one-cell parent row (physical row 12) and the four-column header row
    (physical row 13) belong to the template.  Data rows (physical row 14 on)
    are writable: extra rows are cloned from the existing styled data row, and
    the template example rows are cleared.  With no verified records the
    second example row is removed and the single remaining data row carries
    the exact missing-data placeholder in the value column, so besides the
    header only one result row remains.
    """
    if language not in S82_TOP_HEADERS:
        raise MutationViolation(f"unsupported S8.2 language: {language}")
    if len(table.rows) < 16:
        raise MutationViolation("S8.2 formal layout requires 16 Section-8 rows")
    parent = unique_cells(table.rows[12])
    if len(parent) != 1:
        raise MutationViolation("S8.2 parent must be a one-cell row")
    header = tuple(cell.text.strip() for cell in unique_cells(table.rows[13]))
    if header != S82_TOP_HEADERS[language]:
        raise MutationViolation(
            f"S8.2 header mismatch: expected {S82_TOP_HEADERS[language]}, found {header}"
        )
    normalized = [tuple(str(value) for value in record[:4]) for record in records]
    if any(len(record) != 4 for record in normalized):
        raise MutationViolation("each S8.2 record must contain substance/basis/type/value")
    if not normalized:
        normalized = [("", "", "", S82_MISSING[language])]
    while len(table.rows) < 14 + len(normalized):
        table._tbl.append(copy.deepcopy(table.rows[14]._tr))
    while len(table.rows) > 14 + len(normalized):
        table._tbl.remove(table.rows[-1]._tr)
    for position, row in enumerate(list(table.rows)[14:14 + len(normalized)]):
        cells = unique_cells(row)
        if len(cells) != 4:
            raise MutationViolation("S8.2 data row must have four cells")
        for target, value in zip(cells, normalized[position]):
            set_value_cell_text(target, value)
    return {
        "record_count": len(records),
        "row_count": len(normalized),
        "placeholder": not bool(records),
    }


def clear_value_cells(document) -> None:
    """Clear only writable value cells, leaving all labels and headings intact."""
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            if row_index == 0:
                continue
            cells = unique_cells(row)
            if not cells:
                continue
            if table_index == 2 and row_index in {2, 3}:
                # S3 parent row and three-column table header are locked.
                continue
            if table_index == 7 and row_index == 1:
                # S8.1 is a locked parent node, not a value slot.
                continue
            if table_index == 7 and row_index in {12, 13}:
                # S8.2 parent row and four-column header are locked.
                continue
            if table_index == 7 and row_index >= 14:
                for cell in cells:
                    set_value_cell_text(cell, "")
                continue
            if table_index == 2 and row_index >= 4:
                for cell in cells:
                    set_value_cell_text(cell, "")
                continue
            if len(cells) == 1:
                set_value_cell_text(cells[0], "")
            else:
                for cell in cells[1:]:
                    set_value_cell_text(cell, "")


@dataclass(frozen=True)
class LockedCellSnapshot:
    table_index: int
    row_key: tuple[str, int]
    cell_role: str
    tc_pr: str
    paragraph_props: tuple[str, ...]
    run_props: tuple[tuple[str, ...], ...]
    text: str


def _without_text(element) -> str:
    if element is None:
        return ""
    clone = copy.deepcopy(element)
    for text_node in clone.xpath(".//w:t"):
        text_node.text = ""
    return clone.xml


def _cell_style_snapshot(cell) -> tuple[str, tuple[str, ...], tuple[tuple[str, ...], ...]]:
    tc_pr = _without_text(cell._tc.tcPr)
    p_props = tuple(_without_text(paragraph._p.pPr) for paragraph in cell.paragraphs)
    r_props = tuple(
        tuple(_without_text(run._r.rPr) for run in paragraph.runs)
        for paragraph in cell.paragraphs
    )
    return tc_pr, p_props, r_props


def locked_cell_snapshots(document) -> list[LockedCellSnapshot]:
    """Snapshot sequence/label cells and all locked table headers.

    Normal field rows lock the first physical cell.  S3/S8.2 table headers
    lock every header cell; S3 data rows are explicitly writable data rows.
    The row key uses label text with the numeric prefix removed plus an
    occurrence number, allowing S2/S9 approved row omission without confusing
    later rows.
    """
    snapshots: list[LockedCellSnapshot] = []
    for table_index, table in enumerate(document.tables):
        occurrence: dict[str, int] = {}
        for row_index, row in enumerate(table.rows):
            cells = unique_cells(row)
            if not cells:
                continue
            label = cells[0].text.strip()
            logical = re.sub(r"^\s*\d+\.\d+\s*", "", label)
            logical = re.sub(r"\s+", " ", logical)
            occurrence[logical] = occurrence.get(logical, 0) + 1
            row_key = (logical, occurrence[logical])
            if row_index == 0:
                protected = cells
            elif table_index == 2 and row_index in {2, 3}:
                protected = cells
            elif table_index == 2 and row_index >= 4:
                protected = []
            elif table_index == 7 and row_index == 12:
                # S8.2 locked one-cell parent row.
                protected = cells
            elif table_index == 7 and row_index == 13:
                # S8.2 locked four-column header row.
                protected = cells
            elif table_index == 7 and row_index >= 14:
                # S8.2 writable top-level data rows.
                protected = []
            elif len(cells) == 1:
                # Feishu marks S11/S12/S13/S15/S16 note slots as whole-slot
                # writable content, not as a sequence/label column.
                protected = []
            else:
                protected = cells[:1]
            for cell_index, cell in enumerate(protected):
                tc_pr, p_props, r_props = _cell_style_snapshot(cell)
                role = "sequence_label" if cell_index == 0 else "sub_label_or_header"
                snapshots.append(LockedCellSnapshot(
                    table_index, row_key, role, tc_pr, p_props, r_props, cell.text,
                ))
    return snapshots


def compare_locked_skeleton(template, output) -> list[str]:
    """Return release-blocking differences in locked cells."""
    expected = locked_cell_snapshots(template)
    actual = locked_cell_snapshots(output)
    # Match on the stable label body, not occurrence index.  S2/S9 are
    # allowed to remove missing rows, and repeated children (for example
    # multiple 2.8 rows) must not make later rows look like format drift.
    expected_map: dict[tuple[int, str, str], list[LockedCellSnapshot]] = {}
    for snapshot in expected:
        expected_map.setdefault(
            (snapshot.table_index, snapshot.row_key[0], snapshot.cell_role),
            [],
        ).append(snapshot)
    errors: list[str] = []
    for actual_item in actual:
        key = (actual_item.table_index, actual_item.row_key[0], actual_item.cell_role)
        candidates = expected_map.get(key)
        if not candidates:
            if actual_item.cell_role == "sequence_label":
                errors.append(f"locked label text changed or is not in template skeleton: {key}")
            else:
                errors.append(f"locked cell is not in template skeleton: {key}")
            continue
        expected_item = next(
            (candidate for candidate in candidates
             if candidate.tc_pr == actual_item.tc_pr
             and candidate.paragraph_props == actual_item.paragraph_props
             and candidate.run_props == actual_item.run_props),
            candidates[0],
        )
        if expected_item.tc_pr != actual_item.tc_pr:
            errors.append(f"locked cell tcPr changed: {key}")
        if expected_item.paragraph_props != actual_item.paragraph_props:
            errors.append(f"locked cell paragraph properties changed: {key}")
        if expected_item.run_props != actual_item.run_props:
            errors.append(f"locked cell run properties changed: {key}")
        if expected_item.cell_role == "sequence_label":
            expected_text = re.sub(r"^\s*\d+\.\d+", "<SEQ>", expected_item.text)
            actual_text = re.sub(r"^\s*\d+\.\d+", "<SEQ>", actual_item.text)
            if expected_text != actual_text:
                errors.append(f"locked label text changed: {key}")
    # The formal S8.2 header row is a locked top-level structure.  Its text is
    # checked explicitly here because data-row writes share the same table;
    # formatting is covered by locked_cell_snapshots above.  Nested child
    # tables, when present in older baselines, are still checked below for
    # rollback/audit compatibility.
    if len(template.tables) > 7 and len(output.tables) > 7:
        template_t7, output_t7 = template.tables[7], output.tables[7]
        if len(template_t7.rows) > 13 and len(output_t7.rows) > 13:
            for expected_cell, actual_cell in zip(
                unique_cells(template_t7.rows[13]), unique_cells(output_t7.rows[13])
            ):
                if expected_cell.text != actual_cell.text:
                    errors.append("locked S8.2 header text changed: table 7 row 13")
                elif _cell_style_snapshot(expected_cell) != _cell_style_snapshot(actual_cell):
                    errors.append("locked S8.2 header formatting changed: table 7 row 13")
    for table_index, template_table in enumerate(template.tables):
        if table_index >= len(output.tables):
            continue
        output_table = output.tables[table_index]
        for row_index, template_row in enumerate(template_table.rows):
            if row_index >= len(output_table.rows):
                continue
            for template_cell, output_cell in zip(unique_cells(template_row), unique_cells(output_table.rows[row_index])):
                template_children = list(template_cell.tables)
                output_children = list(output_cell.tables)
                if not template_children:
                    continue
                if len(template_children) != len(output_children):
                    errors.append(f"locked child-table count changed: table {table_index} row {row_index}")
                    continue
                for child_index, (expected_child, actual_child) in enumerate(zip(template_children, output_children)):
                    if len(expected_child.rows) == 0 or len(actual_child.rows) == 0:
                        errors.append(f"locked child-table header missing: table {table_index} row {row_index}")
                        continue
                    expected_header = unique_cells(expected_child.rows[0])
                    actual_header = unique_cells(actual_child.rows[0])
                    if len(expected_header) != len(actual_header):
                        errors.append(f"locked child-table header width changed: table {table_index} row {row_index}")
                        continue
                    for header_cell, actual_header_cell in zip(expected_header, actual_header):
                        if header_cell.text != actual_header_cell.text:
                            errors.append(f"locked child-table header text changed: table {table_index} row {row_index}")
                        expected_style = _cell_style_snapshot(header_cell)
                        actual_style = _cell_style_snapshot(actual_header_cell)
                        if expected_style != actual_style:
                            errors.append(f"locked child-table header formatting changed: table {table_index} row {row_index}")
    return errors


__all__ = [
    "MutationViolation",
    "LockedCellSnapshot",
    "unique_cells",
    "set_value_cell_text",
    "set_sequence_prefix",
    "write_row_values",
    "write_s82_top_rows",
    "S82_TOP_HEADERS",
    "S82_CHILD_HEADERS",
    "S82_MISSING",
    "clear_value_cells",
    "locked_cell_snapshots",
    "compare_locked_skeleton",
]
