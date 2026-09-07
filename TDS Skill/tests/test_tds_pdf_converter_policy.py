from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = (ROOT / "scripts" / "convert_docx_to_pdf.py").read_text(encoding="utf-8")
CLI = (ROOT / "scripts" / "tds_cli.py").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
CONTRACT = (ROOT / "docs" / "pdf_publication_contract.md").read_text(encoding="utf-8")


def test_converter_is_bundled_and_docx_first():
    assert (ROOT / "scripts" / "convert_docx_to_pdf.py").is_file()
    assert "word2pdf" in CONVERTER
    assert "WPSCLI_PATH" in CONVERTER
    assert "source_is_final_docx" in CONVERTER
    assert "independent_pdf_authoring" in CONVERTER
    assert "soffice" not in CONVERTER.lower()
    assert "libreoffice" not in CONVERTER.lower()


def test_build_preflights_docx_before_pdf_and_records_evidence():
    assert "--docx-only" in CLI
    assert "pdf_conversion" in CLI
    assert "--evidence" in CLI
    assert "最终 DOCX" in SKILL
    assert "先完成 Word，再转换 PDF" in CONTRACT
