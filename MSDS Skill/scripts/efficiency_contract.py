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
BUSINESS_STAGES = (
    "extract_all_source_information",
    "constrained_information_normalization",
    "fixed_structure_template_overwrite",
    "post_overwrite_fine_tuning",
)


def load_efficiency_spec(path: Path | None = None) -> dict:
    """Load the active machine-readable V3.24 efficiency contract."""
    return json.loads((path or SPEC_PATH).read_text(encoding="utf-8"))


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


__all__ = ["BUSINESS_STAGES", "SPEC_PATH", "StageTimer",
           "load_efficiency_spec", "validate_efficiency_spec"]
