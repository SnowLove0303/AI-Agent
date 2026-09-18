from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from benchmark_efficiency import parse_worker_counts, summarize  # noqa: E402


def test_benchmark_summarizes_successes_and_failures():
    report = summarize([3.0, 1.0, 2.0], [{"type": "timeout"}])
    assert report["median_seconds"] == 2.0
    assert report["maximum_seconds"] == 3.0
    assert report["failure_count"] == 1


def test_benchmark_worker_counts_are_positive_and_deduplicated():
    assert parse_worker_counts("1, 2, 2, 4") == [1, 2, 4]
    with pytest.raises(ValueError, match="positive"):
        parse_worker_counts("0,2")


def test_empty_benchmark_summary_is_explicit():
    report = summarize([])
    assert report["median_seconds"] is None
    assert report["maximum_seconds"] is None
    assert report["failure_count"] == 0
