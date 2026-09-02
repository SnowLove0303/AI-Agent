#!/usr/bin/env python3
"""Deterministic DOCX -> PDF publication adapter for the MSDS skill.

The adapter deliberately accepts one already-audited DOCX and writes one PDF.
It uses an isolated LibreOffice profile and a temporary output directory so a
failed conversion never leaves a partially written customer PDF behind.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_soffice(explicit: str | None = None) -> str:
    candidates = []
    if explicit:
        candidates.append(explicit)
    env_path = os.environ.get("SOFFICE_PATH")
    if env_path:
        candidates.append(env_path)
    candidates.extend(("soffice.com", "soffice.exe", "soffice"))
    for candidate in candidates:
        resolved = shutil.which(candidate) or candidate
        if Path(resolved).exists() or shutil.which(candidate):
            return str(resolved)
    raise FileNotFoundError(
        "LibreOffice executable not found; set SOFFICE_PATH or pass --soffice"
    )


def version(soffice: str) -> str:
    try:
        result = subprocess.run(
            [soffice, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (result.stdout or result.stderr).strip()
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return f"unavailable: {exc}"


def count_pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception:
        # Keep conversion usable in minimal environments; the release gate
        # still requires an independent page-count/render check.
        data = path.read_bytes()
        matches = re.findall(rb"/Type\s*/Page\b", data)
        return len(matches) or None


def convert(input_path: Path, output_path: Path, timeout: int = 180, soffice: str | None = None) -> dict:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if input_path.suffix.lower() != ".docx":
        raise ValueError(f"input must be .docx: {input_path}")
    if input_path == output_path:
        raise ValueError("input DOCX and output PDF must be different files")

    executable = find_soffice(soffice)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    source_hash = sha256(input_path)
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # Keep the converted temporary file on the destination volume: Windows
    # cannot atomically replace a file across volumes (for example C: -> F:).
    with tempfile.TemporaryDirectory(prefix="msds_lo_profile_") as profile, tempfile.TemporaryDirectory(
        prefix="msds_pdf_output_", dir=str(output_path.parent)
    ) as converted:
        profile_uri = Path(profile).resolve().as_uri()
        command = [
            executable,
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            converted,
            str(input_path),
        ]
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=flags,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"LibreOffice conversion timed out after {timeout}s") from exc
        generated = Path(converted) / f"{input_path.stem}.pdf"
        if result.returncode != 0 or not generated.is_file() or generated.stat().st_size == 0:
            diagnostics = "\n".join(x for x in (result.stdout, result.stderr) if x)
            raise RuntimeError(
                f"LibreOffice conversion failed (returncode={result.returncode}).\n{diagnostics}"
            )
        os.replace(generated, output_path)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"conversion produced no usable PDF: {output_path}")
    evidence = {
        "converter": "libreoffice-headless",
        "converter_version": version(executable),
        "source_docx": str(input_path),
        "source_sha256": source_hash,
        "output_pdf": str(output_path),
        "output_sha256": sha256(output_path),
        "page_count": count_pdf_pages(output_path),
        "elapsed_seconds": round(time.time() - started, 3),
        "source_is_final_docx": True,
        "independent_pdf_authoring": False,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert one audited DOCX to one PDF")
    parser.add_argument("input_docx", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--soffice")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    try:
        evidence = convert(args.input_docx, args.output_pdf, args.timeout, args.soffice)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
