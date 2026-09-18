#!/usr/bin/env python3
"""Non-publishing V3.26 efficiency benchmark.

The command measures the same source/cache path used by the formal workflow,
but every packet and matrix is created below a temporary directory that is
removed before the command exits.  It is therefore safe to run from a
Harness without changing a customer's formal output directory.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from pathlib import Path

from evidence_packet import prepare_packet
from msds_pipeline import build_matrix


def summarize(samples: list[float], failures: list[dict] | None = None) -> dict:
    """Return stable median/maximum metrics for successful samples."""
    failures = list(failures or [])
    values = [round(float(value), 6) for value in samples]
    return {
        "count": len(values),
        "median_seconds": round(statistics.median(values), 6) if values else None,
        "maximum_seconds": round(max(values), 6) if values else None,
        "samples_seconds": values,
        "failure_count": len(failures),
        "failures": failures,
    }


def parse_worker_counts(value: str) -> list[int]:
    counts = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        count = int(raw)
        if count < 1:
            raise ValueError("worker counts must be positive integers")
        if count not in counts:
            counts.append(count)
    if not counts:
        raise ValueError("at least one worker count is required")
    return counts


def _measure_packet(source: Path, model: str | None, cache_dir: Path,
                    runs: int) -> dict:
    cold_samples = []
    warm_samples = []
    failures = []
    for index in range(runs):
        # Isolate each cold sample so a previous sample cannot turn the next
        # run into an accidental cache hit. The second lookup in the same
        # private root is the corresponding warm sample.
        run_cache = cache_dir / f"packet-run-{index}"
        packet_path = cache_dir.parent / f"packet-{index}.json"
        started = time.perf_counter()
        try:
            _packet, reused = prepare_packet(
                source, packet_path, model=model, cache_dir=run_cache
            )
            elapsed = time.perf_counter() - started
            (warm_samples if reused else cold_samples).append(elapsed)
            # Force a second lookup against the same source/key so a single
            # invocation provides an observable warm-cache sample as well.
            started = time.perf_counter()
            prepare_packet(source, packet_path, model=model, cache_dir=run_cache)
            warm_samples.append(time.perf_counter() - started)
        except Exception as exc:
            failures.append({
                "run": index + 1,
                "type": type(exc).__name__,
                "message": str(exc),
            })
    return {
        "cold_cache": summarize(cold_samples, failures),
        "warm_cache": summarize(warm_samples, failures),
    }


def _measure_matrices(source: Path, facts_path: Path, model: str | None,
                      cache_dir: Path, worker_counts: list[int], runs: int,
                      do_pdf: bool, timeout: int, wpscli: str | None) -> dict:
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    results = {}
    for workers in worker_counts:
        samples = []
        failures = []
        for index in range(runs):
            run_root = cache_dir.parent / f"matrix-{workers}-{index}"
            started = time.perf_counter()
            try:
                report = build_matrix(
                    source=source, facts=facts, out_root=run_root, model=model,
                    do_pdf=do_pdf, timeout=timeout, pdf_workers=workers,
                    wpscli=wpscli, cache_dir=cache_dir,
                )
                samples.append(time.perf_counter() - started)
                # Keep the result small while retaining the release-relevant
                # telemetry needed to compare runs.
                failures.extend((report.get("timing", {}).get("pdf", {})
                                 .get("failures", [])))
            except Exception as exc:
                failures.append({
                    "run": index + 1,
                    "type": type(exc).__name__,
                    "message": str(exc),
                })
        results[str(workers)] = summarize(samples, failures)
    return results


def run_benchmark(*, source: Path, facts: Path | None = None,
                  model: str | None = None, worker_counts: list[int] | None = None,
                  runs: int = 1, docx_only: bool = False, timeout: int = 300,
                  wpscli: str | None = None) -> dict:
    if runs < 1:
        raise ValueError("runs must be at least 1")
    source = Path(source).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if facts is not None:
        facts = Path(facts).expanduser().resolve()
        if not facts.is_file():
            raise FileNotFoundError(facts)
    worker_counts = worker_counts or [1, 2, 3]
    with tempfile.TemporaryDirectory(prefix="msds_efficiency_benchmark_") as root:
        root_path = Path(root)
        cache_dir = root_path / ".msds_cache"
        packet = _measure_packet(source, model, cache_dir, runs)
        matrices = None
        if facts is not None:
            matrices = _measure_matrices(
                source, facts, model, cache_dir, worker_counts, runs,
                do_pdf=not docx_only, timeout=timeout, wpscli=wpscli,
            )
        return {
            "benchmark_schema_version": "3.26.0",
            "publishes_formal_matrix": False,
            "source": str(source),
            "facts": str(facts) if facts is not None else None,
            "runs": runs,
            "worker_counts": worker_counts if facts is not None else [],
            "mode": "docx-only" if docx_only else "pdf-enabled" if facts is not None else "packet-only",
            "packet": packet,
            "matrices": matrices,
            "environment": {
                "python": os.sys.version.split()[0],
                "platform": os.name,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--facts", type=Path,
                        help="optional approved facts JSON for temporary matrix runs")
    parser.add_argument("--model", default=None)
    parser.add_argument("--worker-counts", default="1,2,3",
                        help="comma-separated PDF worker counts, e.g. 1,2,3,4")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--docx-only", action="store_true",
                        help="benchmark matrix construction without WPS PDF conversion")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--wpscli", default=None)
    parser.add_argument("--json", type=Path,
                        help="optional path for the benchmark report")
    args = parser.parse_args()
    try:
        report = run_benchmark(
            source=args.source, facts=args.facts, model=args.model,
            worker_counts=parse_worker_counts(args.worker_counts), runs=args.runs,
            docx_only=args.docx_only, timeout=args.timeout, wpscli=args.wpscli,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"outcome": "BENCHMARK_FAIL", "error": str(exc)},
                         ensure_ascii=False, indent=2))
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
