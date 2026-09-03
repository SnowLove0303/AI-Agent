"""Deterministic scoring, evidence, and package-discovery primitives.

This module is deliberately independent from document generation.  Existing
auditors can be adapted into :class:`EvidenceRecord` values without changing
the template overwrite pipeline.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import hashlib
import json
import re
from typing import Any, Iterable

EVIDENCE_SCHEMA_VERSION = "1.0"
STATUSES = {"PASS", "FAIL", "NOT_CHECKED", "ERROR", "OBSERVED"}
SEVERITIES = {"B0", "B1", "B2", "NONE"}
OUTCOMES = {"RELEASE_PASS", "RELEASE_FAIL", "NOT_READY", "OBSERVATION_ONLY"}
CATEGORY_WEIGHTS = {
    "source_semantics": 30,
    "template_control": 25,
    "docx_visual": 20,
    "four_format": 10,
    "pdf_quality": 10,
    "package_evidence": 5,
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    points: float
    severity: str
    source_of_truth: str
    pass_condition: str
    evidence_kind: str
    description: str


RULES = (
    Rule("ID-001", "package_evidence", 1, "B0", "eight-file contract", "Exactly one DOCX and one PDF exist for each matrix slot", "file", "Eight-file identity and completeness"),
    Rule("ID-002", "source_semantics", 3, "B1", "source and matrix report", "Product and source identities are present and consistent", "identity", "Product/source identity"),
    Rule("SRC-001", "source_semantics", 8, "B1", "source MSDS", "Output facts are traceable to the verified source semantic payload", "source-map", "Source fact fidelity"),
    Rule("SRC-002", "source_semantics", 5, "B1", "template/example exclusion rule", "Illustrative template facts and unsupported inference are absent", "text-scan", "Example-fact and inference leakage"),
    Rule("SRC-003", "source_semantics", 4, "B1", "semantic mapping policy", "Existing source data is classified into the correct endpoint", "mapping", "Semantic endpoint classification"),
    Rule("S2-001", "source_semantics", 3, "B1", "Section 2 GHS policy", "Pictogram, label tips, line breaks, omission and numbering rules pass", "section", "Section 2"),
    Rule("S3-001", "source_semantics", 2, "B1", "Section 3 component rule", "Each component occupies exactly one data row", "section", "Section 3 one-component-per-row"),
    Rule("S8-001", "template_control", 3, "B1", "Section 8 mapping policy", "Hand protection, 8.2 engineering controls and locked 8.1 are preserved", "section", "Section 8"),
    Rule("S9-001", "source_semantics", 2, "B1", "Section 9 omission policy", "Missing-data property rows are omitted and surviving items are renumbered", "section", "Section 9"),
    Rule("S11-001", "source_semantics", 3, "B1", "structured toxicology policy", "Existing toxicology is retained as structured source-grounded fields through 11.10", "section", "Section 11"),
    Rule("S14-001", "template_control", 1, "B1", "Section 14 line-break policy", "Transport fields use the required logical line breaks", "section", "Section 14"),
    Rule("TPL-001", "template_control", 8, "B0", "maintained template hash/snapshot", "Output lineage and geometry match the language-specific maintained template", "geometry", "Template lineage and geometry"),
    Rule("TPL-002", "template_control", 7, "B0", "mutation whitelist", "Only whitelisted value-cell/row mutations occur", "whitelist", "Controlled mutation"),
    Rule("TPL-003", "template_control", 6, "B0", "locked skeleton contract", "Sequence/label columns and protected XML/format properties are unchanged", "locked-skeleton", "Locked skeleton"),
    Rule("PAR-001", "four_format", 5, "B1", "unified semantic model", "Four variants have equivalent product facts and section presence", "parity", "Semantic parity"),
    Rule("PAR-002", "four_format", 5, "B1", "company overlay policy", "Only approved company fields vary by company", "parity", "Company parity"),
    Rule("PDF-001", "pdf_quality", 5, "B0", "DOCX-first publication contract", "Every PDF is traceable to its corresponding final DOCX", "derivation", "DOCX-to-PDF derivation"),
    Rule("PDF-002", "pdf_quality", 5, "B1", "PDF render QA", "PDF page structure and critical-page visual QA pass", "pdf-qa", "PDF structural and visual QA"),
    Rule("DOCX-001", "docx_visual", 12, "B1", "DOCX render QA", "Final DOCX pages render without clipping, overflow, blank pages, or missing images", "docx-qa", "DOCX structural and visual QA"),
    Rule("DOCX-002", "docx_visual", 8, "B2", "DOCX readability policy", "Critical sections and customer-facing text remain readable after rendering", "docx-qa", "DOCX readability"),
    Rule("PKG-001", "package_evidence", 2, "B1", "release package contract", "Clean package has one root, exact manifest, and no transient artifacts", "zip", "ZIP/package integrity"),
    Rule("PKG-002", "package_evidence", 2, "B1", "V2.9 inheritance contract", "V2.9 inheritance audit and required release audits pass", "audit", "Legacy and release audit coverage"),
)


@dataclass
class EvidenceRecord:
    rule_id: str
    category: str
    severity: str
    status: str
    source_of_truth: str
    method: str
    pass_condition: str
    observed: Any = None
    evidence_paths: list[str] = field(default_factory=list)
    message: str = ""
    points_awarded: float = 0
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def rule_map() -> dict[str, Rule]:
    result = {rule.rule_id: rule for rule in RULES}
    if len(result) != len(RULES):
        raise ValueError("duplicate rule_id in audit registry")
    for rule in RULES:
        if rule.category not in CATEGORY_WEIGHTS or rule.severity not in SEVERITIES:
            raise ValueError(f"invalid rule metadata: {rule.rule_id}")
    return result


def evidence(rule_id: str, status: str, *, method: str, observed: Any = None,
             evidence_paths: Iterable[str] = (), message: str = "",
             severity: str | None = None, points_awarded: float | None = None) -> EvidenceRecord:
    rule = rule_map()[rule_id]
    if status not in STATUSES:
        raise ValueError(f"invalid evidence status: {status}")
    sev = severity or (rule.severity if status == "FAIL" else "NONE")
    if sev not in SEVERITIES:
        raise ValueError(f"invalid evidence severity: {sev}")
    awarded = points_awarded if points_awarded is not None else (rule.points if status in {"PASS", "OBSERVED"} else 0)
    return EvidenceRecord(rule_id, rule.category, sev, status, rule.source_of_truth,
                          method, rule.pass_condition, observed,
                          [str(Path(p)) for p in evidence_paths], message, awarded)


def validate_evidence(records: Iterable[EvidenceRecord], *, require_all: bool = True) -> list[str]:
    records = list(records)
    errors: list[str] = []
    known = rule_map()
    seen: set[str] = set()
    for record in records:
        if record.rule_id not in known:
            errors.append(f"unknown rule_id: {record.rule_id}")
        if record.rule_id in seen:
            errors.append(f"duplicate evidence rule_id: {record.rule_id}")
        seen.add(record.rule_id)
        if record.status not in STATUSES:
            errors.append(f"invalid status for {record.rule_id}: {record.status}")
        if record.severity not in SEVERITIES:
            errors.append(f"invalid severity for {record.rule_id}: {record.severity}")
        if not record.source_of_truth or not record.method or not record.pass_condition:
            errors.append(f"missing provenance fields: {record.rule_id}")
        if record.status in {"PASS", "FAIL", "OBSERVED"} and not record.message:
            errors.append(f"missing message: {record.rule_id}")
        if record.status in {"PASS", "FAIL", "OBSERVED"} and not record.evidence_paths:
            errors.append(f"missing evidence path: {record.rule_id}")
    if require_all:
        missing = sorted(set(known) - seen)
        errors.extend(f"missing required rule: {rule_id}" for rule_id in missing)
    return errors


def score_and_decide(records: Iterable[EvidenceRecord], *, observation_only: bool = False) -> dict[str, Any]:
    records = sorted(records, key=lambda r: r.rule_id)
    errors = validate_evidence(records, require_all=True)
    score = round(sum(r.points_awarded for r in records), 2)
    blockers = [r.to_dict() for r in records if r.status == "FAIL" and r.severity in {"B0", "B1"}]
    incomplete = [r.to_dict() for r in records if r.status in {"NOT_CHECKED", "ERROR"}]
    if observation_only:
        outcome = "OBSERVATION_ONLY"
    elif blockers:
        outcome = "RELEASE_FAIL"
    elif errors or incomplete or len(records) != len(RULES):
        outcome = "NOT_READY"
    elif score >= 95:
        outcome = "RELEASE_PASS"
    else:
        outcome = "NOT_READY"
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "score": score,
        "score_max": 100,
        "outcome": outcome,
        "blockers": blockers,
        "incomplete": incomplete,
        "evidence_errors": errors,
        "records": [r.to_dict() for r in records],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


MATRIX = {
    "cn_guanzhi": ("MSDS_CN_冠志", "MSDS_CN_Guanzhi"),
    "cn_guocai": ("MSDS_CN_国彩", "MSDS_CN_Guocai"),
    "en_guanzhi": ("MSDS_EN_冠志", "MSDS_EN_Guanzhi"),
    "en_guocai": ("MSDS_EN_国彩", "MSDS_EN_Guocai"),
}


def discover_package(root: Path, model: str) -> dict[str, Any]:
    """Find exactly one file per matrix slot, allowing nested variant folders."""
    root = Path(root)
    files: dict[str, dict[str, str | None]] = {}
    errors: list[str] = []
    all_files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
    for key, aliases in MATRIX.items():
        item: dict[str, str | None] = {}
        for ext in ("docx", "pdf"):
            names = {f"{model}_{suffix}.{ext}" for suffix in aliases}
            matches = sorted(p for p in all_files if p.name in names)
            if len(matches) != 1:
                errors.append(f"{key}.{ext}: expected 1, found {len(matches)}")
                item[ext] = None if not matches else "|".join(str(p) for p in matches)
            elif matches[0].stat().st_size == 0:
                errors.append(f"{key}.{ext}: zero-byte file")
                item[ext] = str(matches[0])
            else:
                item[ext] = str(matches[0])
        files[key] = item
    return {"root": str(root), "model": model, "files": files, "errors": errors,
            "complete": not errors}


def write_reports(result: dict[str, Any], json_path: Path, text_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"MSDS deliverable audit {result.get('schema_version', EVIDENCE_SCHEMA_VERSION)}",
        f"Model: {result.get('model', '')}",
        f"Outcome: {result.get('outcome', 'NOT_READY')}",
        f"Score: {result.get('score', 0)}/{result.get('score_max', 100)}",
        "",
        "Rule results:",
    ]
    for record in result.get("records", []):
        lines.append(f"- {record['rule_id']} [{record['status']}/{record['severity']}] {record['message']}")
    if result.get("blockers"):
        lines.extend(["", "Blockers:"] + [f"- {r['rule_id']}: {r['message']}" for r in result["blockers"]])
    if result.get("evidence_errors"):
        lines.extend(["", "Evidence errors:"] + [f"- {e}" for e in result["evidence_errors"]])
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
