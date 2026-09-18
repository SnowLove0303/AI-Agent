#!/usr/bin/env python3
"""Run the resumable MSDS efficiency workflow.

This command is a process boundary for Harness/Agent callers.  It deliberately
does not approve facts or infer missing values.  Its job is to make the safe
sequence impossible to accidentally skip:

    prepare/reuse evidence packet -> external review -> one-shot preflight
    -> formal build

Every checkpoint is written atomically below one caller-owned workspace.  A
packet-only invocation never clones a template, and a blocked preflight never
starts the formal build or PDF conversion.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from evidence_packet import prepare_packet
from msds_pipeline import ReleaseBlocked, build_matrix
from preflight_facts import run as run_preflight
from source_ingest import SourceSelectionError, discover_source


WORKFLOW_SCHEMA_VERSION = "3.26.0"


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
            mode="w", encoding="utf-8", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _base_state(*, workspace: Path, source: Path, model: str | None,
                cache_dir: Path, packet_path: Path) -> dict[str, Any]:
    return {
        "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": "starting",
        "workspace": str(workspace),
        "source_requested": str(source),
        "model": model,
        "cache_dir": str(cache_dir),
        "packet_path": str(packet_path),
        "started_at_epoch": time.time(),
        "stages": {
            "evidence": {"status": "pending"},
            "review": {"status": "pending"},
            "preflight": {"status": "pending"},
            "build": {"status": "pending"},
        },
    }


def _save_state(state: dict[str, Any], path: Path) -> None:
    state["updated_at_epoch"] = time.time()
    _write_json_atomic(path, state)


def _packet_stage(packet: dict[str, Any], reused: bool) -> dict[str, Any]:
    source = packet.get("source") if isinstance(packet.get("source"), dict) else {}
    return {
        "status": "reused" if reused else "ready",
        "packet_cache_key": packet.get("packet_cache_key"),
        "source_sha256": source.get("sha256"),
        "source_format": source.get("format"),
        "review_summary": packet.get("review_summary", {}),
        "build_allowed": packet.get("build_allowed") is True,
        "next_required_stage": (packet.get("checkpoint") or {}).get(
            "next_required_stage", "agent_review"
        ),
    }


def run_workflow(*, source: Path, workspace: Path, model: str | None = None,
                 facts: Path | None = None, no_pdf: bool = False,
                 timeout: int = 300, pdf_workers: int = 2,
                 wpscli: str | None = None, family_profile: Path | None = None,
                 revision: str | None = None, agent_review_seconds: float | None = None,
                 human_wait_seconds: float | None = None, retry_count: int = 0,
                 docx_preview_dir: Path | None = None) -> dict[str, Any]:
    """Run or resume the safe workflow and return its checkpoint report."""
    workspace = Path(workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    source = Path(source).expanduser()
    cache_dir = workspace / ".msds_cache"
    packet_path = workspace / "evidence-packet.json"
    state_path = workspace / "workflow-state.json"
    state = _base_state(
        workspace=workspace, source=source, model=model,
        cache_dir=cache_dir, packet_path=packet_path,
    )
    _save_state(state, state_path)

    selected = discover_source(source, model=model)
    packet, reused = prepare_packet(
        selected.original_path, packet_path, model=model, cache_dir=cache_dir,
    )
    state["source"] = {
        "path": str(selected.original_path),
        "format": selected.source_format,
        "sha256": selected.source_sha256,
    }
    state["stages"]["evidence"] = _packet_stage(packet, reused)
    _save_state(state, state_path)

    if facts is None:
        state["status"] = "awaiting_review"
        state["stages"]["review"] = {
            "status": "required",
            "packet_status": packet.get("status"),
            "next_action": "create reviewed approved facts JSON from facts_draft",
        }
        _save_state(state, state_path)
        return {
            "outcome": "EVIDENCE_PACKET_REUSED" if reused else "EVIDENCE_PACKET_READY",
            "status": state["status"],
            "packet": str(packet_path),
            "state": str(state_path),
            "review_summary": packet.get("review_summary", {}),
            "next_action": state["stages"]["review"]["next_action"],
        }

    facts = Path(facts).expanduser().resolve()
    state["facts"] = str(facts)
    state["stages"]["review"] = {
        "status": "supplied",
        "facts": str(facts),
        "packet_remains_non_approving": packet.get("build_allowed") is not True,
    }
    _save_state(state, state_path)

    preflight_path = workspace / "preflight.json"
    try:
        preflight = run_preflight(
            selected.original_path, facts, model,
            family_profile=family_profile, cache_dir=cache_dir,
        )
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        preflight = {"status": "blocked", "errors": [str(exc)]}
    _write_json_atomic(preflight_path, preflight)
    state["stages"]["preflight"] = {
        "status": "passed" if preflight.get("status") == "ready" else "blocked",
        "report": str(preflight_path),
        "error_count": len(preflight.get("errors") or []),
    }
    if preflight.get("status") != "ready":
        state["status"] = "preflight_blocked"
        state["stages"]["build"] = {
            "status": "not_started",
            "reason": "preflight must pass before template cloning or PDF conversion",
        }
        _save_state(state, state_path)
        return {
            "outcome": "PREFLIGHT_BLOCKED",
            "status": state["status"],
            "preflight": str(preflight_path),
            "state": str(state_path),
            "errors": preflight.get("errors", []),
        }

    try:
        facts_payload = _read_json(facts)
        output_root = workspace / "output"
        report = build_matrix(
            source=selected.original_path,
            facts=facts_payload,
            out_root=output_root,
            model=model,
            revision=revision,
            do_pdf=not no_pdf,
            timeout=timeout,
            pdf_workers=pdf_workers,
            wpscli=wpscli,
            docx_preview_dir=docx_preview_dir,
            cache_dir=cache_dir,
            family_profile=family_profile,
            agent_review_seconds=agent_review_seconds,
            human_wait_seconds=human_wait_seconds,
            retry_count=retry_count,
        )
    except (OSError, json.JSONDecodeError, FileNotFoundError, ReleaseBlocked,
            SourceSelectionError, ValueError, RuntimeError) as exc:
        state["status"] = "release_failed"
        state["stages"]["build"] = {
            "status": "failed",
            "error": str(exc),
        }
        _save_state(state, state_path)
        return {
            "outcome": "RELEASE_FAIL",
            "status": state["status"],
            "state": str(state_path),
            "error": str(exc),
        }

    state["status"] = "release_pass"
    state["stages"]["build"] = {
        "status": "passed",
        "output_root": report.get("output_root"),
        "docx_count": report.get("docx_count"),
        "pdf_count": report.get("pdf_count"),
        "matrix_report": str(Path(report["output_root"]) / "matrix-report.json"),
    }
    _save_state(state, state_path)
    return {
        "outcome": "RELEASE_PASS",
        "status": state["status"],
        "state": str(state_path),
        "output_root": report.get("output_root"),
        "docx_count": report.get("docx_count"),
        "pdf_count": report.get("pdf_count"),
        "timing": report.get("timing"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resumable MSDS workflow: prepare/reuse evidence, wait for reviewed "
            "facts, run one-shot preflight, then build the formal matrix."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--facts", type=Path,
                        help="reviewed approved facts JSON; omit to stop at review checkpoint")
    parser.add_argument("--family-profile", type=Path, default=None)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--pdf-workers", type=int, default=2)
    parser.add_argument("--wpscli", default=None)
    parser.add_argument("--docx-preview-dir", type=Path, default=None)
    parser.add_argument("--agent-review-seconds", type=float, default=None)
    parser.add_argument("--human-wait-seconds", type=float, default=None)
    parser.add_argument("--retry-count", type=int, default=0)
    args = parser.parse_args()
    try:
        result = run_workflow(
            source=args.source, workspace=args.workspace, model=args.model,
            facts=args.facts, no_pdf=args.no_pdf, timeout=args.timeout,
            pdf_workers=args.pdf_workers, wpscli=args.wpscli,
            family_profile=args.family_profile, revision=args.revision,
            agent_review_seconds=args.agent_review_seconds,
            human_wait_seconds=args.human_wait_seconds,
            retry_count=args.retry_count, docx_preview_dir=args.docx_preview_dir,
        )
    except (OSError, json.JSONDecodeError, SourceSelectionError, ValueError,
            RuntimeError) as exc:
        print(json.dumps({"outcome": "WORKFLOW_BLOCKED", "error": str(exc)},
                         ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("outcome") in {
        "EVIDENCE_PACKET_READY", "EVIDENCE_PACKET_REUSED", "RELEASE_PASS"
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
