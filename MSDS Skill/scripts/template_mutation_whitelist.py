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

# Blank cells are not automatically writable.  These are explicit semantic
# input exceptions; the S8 recommendation is source-gated and is written only
# when the source provides a non-empty recommendation.
BLANK_VALUE_SLOTS = {(0, 1), (1, 1)}


class MutationViolation(RuntimeError):
    """Raised when a generator attempts to mutate outside the whitelist."""


@dataclass(frozen=True)
class TemplateSlot:
    table_index: int
    row_index: int
    cell_indices: tuple[int, ...]
    role: str
    authorized: bool


class TemplateSlotRegistry:
    """Runtime map of template-owned writable cells.

    It is built from the cloned template before clearing values.  Formatting,
    merges and labels remain in the DOCX; the registry only answers where data
    may go.
    """

    def __init__(self, slots: dict[tuple[int, int], TemplateSlot]):
        self.slots = slots

    @classmethod
    def from_document(cls, document) -> "TemplateSlotRegistry":
        slots = {}
        for table_index, table in enumerate(document.tables):
            for row_index, row in enumerate(table.rows):
                cells = unique_cells(row)
                if not cells or row_index == 0:
                    continue
                if table_index == 2 and row_index >= 4:
                    slots[table_index, row_index] = TemplateSlot(
                        table_index, row_index, tuple(range(len(cells))), "s3_data", True)
                    continue
                if table_index == 2 and row_index in {2, 3}:
                    continue
                if table_index == 7 and row_index >= 14:
                    slots[table_index, row_index] = TemplateSlot(
                        table_index, row_index, tuple(range(len(cells))), "s82_data", True)
                    continue
                if table_index == 7 and row_index == 1:
                    continue
                if table_index == 7 and row_index in {12, 13}:
                    continue
                if (
                    table_index == 10
                    and len(cells) >= 3
                    and cells[0].text.strip().startswith("11.7")
                ):
                    slots[table_index, row_index] = TemplateSlot(
                        table_index, row_index, (len(cells) - 1,), "endpoint_value", True)
                    continue
                if len(cells) == 1:
                    slots[table_index, row_index] = TemplateSlot(
                        table_index, row_index, (0,), "note", True)
                    continue
                payload = tuple(index for index, cell in enumerate(cells[1:], 1)
                                if cell.text.strip())
                if not payload and (table_index, row_index) in BLANK_VALUE_SLOTS:
                    payload = tuple(range(1, len(cells)))
                slots[table_index, row_index] = TemplateSlot(
                    table_index, row_index, payload, "field", bool(payload))
        return cls(slots)

    def writable_cells(self, table_index: int, row_index: int, row) -> list:
        slot = self.slots.get((table_index, row_index))
        if not slot or not slot.authorized:
            return []
        cells = unique_cells(row)
        return [cells[index] for index in slot.cell_indices if index < len(cells)]

    def is_authorized(self, table_index: int, row_index: int) -> bool:
        slot = self.slots.get((table_index, row_index))
        return bool(slot and slot.authorized and slot.cell_indices)


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


def english_body_cells(table_index: int, row_index: int, row) -> list:
    """Return the EN cells whose non-bold value runs use the body exemplar.

    The first cell is normally a locked sequence/label cell.  S3 and S8.2
    data rows are explicit all-value subtables; Section 11 keeps its middle
    sublabel locked and its final cell as the value cell.
    """
    cells = unique_cells(row)
    if not cells or row_index == 0:
        return []
    if table_index == 2:
        if row_index in {2, 3}:
            return []
        if row_index >= 4:
            return cells
    if table_index == 7:
        if row_index in {1, 12, 13}:
            return []
        if row_index >= 14:
            return cells
    if len(cells) == 1:
        return cells
    if table_index == 10 and len(cells) >= 3:
        return cells[-1:]
    return cells[1:]


def _clear_paragraph_content(paragraph) -> None:
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def normalize_value_text(text: str) -> str:
    """Remove synthetic slash separators before writing a value cell.

    `` / `` is a legacy joiner, not source content.  It can wrap as a lone
    slash in Word.  Preserve compact source slashes such as ``通风/排气`` and
    ``有/无``; only the synthetic spaced separator becomes a semantic line
    break.  Empty lines and a slash-only line are never customer-facing.
    """
    normalized = re.sub(r"[ \t\u3000]+[/／][ \t\u3000]+", "\n", str(text or ""))
    normalized = re.sub(r"(?m)^[ \t]*[/／][ \t]*", "", normalized)
    return "\n".join(
        line.rstrip() for line in normalized.splitlines()
        if line.strip() and line.strip() not in {"/", "／"}
    )


def _write_paragraph_content(paragraph, text: str) -> None:
    """Replace text while retaining the paragraph and first run properties."""
    text = normalize_value_text(text)
    old_rpr = None
    for run in paragraph.runs:
        if run._r.rPr is not None:
            old_rpr = copy.deepcopy(run._r.rPr)
            break
    if old_rpr is None and paragraph._p.pPr is not None:
        template_rpr = paragraph._p.pPr.find(qn("w:rPr"))
        if template_rpr is not None:
            old_rpr = copy.deepcopy(template_rpr)
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


def write_row_values(row, values: Sequence[object], *, table_index: int | None = None,
                     row_index: int | None = None,
                     registry: TemplateSlotRegistry | None = None) -> dict | None:
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
        targets = registry.writable_cells(table_index, row_index, row) if registry else cells
        if targets:
            content = "\n".join(values[:-1]) if len(values) > 1 and not values[-1].strip() else "\n".join(values)
            set_value_cell_text(targets[0], content)
        return

    payload = _payload_for_field_row(cells, values)
    if (
        table_index == 10
        and len(cells) >= 3
        and cells[0].text.strip().startswith("11.7")
    ):
        targets = registry.writable_cells(table_index, row_index, row) if registry else [cells[-1]]
        if targets:
            set_value_cell_text(targets[-1], values[-1] if values else "")
        return None
    if registry is not None:
        targets = registry.writable_cells(table_index, row_index, row)
        if not targets:
            if any(value.strip() for value in payload):
                return {"status": "skipped_blank_template_slot",
                        "table_index": table_index, "row_index": row_index}
            return None
        for cell, value in zip(targets, payload):
            set_value_cell_text(cell, value)
        return None
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
    entire workplace-component block is removed; an empty source slot is not
    customer-facing content and must not become a synthetic placeholder row.
    """
    if language not in S82_TOP_HEADERS:
        raise MutationViolation(f"unsupported S8.2 language: {language}")
    normalized = [tuple(str(value) for value in record[:4]) for record in records]
    if any(len(record) != 4 for record in normalized):
        raise MutationViolation("each S8.2 record must contain substance/basis/type/value")
    if not normalized:
        while len(table.rows) > 12:
            table._tbl.remove(table.rows[-1]._tr)
        return {
            "record_count": 0,
            "row_count": 0,
            "placeholder": False,
            "hidden": True,
        }
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
        "placeholder": False,
    }


def clear_value_cells(document, registry: TemplateSlotRegistry | None = None) -> None:
    """Clear only writable value cells, leaving all labels and headings intact."""
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            if row_index == 0:
                continue
            cells = unique_cells(row)
            if not cells:
                continue
            if registry is not None:
                for cell in registry.writable_cells(table_index, row_index, row):
                    set_value_cell_text(cell, "")
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


def _format_anchor(cell) -> tuple[str, str, str]:
    """Return the immutable formatting anchor for a writable cell.

    Value text may change and may use semantic line breaks, but the cell,
    first paragraph and first run must retain the fresh template's format.
    """
    tc_pr = _without_text(cell._tc.tcPr)
    paragraph = cell.paragraphs[0] if cell.paragraphs else None
    p_pr = _without_text(paragraph._p.pPr) if paragraph is not None else ""
    run = paragraph.runs[0] if paragraph is not None and paragraph.runs else None
    if run is not None and run._r.rPr is not None:
        r_pr = _without_text(run._r.rPr)
    elif paragraph is not None and paragraph._p.pPr is not None:
        r_pr = _without_text(paragraph._p.pPr.find(qn("w:rPr")))
    else:
        r_pr = ""
    return tc_pr, p_pr, r_pr


def _row_label(row) -> str:
    cells = unique_cells(row)
    return _canonical_locked_text(cells[0].text) if cells else ""


def _canonical_locked_text(text: str) -> str:
    """Compare stable labels while allowing approved source-faithful aliases."""
    text = re.sub(r"\t.*$", "", text)
    text = re.sub(r"^\s*\d+\.\d+\s*", "", text.strip())
    text = re.sub(r"^<SEQ>\s*", "", text)
    # The CN source heading is "标签要素" and the formal baseline uses the
    # longer "GHS标签要素".  The source-faithful alias is intentionally
    # limited to this Section 2 label and to the requested punctuation fix.
    text = re.sub(r"^(?:GHS)?标签要素[：:]?$", "标签要素", text)
    text = re.sub(r"^其他危害[：:]?$", "其他危害", text)
    return text


def _row_candidates(template_table, output_table, table_index, output_index, output_row):
    output_cells = unique_cells(output_row)
    if table_index == 2 and output_index >= 4:
        reference_index = min(output_index, len(template_table.rows) - 1)
        return [template_table.rows[reference_index]] if len(template_table.rows) > 4 else []
    if table_index == 7 and output_index >= 14:
        reference_index = min(output_index, len(template_table.rows) - 1)
        return [template_table.rows[reference_index]] if len(template_table.rows) > 14 else []
    if not output_cells:
        return []
    label = _row_label(output_row)
    candidates = [
        row for row in template_table.rows
        if len(unique_cells(row)) == len(output_cells)
        and (len(output_cells) == 1 or _row_label(row) == label)
    ]
    if not candidates and output_index < len(template_table.rows):
        candidate = template_table.rows[output_index]
        if len(unique_cells(candidate)) == len(output_cells):
            candidates = [candidate]
    return candidates


def _row_paging_signature(row) -> tuple[bool, bool]:
    """Return the Word row settings that control page crossing behavior."""
    tr_pr = row._tr.trPr
    if tr_pr is None:
        return False, False
    return (
        tr_pr.find(qn("w:cantSplit")) is not None,
        tr_pr.find(qn("w:tblHeader")) is not None,
    )


def audit_cross_page_contract(template, output) -> dict:
    """Verify table spanning and surviving row page-crossing settings.

    Word permits a table to continue on a later page by default.  ``w:cantSplit``
    is a row-level instruction: it prevents that row from splitting internally
    but does not prohibit the table from spanning pages.  The maintained formal
    templates require every row to be breakable; output rows must preserve that
    baseline after approved row omission.
    """
    errors: list[str] = []
    tables: list[dict] = []
    if len(template.tables) != len(output.tables):
        return {"errors": [
            f"table count changed for cross-page contract: {len(template.tables)} -> {len(output.tables)}"
        ], "tables": []}
    for table_index, (template_table, output_table) in enumerate(
        zip(template.tables, output.tables), start=1
    ):
        template_pr = template_table._tbl.tblPr
        output_pr = output_table._tbl.tblPr
        template_layout = template_pr.find(qn("w:tblLayout")) if template_pr is not None else None
        output_layout = output_pr.find(qn("w:tblLayout")) if output_pr is not None else None
        template_layout_type = template_layout.get(qn("w:type")) if template_layout is not None else None
        output_layout_type = output_layout.get(qn("w:type")) if output_layout is not None else None
        template_table_blocked = bool(
            template_pr is not None and template_pr.find(qn("w:cantSplit")) is not None
        )
        output_table_blocked = bool(
            output_pr is not None and output_pr.find(qn("w:cantSplit")) is not None
        )
        if template_layout_type != output_layout_type:
            errors.append(
                f"table {table_index} layout changed: {template_layout_type} -> {output_layout_type}"
            )
        if template_table_blocked != output_table_blocked:
            errors.append(f"table {table_index} cross-page permission changed")

        template_rows = [_row_paging_signature(row) for row in template_table.rows]
        output_rows = [_row_paging_signature(row) for row in output_table.rows]
        for row_index, (cant_split, _) in enumerate(template_rows):
            if cant_split:
                errors.append(
                    f"table {table_index} template row {row_index} blocks cross-page row breaking"
                )
        for row_index, (cant_split, _) in enumerate(output_rows):
            if cant_split:
                errors.append(
                    f"table {table_index} output row {row_index} blocks cross-page row breaking"
                )
        checked = 0
        for output_index, output_row in enumerate(output_table.rows):
            output_cells = unique_cells(output_row)
            # Several formal tables use consecutive one-cell rows.  Their
            # labels are intentionally writable note slots, so label matching
            # cannot distinguish them; approved omission keeps their physical
            # positions stable and the row index is the safer anchor.
            if (
                len(output_cells) == 1
                and output_index < len(template_table.rows)
                and len(unique_cells(template_table.rows[output_index])) == 1
            ):
                candidates = [template_table.rows[output_index]]
            else:
                candidates = _row_candidates(
                    template_table, output_table, table_index - 1, output_index, output_row
                )
            if not candidates:
                errors.append(
                    f"table {table_index} row {output_index} has no cross-page template anchor"
                )
                continue
            expected_signature = _row_paging_signature(candidates[0])
            actual_signature = _row_paging_signature(output_row)
            if expected_signature != actual_signature:
                errors.append(
                    f"table {table_index} row {output_index} cross-page row settings changed: "
                    f"{expected_signature} -> {actual_signature}"
                )
            checked += 1
        tables.append({
            "index": table_index,
            "template_layout": template_layout_type,
            "output_layout": output_layout_type,
            "template_allows_cross_page": not template_table_blocked,
            "output_allows_cross_page": not output_table_blocked,
            "template_row_breakable": sum(not cant for cant, _ in template_rows),
            "output_row_breakable": sum(not cant for cant, _ in output_rows),
            "template_row_cant_split": sum(cant for cant, _ in template_rows),
            "output_row_cant_split": sum(cant for cant, _ in output_rows),
            "template_all_rows_breakable": not any(cant for cant, _ in template_rows),
            "output_all_rows_breakable": not any(cant for cant, _ in output_rows),
            "surviving_rows_checked": checked,
        })
    return {"errors": errors, "tables": tables}


def _style_signature(element):
    """Compare OOXML formatting without document-part namespace noise."""
    if element is None:
        return ()
    return (
        element.tag,
        tuple(sorted((key, value) for key, value in element.attrib.items())),
        tuple(_style_signature(child) for child in element),
    )


def _format_layout_anchor(cell) -> tuple[str, str]:
    tc_pr = _without_text(cell._tc.tcPr)
    paragraph = cell.paragraphs[0] if cell.paragraphs else None
    p_pr = _without_text(paragraph._p.pPr) if paragraph is not None else ""
    return tc_pr, p_pr


def _value_run_rpr(run, paragraph):
    if run._r.rPr is not None:
        return run._r.rPr
    if paragraph._p.pPr is not None:
        return paragraph._p.pPr.find(qn("w:rPr"))
    return None


def compare_format_anchors(template, output, *, language: str = "cn",
                           approved_en_body_rpr=None) -> list[str]:
    """Audit all surviving cells against the fresh template's format anchors.

    This is deliberately separate from the locked-label audit: the latter
    protects labels, while this audit prevents a writable value cell from
    becoming a silently re-formatted paragraph. Approved row omissions and S3
    or S8.2 styled-row cloning are handled by candidate matching.
    """
    errors: list[str] = []
    if len(template.tables) != len(output.tables):
        return [f"table count changed: {len(template.tables)} -> {len(output.tables)}"]
    for table_index, (template_table, output_table) in enumerate(
        zip(template.tables, output.tables)
    ):
        if _without_text(template_table._tbl.tblPr) != _without_text(output_table._tbl.tblPr):
            errors.append(f"table properties changed: table {table_index}")
        if _without_text(template_table._tbl.tblGrid) != _without_text(output_table._tbl.tblGrid):
            errors.append(f"table grid changed: table {table_index}")
    for table_index, output_table in enumerate(output.tables):
        template_table = template.tables[table_index]
        for output_index, output_row in enumerate(output_table.rows):
            candidates = _row_candidates(template_table, output_table, table_index,
                                          output_index, output_row)
            if not candidates:
                errors.append(f"no template format anchor: table {table_index} row {output_index}")
                continue
            output_cells = unique_cells(output_row)
            matched = False
            body_cells = english_body_cells(table_index, output_index, output_row) \
                if language == "en" else []
            body_tc_ids = {hash(cell._tc) for cell in body_cells}
            for candidate in candidates:
                candidate_cells = unique_cells(candidate)
                if len(candidate_cells) != len(output_cells):
                    continue
                if _without_text(output_row._tr.trPr) != _without_text(candidate._tr.trPr):
                    continue
                cell_formats_match = True
                for expected_cell, actual_cell in zip(candidate_cells, output_cells):
                    if hash(actual_cell._tc) in body_tc_ids:
                        if _format_layout_anchor(expected_cell) != _format_layout_anchor(actual_cell):
                            cell_formats_match = False
                            break
                    elif _format_anchor(expected_cell) != _format_anchor(actual_cell):
                        cell_formats_match = False
                        break
                if cell_formats_match:
                    matched = True
                    break
            if not matched:
                errors.append(f"template format anchor changed: table {table_index} row {output_index}")
                continue
            if language == "en" and approved_en_body_rpr is not None:
                for cell in body_cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            if run.text.strip() and not run.bold:
                                actual_rpr = _value_run_rpr(run, paragraph)
                                if (_style_signature(actual_rpr)
                                        != _style_signature(approved_en_body_rpr)):
                                    errors.append(
                                        f"EN body value format is not the approved exemplar: "
                                        f"table {table_index} row {output_index}"
                                    )
                                    break

    for section_index, (template_section, output_section) in enumerate(
        zip(template.sections, output.sections)
    ):
        if _without_text(template_section._sectPr) != _without_text(output_section._sectPr):
            errors.append(f"section properties changed: section {section_index}")
        for role in ("header", "footer"):
            template_tables = getattr(template_section, role).tables
            output_tables = getattr(output_section, role).tables
            if len(template_tables) != len(output_tables):
                errors.append(f"{role} table count changed: section {section_index}")
                continue
            for table_index, output_table in enumerate(output_tables):
                template_table = template_tables[table_index]
                for row_index, output_row in enumerate(output_table.rows):
                    if row_index >= len(template_table.rows):
                        errors.append(f"{role} row added: section {section_index} table {table_index}")
                        continue
                    expected_cells = unique_cells(template_table.rows[row_index])
                    actual_cells = unique_cells(output_row)
                    if len(expected_cells) != len(actual_cells) or any(
                        _format_anchor(expected) != _format_anchor(actual)
                        for expected, actual in zip(expected_cells, actual_cells)
                    ):
                        errors.append(f"{role} format changed: section {section_index} table {table_index} row {row_index}")
    return errors


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
            logical = _canonical_locked_text(label)
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
            expected_text = _canonical_locked_text(expected_text)
            actual_text = _canonical_locked_text(actual_text)
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
    "english_body_cells",
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
    "compare_format_anchors",
    "audit_cross_page_contract",
]
