from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evidence_packet import (  # noqa: E402
    packet_direct_build_errors,
    prepare_packet,
    validate_packet_provenance,
)
from source_ingest import discover_source  # noqa: E402
from preflight_facts import run as run_preflight  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "regression_HPU-7660_source.docx"


def test_evidence_packet_is_review_required_and_reusable(tmp_path):
    packet_path = tmp_path / "evidence" / "HPU-7660.packet.json"
    cache_dir = tmp_path / ".msds_cache"

    packet, reused = prepare_packet(
        FIXTURE, packet_path, model="HPU-7660", cache_dir=cache_dir
    )
    assert reused is False
    assert packet["status"] == "needs-review"
    assert packet["build_allowed"] is False
    assert packet["facts_draft"]["source_sha256"] == packet["source"]["sha256"]
    assert packet["review_summary"]["source_units"] > 0
    assert packet["checkpoint"]["next_required_stage"] == "agent_review"

    second, reused = prepare_packet(
        FIXTURE, packet_path, model="HPU-7660", cache_dir=cache_dir
    )
    assert reused is True
    assert second["packet_cache_key"] == packet["packet_cache_key"]
    assert second["build_allowed"] is False


def test_preflight_reports_all_contract_errors_without_template_or_pdf_work(tmp_path):
    facts_path = tmp_path / "facts.json"
    facts_path.write_text('{"model":"HPU-7660"}\n', encoding="utf-8")
    result = run_preflight(FIXTURE, facts_path, "HPU-7660")
    assert result["status"] == "blocked"
    assert len(result["errors"]) >= 4
    assert result["blockers"] == result["errors"]
    assert result["template_clone_started"] is False
    assert result["pdf_converter_started"] is False


def test_preflight_blocks_non_object_facts_json(tmp_path):
    facts_path = tmp_path / "facts.json"
    facts_path.write_text("[]\n", encoding="utf-8")
    result = run_preflight(FIXTURE, facts_path, "HPU-7660")
    assert result["status"] == "blocked"
    assert result["errors"] == ["facts JSON root must be an object"]
    assert result["blockers"] == result["errors"]


def test_packet_provenance_is_validated_but_unapproved_packet_cannot_build(tmp_path):
    packet_path = tmp_path / "evidence" / "HPU-7660.packet.json"
    cache_dir = tmp_path / ".msds_cache"
    packet, _ = prepare_packet(
        FIXTURE, packet_path, model="HPU-7660", cache_dir=cache_dir
    )
    selection = discover_source(FIXTURE, model="HPU-7660")

    assert validate_packet_provenance(packet, selection, "HPU-7660") == []
    errors = packet_direct_build_errors(packet, selection, "HPU-7660")
    assert any("review-required" in error for error in errors)

    stale = dict(packet)
    stale["packet_cache_key"] = "stale"
    stale_errors = validate_packet_provenance(stale, selection, "HPU-7660")
    assert any("cache key" in error for error in stale_errors)


def test_preflight_explicitly_rejects_packet_as_approved_facts(tmp_path):
    packet_path = tmp_path / "evidence" / "HPU-7660.packet.json"
    packet, _ = prepare_packet(
        FIXTURE, packet_path, model="HPU-7660", cache_dir=tmp_path / ".msds_cache"
    )
    facts_path = tmp_path / "facts.json"
    facts_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    result = run_preflight(FIXTURE, facts_path, "HPU-7660")

    assert result["status"] == "blocked"
    assert any("review-required" in error for error in result["errors"])
