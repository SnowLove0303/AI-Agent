#!/usr/bin/env python3
"""Shared DOCX-first build pipeline for the unified MSDS skill (v3.18.1).

Business role: one parameterized path replaces the per-model copied
generators.  Input is an *approved* standardized model file::

    {"model": ..., "revision": ..., "source_sha256": ...,
     "zh": {"s1": [...], ..., "s16": [...]},
     "en": {...} | null,
     "s8_control_parameters": {"zh": [...], "en": [...]},
     "source_mapping": {"status": "reviewed", "items": [...]},
     "translation_review": [...]}

``en`` must be produced by ``draft_en_facts.py`` (translation OF the
standardized model) and hand-cleared; a missing ``en`` or a non-empty
``translation_review`` fails closed for formal release.  S1 values are
written verbatim (no hidden appending); company overlay comes only from
the approved profile constants.

Every variant runs the release gates before any PDF is converted; any
gate failure raises :class:`ReleaseBlocked` and no PDF is produced.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from docx import Document

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SKILL_ROOT = SCRIPTS.parent
from convert_docx_to_pdf import convert as convert_pdf  # noqa: E402
from ghs_pictogram_policy import extract_first_embedded_image, insert_source_pictogram  # noqa: E402
from normalize_en_layout import normalize_en_document  # noqa: E402
from output_matrix import output_names  # noqa: E402
from section2_ghs_policy import (  # noqa: E402
    is_missing_section2_value,
    project_source_cn_headings,
    row_has_visual_content,
    suppress_missing_section2_rows_and_renumber,
)
from section2_hp_policy import is_missing_data_value  # noqa: E402
from missing_data_policy import apply_source_absence_policy  # noqa: E402
from product_identity_policy import audit_identity, expected_identity  # noqa: E402
from section_overwrite_rules import (  # noqa: E402
    validate_section_payload,
    validate_section_template,
)
from source_ingest import discover_source, prepare_source  # noqa: E402
from structured_toxicology_policy import (  # noqa: E402
    audit_field_value_integrity,
    audit_study_separation,
)
from template_mutation_whitelist import (  # noqa: E402
    clear_value_cells,
    set_sequence_prefix,
    TemplateSlotRegistry,
    unique_cells,
    write_s82_top_rows,
)
import template_runtime as base  # noqa: E402

import audit_english_terminology as audit_terms  # noqa: E402
import audit_section2_release as audit_s2  # noqa: E402
import audit_template_mutation_whitelist as audit_whitelist  # noqa: E402
import audit_whitespace as audit_ws  # noqa: E402

REVISION_DEFAULT = "2025/2/22"
RESIDUAL_IDS = ("PU-2345", "PEA-4139")

# Guanzhi contact block, mirroring the approved formal template/supplier
# record.  Guocai contact comes from the skill company overlay (§14).
GUANZHI_TEL = "86-20-82567990"
GUANZHI_FAX = "86-20-32214789"
GUOCAI_TEL = "86-763-2811205"
GUOCAI_FAX = "86-763-2811024"
PINNED_TEMPLATE_SHA256 = {
    "zh": "3cb250303778b70ab0dbfedc4392ac628228d80146e6376f410157cb08993622",
    "en": "003ff6bac27bf3bc99f0426ea8ed596487b0399f30428c406227d8f7c1b3dd46",
    "en_source": "59445b62c6d33b25a2e04c05778d428656f1ce0cbe7c21212721b145468c4416",
}
SECTION_KEYS = {f"s{i}" for i in range(1, 17)}


def company_tel(language: str, brand: str) -> str:
    return GUOCAI_TEL if brand == "guocai" else GUANZHI_TEL


def company_fax(language: str, brand: str) -> str:
    return GUOCAI_FAX if brand == "guocai" else GUANZHI_FAX


class ReleaseBlocked(RuntimeError):
    """A release gate failed; the variant must not ship."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_template_baselines(template_cn: Path, template_en: Path,
                                template_en_source: Path) -> dict[str, str]:
    """Reject a modified active template before it can become a new baseline."""
    paths = {"zh": template_cn, "en": template_en, "en_source": template_en_source}
    actual = {key: sha256(path) for key, path in paths.items()}
    errors = [f"{key} template hash {actual[key]} != pinned {PINNED_TEMPLATE_SHA256[key]}"
              for key in paths if actual[key] != PINNED_TEMPLATE_SHA256[key]]
    if errors:
        raise ReleaseBlocked("template baseline: " + "; ".join(errors))
    return actual


def validate_approved_facts(facts: dict, source: Path, model: str) -> None:
    """Fail before cloning templates when the facts contract is unsafe."""
    errors = []
    if facts.get("model") != model:
        errors.append(f"facts model {facts.get('model')!r} does not match {model!r}")
    source_hash = sha256(source)
    if facts.get("source_sha256") != source_hash:
        errors.append("facts source_sha256 does not match the selected original source")
    errors.extend(validate_source_mapping(facts, model, source_hash))
    required = {f"s{i}" for i in range(1, 17)}
    for language in ("zh", "en"):
        layer = facts.get(language)
        if not isinstance(layer, dict):
            errors.append(f"{language} semantic layer is missing")
            continue
        missing = sorted(required - set(layer))
        if missing:
            errors.append(f"{language} semantic layer missing: {', '.join(missing)}")
        s2 = layer.get("s2")
        if not isinstance(s2, list) or len(s2) < 15:
            errors.append(f"{language} Section 2 must be a 15-slot semantic projection")
            continue
        labels = [str(row[0]).strip() for row in s2 if isinstance(row, (list, tuple)) and row]
        prefixes = [re.match(r"^(\d+\.\d+)", label).group(1)
                    if re.match(r"^(\d+\.\d+)", label) else ""
                    for label in labels[:3]]
        if len(labels) < 15 or prefixes != ["2.1", "2.2", "2.3"]:
            errors.append(f"{language} Section 2 slots are not canonically ordered")
        if language == "zh":
            required_words = ((0, "紧急情况概述"), (1, "GHS危险性类别"),
                              (2, "GHS标签要素"), (14, "其他危害"))
            for index, word in required_words:
                if index >= len(labels) or word not in labels[index]:
                    errors.append(f"zh Section 2 slot {index + 1} must be {word}")
    if errors:
        raise ReleaseBlocked("facts contract: " + "; ".join(errors))


def validate_source_mapping(facts: dict, model: str, source_hash: str) -> list[str]:
    """Require an explicit, source-bound disposition for every source section."""
    mapping = facts.get("source_mapping")
    if not isinstance(mapping, dict):
        return ["source_mapping is missing"]
    errors = []
    if mapping.get("model") != model:
        errors.append("source_mapping model does not match requested model")
    if mapping.get("source_sha256") != source_hash:
        errors.append("source_mapping source_sha256 does not match the selected original source")
    if mapping.get("status") != "reviewed":
        errors.append("source_mapping status must be reviewed")
    unresolved = mapping.get("unresolved")
    if unresolved != []:
        errors.append("source_mapping unresolved must be empty")
    items = mapping.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["source_mapping items are missing"]
    decisions = {"mapped", "omitted", "not_applicable", "unresolved"}
    locators = set()
    covered = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"source_mapping item {index} is not an object")
            continue
        locator = item.get("source_locator")
        section = item.get("source_section")
        text = item.get("source_text")
        decision = item.get("decision")
        if not isinstance(locator, str) or not locator.strip():
            errors.append(f"source_mapping item {index} has no source_locator")
        elif locator in locators:
            errors.append(f"source_mapping duplicate source_locator: {locator}")
        else:
            locators.add(locator)
        if section not in SECTION_KEYS:
            errors.append(f"source_mapping item {index} has invalid source_section")
        else:
            covered.add(section)
        if not isinstance(text, str) or not text.strip():
            errors.append(f"source_mapping item {index} has no source_text")
        if decision not in decisions:
            errors.append(f"source_mapping item {index} has invalid decision")
        elif decision == "mapped":
            if item.get("target_section") not in SECTION_KEYS:
                errors.append(f"source_mapping item {index} mapped without target_section")
        elif decision in {"omitted", "not_applicable"}:
            if not isinstance(item.get("reason"), str) or not item["reason"].strip():
                errors.append(f"source_mapping item {index} {decision} without reason")
        elif decision == "unresolved":
            errors.append(f"source_mapping item {index} remains unresolved")
    missing_sections = sorted(SECTION_KEYS - covered)
    if missing_sections:
        errors.append("source_mapping missing sections: " + ", ".join(missing_sections))
    return errors


def company(language: str, brand: str) -> tuple[str, str]:
    if language == "en":
        if brand == "guocai":
            return base.EN_GUOCAI, base.EN_GUOCAI_ADDR
        return base.EN_GUANZHI, base.EN_GUANZHI_ADDR
    if brand == "guocai":
        return base.CN_GUOCAI, base.CN_GUOCAI_ADDR
    return base.CN_GUANZHI, base.CN_GUANZHI_ADDR


def template_for(template_cn: Path, template_en: Path, language: str) -> Path:
    if language == "en":
        return template_en
    if language == "zh":
        return template_cn
    raise ValueError(f"unsupported language: {language}")


def set_paragraph_text(paragraph, text: str) -> None:
    base.set_paragraph_text(paragraph, text)


def set_cell_text(cell, text: str) -> None:
    base.set_cell_text(cell, text)


def align_note_section_rows(values, table) -> list:
    """Fit optional source notes before numbered endpoint rows.

    S11/S12 templates reserve leading one-cell explanation slots.  A missing
    source note must consume an empty slot, not shift the first numbered
    endpoint into the note cell.
    """
    rows = list(values or [])
    note_slots = 0
    for row in list(table.rows)[1:]:
        if len(unique_cells(row)) != 1:
            break
        note_slots += 1
    if not note_slots:
        return rows
    notes = [row for row in rows if len(row) <= 1]
    endpoints = [row for row in rows if len(row) > 1]
    return notes[:note_slots] + [[""]] * max(0, note_slots - len(notes)) + endpoints


def suppress_s8_recommendation_value(rows, language: str) -> list:
    """Keep the template's recommendation label but never write its value."""
    output = []
    for row in list(rows or []):
        values = list(row) if isinstance(row, (list, tuple)) else [row]
        label = str(values[0]) if values else ""
        if re.match(r"^\s*(?:建议|recommendation)\b", label, re.I):
            output.append([label] + [""] * max(0, len(values) - 1))
        else:
            output.append(values)
    return output


def write_body(doc, facts: dict, language: str) -> dict:
    base.sanitize_template_artifacts(doc)
    registry = TemplateSlotRegistry.from_document(doc)
    clear_value_cells(doc, registry=registry)
    skipped_slots = []
    policy_facts = dict(facts)
    for sec in range(1, 17):
        table = doc.tables[sec - 1]
        rows = base.project_rows_to_template(facts[f"s{sec}"], language, sec, table)
        if sec == 8:
            rows = suppress_s8_recommendation_value(rows, language)
        if sec in (11, 12):
            rows = align_note_section_rows(rows, table)
            policy_facts[f"s{sec}"] = rows
        validate_section_payload(sec, rows, table)
        for row_index, values in enumerate(rows, 1):
            if row_index >= len(table.rows):
                raise RuntimeError(f"template capacity mismatch S{sec}: row {row_index}")
            audit = base.set_row(table.rows[row_index], values, table_index=sec - 1,
                                 row_index=row_index, registry=registry)
            if audit:
                audit["section"] = sec
                skipped_slots.append(audit)
    write_s82_top_rows(
        doc.tables[7],
        (facts.get("s8_control_parameters") or {}).get(language, []),
        language,
    )
    absence = apply_source_absence_policy(doc, policy_facts, unique_cells)
    return {"skipped_blank_template_slots": skipped_slots, **absence}


def write_header_footer(doc, language: str, brand: str, product: str, revision: str) -> None:
    is_en = language == "en"
    company_name, _ = company(language, brand)
    for section in doc.sections:
        for table in section.header.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() in {*RESIDUAL_IDS, product}:
                        set_cell_text(cell, product)
        for table in section.footer.tables:
            if not table.rows:
                continue
            cells = unique_cells(table.rows[0])
            if cells:
                set_cell_text(cells[0],
                              f"{company_name}\n{product}-MSDS" if is_en else f"{company_name}  {product}-MSDS")
                if len(cells) > 1:
                    set_cell_text(cells[1],
                                  f"Revision date: {revision}" if is_en else f"修订日期：{revision}")


def replace_residual_product_ids(doc, product: str) -> None:
    def visit(container) -> None:
        for paragraph in container.paragraphs:
            if paragraph.text.strip() in RESIDUAL_IDS:
                set_paragraph_text(paragraph, product)
        for table in container.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() in RESIDUAL_IDS:
                        set_cell_text(cell, product)

    visit(doc)
    for section in doc.sections:
        visit(section.header)
        visit(section.footer)


def suppress_s9(doc) -> dict:
    table = doc.tables[8]
    removed, visible = [], []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        label = cells[0].text.strip() if cells else ""
        if not value or is_missing_data_value(value):
            removed.append(label)
            table._tbl.remove(row._tr)
        else:
            visible.append(row)
    labels = []
    for number, row in enumerate(visible, 1):
        cells = unique_cells(row)
        if not cells or not cells[0].paragraphs:
            continue
        paragraph = cells[0].paragraphs[0]
        current = paragraph.text
        updated = re.sub(r"^(\s*)9\.\d+\b", rf"\g<1>9.{number}", current, count=1)
        if updated != current:
            set_sequence_prefix(cells[0], 9, number)
        labels.append(updated.strip())
    return {"removed_count": len(removed), "removed_labels": removed,
            "visible_count": len(labels), "visible_labels": labels}


def suppress_empty_s82_engineering_control(doc) -> dict:
    """Hide the standalone S8.2 row when its source-backed value is empty."""
    table = doc.tables[7]
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        if not cells or not re.match(r"^\s*8\.2\b", cells[0].text):
            continue
        if not any(cell.text.strip() for cell in cells[1:]):
            label = cells[0].text.strip()
            table._tbl.remove(row._tr)
            return {"hidden": True, "removed_label": label}
        return {"hidden": False, "removed_label": None}
    return {"hidden": False, "removed_label": None}


# ---------------------------------------------------------------- gates

def gate_locked_labels(template_path: Path, docx_path: Path, *,
                       template_document=None, output_document=None,
                       language: str = "cn") -> list[str]:
    template = template_document or Document(str(template_path))
    output = output_document or Document(str(docx_path))
    report = audit_whitelist.audit(template_path, docx_path,
                                   template=template, output=output,
                                   language=language)
    return report.get("errors", []) if isinstance(report, dict) else []


def gate_section2(docx_path: Path, require_pictogram: bool, document=None) -> list[str]:
    errors, _info = audit_s2.run(docx_path, require_pictogram=require_pictogram,
                                 document=document)
    return errors


def gate_whitespace(docx_path: Path, document=None) -> list[str]:
    report = audit_ws.run(str(docx_path), document=document)
    return [json.dumps(issue, ensure_ascii=False) for issue in report.get("issues", [])]


def gate_terminology(docx_path: Path) -> list[str]:
    return audit_terms.run(docx_path)


def gate_s11_toxicology(docx_path: Path, document=None) -> list[str]:
    doc = document or Document(str(docx_path))
    table = doc.tables[10]
    lines = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        for cell in cells[1:]:
            lines.extend(line for line in cell.text.split("\n") if line.strip())
    return audit_field_value_integrity(lines) + audit_study_separation(lines)


def gate_s9_leftover(docx_path: Path, document=None) -> list[str]:
    doc = document or Document(str(docx_path))
    table = doc.tables[8]
    errors = []
    numbers = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        label = cells[0].text.strip() if cells else ""
        if not value or is_missing_data_value(value):
            errors.append(f"missing-data S9 row remains: {label}")
        match = re.match(r"^\s*9\.(\d+)\b", label)
        if match:
            numbers.append(int(match.group(1)))
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"S9 numbering is not continuous: {numbers}")
    return errors


def gate_product_identity(docx_path: Path, language: str, product: str,
                          document=None) -> list[str]:
    if language != "zh":
        return []
    doc = document or Document(str(docx_path))
    rows = doc.tables[0].rows
    if len(rows) < 3:
        return ["Section 1 is missing the product/chinese-name rows"]
    cells = unique_cells(rows[1])
    product_value = cells[1].text if len(cells) > 1 else ""
    cells = unique_cells(rows[2])
    chinese_value = cells[1].text if len(cells) > 1 else ""
    return [f"identity: {error}" for error in audit_identity(
        chinese_name=chinese_value, model=product,
        product_name_value=product_value, chinese_name_value=chinese_value,
        header_text=product, footer_text=f"{product}-MSDS",
    )]


def gate_s8_recommendation(docx_path: Path, document=None) -> list[str]:
    doc = document or Document(str(docx_path))
    errors = []
    for row in doc.tables[7].rows[1:]:
        cells = unique_cells(row)
        if not cells or not re.match(r"^\s*(?:建议|recommendation)\b", cells[0].text, re.I):
            continue
        if any(cell.text.strip() for cell in cells[1:]):
            errors.append("Section 8 recommendation value must remain blank")
    return errors


# ---------------------------------------------------------------- build

def build_one(*, template_cn: Path, template_en: Path, template_en_source: Path,
              source: Path, facts: dict, language: str, brand: str,
              product: str, revision: str, out_docx: Path,
              with_pictogram: bool, source_media: Path | None = None,
              template_document=None, source_sha256: str | None = None,
              template_sha256: str | None = None,
              template_en_source_sha256: str | None = None) -> dict:
    template = template_for(template_cn, template_en, language)
    expected_template_hash = PINNED_TEMPLATE_SHA256[language]
    actual_template_hash = template_sha256 or sha256(template)
    if actual_template_hash != expected_template_hash:
        raise ReleaseBlocked(
            f"{language} active template hash {actual_template_hash} != pinned {expected_template_hash}"
        )
    if language == "en":
        actual_source_hash = template_en_source_sha256 or sha256(template_en_source)
        if actual_source_hash != PINNED_TEMPLATE_SHA256["en_source"]:
            raise ReleaseBlocked(
                f"EN source template hash {actual_source_hash} != pinned "
                f"{PINNED_TEMPLATE_SHA256['en_source']}"
            )
    # Stage beside the requested output so the final replacement is atomic on
    # Windows.  Staging under the skill root would cross volumes for the
    # normal F: formal-output location and make os.replace fail with WinError 17.
    stage_root = out_docx.parent
    stage_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{out_docx.stem}.", dir=stage_root) as temp_dir:
        staged_docx = Path(temp_dir) / out_docx.name
        shutil.copy2(template, staged_docx)
        doc = Document(str(staged_docx))
        base.validate_template_capacity(doc, language)
        validate_section_template(doc, language)
        lang_facts = {key: (list(value) if isinstance(value, list) else value)
                      for key, value in facts[language].items()}
        s1 = [list(row) for row in lang_facts["s1"]]
        # Company identity/contacts are overlay-controlled.  The Guanzhi address
        # remains source-authoritative so a source spelling such as 掬泉 is not
        # silently replaced by a stale profile literal.
        company_name, company_addr = company(language, brand)
        if language == "zh" and len(s1) > 1:
            identity = expected_identity(s1[1][1] if len(s1[1]) > 1 else "", product)
            s1[0][1] = identity.product_name_value
            s1[1][1] = identity.chinese_name_value
        if brand == "guanzhi" and len(s1) > 6:
            source_address = s1[6][1] if len(s1[6]) > 1 else ""
            if str(source_address).strip():
                company_addr = str(source_address)
        tel = company_tel(language, brand)
        fax = company_fax(language, brand)
        supplier_rows = [[None, company_name], [None, company_addr], [None, tel], [None, fax]]
        for offset, (_, value) in enumerate(supplier_rows):
            if len(s1) > 5 + offset and len(s1[5 + offset]) > 1:
                s1[5 + offset][1] = value
        lang_facts["s1"] = s1
        lang_facts["s8_control_parameters"] = (facts.get("s8_control_parameters") or {}).get(language, [])
        base.ensure_s3_component_rows(doc, component_count=len(lang_facts["s3"]) - 3)
        body_audit = write_body(doc, lang_facts, language)
        if language == "en":
            normalize_en_document(doc, template_path=template_en,
                                  template_document=template_document)
        pictogram_audit = insert_source_pictogram(doc, source_media or source) if with_pictogram else {
            "source_image_name": None, "skipped": "source has no embedded image"}
        s2_heading_policy = project_source_cn_headings(doc, language)
        s2_policy = suppress_missing_section2_rows_and_renumber(
            doc, set_paragraph_text, number_map=facts.get("s2_number_map")
        )
        s9_policy = suppress_s9(doc)
        s8_policy = suppress_empty_s82_engineering_control(doc)
        write_header_footer(doc, language, brand, product, revision)
        replace_residual_product_ids(doc, product)
        doc.save(staged_docx)

        blockers: list[str] = []
        blockers.extend(f"locked-labels: {e}" for e in gate_locked_labels(
            template, staged_docx, template_document=template_document,
            output_document=doc, language=language))
        blockers.extend(f"section2: {e}" for e in gate_section2(
            staged_docx, require_pictogram=with_pictogram, document=doc))
        blockers.extend(f"whitespace: {e}" for e in gate_whitespace(staged_docx, document=doc))
        blockers.extend(f"s9: {e}" for e in gate_s9_leftover(staged_docx, document=doc))
        blockers.extend(f"s11: {e}" for e in gate_s11_toxicology(staged_docx, document=doc))
        blockers.extend(gate_product_identity(staged_docx, language, product, document=doc))
        blockers.extend(f"s8: {e}" for e in gate_s8_recommendation(staged_docx, document=doc))
        if language == "en":
            blockers.extend(f"terminology: {e}" for e in gate_terminology(staged_docx))
        if blockers:
            raise ReleaseBlocked(f"{language}/{brand}: " + "; ".join(blockers[:8]))

        out_docx.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_docx, out_docx)
    return {
        "product": product,
        "brand": brand,
        "language": "en-US" if language == "en" else "zh-CN",
        "source_docx": str(source),
        "source_docx_sha256": source_sha256 or sha256(source),
        "template_reference": str(template),
        "template_reference_sha256": template_sha256 or sha256(template),
        "template_source_reference": str(template_en_source) if language == "en" else None,
        "template_source_reference_sha256": (template_en_source_sha256 or sha256(template_en_source)) if language == "en" else None,
        "template_geometry": base.template_geometry(language),
        "output_geometry": {"table_count": 16,
                            "rows": [len(table.rows) for table in doc.tables],
                            "s3_component_rows": len(lang_facts["s3"]) - 3},
        "section2_policy": s2_policy,
        "section2_heading_policy": s2_heading_policy,
        "pictogram": pictogram_audit,
        "section9_policy": s9_policy,
        "section8_policy": s8_policy,
        "source_presence_policy": body_audit,
        "status": "ready",
        "formal_ready": True,
        "blockers": [],
        "translation_review": [] if language == "zh" else [{"status": "reviewed-model-translation"}],
        "output_path": str(out_docx),
    }


def source_has_images(source: Path | None) -> bool:
    import zipfile

    if source is None or source.suffix.lower() not in {".docx", ".docm"}:
        # Non-OOXML source adapters do not silently infer pictograms from a
        # Spreadsheet/text preview; a verified image adapter can opt in later.
        return False
    with zipfile.ZipFile(source) as archive:
        return any(name.startswith("word/media/") and not name.endswith("/")
                   for name in archive.namelist())


def gate_output_matrix(root: Path, model: str, records: list[dict], do_pdf: bool) -> None:
    """Require one complete, evidence-bound matrix before promotion."""
    expected_docx = set(output_names(model))
    expected = expected_docx | ({Path(name).with_suffix(".pdf").name for name in expected_docx}
                                if do_pdf else set())
    errors = []
    for name in sorted(expected):
        path = root / name
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty matrix file: {name}")
    if len({Path(record["output_path"]).name for record in records}) != 4:
        errors.append("matrix must contain four unique DOCX records")
    for record in records:
        docx = Path(record["output_path"])
        if do_pdf:
            pdf = Path(record.get("pdf_path", ""))
            evidence = record.get("pdf_evidence") or {}
            if not pdf.is_file():
                errors.append(f"missing PDF for {docx.name}")
                continue
            if evidence.get("source_sha256") != sha256(docx):
                errors.append(f"PDF evidence is not bound to final DOCX: {docx.name}")
            if evidence.get("output_sha256") != sha256(pdf):
                errors.append(f"PDF evidence hash mismatch: {pdf.name}")
            if evidence.get("source_is_final_docx") is not True:
                errors.append(f"PDF lineage flag missing: {pdf.name}")
    if errors:
        raise ReleaseBlocked("output matrix: " + "; ".join(errors[:8]))


def build_matrix(*, source: Path, facts: dict, out_root: Path,
                 model: str | None = None, revision: str | None = None,
                 do_pdf: bool = True, timeout: int = 300) -> dict:
    model = model or facts.get("model") or ""
    if not model:
        raise ValueError("model is required (argument or facts['model'])")
    if not facts.get("zh") or not facts.get("en"):
        raise ReleaseBlocked("approved zh+en facts are both required; "
                             "draft en with draft_en_facts.py and clear translation_review first")
    if facts.get("translation_review"):
        raise ReleaseBlocked(f"translation_review is not empty: {len(facts['translation_review'])} items")
    revision = revision or facts.get("revision") or REVISION_DEFAULT
    selection = discover_source(Path(source), model=model)
    validate_approved_facts(facts, selection.original_path, model)
    out_root.parent.mkdir(parents=True, exist_ok=True)
    names = output_names(model)
    variants = [("zh", "guanzhi"), ("zh", "guocai"), ("en", "guanzhi"), ("en", "guocai")]
    name_map = {("zh", "guanzhi"): names[0], ("zh", "guocai"): names[1],
                ("en", "guanzhi"): names[2], ("en", "guocai"): names[3]}
    template_paths = {
        "zh": SKILL_ROOT / "examples" / "template_reference.docx",
        "en": SKILL_ROOT / "examples" / "template_reference_en.docx",
        "en_source": SKILL_ROOT / "examples" / "template_reference_en_source.docx",
    }
    template_hashes = validate_template_baselines(
        template_paths["zh"], template_paths["en"], template_paths["en_source"])
    template_documents = {
        language: Document(str(template_paths[language])) for language in ("zh", "en")
    }
    for language, template_document in template_documents.items():
        validate_section_template(template_document, language)
    template_en_source_sha256 = template_hashes["en_source"]
    records = []
    timing = {"variants": [], "docx_seconds": 0.0, "pdf_seconds": 0.0}
    total_started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=f".{model}_matrix_", dir=out_root.parent) as stage_dir:
        stage_root = Path(stage_dir)
        with prepare_source(selection) as prepared:
            with_pictogram = source_has_images(prepared.extraction_path)
            for language, brand in variants:
                out_docx = stage_root / name_map[(language, brand)]
                variant_started = time.perf_counter()
                record = build_one(
                    template_cn=SKILL_ROOT / "examples" / "template_reference.docx",
                    template_en=SKILL_ROOT / "examples" / "template_reference_en.docx",
                    template_en_source=SKILL_ROOT / "examples" / "template_reference_en_source.docx",
                    source=selection.original_path, source_media=prepared.extraction_path,
                    facts=facts, language=language, brand=brand,
                    product=model, revision=revision, out_docx=out_docx,
                    with_pictogram=with_pictogram,
                    template_document=template_documents[language],
                    source_sha256=selection.source_sha256,
                    template_sha256=template_hashes[language],
                    template_en_source_sha256=template_en_source_sha256)
                docx_seconds = time.perf_counter() - variant_started
                timing["docx_seconds"] += docx_seconds
                timing_item = {"language": language, "brand": brand,
                               "docx_seconds": round(docx_seconds, 3),
                               "pdf_seconds": 0.0}
                if do_pdf:
                    out_pdf = out_docx.with_suffix(".pdf")
                    pdf_started = time.perf_counter()
                    evidence = convert_pdf(out_docx, out_pdf, timeout=timeout)
                    timing_item["pdf_seconds"] = round(time.perf_counter() - pdf_started, 3)
                    timing["pdf_seconds"] += timing_item["pdf_seconds"]
                    record["pdf_path"] = str(out_pdf)
                    record["pdf_evidence"] = evidence
                timing["variants"].append(timing_item)
                records.append(record)
        gate_output_matrix(stage_root, model, records, do_pdf)
        out_root.mkdir(parents=True, exist_ok=True)
        expected_docx = set(output_names(model))
        for name in sorted(expected_docx):
            os.replace(stage_root / name, out_root / name)
            if do_pdf:
                pdf_name = Path(name).with_suffix(".pdf").name
                os.replace(stage_root / pdf_name, out_root / pdf_name)
        for record in records:
            old_docx = Path(record["output_path"])
            final_docx = out_root / old_docx.name
            record["output_path"] = str(final_docx)
            if do_pdf:
                old_pdf = Path(record["pdf_path"])
                final_pdf = out_root / old_pdf.name
                record["pdf_path"] = str(final_pdf)
                record["pdf_evidence"]["source_docx"] = str(final_docx)
                record["pdf_evidence"]["output_pdf"] = str(final_pdf)
    timing["total_seconds"] = round(time.perf_counter() - total_started, 3)
    report = {
        "product": model,
        "matrix": "2 brands x 2 languages x 2 formats" if do_pdf else "2 brands x 2 languages (DOCX only)",
        "docx_count": 4,
        "pdf_count": 4 if do_pdf else 0,
        "formal_ready_count": 4,
        "draft_count": 0,
        "shared_blocker": None,
        "source": str(selection.original_path),
        "source_format": selection.source_format,
        "source_sha256": selection.source_sha256,
        "records": records,
        "timing": timing,
    }
    (out_root / "matrix-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
