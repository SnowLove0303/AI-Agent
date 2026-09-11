#!/usr/bin/env python3
"""Mechanical source-fact extractor for the unified MSDS pipeline (v3.19.0).

Business role: the overwrite core is *extract -> standardize (CN) -> render
CN -> translate EN from the standardized model*.  This module does the first
mechanical step only: it reads a nonstandard source DOCX and produces a
standardized CN semantic draft plus an explicit human/agent review queue.

Mechanical (deterministic, auditable) vs review (judgment needed):

* AUTO: S1 supplier block verbatim; S3 component rows split into
  name/CAS/content; S4-S7 label/value pairs verbatim; S9 property rows
  verbatim with missing-sentinel marking; S10/S12-S16 endpoint rows verbatim;
  S2 H/P coded-statement segmentation (regex); embedded-image inventory.
* REVIEW: model fallback to filename; S3 multi-line misalignment; label
  ingredient phrasing variants; S2 per-route synthesis; S9 ambiguous
  missing-vs-applicability wording; S11 endpoint mapping (incl. the
  主要粘膜刺激性 alias), multi-study splits, combined 生殖毒性 splits,
  STOT/overall synthesis; any table whose row count differs from the
  expected nonstandard shape.

Output JSON shape (sections mirror the generator fact shape)::

    {"model": ..., "source_sha256": ...,
     "sections": {"s1": [[label, value], ...], ...},
     "review": [{"section": ..., "issue": ..., "detail": ...}],
     "source_mapping": {"status": "needs-review", "items": [...]},
     "source_coverage": {"status": "ready", "source_units": [...]},
     "fact_ledger": [{"fact_id": ..., "source_locator": ...}],
     "output_traceability": {"status": "needs-review", "items": [...]},
     "images": [{"name": ..., "size": ...}]}

Values use ``\\n``-joined logical lines; missing sentinels are kept verbatim
(the build stage applies the omission policy).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from section2_hp_policy import _CODE_RE, is_missing_data_value, split_coded_statements  # noqa: E402
from agent_execution_contract import blank_execution_contract  # noqa: E402
from source_interpretation_contract import blank_output_traceability  # noqa: E402
from source_ingest import (  # noqa: E402
    discover_source,
    prepare_source,
    require_section_extraction,
    SourceSelectionError,
)

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None


MODEL_RE = re.compile(r"\b([A-Z]{1,4}-\d{3,4}[A-Z0-9]*)\b")
CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
LABEL_INGREDIENT_RE = re.compile(r"(列在标签上|有害成分|label)")
SIGNAL_RE = re.compile(r"信号词\s*[：:]\s*(.*)")
CATEGORY_RE = re.compile(r"(类别\s*\S*|\(H\d+[a-zA-Z]*\))")
MISSING_HINT_RE = re.compile(r"(无适用资料|无数据资料|暂无|未提供|不详)")
OTHER_HAZARDS_RE = re.compile(
    r"^\s*2\.3\s*(?:其他危险|其他危害|other hazards)\s*[:：]?\s*(.*)$",
    re.I,
)
PROTECTIVE_MATERIAL_RE = re.compile(
    r"^\s*(氟化橡胶\s*[–-]\s*FKM|丁基橡胶\s*[–-]\s*IIR|丁腈橡胶\s*[–-]\s*NBR)\s*[:：]\s*(.+?)\s*$",
    re.I,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_cells(row):
    out, seen = [], set()
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            out.append(cell)
    return out


def _clean(text: str) -> str:
    return re.sub(r"[\t\u3000]+", " ", text or "").strip()


def cell_lines(cell) -> list[str]:
    parts = []
    for paragraph in cell.paragraphs:
        text = _clean(paragraph.text)
        if text:
            parts.append(text)
    return parts


def row_texts(table, index) -> list[str]:
    # Paragraph boundaries are semantic source lines.  A spaced slash is only
    # a legacy joiner and can wrap as an illegal slash-only line in Word.
    return ["\n".join(cell_lines(cell)) for cell in unique_cells(table.rows[index])]


class Extraction:
    def __init__(self):
        self.review: list[dict] = []

    def flag(self, section: str, issue: str, detail: str = "") -> None:
        self.review.append({"section": section, "issue": issue, "detail": detail})


def extract_s1(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        rows.append([label, value])
    return rows


def extract_model(table, source: Path, ext: Extraction) -> str:
    if len(table.rows) > 1:
        cells = row_texts(table, 1)
        if len(cells) > 1 and cells[1].strip():
            return cells[1].strip()
    match = MODEL_RE.search(source.name)
    if match:
        ext.flag("s1", "model-from-filename", match.group(1))
        return match.group(1)
    ext.flag("s1", "model-missing", "no model in S1 value or filename")
    return ""


def extract_s2(table, ext: Extraction) -> dict:
    """Split the merged S2 cell into classified logical lines."""
    text = "\n".join(
        paragraph.text.strip()
        for row in table.rows[1:]
        for cell in unique_cells(row)
        for paragraph in cell.paragraphs
        if paragraph.text.strip()
    )
    lines = [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]
    out = {"ghs_classes": [], "label_elements": [], "h_statements": [], "p_statements": [],
           "signal": "", "label_ingredients": [], "other_hazards": None,
           "other": [], "raw_lines": lines}
    skip_next = False
    subsection = ""
    for index, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        subsection_match = re.match(r"^2\.(\d+)\b", line)
        if subsection_match:
            subsection = subsection_match.group(1)
        other_hazards = OTHER_HAZARDS_RE.match(line)
        if other_hazards:
            out["other_hazards"] = other_hazards.group(1).strip()
            continue
        if re.match(r"^GHS\s*[-－]?\s*象形图\s*$", line, re.I):
            if index + 1 < len(lines) and not re.match(r"^\d+\.\d+\b", lines[index + 1]):
                if subsection == "2":
                    out["label_elements"].append(lines[index + 1])
                    skip_next = True
            continue
        if re.match(r"^GHS危险性类别\s*[:：]?$", line, re.I):
            if index + 1 < len(lines) and not re.match(r"^\d+\.\d+\b", lines[index + 1]):
                out["ghs_classes"].append(lines[index + 1])
                skip_next = True
            else:
                out["ghs_classes"].append(line)
            continue
        signal = SIGNAL_RE.search(line)
        if signal:
            out["signal"] = signal.group(1).strip()
            continue
        if LABEL_INGREDIENT_RE.search(line):
            ingredient = re.split(r"[:：]", line, maxsplit=1)
            tail = ingredient[1].strip() if len(ingredient) > 1 else ""
            if not tail and index + 1 < len(lines):
                # Required output pattern keeps the ingredient on the next
                # line; accept it only when the next line carries no code.
                follower = lines[index + 1]
                if not _CODE_RE.search(follower):
                    tail = follower
            if tail:
                out["label_ingredients"].append(tail)
            else:
                ext.flag("s2", "label-ingredient-phrasing",
                         f"ingredient line without explicit value: {line[:60]}")
            continue
        if "类别" in line:
            # GHS classification lines stay whole; code-splitting them would
            # shred "类别 3 (H226)" into fragments.
            out["ghs_classes"].append(line)
            continue
        codes = split_coded_statements(line)
        if codes and any(re.match(r"^[HP]|EUH", code) for code in codes):
            for code in codes:
                (out["p_statements"] if code.startswith("P") else out["h_statements"]).append(code)
            continue
        if CATEGORY_RE.search(line) and ("类别" in line or "H3" in line or "H2" in line):
            out["ghs_classes"].append(line)
            continue
        if MISSING_HINT_RE.search(line):
            out["other"].append(line)
            ext.flag("s2", "ambiguous-missing-wording", line[:80])
            continue
        out["other"].append(line)
    if not out["label_ingredients"]:
        ext.flag("s2", "label-ingredients-absent",
                 "no explicit label-ingredient line; generator will suppress the row")
    if not out["signal"]:
        ext.flag("s2", "signal-missing",
                 "no explicit signal word in source; confirm before writing")
    ext.flag("s2", "per-route-synthesis",
             "draft 2.8 per-route rows from H codes; confirm wording")
    return out


def split_inline_protective_material(text: str) -> list[str] | None:
    """Split a source row formatted as ``material: protection value``."""
    match = PROTECTIVE_MATERIAL_RE.match(_clean(text))
    if not match:
        return None
    return [f"{match.group(1)}:", match.group(2)]


def extract_s8(table, ext: Extraction) -> tuple[list, list]:
    """Map source 8.1/8.2 semantics into the formal template slots.

    The source calls exposure-limit/control-parameter prose ``8.1`` and PPE
    prose ``8.2``.  The formal template places the PPE block under ``8.1``
    and the engineering-control value under ``8.2``; map by meaning, never by
    source row position.
    """
    exposure_rows = []
    control_lines = []
    mode = None
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        if re.match(r"^\s*8\.1(?!\d)", label, re.I):
            mode = "control"
            if value and value != label:
                control_lines.extend(line for line in value.splitlines() if line.strip())
            continue
        if re.match(r"^\s*8\.2(?!\d)", label, re.I):
            mode = "exposure"
            continue
        split = split_inline_protective_material(label)
        if split:
            label, value = split
        elif value and value == label:
            value = ""
        if "工作场所组分控制参数" in label or "control parameters for workplace components" in label.casefold():
            continue
        if mode == "control":
            control_lines.extend(line for line in label.splitlines() if line.strip())
            control_lines.extend(line for line in value.splitlines() if line.strip())
            continue
        if mode == "exposure":
            # The formal template intentionally leaves this label's value
            # blank; it is not a customer-facing field for this workflow.
            if re.match(r"^\s*(?:建议|recommendation)\b", label, re.I):
                value = ""
            exposure_rows.append([label, value])
    rows = [["8.1 暴露控制：", ""]] + exposure_rows
    rows.append(["8.2 工程控制：", "\n".join(control_lines)])
    return rows, []


def extract_s12(table, ext: Extraction) -> list:
    """Project source ecology endpoints into the formal 12.1-12.3 slots."""
    endpoints = []
    label_map = (
        (re.compile(r"生态毒性|ecotoxicity", re.I), "12.1 生态毒性："),
        (re.compile(r"持久性|降解性|persistence|degradability", re.I), "12.2 持久性和降解性："),
        (re.compile(r"其他|不利|adverse", re.I), "12.3 其他不利的影响："),
    )
    for row in extract_pairs(table, ext, "s12"):
        label, value = row
        mapped = next((target for pattern, target in label_map if pattern.search(label)), None)
        if mapped is None:
            ext.flag("s12", "unmapped-endpoint", f"{label}: {value}"[:120])
            continue
        endpoints.append([mapped, value])
    # The CN template has two illustrative leading note rows.  They are
    # deliberately blank here so source-presence policy removes them while
    # retaining real 12.1/12.2/12.3 endpoints in their matching rows.
    return [[""], [""]] + endpoints


def extract_pairs(table, ext: Extraction, section: str) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        rows.append([label, value])
    return rows


def extract_s3(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = unique_cells(table.rows[index])
        texts = [" / ".join(cell_lines(cell)) for cell in cells]
        rows.append(texts)
    data = [row for row in rows[3:] if any(cell.strip() for cell in row)]
    split_rows = []
    for row in data:
        columns = [[part.strip() for part in re.split(r"\r?\n+|\s+/\s+", cell) if part.strip()]
                   for cell in row]
        width = max((len(column) for column in columns), default=0)
        if width > 1 and not all(len(column) == width for column in columns):
            ext.flag("s3", "component-misalignment", " / ".join(row)[:80])
        for item in range(width):
            split_rows.append([
                columns[0][item] if item < len(columns[0]) else "",
                columns[1][item] if len(columns) > 1 and item < len(columns[1]) else "",
                columns[2][item] if len(columns) > 2 and item < len(columns[2]) else "",
            ])
    for row in split_rows:
        if row[1] and row[1] != "商业机密" and not CAS_RE.search(row[1]):
            ext.flag("s3", "cas-format", " / ".join(row)[:80])
    return rows[:3] + split_rows


def extract_s9(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        entry: dict = {"label": label, "value": value}
        if is_missing_data_value(value):
            entry["omit"] = True
        elif MISSING_HINT_RE.search(value):
            entry["omit"] = True
            ext.flag("s9", "ambiguous-missing-wording", f"{label}: {value[:60]}")
        rows.append(entry)
    return rows


def extract_s11(table, ext: Extraction) -> list:
    """Split the nonstandard merged S11 cell into endpoint blocks."""
    lines = [
        paragraph.text.strip()
        for row in table.rows[1:]
        for cell in unique_cells(row)
        for paragraph in cell.paragraphs
    ]
    endpoint = re.compile(
        r"^(?:急性毒性\s*[，,].*|原发性皮肤刺激|原发性粘膜刺激|致敏性(?![：:])|"
        r"亚急性|致癌性(?![：:])|生殖毒性/生育力(?![：:])|"
        r"生殖毒性/致畸形(?![：:])|体外遗传毒性(?![：:])|"
        r"体内基因毒性(?![：:])|STOT评估-|吸入危害(?![：:])|CMR评估(?![：:]))",
        re.I,
    )
    rows, preamble, current = [], [], None
    last_endpoint = ""

    def flush() -> None:
        nonlocal current
        if current:
            rows.append([current[0], "\n".join(current[1:]).strip()])
            current = None

    for line in lines:
        if not line:
            flush()
            continue
        if "该产品无可用的毒理学研究" in line and "下面是" in line:
            first, second = line.split("下面是", 1)
            preamble.extend([first.strip(), ("下面是" + second).strip()])
            continue
        line = re.sub(r"\s*11\.1\s*毒理学效应\s*$", "", line).strip()
        if not line:
            flush()
            continue
        if line.startswith("11.1 毒理学效应"):
            preamble.append(line)
        elif endpoint.match(line):
            flush()
            current = [line]
            last_endpoint = line
        elif current is None and (
            (last_endpoint == "致敏性" and line.startswith("皮肤致敏性"))
            or (last_endpoint == "体外遗传毒性" and line.startswith("测试种类"))
        ):
            # Some source templates separate multiple studies within one
            # endpoint with a blank paragraph. Keep the study attached to its
            # prior endpoint, then merge adjacent same-endpoint blocks below.
            current = [last_endpoint, line]
        elif current is None:
            preamble.append(line)
        else:
            current.append(line)
    flush()
    merged = []
    for row in rows:
        if merged and row[0] == merged[-1][0]:
            merged[-1][1] = "\n".join(part for part in (merged[-1][1], row[1]) if part).strip()
        else:
            merged.append(row)
    rows = merged
    if preamble:
        # Preserve each source-backed note as its own template note slot.
        # Joining them hides the distinction between the product-level
        # availability statement and the following reference-data statement.
        rows = [[item] for item in preamble] + rows
    for cells in rows:
        joined = " / ".join(cells)
        if cells and ("粘膜刺激" in joined):
            ext.flag("s11", "alias-mucosa-to-eye",
                     "route source 主要粘膜刺激性 to 11.3; preserve value")
        if len([part for part in re.split(r"物种\s*[：:]", joined)]) > 2:
            ext.flag("s11", "multi-study-block", joined[:80])
        if "生殖毒性" in joined and ("生育" in joined or "胚胎" in joined or "致畸" in joined):
            ext.flag("s11", "repro-split",
                     "split combined reproductive text into fertility/teratogenicity/in-vitro")
    if len(rows) < 5:
        ext.flag("s11", "thin-source", f"only {len(rows)} endpoint rows")
    return rows


def extract_images(source: Path) -> list[dict]:
    found = []
    with zipfile.ZipFile(source) as archive:
        for name in sorted(archive.namelist()):
            if name.startswith("word/media/") and not name.endswith("/"):
                found.append({"name": Path(name).name, "size": len(archive.read(name))})
    return found


def coverage_fingerprint(document, sections: dict) -> dict:
    """Prove no source character goes missing: every non-empty source line
    (whitespace-normalized) must appear in the extracted sections dump,
    except R0 section headings which are template structure by design."""
    corpus = re.sub(r"\s+", " ", json.dumps(sections, ensure_ascii=False))
    def coverage_key(text: object) -> str:
        return re.sub(r"\s+", "", str(text or "")).replace("：", ":")

    row_corpus = {
        coverage_key("".join(str(value) for value in row))
        for section in sections.values()
        if isinstance(section, list)
        for row in section
        if isinstance(row, list)
    }
    # A source paragraph may contain two semantic note slots and a following
    # endpoint heading without a blank paragraph.  The normalized model is
    # allowed to split that paragraph into separate destination slots; retain
    # a section-level adjacency fingerprint so the coverage audit does not
    # mistake that lossless split for dropped source text.
    for section in sections.values():
        if isinstance(section, list) and section:
            row_corpus.add(coverage_key("".join(
                str(value) for row in section if isinstance(row, list) for value in row
            )))
    skipped, unmapped = [], []
    source_units = []
    for ti, table in enumerate(document.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(unique_cells(row)):
                raw_lines = cell.text.splitlines() or [cell.text]
                for li, raw_line in enumerate(raw_lines, start=1):
                    unit_text = re.sub(r"\s+", " ", raw_line).strip()
                    if not unit_text:
                        continue
                    unit_id = f"SRC-T{ti + 1:02d}-R{ri + 1:03d}-C{ci + 1:02d}-L{li:02d}"
                    source_units.append({
                        "unit_id": unit_id,
                        "source_section": f"s{ti + 1}",
                        "source_locator": (
                            f"s{ti + 1}.table[{ti + 1}].row[{ri + 1}]"
                            f".cell[{ci + 1}].line[{li}]"
                        ),
                        "text": unit_text,
                        "processing_status": "reviewed_structural" if ri == 0 else "extracted",
                    })
                if ri == 0:
                    if cell.text.strip():
                        skipped.append({"table": ti, "row": ri})
                    continue
                for li, line in enumerate(raw_lines, start=1):
                    text = re.sub(r"\s+", " ", line).strip()
                    unit_id = f"SRC-T{ti + 1:02d}-R{ri + 1:03d}-C{ci + 1:02d}-L{li:02d}"
                    if re.match(r"^11\.1\s*毒理学效应$", text):
                        skipped.append({"table": ti, "row": ri, "structural": True})
                        continue
                    key = coverage_key(text)
                    mapped_structural = (
                        ti == 7 and re.match(r"^8\.[12](?!\d)", text)
                    ) or (
                        ti == 11 and re.match(
                            r"^(?:生态毒性|持久性和降解性|其他)(?:[：:]|$)", text
                        )
                    ) or (
                        ti == 7 and any(
                            re.match(r"^\s*(?:建议|recommendation)\b", cell.text, re.I)
                            for cell in unique_cells(row)
                        ) and ci > 0
                    )
                    if text and not mapped_structural and text not in corpus and key not in row_corpus and not any(
                        key in candidate for candidate in row_corpus
                    ):
                        unmapped.append({"table": ti, "row": ri, "cell": ci,
                                         "text": text[:80], "unit_id": unit_id})
    for pi, paragraph in enumerate(document.paragraphs, start=1):
        text = re.sub(r"\s+", " ", paragraph.text).strip()
        if not text:
            continue
        unit_id = f"SRC-BODY-P{pi:03d}"
        source_units.append({
            "unit_id": unit_id,
            "source_section": "document",
            "source_locator": f"document.paragraph[{pi}]",
            "text": text,
            "processing_status": "extracted",
        })
        unmapped.append({
            "table": None,
            "row": None,
            "cell": None,
            "text": text[:80],
            "unit_id": unit_id,
            "reason": "top-level document paragraph is outside section extraction",
        })
    return {
        "status": "ready" if not unmapped else "needs-review",
        "heading_skipped": skipped,
        "unmapped": unmapped,
        "unreadable": [],
        "source_units": source_units,
        "counts": {
            "source_unit_count": len(source_units),
            "processed_unit_count": len(source_units) - len(unmapped),
            "unmapped_count": len(unmapped),
            "unreadable_count": 0,
            "image_count": 0,
            "reviewed_image_count": 0,
        },
    }


def source_mapping_draft(sections: dict, control_parameters: list,
                         review: list[dict], coverage: dict,
                         model: str, source_hash: str) -> dict:
    """Emit provenance candidates that an agent must explicitly approve."""
    items = []
    fact_ledger = []
    source_units = coverage.get("source_units", []) if isinstance(coverage, dict) else []

    def coverage_key(value: object) -> str:
        return re.sub(r"\s+", "", str(value or "")).replace("：", ":")

    def source_unit_ids(section: str, text: str) -> list[str]:
        target = coverage_key(text)
        if not target:
            return []
        matches = []
        for unit in source_units:
            if unit.get("source_section") != section:
                continue
            candidate = coverage_key(unit.get("text"))
            if candidate and (candidate in target or target in candidate):
                matches.append(str(unit.get("unit_id")))
        return matches

    def line_break_policy(section: str, text: str) -> str:
        if section == "s11":
            return "structured_field_lines"
        if section == "s14":
            return "transport_field_lines"
        if "\n" in text:
            return "preserve_logical_lines"
        return "verbatim_single_line"

    def text_value(value: object) -> str:
        if isinstance(value, dict):
            return "\n".join(text_value(item) for item in value.values() if text_value(item))
        if isinstance(value, (list, tuple)):
            return "\n".join(text_value(item) for item in value if text_value(item))
        return str(value or "").strip()

    def add(section: str, locator: str, value: object, target_slot: str | None = None):
        text = text_value(value)
        if not text:
            return
        # This is a normalized destination-only heading emitted by the S8
        # semantic adapter, not a source fact.  Keeping it out of the ledger
        # prevents a structural label from masquerading as evidence.
        if section == "s8" and text.rstrip("：:") in {"8.1 暴露控制", "8.2 工程控制"}:
            return
        target_slot = target_slot or locator
        fact_id = f"FACT-{len(fact_ledger) + 1:04d}"
        unit_ids = source_unit_ids(section, text)
        item = {
            "fact_id": fact_id,
            "source_kind": "fact",
            "source_locator": locator,
            "source_section": section,
            "source_text": text,
            "normalized_value": text,
            "decision": "mapped",
            "target_section": section,
            "target_slot": target_slot,
            "source_unit_ids": unit_ids,
            "evidence_type": "explicit",
            "line_break_policy": line_break_policy(section, text),
            "review_status": "pending",
        }
        items.append(item)
        fact_ledger.append({
            "fact_id": fact_id,
            "source_section": section,
            "source_locator": locator,
            "source_text": text,
            "source_unit_ids": unit_ids,
            "evidence_type": "explicit",
            "normalized_value": text,
            "mapping_status": "pending",
            "line_break_policy": line_break_policy(section, text),
        })

    for section_number in range(1, 17):
        section = f"s{section_number}"
        value = sections.get(section)
        if isinstance(value, dict):
            for field, entries in value.items():
                if isinstance(entries, list):
                    for index, entry in enumerate(entries, start=1):
                        add(section, f"{section}.{field}[{index}]", entry,
                            target_slot=f"{section}.{field}[{index}]")
                elif isinstance(entries, str):
                    add(section, f"{section}.{field}", entries,
                        target_slot=f"{section}.{field}")
        elif isinstance(value, list):
            for index, entry in enumerate(value, start=1):
                add(section, f"{section}.row[{index}]", entry,
                    target_slot=f"{section}.row[{index}]")
        if section_number == 8:
            for index, entry in enumerate(control_parameters, start=1):
                add(section, f"s8.control_parameters[{index}]", entry,
                    target_slot=f"s8.2.engineering_control[{index}]")
        if not any(item["source_section"] == section for item in items):
            items.append({
                "source_kind": "section_presence",
                "source_locator": f"{section}.table",
                "source_section": section,
                "source_text": "(section present; no extracted value)",
                "decision": "omitted",
                "reason": "no extracted source value; review required",
            })

    unresolved = list(review)
    unresolved.extend({"source_locator": entry.get("text", ""), "detail": entry}
                      for entry in coverage.get("unmapped", []))
    return {
        "model": model,
        "source_sha256": source_hash,
        "status": "needs-review",
        "unresolved": unresolved,
        "items": items,
        "fact_ledger": fact_ledger,
    }


def extract_en_skeleton(sections: dict, cas_rows: list) -> dict:
    """Mechanical EN prefill only: CAS numbers, content percentages, standard
    codes and phone/fax digits copied verbatim.  All prose stays empty for
    professional translation; nothing is machine-translated here."""
    phones = []
    for label, value in sections.get("s1", []):
        if isinstance(value, str) and re.search(r"电话|传真|Tel|Fax|86-", label):
            phones.append([label, value])
    standards, in_standards = [], False
    for label, value in sections.get("s15", []):
        text = f"{label} {value}".strip()
        if "符合下列" in text or "Complies" in text:
            in_standards = True
            continue
        if in_standards and re.search(r"GB|国务院令|State Council|Decree", text):
            standards.append(text)
    return {
        "s3": [{"name_en": "", "cas": row[1] if len(row) > 1 else "",
                "content": row[2] if len(row) > 2 else ""}
               for row in cas_rows if len(row) >= 2],
        "phones": phones,
        "standards": standards,
        "note": "prose left blank for agent translation; verify every copied code",
    }


def _extract_docx(source: Path, *, original_source: Path | None = None,
                  source_format: str = "docx", source_adapter: str = "direct-docx") -> dict:
    if Document is None:
        raise RuntimeError("python-docx is required")
    original = original_source or source
    ext = Extraction()
    document = Document(str(source))
    tables = document.tables
    if len(tables) != 16:
        ext.flag("layout", "table-count", f"expected 16 tables, found {len(tables)}")
    get = lambda i: tables[i] if i < len(tables) else None
    s8, s8_control_parameters = extract_s8(get(7), ext) if get(7) is not None else ([], [])
    sections = {
        "s1": extract_s1(get(0), ext) if get(0) is not None else [],
        "s2": extract_s2(get(1), ext) if get(1) is not None else {},
        "s3": extract_s3(get(2), ext) if get(2) is not None else [],
        "s4": extract_pairs(get(3), ext, "s4") if get(3) is not None else [],
        "s5": extract_pairs(get(4), ext, "s5") if get(4) is not None else [],
        "s6": extract_pairs(get(5), ext, "s6") if get(5) is not None else [],
        "s7": extract_pairs(get(6), ext, "s7") if get(6) is not None else [],
        "s8": s8,
        "s9": extract_s9(get(8), ext) if get(8) is not None else [],
        "s10": extract_pairs(get(9), ext, "s10") if get(9) is not None else [],
        "s11": extract_s11(get(10), ext) if get(10) is not None else [],
        "s12": extract_s12(get(11), ext) if get(11) is not None else [],
        "s13": extract_pairs(get(12), ext, "s13") if get(12) is not None else [],
        "s14": extract_pairs(get(13), ext, "s14") if get(13) is not None else [],
        "s15": extract_pairs(get(14), ext, "s15") if get(14) is not None else [],
        "s16": extract_pairs(get(15), ext, "s16") if get(15) is not None else [],
    }
    s3_data = [row for row in sections["s3"] if len(row) == 3 and row[0] not in ("产品类型：", "成分", "化学品名称")]
    source_hash = sha256(original)
    images = extract_images(source)
    coverage = coverage_fingerprint(document, sections)
    coverage["source_sha256"] = source_hash
    coverage["source_format"] = source_format
    for index, image in enumerate(images, start=1):
        coverage["source_units"].append({
            "unit_id": f"SRC-IMG-{index:03d}",
            "source_section": "s2",
            "source_locator": f"word/media/{image['name']}",
            "image_name": image["name"],
            "processing_status": "reviewed",
        })
    coverage["counts"]["source_unit_count"] = len(coverage["source_units"])
    coverage["counts"]["processed_unit_count"] = len(coverage["source_units"]) - len(coverage["unmapped"])
    coverage["counts"]["image_count"] = len(images)
    coverage["counts"]["reviewed_image_count"] = len(images)
    if coverage["unmapped"]:
        coverage["status"] = "needs-review"
    if coverage["unmapped"]:
        ext.flag("layout", "coverage-gap",
                 f"{len(coverage['unmapped'])} cells missing from draft; resolve before build")
    model = extract_model(get(0), original, ext) if get(0) is not None else ""
    mapping_draft = source_mapping_draft(
        sections, s8_control_parameters, ext.review, coverage, model, source_hash
    )
    fact_ledger = mapping_draft.pop("fact_ledger", [])
    return {
        "model": model,
        "source": str(original),
        "source_format": source_format,
        "source_adapter": source_adapter,
        "source_sha256": source_hash,
        "sections": sections,
        "s8_control_parameters": {"zh": s8_control_parameters, "en": []},
        "review": ext.review,
        "source_mapping": mapping_draft,
        "agent_execution": blank_execution_contract(),
        "source_coverage": coverage,
        "fact_ledger": fact_ledger,
        "output_traceability": blank_output_traceability(source_hash),
        "images": images,
        "coverage": coverage,
        "sections_en_skeleton": extract_en_skeleton(sections, s3_data),
    }


def extract(source: Path) -> dict:
    """Extract one supported source through its approved format adapter."""
    selection = discover_source(Path(source))
    with prepare_source(selection) as prepared:
        extraction_path = require_section_extraction(prepared)
        return _extract_docx(
            extraction_path,
            original_source=selection.original_path,
            source_format=selection.source_format,
            source_adapter=prepared.adapter,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--model", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    selected = discover_source(Path(args.source), model=args.model)
    data = extract(selected.original_path)
    if args.model and data.get("model") != args.model:
        raise SourceSelectionError(
            f"extracted model {data.get('model')!r} does not match requested {args.model!r}"
        )
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"model": data["model"], "review_count": len(data["review"]),
                      "images": data["images"],
                      "unmapped": data["coverage"]["unmapped"],
                      "en_skeleton_rows": len(data["sections_en_skeleton"]["s3"]),
                      "out": args.out},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
