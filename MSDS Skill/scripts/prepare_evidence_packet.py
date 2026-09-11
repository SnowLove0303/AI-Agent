#!/usr/bin/env python3
"""Prepare one reusable source-evidence packet for an MSDS overwrite run."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_packet import prepare_packet  # noqa: E402
from source_ingest import SourceSelectionError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract and cache source coverage/fact-ledger evidence once. "
            "The resulting packet is review-required and cannot be used as approved facts."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", type=Path)
    source_group.add_argument("--source-dir", type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--cache-dir", type=Path, default=None,
        help="persistent cache root; defaults to <packet-directory>/.msds_cache",
    )
    args = parser.parse_args()
    try:
        packet, reused = prepare_packet(
            args.source or args.source_dir,
            args.out,
            model=args.model,
            cache_dir=args.cache_dir,
        )
    except (OSError, ValueError, RuntimeError, SourceSelectionError) as blocked:
        print(json.dumps({"outcome": "EVIDENCE_PACKET_BLOCKED", "error": str(blocked)},
                         ensure_ascii=False, indent=2))
        return 1
    summary = {
        "outcome": "EVIDENCE_PACKET_REUSED" if reused else "EVIDENCE_PACKET_READY",
        "status": packet["status"],
        "build_allowed": packet["build_allowed"],
        "model": packet["model"],
        "source_sha256": packet["source"]["sha256"],
        "packet_cache_key": packet["packet_cache_key"],
        "review_summary": packet["review_summary"],
        "next_required_stage": packet["checkpoint"]["next_required_stage"],
        "out": str(args.out),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
