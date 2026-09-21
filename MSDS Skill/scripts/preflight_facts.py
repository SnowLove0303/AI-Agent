#!/usr/bin/env python3
"""Cheap, non-mutating facts preflight for Harness review loops."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from family_profile import FamilyProfileError, review_profile  # noqa: E402
from msds_pipeline import approved_facts_errors  # noqa: E402
from source_ingest import (  # noqa: E402
    SourceSelectionError,
    discover_source,
    prepare_source,
)


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
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


def run(source: Path, facts_path: Path, model: str | None = None,
        *, family_profile: Path | None = None,
        cache_dir: Path | None = None) -> dict:
    """Return all blockers without loading a template or resolving WPS."""
    facts = json.loads(Path(facts_path).read_text(encoding="utf-8"))
    if not isinstance(facts, dict):
        errors = ["facts JSON root must be an object"]
        return {
            "status": "blocked",
            "errors": errors,
            "blockers": errors,
            "template_clone_started": False,
            "pdf_converter_started": False,
        }
    resolved_model = model or facts.get("model") or ""
    if not resolved_model:
        errors = ["model is required (argument or facts['model'])"]
        return {
            "status": "blocked",
            "errors": errors,
            "blockers": errors,
        }
    selected = discover_source(Path(source), model=resolved_model)
    errors = approved_facts_errors(facts, selected.original_path, resolved_model)
    profile_report = None
    if family_profile is not None:
        cache_root = (Path(cache_dir).expanduser().resolve()
                      if cache_dir is not None
                      else Path(facts_path).expanduser().resolve().parent / ".msds_cache")
        try:
            with prepare_source(selected, cache_dir=cache_root) as prepared:
                profile_report = review_profile(
                    family_profile, selected.original_path, resolved_model,
                    prepared_source=prepared.extraction_path,
                )
        except (FamilyProfileError, OSError, ValueError) as exc:
            errors.append(f"family profile: {exc}")
        else:
            errors.extend("family profile: " + error
                          for error in profile_report.get("errors", []))
    return {
        "status": "ready" if not errors else "blocked",
        "errors": errors,
        # Keep the original ``errors`` field and expose the older caller
        # vocabulary too.  A preflight blocker must never be dropped merely
        # because a wrapper uses the legacy key.
        "blockers": errors,
        "model": resolved_model,
        "source": str(selected.original_path),
        "source_format": selected.source_format,
        "source_sha256": selected.source_sha256,
        "facts": str(Path(facts_path).resolve()),
        "cache_dir": str(cache_root) if family_profile is not None else None,
        "family_profile": profile_report,
        "template_clone_started": False,
        "pdf_converter_started": False,
        "next_action": "build_eight" if not errors else "fix every listed blocker, then rerun preflight",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate all source/facts/OpenSpec blockers before DOCX cloning. "
            "This command never writes a template or starts PDF conversion."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", type=Path)
    source_group.add_argument("--source-dir", type=Path)
    parser.add_argument("--facts", required=True, type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--family-profile", type=Path, default=None)
    parser.add_argument("--cache-dir", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = run(
            args.source or args.source_dir, args.facts, args.model,
            family_profile=args.family_profile, cache_dir=args.cache_dir,
        )
    except (OSError, json.JSONDecodeError, SourceSelectionError, ValueError, RuntimeError) as blocked:
        errors = [str(blocked)]
        result = {"status": "blocked", "errors": errors, "blockers": errors}
    if args.out is not None:
        _write_json_atomic(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
