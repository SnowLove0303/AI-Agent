"""Build and reuse the mechanical source-evidence packet.

The packet is a speed and correctness boundary, not an approval shortcut.  It
contains the extractor's source inventory, fact-ledger scaffold and review
queue in one source-hash-bound file.  Its status always remains
``needs-review`` until an Agent completes the OpenSpec acknowledgements,
mapping decisions and output traceability in a separate approved facts file.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from extract_source_facts import extract
from source_ingest import SourceSelection, source_adapter_cache_key


SKILL_ROOT = Path(__file__).resolve().parent.parent
VERSION_PATH = SKILL_ROOT / "VERSION.txt"
PACKET_SCHEMA_VERSION = "3.24.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skill_version() -> str:
    """Read the public package version without importing build-time modules."""
    lines = VERSION_PATH.read_text(encoding="utf-8").splitlines()
    return lines[1].strip() if len(lines) > 1 else PACKET_SCHEMA_VERSION


def packet_cache_key(selection: SourceSelection, model: str | None = None) -> str:
    """Return a cache key bound to source bytes and extractor/spec bytes."""
    extractor_hash = _sha256(Path(__file__).with_name("extract_source_facts.py"))
    ingest_hash = _sha256(Path(__file__).with_name("source_ingest.py"))
    spec_hash = _sha256(SKILL_ROOT / "openspec" / "source_interpretation_contract.json")
    payload = {
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "skill_version": skill_version(),
        "source_format": selection.source_format,
        "source_sha256": selection.source_sha256,
        "model": model or "",
        "extractor_sha256": extractor_hash,
        "source_ingest_sha256": ingest_hash,
        "source_interpretation_spec_sha256": spec_hash,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _packet_cache_path(cache_dir: Path, key: str) -> Path:
    return Path(cache_dir).expanduser().resolve() / "evidence-packets" / f"{key}.json"


def _matches(packet: object, selection: SourceSelection, model: str | None,
             key: str) -> bool:
    if not isinstance(packet, dict):
        return False
    source = packet.get("source")
    draft = packet.get("facts_draft")
    return (
        packet.get("packet_schema_version") == PACKET_SCHEMA_VERSION
        and packet.get("packet_cache_key") == key
        and isinstance(source, dict)
        and source.get("sha256") == selection.source_sha256
        and source.get("format") == selection.source_format
        and packet.get("model") == (model or draft.get("model") if isinstance(draft, dict) else model)
        and isinstance(draft, dict)
        and draft.get("source_sha256") == selection.source_sha256
    )


def _review_summary(draft: dict) -> dict:
    coverage = draft.get("source_coverage") or {}
    mapping = draft.get("source_mapping") or {}
    traceability = draft.get("output_traceability") or {}
    return {
        "source_units": len(coverage.get("source_units") or []),
        "processed_units": coverage.get("counts", {}).get("processed_unit_count", 0),
        "coverage_unmapped": len(coverage.get("unmapped") or []),
        "fact_ledger_items": len(draft.get("fact_ledger") or []),
        "extractor_review_items": len(draft.get("review") or []),
        "mapping_items": len(mapping.get("items") or []),
        "mapping_unresolved": len(mapping.get("unresolved") or []),
        "output_traceability_items": len(traceability.get("items") or []),
        "status": "needs-review",
    }


def make_packet(selection: SourceSelection, draft: dict, model: str | None,
                key: str, *, packet_reused: bool,
                source_adapter_cache_reused: bool) -> dict:
    """Wrap a mechanical draft in a review-oriented, non-approving packet."""
    resolved_model = model or draft.get("model") or ""
    review_queue = list(draft.get("review") or [])
    review_queue.extend(draft.get("source_mapping", {}).get("unresolved") or [])
    return {
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "skill_version": skill_version(),
        "packet_cache_key": key,
        "status": "needs-review",
        "build_allowed": False,
        "model": resolved_model,
        "source": {
            "path": str(selection.original_path),
            "format": selection.source_format,
            "sha256": selection.source_sha256,
            "adapter_cache_key": source_adapter_cache_key(selection)
            if selection.source_format in {"doc", "odt", "rtf"} else None,
        },
        "cache": {
            "packet_reused": packet_reused,
            "source_adapter_cache_reused": source_adapter_cache_reused,
            "cache_key": key,
        },
        "checkpoint": {
            "completed": [
                "source_selected",
                "source_extracted_once",
                "source_coverage_indexed",
                "fact_ledger_scaffolded",
            ],
            "next_required_stage": "agent_review",
            "required_before_build": [
                "complete source_mapping with a disposition for every source unit",
                "complete output_traceability for every output value and empty decision",
                "complete the full OpenSpec agent_execution acknowledgement record",
                "resolve every ambiguity or conflict; do not guess missing source facts",
            ],
        },
        "review_summary": _review_summary(draft),
        "review_queue": review_queue,
        "source_index": draft.get("source_coverage", {}).get("source_units", []),
        "facts_draft": draft,
    }


def prepare_packet(source: Path, out: Path, *, model: str | None = None,
                   cache_dir: Path | None = None) -> tuple[dict, bool]:
    """Load a matching packet or extract exactly once and persist the result."""
    from source_ingest import discover_source

    selected = discover_source(Path(source), model=model)
    cache_root = Path(cache_dir or (Path(out).parent / ".msds_cache"))
    key = packet_cache_key(selected, model)
    cached_path = _packet_cache_path(cache_root, key)
    if cached_path.is_file():
        try:
            cached = json.loads(cached_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cached = None
        if _matches(cached, selected, model, key):
            packet = dict(cached)
            packet.setdefault("cache", {})["packet_reused"] = True
            _write_json_atomic(Path(out), packet)
            return packet, True

    adapter_cache_path = (
        cache_root.expanduser().resolve() / "source-adapters"
        / f"{source_adapter_cache_key(selected)}.docx"
    )
    adapter_reused = adapter_cache_path.is_file()
    draft = extract(selected.original_path, cache_dir=cache_root)
    if model and draft.get("model") != model:
        raise ValueError(
            f"extracted model {draft.get('model')!r} does not match requested {model!r}"
        )
    packet = make_packet(
        selected, draft, model, key,
        packet_reused=False,
        source_adapter_cache_reused=adapter_reused,
    )
    _write_json_atomic(cached_path, packet)
    _write_json_atomic(Path(out), packet)
    return packet, False


__all__ = [
    "PACKET_SCHEMA_VERSION", "make_packet", "packet_cache_key",
    "prepare_packet", "skill_version",
]
