from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evidence_packet import prepare_packet  # noqa: E402
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
    assert result["template_clone_started"] is False
    assert result["pdf_converter_started"] is False
