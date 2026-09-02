from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
CONTRACT = (ROOT / "docs" / "pdf_publication_contract.md").read_text(encoding="utf-8")
ADOPTION = (ROOT / "docs" / "pdf_converter_adoption.md").read_text(encoding="utf-8")


def test_converter_adapter_is_bundled_and_is_docx_first():
    assert (ROOT / "scripts" / "convert_docx_to_pdf.py").is_file()
    assert "scripts/convert_docx_to_pdf.py" in SKILL
    assert "final audited DOCX -> deterministic conversion adapter -> PDF preflight" in CONTRACT
    assert "source_is_final_docx" in (ROOT / "scripts" / "convert_docx_to_pdf.py").read_text(encoding="utf-8")


def test_pdf_path_forbids_independent_authoring():
    for text in (SKILL, CONTRACT, ADOPTION):
        assert "independent" in text.lower()
        assert "DOCX" in text
    assert "independent_pdf_authoring" in (ROOT / "scripts" / "convert_docx_to_pdf.py").read_text(encoding="utf-8")


def test_upstream_adoption_is_documented():
    assert "github.com/Guki125/dconv" in ADOPTION
    assert "github.com/AlJohri/docx2pdf" in ADOPTION
