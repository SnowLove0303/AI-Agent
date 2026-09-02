from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_contract_and_rollback_copies_exist():
    for p in ['docs/v2_9_inheritance_contract.md','legacy_v2_9/SKILL_v2.9.md','legacy_v2_9/CHANGELOG_v2.9.md','legacy_v2_9/sentence_boundary_policy_v2.9.py','scripts/audit_v29_inheritance.py']:
        assert (ROOT/p).exists(), p
