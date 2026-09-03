from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from deliverable_audit_framework import RULES  # noqa: E402


def test_checklist_covers_every_registered_rule_once():
    text = (ROOT / "docs" / "deliverable_audit_checklist.md").read_text(encoding="utf-8")
    listed = re.findall(r"\|\s*([A-Z0-9]+-\d{3})\s*\|", text)
    expected = [rule.rule_id for rule in RULES]
    assert set(listed) == set(expected)
    assert len(listed) == len(set(listed))


def test_evaluation_docs_define_outcomes_and_weights():
    text = (ROOT / "docs" / "deliverable_evaluation_standard.md").read_text(encoding="utf-8")
    for token in ("RELEASE_PASS", "RELEASE_FAIL", "NOT_READY", "OBSERVATION_ONLY", "100", "95"):
        assert token in text
