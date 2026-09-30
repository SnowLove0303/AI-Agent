from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "j" + "ev",
    "system" + " " + "one",
    "global_" + "ledger",
    "decision" + " " + "ledger",
    "adju" + "dicat",
    "ZE" + "N_" + "API_KEY",
    "J" + "EV_" + "API_KEY",
    "J" + "EV_" + "ENDPOINT",
    "J" + "EV_" + "MODEL",
    "opencode.ai/" + "zen",
)


def find_forbidden(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        relative = path.relative_to(root).as_posix().lower()
        if any(token.lower() in relative for token in FORBIDDEN):
            findings.append(relative)
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for token in FORBIDDEN:
            if token.lower() in text:
                findings.append(f"{relative}:{token}")
    return findings


def test_forbidden_reference_detector_catches_synthetic_reference():
    synthetic = "prefix " + "J" + "EV_API_KEY" + " suffix"
    assert any(token.lower() in synthetic.lower() for token in FORBIDDEN)


def test_package_has_no_remote_semantic_dependency():
    assert find_forbidden(ROOT) == []
