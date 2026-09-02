from pathlib import Path

def test_pdf_contract_present():
    root=Path(__file__).resolve().parents[1]
    s=(root/'SKILL.md').read_text(encoding='utf-8')
    assert 'eight synchronized deliverables' in s
    assert 'PDF publication layer' in s
    assert 'final audited DOCX -> deterministic conversion adapter -> PDF preflight -> full-page render QA' in s
    assert 'scripts/convert_docx_to_pdf.py' in s
    assert (root/'scripts'/'audit_eight_file_release.py').exists()
