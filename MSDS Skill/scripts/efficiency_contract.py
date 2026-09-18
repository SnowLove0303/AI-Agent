"""V3.24 business-stage contract and low-overhead timing recorder."""
from __future__ import annotations

import json
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SKILL_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = SKILL_ROOT / "openspec" / "efficiency_contract.json"
V326_SPEC_PATH = SKILL_ROOT / "openspec" / "efficiency_v326_contract.json"
V326_CACHE_SPEC_PATH = SKILL_ROOT / "openspec" / "cache_contract.json"
V326_FAMILY_SPEC_PATH = SKILL_ROOT / "openspec" / "family_profile_contract.json"
V326_TELEMETRY_SPEC_PATH = SKILL_ROOT / "openspec" / "telemetry_contract.json"
BUSINESS_STAGES = (
    "extract_all_source_information",
    "constrained_information_normalization",
    "fixed_structure_template_overwrite",
    "post_overwrite_fine_tuning",
)


def load_efficiency_spec(path: Path | None = None) -> dict:
    """Load the active machine-readable V3.24 efficiency contract."""
    return json.loads((path or SPEC_PATH).read_text(encoding="utf-8"))


def load_v326_specs() -> dict[str, dict]:
    """Load the additive V3.26 contracts without changing V3.24 semantics."""
    paths = {
        "efficiency": V326_SPEC_PATH,
        "cache": V326_CACHE_SPEC_PATH,
        "family_profile": V326_FAMILY_SPEC_PATH,
        "telemetry": V326_TELEMETRY_SPEC_PATH,
    }
    return {name: json.loads(path.read_text(encoding="utf-8"))
            for name, path in paths.items()}


def validate_v326_specs(specs: dict[str, dict] | None = None) -> list[str]:
    """Validate installed V3.26 contract files before they drive a build."""
    specs = specs or load_v326_specs()
    errors: list[str] = []
    required = {"efficiency", "cache", "family_profile", "telemetry"}
    missing = sorted(required - set(specs))
    if missing:
        return [f"missing V3.26 contract: {name}" for name in missing]
    for name, spec in specs.items():
        if spec.get("status") != "active":
            errors.append(f"V3.26 {name} contract must be active")
        if spec.get("version") != "3.26.0":
            errors.append(f"V3.26 {name} contract version must be 3.26.0")
    efficiency = specs["efficiency"]
    if efficiency.get("business_stages") != list(BUSINESS_STAGES):
        errors.append("V3.26 business stage order mismatch")
    if efficiency.get("baseline", {}).get("revision") != "3e5eef903da06b249bce3b4fbd43f49b3e97b087":
        errors.append("V3.26 baseline revision is not recorded")
    telemetry = specs["telemetry"]
    if not set(("stage_events", "stage_totals", "cache", "pdf", "variants")) <= set(
        telemetry.get("required_report_sections", [])
    ):
        errors.append("V3.26 telemetry report fields are incomplete")
    return errors


def validate_v326_telemetry(report: dict) -> list[str]:
    """Validate the additive V3.26 telemetry shape without enforcing it.

    This helper is intentionally observational: callers may log a telemetry
    defect, but must not turn a successful release into a semantic pass or
    convert a release blocker into a warning because instrumentation is bad.
    """
    timing = report.get("timing", report) if isinstance(report, dict) else {}
    errors: list[str] = []
    required = {"stage_events", "stage_totals", "cache", "pdf", "variants",
                "time_categories"}
    missing = sorted(required - set(timing))
    errors.extend(f"missing telemetry field: {name}" for name in missing)
    if not isinstance(timing.get("stage_events"), list):
        errors.append("telemetry stage_events must be a list")
    if not isinstance(timing.get("stage_totals"), dict):
        errors.append("telemetry stage_totals must be an object")
    if not isinstance(timing.get("variants"), list):
        errors.append("telemetry variants must be a list")
    else:
        for index, variant in enumerate(timing["variants"]):
            if not isinstance(variant, dict):
                errors.append(f"telemetry variant {index} must be an object")
                continue
            for field in ("language", "brand", "docx_seconds", "pdf_seconds"):
                if field not in variant:
                    errors.append(f"telemetry variant {index} missing {field}")
    pdf = timing.get("pdf")
    if not isinstance(pdf, dict):
        errors.append("telemetry pdf must be an object")
    else:
        for field in ("workers", "batch_seconds", "converter", "lineage_verified"):
            if field not in pdf:
                errors.append(f"telemetry pdf missing {field}")
    categories = timing.get("time_categories")
    if not isinstance(categories, dict):
        errors.append("telemetry time_categories must be an object")
    else:
        for name in ("machine", "agent_review", "human_wait", "retry"):
            if name not in categories:
                errors.append(f"telemetry time_categories missing {name}")
    return errors


def validate_efficiency_spec(spec: dict | None = None) -> list[str]:
    """Return installation/contract errors without touching any DOCX."""
    spec = spec or load_efficiency_spec()
    errors: list[str] = []
    if spec.get("status") != "active":
        errors.append("efficiency OpenSpec status must be active")
    if not spec.get("spec_id") or not spec.get("version"):
        errors.append("efficiency OpenSpec spec_id and version are required")
    stages = spec.get("business_stages")
    stage_ids = [stage.get("id") for stage in stages] if isinstance(stages, list) else []
    if tuple(stage_ids) != BUSINESS_STAGES:
        errors.append(f"business stage order mismatch: {stage_ids}")
    if any(stage.get("sequence") != index for index, stage in enumerate(stages or [], 1)):
        errors.append("business stage sequence numbers are not continuous")
    targets = spec.get("target_points") or []
    target_ids = [target.get("id") for target in targets]
    if len(target_ids) != len(set(target_ids)) or not all(target_ids):
        errors.append("efficiency target point IDs must be present and unique")
    if not isinstance(spec.get("non_goals"), list) or not spec["non_goals"]:
        errors.append("efficiency non_goals must be a non-empty list")
    if not isinstance(spec.get("release_blockers"), list) or not spec["release_blockers"]:
        errors.append("efficiency release_blockers must be a non-empty list")
    return errors


class StageTimer:
    """Record bounded stage durations with negligible work in the hot path.

    The recorder is deliberately independent of logging and DOCX objects. A
    failed stage is recorded as ``failed`` and the original exception is
    re-raised, so instrumentation cannot turn a release blocker into a pass.
    """

    def __init__(self, clock=time.perf_counter):
        self._clock = clock
        self._events: list[dict] = []

    @contextmanager
    def stage(self, name: str, **details) -> Iterator[None]:
        started = self._clock()
        status = "ok"
        try:
            yield
        except Exception:
            status = "failed"
            raise
        finally:
            event = {"stage": name, "seconds": round(self._clock() - started, 6),
                     "status": status}
            if details:
                event["details"] = details
            self._events.append(event)

    def add(self, name: str, seconds: float, *, status: str = "ok", **details) -> None:
        event = {"stage": name, "seconds": round(float(seconds), 6), "status": status}
        if details:
            event["details"] = details
        self._events.append(event)

    def snapshot(self) -> dict:
        totals = defaultdict(float)
        for event in self._events:
            totals[event["stage"]] += event["seconds"]
        return {
            "events": list(self._events),
            "totals": {name: round(value, 6) for name, value in totals.items()},
            "total_seconds": round(sum(totals.values()), 6),
        }


__all__ = ["BUSINESS_STAGES", "SPEC_PATH", "V326_SPEC_PATH",
           "V326_CACHE_SPEC_PATH", "V326_FAMILY_SPEC_PATH",
           "V326_TELEMETRY_SPEC_PATH", "StageTimer", "load_efficiency_spec",
           "load_v326_specs", "validate_efficiency_spec", "validate_v326_specs",
           "validate_v326_telemetry"]
