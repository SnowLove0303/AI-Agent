"""Review-bound declarative product-family candidates.

Family profiles are deliberately separate from approved facts.  They can
reduce repeated mapping work, but this module never returns a facts model and
never writes a DOCX value.  Only a candidate confirmed by current-source
evidence, reviewed translation evidence or an allowed controlled overlay can
be reported as eligible for a reviewed facts model.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from source_grounding import _source_text


SKILL_ROOT = Path(__file__).resolve().parent.parent
PROFILE_SPEC_PATH = SKILL_ROOT / "openspec" / "family_profile_contract.json"
ALLOWED_DISPOSITIONS = {"candidate", "confirmed", "omitted", "conflict"}
ALLOWED_EVIDENCE = {"current_source", "reviewed_translation", "controlled_overlay"}
TARGET_RE = re.compile(r"^s(?:[1-9]|1[0-6])(?:\.[0-9]+)?$", re.I)


class FamilyProfileError(ValueError):
    """Raised when a family profile cannot be used safely."""


def _text(value: object) -> str:
    return str(value or "").strip()


def _canonical(value: object) -> str:
    return re.sub(r"\s+", "", _text(value).casefold())


def load_profile(path: Path) -> dict:
    """Load one dependency-free JSON family profile."""
    path = Path(path).expanduser().resolve()
    if path.suffix.casefold() != ".json":
        raise FamilyProfileError("family profile must be a JSON file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FamilyProfileError(f"family profile cannot be read: {path}") from exc
    if not isinstance(payload, dict):
        raise FamilyProfileError("family profile root must be an object")
    return payload


def validate_profile(profile: dict, model: str | None = None) -> list[str]:
    """Return structural/profile-scope blockers without touching a DOCX."""
    errors: list[str] = []
    for field in ("profile_id", "family", "models", "candidates"):
        if field not in profile:
            errors.append(f"family profile missing {field}")
    if not isinstance(profile.get("profile_id"), str) or not _text(profile.get("profile_id")):
        errors.append("family profile profile_id must be a non-empty string")
    if not isinstance(profile.get("family"), str) or not _text(profile.get("family")):
        errors.append("family profile family must be a non-empty string")
    models = profile.get("models")
    if not isinstance(models, list) or not models or not all(
        isinstance(item, str) and _text(item) for item in models
    ):
        errors.append("family profile models must be a non-empty string list")
        models = []
    if model and model not in models:
        errors.append(f"family profile does not include requested model {model}")
    candidates = profile.get("candidates")
    if not isinstance(candidates, list):
        errors.append("family profile candidates must be a list")
        candidates = []
    seen = set()
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            errors.append(f"family profile candidate {index} is not an object")
            continue
        candidate_id = _text(candidate.get("candidate_id"))
        if not candidate_id:
            errors.append(f"family profile candidate {index} has no candidate_id")
        elif candidate_id in seen:
            errors.append(f"family profile duplicate candidate_id: {candidate_id}")
        else:
            seen.add(candidate_id)
        target = _text(candidate.get("target"))
        if not TARGET_RE.fullmatch(target):
            errors.append(f"family profile candidate {index} has invalid target: {target}")
        if not _text(candidate.get("value")):
            errors.append(f"family profile candidate {index} has no value")
        if candidate.get("evidence_required") is not True:
            errors.append(f"family profile candidate {index} must require evidence")
        disposition = candidate.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f"family profile candidate {index} has invalid disposition")
        if disposition == "omitted" and not _text(candidate.get("reason")):
            errors.append(f"family profile candidate {index} omitted without reason")
        if disposition == "conflict":
            errors.append(f"family profile candidate {index} is a conflict")
    return errors


def review_profile(path: Path, source: Path, model: str,
                   *, prepared_source: Path | None = None) -> dict:
    """Review candidates against the current source, without approving them."""
    profile = load_profile(path)
    errors = validate_profile(profile, model)
    candidates = profile.get("candidates") if isinstance(profile.get("candidates"), list) else []
    search_path = Path(prepared_source or source).expanduser().resolve()
    corpus = _source_text(search_path)
    suggestions: list[dict] = []
    confirmed: list[dict] = []
    blocked: list[dict] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        disposition = candidate.get("disposition")
        evidence = candidate.get("evidence")
        evidence_type = evidence.get("type") if isinstance(evidence, dict) else None
        candidate_id = _text(candidate.get("candidate_id"))
        if disposition == "conflict":
            blocked.append({"candidate_id": candidate_id, "reason": "conflict"})
            continue
        if disposition != "confirmed":
            suggestions.append({
                "candidate_id": candidate_id,
                "target": _text(candidate.get("target")),
                "status": disposition or "invalid",
            })
            continue
        if evidence_type not in ALLOWED_EVIDENCE:
            blocked.append({"candidate_id": candidate_id,
                            "reason": "confirmed candidate has invalid evidence type"})
            continue
        if not isinstance(evidence, dict) or not _text(evidence.get("source_locator")):
            blocked.append({"candidate_id": candidate_id,
                            "reason": "confirmed candidate has no evidence locator"})
            continue
        if evidence_type == "current_source":
            source_text = _text(evidence.get("source_text"))
            if not source_text or _canonical(source_text) not in _canonical(corpus):
                blocked.append({"candidate_id": candidate_id,
                                "reason": "confirmed candidate has no current-source anchor"})
                continue
        elif evidence.get("status") != "reviewed":
            blocked.append({"candidate_id": candidate_id,
                            "reason": f"{evidence_type} evidence is not reviewed"})
            continue
        confirmed.append({
            "candidate_id": candidate_id,
            "target": _text(candidate.get("target")),
            "value": candidate.get("value"),
            "evidence": evidence,
            "status": "eligible-for-approved-facts-review",
        })
    errors.extend(item["reason"] + ": " + item["candidate_id"] for item in blocked)
    return {
        "profile": str(Path(path).expanduser().resolve()),
        "model": model,
        "source": str(Path(source).expanduser().resolve()),
        "source_search_path": str(search_path),
        "suggestions": suggestions,
        "confirmed": confirmed,
        "blocked": blocked,
        "errors": errors,
        "status": "passed" if not errors else "failed",
        "writes_facts": False,
        "writes_docx": False,
    }


__all__ = [
    "ALLOWED_DISPOSITIONS", "ALLOWED_EVIDENCE", "FamilyProfileError",
    "PROFILE_SPEC_PATH", "load_profile", "review_profile", "validate_profile",
]
