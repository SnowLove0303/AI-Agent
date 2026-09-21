#!/usr/bin/env python3
"""Source-file discovery and format boundary for the MSDS pipeline.

Discovery is deliberately broader than automatic semantic extraction.  A
source format may be found and provenance-recorded before an adapter is
approved for section-aware extraction; the publication-only PDF format is
never treated as a source.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_FORMATS = {
    ".docx": "docx",
    ".doc": "doc",
    ".docm": "docm",
    ".odt": "odt",
    ".rtf": "rtf",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".txt": "txt",
}
OUTPUT_ONLY_FORMATS = {".pdf": "pdf"}
DIRECT_DOCX_FORMATS = {"docx", "docm"}
CONVERTIBLE_WORD_FORMATS = {"doc", "odt", "rtf"}
DISCOVERY_EXCLUDED_DIRS = {
    ".git", ".agents", ".codex", "_task_work", "artifacts", "output",
    "outputs", "_docx_preview", ".msds_cache",
}
GENERATED_OUTPUT_DIRS = {
    "_task_work", "artifacts", "output", "outputs", "_docx_preview",
    ".msds_cache",
}

# The adapter result is content-addressed by the original source.  Bumping
# this value invalidates old converted files if the conversion contract ever
# changes, without requiring a user to manually clear a cache directory.
SOURCE_ADAPTER_CACHE_VERSION = "1"


class SourceSelectionError(ValueError):
    """The source path is missing, unsupported or ambiguous."""


class SourceFormatBlocked(ValueError):
    """A discovered format has no approved automatic semantic adapter yet."""


@dataclass(frozen=True)
class SourceSelection:
    original_path: Path
    source_format: str
    source_sha256: str


@dataclass(frozen=True)
class PreparedSource:
    selection: SourceSelection
    extraction_path: Path | None
    adapter: str
    can_extract_sections: bool
    cache_reused: bool = False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_for(path: Path) -> str:
    if path.suffix.casefold() in OUTPUT_ONLY_FORMATS:
        raise SourceSelectionError(
            "PDF is a publication-only output; select the original Word/source file instead"
        )
    try:
        return SUPPORTED_FORMATS[path.suffix.casefold()]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise SourceSelectionError(
            f"unsupported source format: {path.suffix or '<no extension>'}; "
            f"supported discovery formats: {supported}"
        ) from exc


def _is_formal_output_name(path: Path) -> bool:
    return bool(re.match(
        r"^[A-Za-z0-9][A-Za-z0-9-]*_MSDS_(?:CN|EN)_(?:冠志|国彩)\.(?:docx|pdf)$",
        path.name, re.I,
    ))


def _has_path_part(path: Path, names: set[str]) -> bool:
    excluded = {name.casefold() for name in names}
    return any(part.casefold() in excluded for part in path.parts)


def _is_discovery_candidate(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("~$"):
        return False
    if _is_formal_output_name(path):
        return False
    if _has_path_part(path, DISCOVERY_EXCLUDED_DIRS):
        return False
    return path.suffix.casefold() in SUPPORTED_FORMATS


def _matches_model(path: Path, model: str | None) -> bool:
    if not model:
        return True
    return bool(re.search(rf"(?<![A-Za-z0-9]){re.escape(model)}(?![A-Za-z0-9])",
                          path.name, re.I))


def discover_source(path_or_dir: Path, model: str | None = None) -> SourceSelection:
    """Resolve one explicit or discovered source and bind its original hash."""
    path = Path(path_or_dir).expanduser()
    if path.is_file():
        if _has_path_part(path, GENERATED_OUTPUT_DIRS):
            raise SourceSelectionError(
                "a generated/output directory cannot be used as the original source"
            )
        if _is_formal_output_name(path):
            raise SourceSelectionError(
                "a formal MSDS output cannot be reused as source; select the original source file"
            )
        source_format = _format_for(path)
        return SourceSelection(path.resolve(), source_format, sha256(path))
    if not path.is_dir():
        raise SourceSelectionError(f"source path does not exist: {path}")

    candidates = sorted(
        candidate for candidate in path.rglob("*")
        if _is_discovery_candidate(candidate) and _matches_model(candidate, model)
    )
    if not candidates:
        suffixes = ", ".join(sorted(SUPPORTED_FORMATS))
        raise SourceSelectionError(
            f"no supported source found under {path} for model {model or '<unspecified>'}; "
            f"searched formats: {suffixes}"
        )
    if len(candidates) != 1:
        listed = "\n".join(f"- {candidate}" for candidate in candidates[:20])
        more = "" if len(candidates) <= 20 else f"\n- ... and {len(candidates) - 20} more"
        raise SourceSelectionError(
            "source discovery is ambiguous; pass one explicit --source file:\n"
            + listed + more
        )
    selected = candidates[0].resolve()
    return SourceSelection(selected, _format_for(selected), sha256(selected))


def _find_soffice() -> str:
    candidates = [os.environ.get("SOFFICE_PATH"), shutil.which("soffice.com"),
                  shutil.which("soffice"),
                  r"C:\Program Files\LibreOffice\program\soffice.com"]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise SourceFormatBlocked(
        "legacy word source requires LibreOffice soffice for temporary DOCX conversion"
    )


def source_adapter_cache_key(selection: SourceSelection) -> str:
    """Return the stable key for a converted legacy Word source.

    The original bytes, source format and adapter version are all part of the
    key.  A converted DOCX is therefore never reused for a changed source,
    even when the source keeps the same filename.
    """
    payload = "|".join((
        SOURCE_ADAPTER_CACHE_VERSION,
        selection.source_format,
        selection.source_sha256,
    ))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _valid_cached_docx(path: Path) -> bool:
    """Reject a partial or non-DOCX cache entry before it reaches extraction."""
    return path.is_file() and path.stat().st_size > 0 and zipfile.is_zipfile(path)


def _cached_conversion_path(selection: SourceSelection, cache_dir: Path) -> Path:
    root = Path(cache_dir).expanduser().resolve() / "source-adapters"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{source_adapter_cache_key(selection)}.docx"


def _cache_converted_docx(converted: Path, target: Path) -> Path:
    """Publish one converted DOCX atomically so parallel harness runs are safe."""
    if _valid_cached_docx(target):
        return target
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{target.stem}.", suffix=".tmp", dir=target.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
        shutil.copyfile(converted, temporary)
        if not _valid_cached_docx(temporary):
            raise SourceFormatBlocked("LibreOffice produced an invalid DOCX cache entry")
        os.replace(temporary, target)
        return target
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


@contextmanager
def prepare_source(selection_or_path: SourceSelection | Path,
                   cache_dir: Path | None = None):
    """Prepare a source for the next stage without creating a formal copy."""
    selection = (selection_or_path if isinstance(selection_or_path, SourceSelection)
                 else discover_source(Path(selection_or_path)))
    if selection.source_format in DIRECT_DOCX_FORMATS:
        yield PreparedSource(selection, selection.original_path, "direct-docx", True)
        return
    if selection.source_format in CONVERTIBLE_WORD_FORMATS:
        cached = (_cached_conversion_path(selection, cache_dir)
                  if cache_dir is not None else None)
        if cached is not None and _valid_cached_docx(cached):
            yield PreparedSource(selection, cached, "libreoffice-docx-cache", True, True)
            return
        with tempfile.TemporaryDirectory(prefix="msds_source_adapter_") as temp_dir:
            result = subprocess.run(
                [_find_soffice(), "--headless", "--convert-to", "docx",
                 "--outdir", temp_dir, str(selection.original_path)],
                check=False, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=180,
            )
            converted = Path(temp_dir) / f"{selection.original_path.stem}.docx"
            if result.returncode != 0 or not converted.is_file():
                detail = "\n".join(x for x in (result.stdout, result.stderr) if x).strip()
                raise SourceFormatBlocked(
                    f"{selection.source_format} to temporary DOCX conversion failed"
                    + (f": {detail}" if detail else "")
                )
            extraction_path = (
                _cache_converted_docx(converted, cached)
                if cached is not None else converted
            )
            adapter = "libreoffice-docx-cache" if cached is not None else "libreoffice-docx"
            yield PreparedSource(selection, extraction_path, adapter, True, False)
        return
    # These source formats are discoverable and can be used with a separately
    # approved, source-hash-bound facts model, but are not guessed into the
    # 16-section extractor until their table/coordinate adapter is approved.
    yield PreparedSource(selection, None, "provenance-only", False)


def require_section_extraction(prepared: PreparedSource) -> Path:
    if not prepared.can_extract_sections or prepared.extraction_path is None:
        raise SourceFormatBlocked(
            f"{prepared.selection.source_format} source was discovered and hashed, "
            "but has no approved automatic 16-section semantic extractor; "
            "provide a reviewed facts JSON or add a format adapter first"
        )
    return prepared.extraction_path


__all__ = [
    "CONVERTIBLE_WORD_FORMATS", "DIRECT_DOCX_FORMATS", "PreparedSource",
    "GENERATED_OUTPUT_DIRS",
    "OUTPUT_ONLY_FORMATS",
    "SourceFormatBlocked", "SourceSelection", "SourceSelectionError",
    "SUPPORTED_FORMATS", "SOURCE_ADAPTER_CACHE_VERSION", "discover_source",
    "prepare_source", "source_adapter_cache_key",
    "require_section_extraction", "sha256",
]
