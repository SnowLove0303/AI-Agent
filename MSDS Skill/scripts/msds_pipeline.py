#!/usr/bin/env python3
"""Shared DOCX-first build pipeline for the unified MSDS skill (v3.26.0).

Business role: one parameterized path replaces the per-model copied
generators.  Input is an *approved* standardized model file::

    {"model": ..., "revision": ..., "source_sha256": ...,
     "zh": {"s1": [...], ..., "s16": [...]},
     "en": {...} | null,
     "s8_control_parameters": {"zh": [...], "en": [...]},
     "source_mapping": {"status": "reviewed", "items": [...]},
     "source_coverage": {"status": "ready", "source_units": [...]},
     "fact_ledger": [{"fact_id": ..., "source_locator": ...}],
     "output_traceability": {"status": "reviewed", "items": [...]},
     "agent_execution": {"status": "reviewed", "agent_mutation_boundary": ...},
     "translation_review": [...]}

``en`` must be produced by ``draft_en_facts.py`` (translation OF the
standardized model) and hand-cleared; a missing ``en`` or a non-empty
``translation_review`` fails closed for formal release.  S1 values are
written verbatim (no hidden appending); company overlay comes only from
the approved profile constants.

The matrix completes all four audited DOCX masters before starting the
bounded PDF batch. Every variant still runs the release gates before any PDF
is converted; any gate failure raises :class:`ReleaseBlocked` and no PDF is
produced.
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
from calendar import month_name
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from docx import Document

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SKILL_ROOT = SCRIPTS.parent
from convert_docx_to_pdf import (  # noqa: E402
    convert as convert_pdf,
    find_wpscli,
    preflight as preflight_pdf,
    version as converter_version,
)
from ghs_pictogram_policy import extract_first_embedded_image, insert_source_pictogram  # noqa: E402
from normalize_en_layout import normalize_en_document  # noqa: E402
from output_matrix import output_names  # noqa: E402
from section2_ghs_policy import (  # noqa: E402
    apply_precautionary_layout,
    is_missing_section2_value,
    normalize_s2_projected_rows,
    validate_s2_semantics,
    row_has_visual_content,
    suppress_missing_section2_rows_and_renumber,
)
from section2_hp_policy import is_missing_data_value  # noqa: E402
from missing_data_policy import apply_source_absence_policy  # noqa: E402
from section11_alignment import align_s11_rows  # noqa: E402
from s11_layout_policy import audit as audit_s11_layout  # noqa: E402
from s11_layout_policy import normalize as normalize_s11_layout  # noqa: E402
from agent_execution_contract import validate_agent_execution_contract  # noqa: E402
from source_interpretation_contract import validate_source_interpretation  # noqa: E402
from source_grounding import audit as audit_source_grounding  # noqa: E402
from source_grounding import validate as validate_source_grounding  # noqa: E402
from section2_fact_router import (  # noqa: E402
    audit as audit_section2_fact_router,
    expected_precautionary_group_keys,
)
from layout_preservation_policy import (  # noqa: E402
    audit_s114_vertical_alignment,
    audit_s82,
)
from product_identity_policy import (  # noqa: E402
    audit_english_identity,
    audit_identity,
    english_product_name_errors,
    expected_english_product_name,
    expected_identity,
)
from section_overwrite_rules import (  # noqa: E402
    local_policy_for,
    sanitize_section_payload,
    validate_section_payload,
    validate_section_template,
)
from s8_ppe_policy import align_s8_rows  # noqa: E402
from source_ingest import discover_source, prepare_source  # noqa: E402
from efficiency_contract import StageTimer  # noqa: E402
from evidence_packet import (  # noqa: E402
    looks_like_evidence_packet,
    packet_direct_build_errors,
)
from family_profile import FamilyProfileError, review_profile  # noqa: E402
from audit_context import AuditContext  # noqa: E402
from structured_toxicology_policy import (  # noqa: E402
    audit_field_value_integrity,
    audit_study_separation,
)
from template_mutation_whitelist import (  # noqa: E402
    clear_value_cells,
    enforce_value_typography,
    set_sequence_prefix,
    TemplateSlotRegistry,
    unique_cells,
    write_s82_top_rows,
)
import template_runtime as base  # noqa: E402

import audit_english_terminology as audit_terms  # noqa: E402
import audit_section2_release as audit_s2  # noqa: E402
import audit_openspec_overwrite as audit_openspec  # noqa: E402
import audit_template_mutation_whitelist as audit_whitelist  # noqa: E402
import audit_whitespace as audit_ws  # noqa: E402

# A historical test date must never silently become customer-facing output.
# When the caller does not provide a revision date, the runtime stamps the
# build date and formats it per language in ``format_revision_date``.
REVISION_DEFAULT = None
RESIDUAL_IDS = ("PU-2345", "PEA-4139")

# Guanzhi contact block, mirroring the approved formal template/supplier
# record.  Guocai contact comes from the skill company overlay (§14).
GUANZHI_TEL = "86-20-82567990"
GUANZHI_FAX = "86-20-32214789"
GUOCAI_TEL = "86-763-2811205"
GUOCAI_FAX = "86-763-2811024"
PINNED_TEMPLATE_SHA256 = {
    "zh": "1eb95662289577e4e49f71cff0b0456af11cf9e3e06a6752354f682a4fd76e6b",
    "en": "dca8a1a5940f4410003b032d9ec914291c1e961383305af271ba3cd6b32e495f",
    "en_source": "0c7f3bfd74a85955a32fd691a392077f79c0acc74d2c7765947e02cf7c226c3f",
}
SECTION_KEYS = {f"s{i}" for i in range(1, 17)}


def _notify_progress(callback, event: str, **details) -> None:
    """Send a small machine-readable milestone without changing build semantics."""
    if callback is None:
        return
    payload = {"event": event, **details}
    callback(payload)


def _timed(timer: StageTimer | None, name: str, **details):
    """Use the stage recorder when enabled without burdening direct callers."""
    return timer.stage(name, **details) if timer is not None else nullcontext()


def _notify_last_stage(callback, timer: StageTimer, name: str, **details) -> None:
    """Publish a completed stage without making progress a second timer."""
    if callback is None:
        return
    events = [event for event in timer.snapshot()["events"] if event["stage"] == name]
    if events:
        _notify_progress(callback, "stage_completed", stage=name,
                         seconds=events[-1]["seconds"], **details)


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


def approved_facts_errors(facts: dict, source: Path, model: str,
                          prepared_source: Path | None = None) -> list[str]:
    """Collect every facts blocker before cloning templates.

    Keeping this as a list-producing function lets the Harness run a cheap
    preflight and fix all contract errors in one review cycle.  The production
    builder still raises one release-blocking exception when the list is not
    empty, so this does not weaken any gate.
    """
    errors = []
    if looks_like_evidence_packet(facts):
        errors.extend(packet_direct_build_errors(facts, source, model))
    if not facts.get("zh") or not facts.get("en"):
        errors.append(
            "approved zh+en facts are both required; draft en with draft_en_facts.py "
            "and clear translation_review first"
        )
    if facts.get("translation_review"):
        errors.append(
            f"translation_review is not empty: {len(facts['translation_review'])} items"
        )
    errors.extend(validate_agent_execution_contract(facts))
    if facts.get("model") != model:
        errors.append(f"facts model {facts.get('model')!r} does not match {model!r}")
    source_hash = sha256(source)
    if facts.get("source_sha256") != source_hash:
        errors.append("facts source_sha256 does not match the selected original source")
    errors.extend(validate_source_mapping(facts, model, source_hash))
    errors.extend(validate_source_interpretation(facts, source, model))
    errors.extend(validate_source_grounding(
        facts, source, model, prepared_source=prepared_source
    ))
    errors.extend(audit_section2_fact_router(facts).get("errors", []))
    en_layer = facts.get("en") if isinstance(facts.get("en"), dict) else {}
    en_s1 = en_layer.get("s1") if isinstance(en_layer, dict) else None
    reviewed_en_name = ""
    if isinstance(en_s1, list) and en_s1:
        first_row = en_s1[0]
        if isinstance(first_row, dict):
            reviewed_en_name = str(first_row.get("value") or "")
        elif isinstance(first_row, (list, tuple)) and len(first_row) > 1:
            reviewed_en_name = str(first_row[1] or "")
    errors.extend(english_product_name_errors(reviewed_en_name, model))
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
        errors.extend(validate_s2_semantics(s2, language))
    return errors


def validate_approved_facts(facts: dict, source: Path, model: str,
                            prepared_source: Path | None = None) -> None:
    """Fail before cloning templates when the facts contract is unsafe."""
    errors = approved_facts_errors(
        facts, source, model, prepared_source=prepared_source
    )
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
    decisions = {
        "mapped", "omitted", "not_applicable", "source_only", "duplicate",
        "conflict", "unresolved",
    }
    locators = set()
    target_slots = set()
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
            target_slot = item.get("target_slot")
            if not isinstance(target_slot, str) or not target_slot.strip():
                errors.append(f"source_mapping item {index} mapped without target_slot")
            else:
                target_key = (item.get("target_section"), target_slot.strip())
                if target_key in target_slots:
                    errors.append(f"source_mapping duplicate target_slot: {target_slot}")
                else:
                    target_slots.add(target_key)
                if not target_slot.strip().casefold().startswith(
                    str(item.get("target_section")).casefold() + "."
                ):
                    errors.append(
                        f"source_mapping item {index} target_slot is outside target_section"
                    )
        elif decision in {"omitted", "not_applicable", "source_only", "duplicate", "conflict"}:
            if not isinstance(item.get("reason"), str) or not item["reason"].strip():
                errors.append(f"source_mapping item {index} {decision} without reason")
            if decision == "duplicate" and not isinstance(item.get("canonical_fact_id"), str):
                errors.append(f"source_mapping item {index} duplicate without canonical_fact_id")
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
    """Preserve a source-gated recommendation value without changing labels.

    The formal ``建议 / Recommendation`` label is template-owned, but its
    non-bold value cell is a permitted source input.  The source extractor
    supplies an empty value when the source has no recommendation; in that
    case the existing source-presence policy leaves the approved empty slot
    empty.  This helper remains as a named compatibility boundary so older
    callers cannot silently reintroduce unconditional blanking.
    """
    return [
        list(row) if isinstance(row, (list, tuple)) else [row]
        for row in list(rows or [])
    ]


@dataclass(frozen=True)
class SectionWritePlan:
    """Semantic payload prepared before any value or row mutation."""

    section: int
    rows: list
    inserted_data_rows: int = 0
    semantic_mode: str = "field_rows"

    def as_dict(self) -> dict:
        return {
            "section": self.section,
            "row_count": len(self.rows),
            "inserted_data_rows": self.inserted_data_rows,
            "semantic_mode": self.semantic_mode,
        }


def plan_body_write(doc, facts: dict, language: str) -> tuple[list[SectionWritePlan], dict]:
    """Resolve all section payloads before clearing cells or changing rows.

    This is the boundary between constrained semantic normalization and the
    fixed-template overwrite.  In particular, S11/S12 are aligned against the
    untouched skeleton and S9/S15 capacity is calculated before the registry
    is rebuilt.  The plan contains no DOCX mutation instructions beyond the
    explicitly authorized insertion count.
    """
    plans: list[SectionWritePlan] = []
    policy_facts = dict(facts)
    policy_facts["_local_section_policies"] = {
        str(section): local_policy_for(section) for section in range(1, 17)
    }
    baseline_row_counts = base.template_geometry(language)["rows"]
    for sec in range(1, 17):
        table = doc.tables[sec - 1]
        source_rows = sanitize_section_payload(sec, facts.get(f"s{sec}") or [])
        if sec == 2:
            source_rows = normalize_s2_projected_rows(source_rows)
        if sec == 8:
            # Keep all PPE slots in template order until after values are
            # written.  The source-presence pass may then remove empty rows,
            # but an absent hand/eye row can never shift a later fact.
            source_rows = align_s8_rows(source_rows, language)
        policy_facts[f"s{sec}"] = source_rows
        inserted_count = 0
        if sec in {9, 15}:
            inserted_count = max(
                0, len(source_rows) - (baseline_row_counts[sec - 1] - 1)
            )
        rows = base.project_rows_to_template(source_rows, language, sec, table)
        semantic_mode = "field_rows"
        if sec == 8:
            rows = suppress_s8_recommendation_value(rows, language)
            semantic_mode = "dedicated_ppe_engineering"
        if sec == 11:
            rows = align_s11_rows(source_rows, table)
            policy_facts[f"s{sec}"] = rows
            semantic_mode = "endpoint_notes"
        elif sec == 12:
            rows = align_note_section_rows(rows, table)
            policy_facts[f"s{sec}"] = rows
            semantic_mode = "endpoint_rows"
        # Capacity is intentionally checked after the planned row insertion;
        # shape/semantic checks still run now to fail before any XML mutation.
        validate_section_payload(sec, rows, table, check_capacity=False)
        plans.append(SectionWritePlan(sec, rows, inserted_count, semantic_mode))
    return plans, policy_facts


def apply_post_overwrite_fine_tuning(doc, policy_facts: dict) -> dict:
    """Apply only the bounded row/prefix policies after fixed value writes."""
    absence = apply_source_absence_policy(doc, policy_facts, unique_cells)
    s2_policy = suppress_missing_section2_rows_and_renumber(
        doc, set_paragraph_text, number_map=policy_facts.get("s2_number_map")
    )
    s9_policy = suppress_s9(doc)
    s8_policy = suppress_empty_s82_engineering_control(doc)
    return {
        "source_presence_policy": absence,
        "section2_policy": s2_policy,
        "section9_policy": s9_policy,
        "section8_policy": s8_policy,
    }


def write_body(doc, facts: dict, language: str, *, apply_fine_tuning: bool = True) -> dict:
    """Write a precomputed plan; optionally preserve the legacy one-call API."""
    plans, policy_facts = plan_body_write(doc, facts, language)
    inserted_data_rows = []
    for plan in plans:
        if plan.inserted_data_rows:
            base.ensure_source_data_rows(doc, plan.section, len(plan.rows))
            inserted_data_rows.append({
                "section": plan.section,
                "count": plan.inserted_data_rows,
            })
    # The registry is intentionally built only after all authorized insertions
    # are complete, then all value cells are cleared in one controlled pass.
    registry = TemplateSlotRegistry.from_document(doc)
    clear_value_cells(doc, registry=registry, language=language)
    skipped_slots = []
    baseline_row_counts = base.template_geometry(language)["rows"]
    for plan in plans:
        sec = plan.section
        table = doc.tables[sec - 1]
        rows = plan.rows
        validate_section_payload(sec, rows, table)
        for row_index, values in enumerate(rows, 1):
            if row_index >= len(table.rows):
                raise RuntimeError(f"template capacity mismatch S{sec}: row {row_index}")
            inserted_data_row = (
                sec in {9, 15}
                and row_index >= baseline_row_counts[sec - 1]
            )
            audit = base.set_row(table.rows[row_index], values, table_index=sec - 1,
                                 row_index=row_index, registry=registry,
                                 inserted_data_row=inserted_data_row,
                                 language=language)
            if audit:
                audit["section"] = sec
                skipped_slots.append(audit)
    write_s82_top_rows(
        doc.tables[7],
        (facts.get("s8_control_parameters") or {}).get(language, []),
        language,
    )
    result = {"skipped_blank_template_slots": skipped_slots,
              "inserted_data_rows": inserted_data_rows,
              "local_section_policies": policy_facts["_local_section_policies"],
              "semantic_write_plan": [plan.as_dict() for plan in plans],
              "_policy_facts": policy_facts}
    if apply_fine_tuning:
        fine_tuning = apply_post_overwrite_fine_tuning(doc, policy_facts)
        result.pop("_policy_facts", None)
        result.update(fine_tuning["source_presence_policy"])
    return result


def _parse_revision_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(
        r"(\d{4})\s*(?:年|[-/.])\s*(\d{1,2})\s*(?:月|[-/.])\s*(\d{1,2})",
        text,
    )
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    for pattern in ("%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def format_revision_date(language: str, revision: object) -> str:
    """Format an explicit or build-date revision without a stale fallback."""
    parsed = _parse_revision_date(revision) or date.today()
    if language == "en":
        return f"{month_name[parsed.month]} {parsed.day}, {parsed.year}"
    if language == "zh":
        return f"{parsed.year}年{parsed.month}月{parsed.day}日"
    raise ValueError(f"unsupported language: {language}")


def _footer_protection_prefix(text: str) -> str:
    """Preserve the formal template's sacrificial leading ``P`` guard."""
    return "P" if str(text or "").lstrip().startswith("P") else ""


def write_header_footer(doc, language: str, brand: str, product: str, revision: object) -> None:
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
                    prefix = _footer_protection_prefix(cells[1].text)
                    revision_text = format_revision_date(language, revision)
                    set_cell_text(cells[1],
                                  prefix + (f"Revision date: {revision_text}" if is_en
                                            else f"修订日期：{revision_text}"))


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
        updated = set_sequence_prefix(cells[0], 9, number, prefix_width=5)
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
                       language: str = "cn", audit_context=None) -> list[str]:
    template = template_document or Document(str(template_path))
    output = output_document or Document(str(docx_path))
    report = audit_whitelist.audit(template_path, docx_path,
                                   template=template, output=output,
                                   language=language, context=audit_context)
    return report.get("errors", []) if isinstance(report, dict) else []


def gate_section2(docx_path: Path, require_pictogram: bool, document=None,
                  expected_precautionary_groups=None) -> list[str]:
    errors, _info = audit_s2.run(docx_path, require_pictogram=require_pictogram,
                                 document=document,
                                 expected_precautionary_groups=expected_precautionary_groups)
    return errors


def gate_whitespace(docx_path: Path, document=None, audit_context=None) -> list[str]:
    report = audit_ws.run(str(docx_path), document=document, context=audit_context)
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


def gate_s11_row_height(template_document, output_document,
                        exception: dict | None = None) -> list[str]:
    report = audit_s11_layout(template_document, output_document, exception)
    return report.get("errors", [])


def gate_s82_layout(template_document, output_document, *, language: str,
                    expected_present: bool) -> list[str]:
    report = audit_s82(
        template_document, output_document, language=language,
        expected_present=expected_present,
    )
    return report.get("errors", [])


def gate_s114_vertical_alignment(template_document, output_document) -> list[str]:
    report = audit_s114_vertical_alignment(template_document, output_document)
    return report.get("errors", [])


def gate_product_identity(docx_path: Path, language: str, product: str,
                          document=None) -> list[str]:
    doc = document or Document(str(docx_path))
    rows = doc.tables[0].rows
    if language == "en":
        if len(rows) < 2:
            return ["Section 1 is missing the English product-name row"]
        cells = unique_cells(rows[1])
        product_value = cells[1].text if len(cells) > 1 else ""
        return [f"identity: {error}" for error in audit_english_identity(
            product_name_value=product_value, model=product,
        )]
    if language != "zh":
        return [f"unsupported identity language: {language}"]
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
    """Keep the legacy gate callable while allowing source-gated values.

    The mutation whitelist and locked-format audit validate the label and
    value-cell boundary.  A substantive recommendation is valid customer
    content; only source-presence policy decides whether an absent one stays
    empty.  There is therefore no unconditional blank-value blocker here.
    """
    return []


def gate_openspec_overwrite(template_path: Path, docx_path: Path, *,
                            language: str, template_document=None,
                            output_document=None, audit_context=None) -> list[str]:
    report = audit_openspec.audit(
        template_path, docx_path, language=language,
        template=template_document, output=output_document, context=audit_context,
    )
    return report.get("errors", [])


# ---------------------------------------------------------------- build

def build_one(*, template_cn: Path, template_en: Path, template_en_source: Path,
              source: Path, facts: dict, language: str, brand: str,
              product: str, revision: str, out_docx: Path,
              with_pictogram: bool, source_media: Path | None = None,
              template_document=None, source_sha256: str | None = None,
              template_sha256: str | None = None,
              template_en_source_sha256: str | None = None,
              timing_recorder: StageTimer | None = None) -> dict:
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
        with _timed(timing_recorder, "fixed_structure_template_overwrite",
                    language=language, brand=brand):
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
            elif language == "en" and s1 and len(s1[0]) > 1:
                # The professional English name is a reviewed fact.  Runtime
                # may normalize its whitespace and append the reviewed model,
                # but it may not derive a name from the model or touch labels.
                s1[0][1] = expected_english_product_name(s1[0][1], product)
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
            body_audit = write_body(doc, lang_facts, language, apply_fine_tuning=False)
            policy_facts = body_audit.pop("_policy_facts")
            if language == "en":
                normalize_en_document(doc, template_path=template_en,
                                      template_document=template_document)
            pictogram_audit = insert_source_pictogram(doc, source_media or source) if with_pictogram else {
                "source_image_name": None, "skipped": "source has no embedded image"}
            write_header_footer(doc, language, brand, product, revision)
            replace_residual_product_ids(doc, product)

        with _timed(timing_recorder, "post_overwrite_fine_tuning",
                    language=language, brand=brand):
            fine_tuning = apply_post_overwrite_fine_tuning(doc, policy_facts)
            s2_layout_policy = apply_precautionary_layout(doc)
            body_audit.update(fine_tuning["source_presence_policy"])
            s11_layout_policy = normalize_s11_layout(
                doc, policy_facts.get("s11") or []
            )
            enforce_value_typography(doc, language)
        s2_policy = fine_tuning["section2_policy"]
        s9_policy = fine_tuning["section9_policy"]
        s8_policy = fine_tuning["section8_policy"]
        with _timed(timing_recorder, "docx_save", language=language, brand=brand):
            doc.save(staged_docx)

        audit_context = AuditContext(doc)
        blockers: list[str] = []
        with _timed(timing_recorder, "release_audit", language=language, brand=brand):
            blockers.extend(f"locked-labels: {e}" for e in gate_locked_labels(
                template, staged_docx, template_document=template_document,
                output_document=doc, language=language,
                audit_context=audit_context))
            blockers.extend(f"section2: {e}" for e in gate_section2(
                staged_docx, require_pictogram=with_pictogram, document=doc,
                expected_precautionary_groups=expected_precautionary_group_keys(facts)))
            blockers.extend(f"whitespace: {e}" for e in gate_whitespace(
                staged_docx, document=doc, audit_context=audit_context
            ))
            blockers.extend(f"s9: {e}" for e in gate_s9_leftover(staged_docx, document=doc))
            blockers.extend(f"s11: {e}" for e in gate_s11_toxicology(staged_docx, document=doc))
            blockers.extend(f"s11-layout: {e}" for e in gate_s11_row_height(
                template_document or Document(str(template)), doc, s11_layout_policy
            ))
            blockers.extend(f"s8.2-layout: {e}" for e in gate_s82_layout(
                template_document or Document(str(template)), doc,
                language=language,
                expected_present=bool(lang_facts.get("s8_control_parameters")),
            ))
            blockers.extend(f"s11.4-alignment: {e}" for e in gate_s114_vertical_alignment(
                template_document or Document(str(template)), doc
            ))
            blockers.extend(gate_product_identity(staged_docx, language, product, document=doc))
            blockers.extend(f"s8: {e}" for e in gate_s8_recommendation(staged_docx, document=doc))
            blockers.extend(f"openspec: {e}" for e in gate_openspec_overwrite(
                template, staged_docx, language=language,
                template_document=template_document, output_document=doc,
                audit_context=audit_context,
            ))
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
        "section2_layout_policy": s2_layout_policy,
        "section2_heading_policy": {"changed": [], "locked": True},
        "pictogram": pictogram_audit,
        "section9_policy": s9_policy,
        "section8_policy": s8_policy,
        "section11_layout_policy": s11_layout_policy,
        "section8_2_layout_policy": audit_s82(
            template_document or Document(str(template)), doc,
            language=language,
            expected_present=bool(lang_facts.get("s8_control_parameters")),
        ),
        "section11_4_alignment_policy": audit_s114_vertical_alignment(
            template_document or Document(str(template)), doc
        ),
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


def gate_promoted_output_matrix(root: Path, model: str, records: list[dict],
                                do_pdf: bool) -> None:
    """Re-check the user-visible WORD/PDF matrix after atomic promotion."""
    word_root = root / "WORD"
    pdf_root = root / "PDF"
    expected_docx = set(output_names(model))
    errors = []
    for name in sorted(expected_docx):
        docx = word_root / name
        if not docx.is_file() or docx.stat().st_size == 0:
            errors.append(f"missing or empty promoted DOCX: {name}")
        if do_pdf:
            pdf = pdf_root / Path(name).with_suffix(".pdf").name
            if not pdf.is_file() or pdf.stat().st_size == 0:
                errors.append(f"missing or empty promoted PDF: {pdf.name}")
    for record in records:
        docx = Path(record.get("output_path", ""))
        if docx.parent != word_root:
            errors.append(f"DOCX is outside WORD output root: {docx}")
        if do_pdf:
            pdf = Path(record.get("pdf_path", ""))
            evidence = record.get("pdf_evidence") or {}
            if pdf.parent != pdf_root:
                errors.append(f"PDF is outside PDF output root: {pdf}")
            if evidence.get("source_sha256") != sha256(docx):
                errors.append(f"promoted PDF evidence is not bound to DOCX: {docx.name}")
            if pdf.is_file() and evidence.get("output_sha256") != sha256(pdf):
                errors.append(f"promoted PDF evidence hash mismatch: {pdf.name}")
    if errors:
        raise ReleaseBlocked("promoted output matrix: " + "; ".join(errors[:8]))


def resolve_cache_dir(out_root: Path, cache_dir: Path | None = None) -> Path:
    """Resolve one deterministic cache root for a matrix invocation."""
    if cache_dir is not None:
        return Path(cache_dir).expanduser().resolve()
    return Path(out_root).expanduser().resolve() / ".msds_cache"


def resolve_pdf_workers(requested: int, variant_count: int = 4) -> int:
    """Return a positive worker count bounded by the number of variants."""
    if requested < 1:
        raise ValueError("pdf_workers must be at least 1")
    if variant_count < 1:
        raise ValueError("variant_count must be at least 1")
    return min(int(requested), int(variant_count))


def build_matrix(*, source: Path, facts: dict, out_root: Path,
                 model: str | None = None, revision: str | None = None,
                 do_pdf: bool = True, timeout: int = 300,
                 pdf_workers: int = 2, wpscli: str | None = None,
                 progress_callback=None,
                 docx_preview_dir: Path | None = None,
                 cache_dir: Path | None = None,
                 family_profile: Path | None = None,
                 agent_review_seconds: float | None = None,
                 human_wait_seconds: float | None = None,
                 retry_count: int = 0) -> dict:
    """Build the four DOCX masters, then convert PDFs as one parallel batch.

    DOCX construction and all DOCX gates remain serial and deterministic. PDF
    conversion is independent per variant, so it can run concurrently without
    changing the semantic or template audits. ``docx_preview_dir`` is an
    optional early checkpoint for harnesses that need to inspect audited DOCX
    files while a PDF converter is still running; it is never promoted as the
    formal release matrix.
    """
    model = model or facts.get("model") or ""
    if not model:
        raise ValueError("model is required (argument or facts['model'])")
    if do_pdf:
        resolve_pdf_workers(pdf_workers)
    if agent_review_seconds is not None and agent_review_seconds < 0:
        raise ValueError("agent_review_seconds must be non-negative")
    if human_wait_seconds is not None and human_wait_seconds < 0:
        raise ValueError("human_wait_seconds must be non-negative")
    if retry_count < 0:
        raise ValueError("retry_count must be non-negative")
    timing_recorder = StageTimer()
    total_started = time.perf_counter()
    if not facts.get("zh") or not facts.get("en"):
        raise ReleaseBlocked("approved zh+en facts are both required; "
                             "draft en with draft_en_facts.py and clear translation_review first")
    if facts.get("translation_review"):
        raise ReleaseBlocked(f"translation_review is not empty: {len(facts['translation_review'])} items")
    revision = revision or facts.get("revision") or date.today()
    with _timed(timing_recorder, "extract_all_source_information", model=model):
        selection = discover_source(Path(source), model=model)
    _notify_last_stage(progress_callback, timing_recorder,
                       "extract_all_source_information", model=model)
    _notify_progress(
        progress_callback,
        "source_selected",
        model=model,
        source=str(selection.original_path),
        source_format=selection.source_format,
        source_sha256=selection.source_sha256,
    )
    requested_out_root = Path(out_root).resolve()
    cache_root = resolve_cache_dir(requested_out_root, cache_dir)
    source_prepare_started = time.perf_counter()
    with prepare_source(selection, cache_dir=cache_root) as prepared:
        prepared_source_path = prepared.extraction_path
        prepared_adapter = prepared.adapter
        source_cache_reused = prepared.cache_reused
    timing_recorder.add(
        "extract_all_source_information",
        time.perf_counter() - source_prepare_started,
        adapter=prepared_adapter,
        source_format=selection.source_format,
        cache_dir=str(cache_root),
    )
    _notify_last_stage(progress_callback, timing_recorder,
                       "extract_all_source_information",
                       adapter=prepared_adapter,
                       source_format=selection.source_format)
    family_profile_report = None
    if family_profile is not None:
        try:
            family_profile_report = review_profile(
                Path(family_profile), selection.original_path, model,
                prepared_source=prepared_source_path,
            )
        except (FamilyProfileError, OSError, ValueError) as exc:
            raise ReleaseBlocked(f"family profile: {exc}") from exc
        if family_profile_report.get("errors"):
            raise ReleaseBlocked(
                "family profile: " + "; ".join(family_profile_report["errors"][:8])
            )
        _notify_progress(
            progress_callback,
            "family_profile_reviewed",
            profile=str(Path(family_profile).expanduser().resolve()),
            suggestions=len(family_profile_report.get("suggestions", [])),
            confirmed=len(family_profile_report.get("confirmed", [])),
        )
    with _timed(timing_recorder, "constrained_information_normalization", model=model):
        validate_approved_facts(
            facts, selection.original_path, model,
            prepared_source=prepared_source_path,
        )
        source_grounding_report = audit_source_grounding(
            facts, selection.original_path, model,
            prepared_source=prepared_source_path,
        )
    _notify_last_stage(progress_callback, timing_recorder,
                       "constrained_information_normalization", model=model)
    _notify_progress(progress_callback, "facts_validated", model=model)
    matrix_root = requested_out_root / model
    matrix_root.parent.mkdir(parents=True, exist_ok=True)
    names = output_names(model)
    variants = [("zh", "guanzhi"), ("zh", "guocai"), ("en", "guanzhi"), ("en", "guocai")]
    name_map = {("zh", "guanzhi"): names[0], ("zh", "guocai"): names[1],
                ("en", "guanzhi"): names[2], ("en", "guocai"): names[3]}
    template_paths = {
        "zh": SKILL_ROOT / "examples" / "template_reference.docx",
        "en": SKILL_ROOT / "examples" / "template_reference_en.docx",
        "en_source": SKILL_ROOT / "examples" / "template_reference_en_source.docx",
    }
    with _timed(timing_recorder, "fixed_structure_template_overwrite",
                phase="template_preparation"):
        template_hashes = validate_template_baselines(
            template_paths["zh"], template_paths["en"], template_paths["en_source"])
        template_documents = {
            language: Document(str(template_paths[language])) for language in ("zh", "en")
        }
        for language, template_document in template_documents.items():
            validate_section_template(template_document, language)
    _notify_last_stage(progress_callback, timing_recorder,
                       "fixed_structure_template_overwrite", phase="template_preparation")
    template_en_source_sha256 = template_hashes["en_source"]
    converter_executable = None
    converter_version_text = None
    if do_pdf:
        # Resolve the converter before any DOCX work. A missing or unavailable
        # WPS CLI must fail in seconds rather than after a long partial run.
        with _timed(timing_recorder, "pdf_converter_preflight"):
            converter_executable = find_wpscli(wpscli)
            converter_version_text = converter_version(converter_executable)
        preflight_timeout = min(max(timeout, 1), 30)
        _notify_progress(
            progress_callback,
            "pdf_preflight_started",
            executable=converter_executable,
            version=converter_version_text,
            timeout_seconds=preflight_timeout,
        )
        preflight_started = time.perf_counter()
        preflight_pdf(
            template_paths["zh"],
            timeout=preflight_timeout,
            wpscli=converter_executable,
            converter_version=converter_version_text,
        )
        preflight_seconds = round(time.perf_counter() - preflight_started, 3)
        _notify_progress(
            progress_callback,
            "pdf_converter_ready",
            executable=converter_executable,
            version=converter_version_text,
            preflight_seconds=preflight_seconds,
        )
    _notify_progress(
        progress_callback,
        "templates_ready",
        languages=["zh", "en"],
        template_sha256={"zh": template_hashes["zh"], "en": template_hashes["en"]},
    )
    records = []
    timing = {
        "variants": [],
        "docx_seconds": 0.0,
        "pdf_seconds": 0.0,
        "cache": {
            "root": str(cache_root),
            "source_adapter": prepared_adapter,
            "source_cache_reused": source_cache_reused,
            "evidence_packet": "not-used-by-build",
        },
        "pdf": {
            "workers": None,
            "batch_seconds": 0.0,
            "converter": converter_version_text,
            "lineage_verified": None,
            "failures": [],
            "retries": retry_count,
        },
    }
    with tempfile.TemporaryDirectory(prefix=f".{model}_matrix_", dir=matrix_root.parent) as stage_dir:
        stage_root = Path(stage_dir)
        with_pictogram = source_has_images(prepared_source_path)
        for variant_index, (language, brand) in enumerate(variants):
            out_docx = stage_root / name_map[(language, brand)]
            variant_started = time.perf_counter()
            _notify_progress(
                progress_callback,
                "docx_started",
                index=variant_index + 1,
                total=len(variants),
                language=language,
                brand=brand,
            )
            record = build_one(
                template_cn=SKILL_ROOT / "examples" / "template_reference.docx",
                template_en=SKILL_ROOT / "examples" / "template_reference_en.docx",
                template_en_source=SKILL_ROOT / "examples" / "template_reference_en_source.docx",
                source=selection.original_path, source_media=prepared_source_path,
                facts=facts, language=language, brand=brand,
                product=model, revision=revision, out_docx=out_docx,
                with_pictogram=with_pictogram,
                template_document=template_documents[language],
                source_sha256=selection.source_sha256,
                template_sha256=template_hashes[language],
                template_en_source_sha256=template_en_source_sha256,
                timing_recorder=timing_recorder)
            docx_seconds = time.perf_counter() - variant_started
            timing["docx_seconds"] += docx_seconds
            timing_item = {"language": language, "brand": brand,
                           "docx_seconds": round(docx_seconds, 3),
                           "pdf_seconds": 0.0}
            timing["variants"].append(timing_item)
            records.append(record)
            _notify_progress(
                progress_callback,
                "docx_ready",
                index=variant_index + 1,
                total=len(variants),
                language=language,
                brand=brand,
                seconds=timing_item["docx_seconds"],
                workflow_stages=["fixed_structure_template_overwrite",
                                 "post_overwrite_fine_tuning", "release_audit"],
                staged_path=str(out_docx),
            )

        if docx_preview_dir is not None:
            preview_started = time.perf_counter()
            preview_root = Path(docx_preview_dir).resolve()
            if preview_root == matrix_root:
                raise ValueError("docx_preview_dir must differ from out_root")
            preview_root.mkdir(parents=True, exist_ok=True)
            for record in records:
                staged = Path(record["output_path"])
                preview = preview_root / staged.name
                shutil.copy2(staged, preview)
                record["docx_preview_path"] = str(preview)
            timing_recorder.add("docx_preview_checkpoint",
                                time.perf_counter() - preview_started,
                                count=len(records))
            _notify_progress(
                progress_callback,
                "docx_preview_ready",
                directory=str(preview_root),
                count=len(records),
            )

        if do_pdf:
            workers = resolve_pdf_workers(pdf_workers, len(records))
            timing["pdf"]["workers"] = workers
            timing["pdf"]["converter"] = converter_version_text
            _notify_progress(
                progress_callback,
                "pdf_batch_started",
                workers=workers,
                count=len(records),
            )

            def convert_variant(index: int, record: dict):
                out_docx = Path(record["output_path"])
                out_pdf = out_docx.with_suffix(".pdf")
                pdf_started = time.perf_counter()
                evidence = convert_pdf(
                    out_docx,
                    out_pdf,
                    timeout=timeout,
                    wpscli=converter_executable,
                    converter_version=converter_version_text,
                )
                return index, out_pdf, evidence, time.perf_counter() - pdf_started

            pdf_batch_started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=workers,
                                    thread_name_prefix="msds-pdf") as executor:
                futures = {
                    executor.submit(convert_variant, index, record): index
                    for index, record in enumerate(records)
                }
                for future in as_completed(futures):
                    try:
                        index, out_pdf, evidence, elapsed = future.result()
                    except Exception as exc:
                        timing["pdf"]["failures"].append({
                            "type": type(exc).__name__,
                            "message": str(exc),
                        })
                        timing_recorder.add(
                            "pdf_conversion_failure", 0.0, status="failed",
                            error_type=type(exc).__name__,
                        )
                        raise
                    timing_item = timing["variants"][index]
                    timing_item["pdf_seconds"] = round(elapsed, 3)
                    timing["pdf_seconds"] += timing_item["pdf_seconds"]
                    records[index]["pdf_path"] = str(out_pdf)
                    records[index]["pdf_evidence"] = evidence
                    _notify_progress(
                        progress_callback,
                        "pdf_ready",
                        index=index + 1,
                        total=len(records),
                        language=records[index]["language"],
                        brand=records[index]["brand"],
                        seconds=timing_item["pdf_seconds"],
                    )
            pdf_batch_seconds = time.perf_counter() - pdf_batch_started
            timing["pdf"]["batch_seconds"] = round(pdf_batch_seconds, 3)
            timing_recorder.add("pdf_conversion_batch", pdf_batch_seconds,
                                workers=workers, count=len(records))
        gate_output_matrix(stage_root, model, records, do_pdf)
        matrix_root.mkdir(parents=True, exist_ok=True)
        word_root = matrix_root / "WORD"
        pdf_root = matrix_root / "PDF"
        word_root.mkdir(parents=True, exist_ok=True)
        if do_pdf:
            pdf_root.mkdir(parents=True, exist_ok=True)
        expected_docx = set(output_names(model))
        for name in sorted(expected_docx):
            os.replace(stage_root / name, word_root / name)
            if do_pdf:
                pdf_name = Path(name).with_suffix(".pdf").name
                os.replace(stage_root / pdf_name, pdf_root / pdf_name)
        for record in records:
            old_docx = Path(record["output_path"])
            final_docx = word_root / old_docx.name
            record["output_path"] = str(final_docx)
            if do_pdf:
                old_pdf = Path(record["pdf_path"])
                final_pdf = pdf_root / old_pdf.name
                record["pdf_path"] = str(final_pdf)
                record["pdf_evidence"]["source_docx"] = str(final_docx)
                record["pdf_evidence"]["output_pdf"] = str(final_pdf)
            record["docx_sha256"] = sha256(final_docx)
            if do_pdf:
                record["pdf_sha256"] = sha256(final_pdf)
        gate_promoted_output_matrix(matrix_root, model, records, do_pdf)
    if do_pdf:
        timing["pdf"]["lineage_verified"] = all(
            (record.get("pdf_evidence") or {}).get("source_is_final_docx") is True
            and (record.get("pdf_evidence") or {}).get("source_sha256") == record.get("docx_sha256")
            and (record.get("pdf_evidence") or {}).get("output_sha256") == record.get("pdf_sha256")
            for record in records
        )
    stage_snapshot = timing_recorder.snapshot()
    timing["stage_events"] = stage_snapshot["events"]
    timing["stage_totals"] = stage_snapshot["totals"]
    timing["stage_total_seconds"] = stage_snapshot["total_seconds"]
    timing["total_seconds"] = round(time.perf_counter() - total_started, 3)
    timing["time_categories"] = {
        "machine": {
            "seconds": timing["total_seconds"],
            "source": "measured-by-pipeline",
        },
        "agent_review": {
            "seconds": agent_review_seconds,
            "source": "supplied" if agent_review_seconds is not None else "not-supplied",
        },
        "human_wait": {
            "seconds": human_wait_seconds,
            "source": "supplied" if human_wait_seconds is not None else "not-supplied",
        },
        "retry": {
            "seconds": 0.0,
            "count": retry_count,
            "source": "supplied-pipeline-count",
        },
    }
    report = {
        "telemetry_schema_version": "3.26.0",
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
        "cache_dir": str(cache_root),
        "family_profile": family_profile_report,
        "records": records,
        "output_root": str(matrix_root),
        "word_root": str(matrix_root / "WORD"),
        "pdf_root": str(matrix_root / "PDF") if do_pdf else None,
        "source_grounding": source_grounding_report,
        "timing": timing,
    }
    (matrix_root / "matrix-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _notify_progress(
        progress_callback,
        "matrix_ready",
        model=model,
        docx_count=report["docx_count"],
        pdf_count=report["pdf_count"],
        seconds=timing["total_seconds"],
        out=str(matrix_root),
    )
    return report
