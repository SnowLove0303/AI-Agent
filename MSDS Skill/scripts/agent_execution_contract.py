"""Machine-checkable OpenSpec execution contract for MSDS overwrite.

The contract cannot observe an Agent's private attention, so it requires an
explicit reviewed execution record in the approved facts file and verifies
that every required normative source is present.  The actual DOCX gates remain
the final authority: a self-attestation never bypasses a failed audit.
"""
from __future__ import annotations

import json
from pathlib import Path

from efficiency_contract import validate_efficiency_spec


SKILL_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = SKILL_ROOT / "openspec" / "agent_overwrite_contract.json"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def _normalize_paths(values) -> set[str]:
    return {str(value).replace("\\", "/").lstrip("./") for value in (values or [])}


def validate_spec_installation() -> list[str]:
    """Verify that the active OpenSpec and every normative source are installed."""
    errors: list[str] = []
    if not SPEC_PATH.is_file():
        return [f"OpenSpec file is missing: {SPEC_PATH}"]
    try:
        spec = load_spec()
    except (OSError, json.JSONDecodeError) as exc:
        return [f"OpenSpec cannot be loaded: {exc}"]
    if spec.get("status") != "active":
        errors.append("OpenSpec status must be active")
    if not spec.get("spec_id") or not spec.get("version"):
        errors.append("OpenSpec spec_id and version are required")
    for relative in spec.get("read_before_action", []):
        if not (SKILL_ROOT / relative).is_file():
            errors.append(f"required normative source is missing: {relative}")
    errors.extend(f"efficiency OpenSpec: {error}" for error in validate_efficiency_spec())
    return errors


def validate_agent_execution_contract(facts: dict) -> list[str]:
    """Return release blockers for a missing/incomplete Agent execution record."""
    errors = validate_spec_installation()
    if errors:
        return errors
    spec = load_spec()
    record = facts.get("agent_execution")
    if not isinstance(record, dict):
        return ["agent_execution contract is missing; read the full OpenSpec before approval"]
    if record.get("spec_id") != spec["spec_id"]:
        errors.append("agent_execution spec_id does not match active OpenSpec")
    if record.get("spec_version") != spec["version"]:
        errors.append("agent_execution spec_version does not match active OpenSpec")
    if record.get("status") != "reviewed":
        errors.append("agent_execution status must be reviewed")
    if record.get("read_mode") != "full":
        errors.append("agent_execution read_mode must be full")
    required_sources = _normalize_paths(spec.get("read_before_action"))
    read_sources = _normalize_paths(record.get("read_sources"))
    missing_sources = sorted(required_sources - read_sources)
    if missing_sources:
        errors.append("agent_execution missing read sources: " + ", ".join(missing_sources))
    required_acknowledgements = spec.get("required_acknowledgements", [])
    acknowledgements = record.get("acknowledged")
    if not isinstance(acknowledgements, dict):
        errors.append("agent_execution acknowledged checklist is missing")
    else:
        for key in required_acknowledgements:
            if acknowledgements.get(key) is not True:
                errors.append(f"agent_execution acknowledgement is not true: {key}")
    expected_order = spec.get("operation_order", [])
    if record.get("operation_order") != expected_order:
        errors.append("agent_execution operation_order does not match active OpenSpec")
    mode = record.get("execution_mode")
    if not isinstance(mode, dict):
        errors.append("agent_execution execution_mode is missing")
    else:
        for key, expected in spec.get("execution_mode", {}).items():
            if mode.get(key) != expected:
                errors.append(f"agent_execution execution_mode mismatch: {key}")
    mutation_boundary = record.get("agent_mutation_boundary")
    if mutation_boundary != spec.get("agent_mutation_boundary"):
        errors.append(
            "agent_execution agent_mutation_boundary must exactly match the active OpenSpec"
        )
    sop = facts.get("overwrite_sop")
    expected_sop = spec.get("sop") or {}
    if not isinstance(sop, dict):
        errors.append("overwrite_sop record is missing; complete the Agent overwrite SOP before approval")
    else:
        if sop.get("version") != expected_sop.get("version"):
            errors.append("overwrite_sop version does not match active SOP")
        if sop.get("status") != "reviewed":
            errors.append("overwrite_sop status must be reviewed")
        stages = sop.get("stages")
        required_stages = expected_sop.get("required_stages", [])
        stage_names = [item.get("stage") for item in stages if isinstance(item, dict)] if isinstance(stages, list) else []
        if stage_names != required_stages:
            errors.append("overwrite_sop stages must match the required global order")
        elif any(item.get("status") != "completed" for item in stages):
            errors.append("overwrite_sop every required stage must be completed")
        if sorted(sop.get("loaded_local_sections") or []) != expected_sop.get("required_local_sections", []):
            errors.append("overwrite_sop local Section rule set is incomplete")
        if not isinstance(sop.get("cross_section_routes"), list):
            errors.append("overwrite_sop cross_section_routes must be a list")
        if not isinstance(sop.get("audit_plan"), list) or not sop.get("audit_plan"):
            errors.append("overwrite_sop audit_plan is missing")
    return errors


def blank_execution_contract() -> dict:
    """Return the review-required record emitted by mechanical extraction."""
    spec = load_spec()
    return {
        "spec_id": spec["spec_id"],
        "spec_version": spec["version"],
        "status": "needs-review",
        "read_mode": "full",
        "read_sources": [],
        "acknowledged": {},
        "operation_order": [],
        "execution_mode": {},
        "agent_mutation_boundary": {},
        "overwrite_sop": {"version": load_spec().get("sop", {}).get("version"), "status": "needs-review"},
    }


__all__ = [
    "SPEC_PATH",
    "blank_execution_contract",
    "load_spec",
    "validate_agent_execution_contract",
    "validate_spec_installation",
]
