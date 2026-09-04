import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from extract_source_facts import extract


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "regression_HPU-7660_source.docx"


def test_extractor_detects_model_and_covers_every_cell():
    data = extract(FIXTURE)
    assert data["model"] == "HPU-7660"
    assert len(data["source_sha256"]) == 64
    assert set(data["sections"]) == {f"s{i}" for i in range(1, 17)}
    assert data["coverage"]["unmapped"] == []
    assert data["coverage"]["heading_skipped"]


def test_extractor_splits_components_and_flags_judgment_points():
    data = extract(FIXTURE)
    issues = {(r["section"], r["issue"]) for r in data["review"]}
    assert ("s2", "per-route-synthesis") in issues
    assert ("s11", "alias-mucosa-to-eye") in issues
    assert ("s11", "repro-split") in issues
    components = [row for row in data["sections"]["s3"] if len(row) == 3]
    assert components


def test_extractor_en_skeleton_copies_only_language_independent_facts():
    data = extract(FIXTURE)
    skeleton = data["sections_en_skeleton"]
    assert skeleton["s3"]
    for row in skeleton["s3"]:
        assert row["name_en"] == ""
        assert row["cas"]
    assert skeleton["note"]


def test_extractor_marks_missing_sentinels_without_deciding():
    data = extract(FIXTURE)
    s9 = data["sections"]["s9"]
    assert any(entry.get("omit") for entry in s9)
