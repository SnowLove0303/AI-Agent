#!/usr/bin/env python3
"""Run the unified customer-deliverable audit over one eight-file package."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from zipfile import ZipFile
from xml.etree import ElementTree

from deliverable_audit_framework import (
    RULES, discover_package, evidence, load_json, score_and_decide,
    write_reports,
)
from audit_english_terminology import run as audit_english_terminology


def _paths(package: dict) -> list[str]:
    return [p for item in package["files"].values() for p in item.values() if p]


def _matrix_report(root: Path, explicit: Path | None) -> tuple[dict | None, list[str]]:
    candidates = [explicit] if explicit else [root / "matrix-report.json", *root.rglob("matrix-report.json")]
    for p in candidates:
        if p and p.exists():
            data = load_json(p)
            if data is not None:
                return data, [str(p)]
    return None, []


def _docx_text(path: Path) -> str:
    """Extract visible Word text without requiring python-docx at runtime."""
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return "\n".join(texts)


def run_audit(root: Path, model: str, *, template_cn: Path | None = None,
              template_en: Path | None = None, matrix_report: Path | None = None,
              observation_only: bool = False) -> dict:
    package = discover_package(root, model)
    report, report_paths = _matrix_report(root, matrix_report)
    paths = _paths(package)
    records = []
    records.append(evidence("ID-001", "PASS" if package["complete"] else "FAIL",
                            method="deterministic recursive matrix discovery", observed=package,
                            evidence_paths=paths or [str(root)],
                            message="Eight-file matrix is complete and non-empty" if package["complete"] else "; ".join(package["errors"])))
    identity_ok = bool(report and report.get("product") == model and report.get("docx_count") == 4 and report.get("pdf_count") == 4)
    records.append(evidence("ID-002", "PASS" if identity_ok else "NOT_CHECKED",
                            method="matrix-report identity comparison", observed=report or {},
                            evidence_paths=report_paths or [str(root)],
                            message="Product identity and four DOCX/four PDF counts agree" if identity_ok else "No independently readable matrix identity evidence"))

    # Existing generation reports are treated as adapters, not as replacements
    # for the source.  A package without a report stays NOT_CHECKED (fail closed).
    formal = bool(report and report.get("formal_ready_count") == 4 and not report.get("shared_blocker"))
    for rid, label in (("SRC-001", "Source-fidelity audit"), ("SRC-003", "Semantic mapping audit"),
                       ("S2-001", "Section 2 audit"), ("S3-001", "Section 3 row audit"),
                       ("S8-001", "Section 8 audit"), ("S9-001", "Section 9 omission/order audit"),
                       ("S11-001", "Section 11 structured-toxicology audit"),
                       ("S14-001", "Section 14 line-break audit")):
        ok = formal
        records.append(evidence(rid, "PASS" if ok else "NOT_CHECKED", method="existing matrix-report release adapter",
                                observed={"formal_ready": formal}, evidence_paths=report_paths or [str(root)],
                                message=f"{label} passed through existing release evidence" if ok else f"{label} has no complete evidence"))

    # Scan all extracted OOXML text for customer-facing drafting/provenance
    # phrases and obvious maintained-template sample identity leakage.
    banned = ["源文件未提供", "源文件记载", "按源文件列示", "见2.4-2.6", "See 2.4-2.6", "source file not provided"]
    sample_ids = ["PEA-4139"]
    text_hits = []
    if package["complete"]:
        try:
            for p in [Path(x) for x in paths if x.lower().endswith(".docx")]:
                text = _docx_text(p)
                for needle in banned + sample_ids:
                    if needle in text:
                        text_hits.append(f"{p.name}: {needle}")
                if "_MSDS_EN_" in p.name:
                    text_hits.extend(
                        f"{p.name}: ENGLISH_TERMINOLOGY {issue}"
                        for issue in audit_english_terminology(p, baseline=template_en)
                    )
        except Exception as exc:
            text_hits.append(f"text scan error: {exc}")
        records.append(evidence(
            "SRC-002", "FAIL" if text_hits else "PASS", method="DOCX text scan",
            observed=text_hits, evidence_paths=[str(root)],
            message=("Forbidden drafting/example text found: " + "; ".join(text_hits)
                     if text_hits else "No forbidden drafting or PEA example text found"),
        ))
    else:
        # Duplicate/missing matrix slots already block release.  Do not open
        # every candidate DOCX in an incomplete tree: a deployment folder
        # containing stale copies used to spend minutes in a needless scan
        # after the decisive duplicate error was already known.
        records.append(evidence(
            "SRC-002", "NOT_CHECKED", method="DOCX text scan short-circuit",
            observed={"skipped": "incomplete matrix"}, evidence_paths=[str(root)],
            message="Skipped DOCX text scan because matrix discovery is incomplete",
        ))

    for rid, label in (("DOCX-001", "DOCX structural/visual QA"), ("DOCX-002", "DOCX readability QA")):
        ok = formal
        records.append(evidence(rid, "PASS" if ok else "NOT_CHECKED", method="existing matrix-report render-QA adapter",
                                observed={"formal_ready": formal}, evidence_paths=report_paths or [str(root)],
                                message=f"{label} passed through existing release evidence" if ok else f"{label} has no complete evidence"))

    # Template and whitelist checks are complete only when a matrix report
    # confirms the production audits.  Direct template arguments strengthen
    # evidence; absence remains NOT_CHECKED rather than a false pass.
    template_ok = formal and bool(template_cn and template_en and template_cn.exists() and template_en.exists())
    for rid, label in (("TPL-001", "Template geometry/lineage"), ("TPL-002", "Mutation whitelist"), ("TPL-003", "Locked skeleton")):
        records.append(evidence(rid, "PASS" if template_ok else "NOT_CHECKED", method="template arguments plus release adapter",
                                observed={"template_cn": str(template_cn) if template_cn else None, "template_en": str(template_en) if template_en else None},
                                evidence_paths=[str(p) for p in (template_cn, template_en) if p] or [str(root)],
                                message=f"{label} evidence is present" if template_ok else f"{label} requires maintained CN/EN template arguments and release evidence"))

    for rid, label in (("PAR-001", "Four-format semantic parity"), ("PAR-002", "Company parity"),
                       ("PDF-001", "DOCX-to-PDF derivation"), ("PDF-002", "PDF structural/visual QA"),
                       ("PKG-001", "Package integrity"), ("PKG-002", "Legacy/release audit coverage")):
        ok = formal
        records.append(evidence(rid, "PASS" if ok else "NOT_CHECKED", method="existing matrix-report and package audit adapter",
                                observed={"formal_ready": formal}, evidence_paths=report_paths or [str(root)],
                                message=f"{label} passed through existing release evidence" if ok else f"{label} has no complete evidence"))
    result = score_and_decide(records, observation_only=observation_only)
    result.update({"model": model, "package_root": str(root), "package": package,
                   "matrix_report": report_paths[0] if report_paths else None,
                   "templates": {"cn": str(template_cn) if template_cn else None, "en": str(template_en) if template_en else None}})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("model")
    parser.add_argument("--template-cn", type=Path)
    parser.add_argument("--template-en", type=Path)
    parser.add_argument("--matrix-report", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--observation-only", action="store_true")
    args = parser.parse_args()
    result = run_audit(args.root, args.model, template_cn=args.template_cn, template_en=args.template_en,
                       matrix_report=args.matrix_report, observation_only=args.observation_only)
    report_dir = args.report_dir or args.root / "audit"
    write_reports(result, report_dir / "deliverable-audit.json", report_dir / "deliverable-audit.txt")
    print(f"outcome={result['outcome']} score={result['score']}/{result['score_max']} records={len(result['records'])}")
    return 0 if result["outcome"] in {"RELEASE_PASS", "OBSERVATION_ONLY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
