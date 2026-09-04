#!/usr/bin/env python3
"""Shared DOCX-first build pipeline for the unified MSDS skill (v3.14.2).

Business role: one parameterized path replaces the per-model copied
generators.  Input is an *approved* standardized model file::

    {"model": ..., "revision": ..., "source_sha256": ...,
     "zh": {"s1": [...], ..., "s16": [...]},
     "en": {...} | null,
     "s8_control_parameters": {"zh": [...], "en": [...]},
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
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SKILL_ROOT = SCRIPTS.parent
BASE_PATH = SKILL_ROOT / "_task_work" / "generate_pu2345_eight.py"

_base_spec = importlib.util.spec_from_file_location("msds_base", BASE_PATH)
base = importlib.util.module_from_spec(_base_spec)
_base_spec.loader.exec_module(base)

from compact_cn_layout import compact_cn_document, normalize_footer  # noqa: E402
from convert_docx_to_pdf import convert as convert_pdf  # noqa: E402
from ghs_pictogram_policy import extract_first_embedded_image, insert_source_pictogram  # noqa: E402
from normalize_en_layout import normalize_en_document  # noqa: E402
from output_matrix import output_names  # noqa: E402
from section2_ghs_policy import (  # noqa: E402
    is_missing_section2_value,
    row_has_visual_content,
    suppress_missing_section2_rows_and_renumber,
)
from section2_hp_policy import is_missing_data_value  # noqa: E402
from structured_toxicology_policy import (  # noqa: E402
    audit_field_value_integrity,
    audit_study_separation,
)
from template_mutation_whitelist import (  # noqa: E402
    clear_value_cells,
    compare_locked_skeleton,
    set_sequence_prefix,
    unique_cells,
    write_s82_top_rows,
)

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


def write_body(doc, facts: dict, language: str) -> None:
    clear_value_cells(doc)
    for sec in range(1, 17):
        table = doc.tables[sec - 1]
        rows = base.project_rows_to_template(facts[f"s{sec}"], language, sec, table)
        for row_index, values in enumerate(rows, 1):
            if row_index >= len(table.rows):
                raise RuntimeError(f"template capacity mismatch S{sec}: row {row_index}")
            base.set_row(table.rows[row_index], values, table_index=sec - 1, row_index=row_index)
    write_s82_top_rows(
        doc.tables[7],
        (facts.get("s8_control_parameters") or {}).get(language, []),
        language,
    )


def write_header_footer(doc, language: str, brand: str, product: str, revision: str) -> None:
    is_en = language == "en"
    company_name, _ = company(language, brand)
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            if "Version" in paragraph.text or "版本" in paragraph.text:
                set_paragraph_text(paragraph, "Version: 1.0" if is_en else "版本：1.0")
            elif paragraph.text.strip() and ("安全" in paragraph.text or "Material" in paragraph.text):
                set_paragraph_text(paragraph, "Material Safety Data Sheet" if is_en else "物料安全数据表")
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


# ---------------------------------------------------------------- gates

def gate_locked_labels(template_path: Path, docx_path: Path) -> list[str]:
    template = Document(str(template_path))
    output = Document(str(docx_path))
    errors = compare_locked_skeleton(template, output)
    report = audit_whitelist.audit(template_path, docx_path)
    if isinstance(report, dict) and report.get("errors"):
        errors.extend(report["errors"])
    return errors


def gate_section2(docx_path: Path, require_pictogram: bool) -> list[str]:
    errors, _info = audit_s2.run(docx_path, require_pictogram=require_pictogram)
    return errors


def gate_whitespace(docx_path: Path) -> list[str]:
    report = audit_ws.run(str(docx_path))
    return [json.dumps(issue, ensure_ascii=False) for issue in report.get("issues", [])]


def gate_terminology(docx_path: Path) -> list[str]:
    return audit_terms.run(docx_path)


def gate_s11_toxicology(docx_path: Path) -> list[str]:
    doc = Document(str(docx_path))
    table = doc.tables[10]
    lines = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        for cell in cells[1:]:
            lines.extend(line for line in cell.text.split("\n") if line.strip())
    return audit_field_value_integrity(lines) + audit_study_separation(lines)


def gate_s9_leftover(docx_path: Path) -> list[str]:
    doc = Document(str(docx_path))
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


# ---------------------------------------------------------------- build

def build_one(*, template_cn: Path, template_en: Path, template_en_source: Path,
              source: Path, facts: dict, language: str, brand: str,
              product: str, revision: str, out_docx: Path,
              with_pictogram: bool) -> dict:
    template = template_for(template_cn, template_en, language)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, out_docx)
    doc = Document(str(out_docx))
    base.validate_template_capacity(doc, language)
    lang_facts = {key: (list(value) if isinstance(value, list) else value)
                  for key, value in facts[language].items()}
    # Company overlay is brand-authoritative: S1 supplier rows always come
    # from the approved profile, never from the facts payload.
    company_name, company_addr = company(language, brand)
    tel = company_tel(language, brand)
    fax = company_fax(language, brand)
    supplier_rows = [[None, company_name], [None, company_addr], [None, tel], [None, fax]]
    s1 = [list(row) for row in lang_facts["s1"]]
    for offset, (_, value) in enumerate(supplier_rows):
        if len(s1) > 5 + offset and len(s1[5 + offset]) > 1:
            s1[5 + offset][1] = value
    lang_facts["s1"] = s1
    lang_facts["s8_control_parameters"] = (facts.get("s8_control_parameters") or {}).get(language, [])
    base.ensure_s3_component_rows(doc, component_count=len(lang_facts["s3"]) - 3)
    write_body(doc, lang_facts, language)
    if language == "en":
        base.normalize_en_document(doc, template_path=template_en)
    pictogram_audit = insert_source_pictogram(doc, source) if with_pictogram else {
        "source_image_name": None, "skipped": "source has no embedded image"}
    s2_policy = suppress_missing_section2_rows_and_renumber(doc, set_paragraph_text)
    s9_policy = suppress_s9(doc)
    write_header_footer(doc, language, brand, product, revision)
    replace_residual_product_ids(doc, product)
    if language == "zh":
        base.compact_cn_document(doc)
    else:
        base.normalize_footer(doc)
    doc.save(out_docx)

    blockers: list[str] = []
    blockers.extend(f"locked-labels: {e}" for e in gate_locked_labels(template, out_docx))
    blockers.extend(f"section2: {e}" for e in gate_section2(out_docx, require_pictogram=with_pictogram))
    blockers.extend(f"whitespace: {e}" for e in gate_whitespace(out_docx))
    blockers.extend(f"s9: {e}" for e in gate_s9_leftover(out_docx))
    blockers.extend(f"s11: {e}" for e in gate_s11_toxicology(out_docx))
    if language == "en":
        blockers.extend(f"terminology: {e}" for e in gate_terminology(out_docx))
    if blockers:
        raise ReleaseBlocked(f"{language}/{brand}: " + "; ".join(blockers[:8]))
    return {
        "product": product,
        "brand": brand,
        "language": "en-US" if language == "en" else "zh-CN",
        "source_docx": str(source),
        "source_docx_sha256": sha256(source),
        "template_reference": str(template),
        "template_reference_sha256": sha256(template),
        "template_source_reference": str(template_en_source) if language == "en" else None,
        "template_source_reference_sha256": sha256(template_en_source) if language == "en" else None,
        "template_geometry": base.template_geometry(language),
        "output_geometry": {"table_count": 16,
                            "rows": [len(table.rows) for table in Document(str(out_docx)).tables],
                            "s3_component_rows": len(lang_facts["s3"]) - 3},
        "section2_policy": s2_policy,
        "pictogram": pictogram_audit,
        "section9_policy": s9_policy,
        "status": "ready",
        "formal_ready": True,
        "blockers": [],
        "translation_review": [] if language == "zh" else [{"status": "reviewed-model-translation"}],
        "output_path": str(out_docx),
    }


def source_has_images(source: Path) -> bool:
    import zipfile

    with zipfile.ZipFile(source) as archive:
        return any(name.startswith("word/media/") and not name.endswith("/")
                   for name in archive.namelist())


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
    out_root.mkdir(parents=True, exist_ok=True)
    names = output_names(model)
    variants = [("zh", "guanzhi"), ("zh", "guocai"), ("en", "guanzhi"), ("en", "guocai")]
    name_map = {("zh", "guanzhi"): names[0], ("zh", "guocai"): names[1],
                ("en", "guanzhi"): names[2], ("en", "guocai"): names[3]}
    with_pictogram = source_has_images(source)
    records = []
    for language, brand in variants:
        out_docx = out_root / name_map[(language, brand)]
        record = build_one(
            template_cn=SKILL_ROOT / "examples" / "template_reference.docx",
            template_en=SKILL_ROOT / "examples" / "template_reference_en.docx",
            template_en_source=SKILL_ROOT / "examples" / "template_reference_en_source.docx",
            source=source, facts=facts, language=language, brand=brand,
            product=model, revision=revision, out_docx=out_docx,
            with_pictogram=with_pictogram)
        if do_pdf:
            out_pdf = out_docx.with_suffix(".pdf")
            evidence = convert_pdf(out_docx, out_pdf, timeout=timeout)
            record["pdf_path"] = str(out_pdf)
            record["pdf_evidence"] = evidence
        records.append(record)
    report = {
        "product": model,
        "matrix": "2 brands x 2 languages x 2 formats" if do_pdf else "2 brands x 2 languages (DOCX only)",
        "docx_count": 4,
        "pdf_count": 4 if do_pdf else 0,
        "formal_ready_count": 4,
        "draft_count": 0,
        "shared_blocker": None,
        "source_docx_sha256": sha256(source),
        "records": records,
    }
    (out_root / "matrix-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
