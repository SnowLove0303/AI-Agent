from copy import deepcopy
from pathlib import Path
import sys

from docx import Document
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_en_layout import sync_en_template_text_format


def _xml(element):
    return etree.tostring(element, method="c14n") if element is not None else b""


def test_en_text_format_is_restored_from_the_maintained_template():
    template = ROOT / "examples" / "template_reference_en.docx"
    document = Document(str(template))
    target = document.tables[0].cell(1, 1).paragraphs[0]
    target.text = "OS-9015"
    target.paragraph_format.alignment = 3
    target.runs[0].font.name = "Courier New"
    target.runs[0].font.size = None

    reference = Document(str(template))
    ref = reference.tables[0].cell(1, 1).paragraphs[0]
    sync_en_template_text_format(document, template)

    assert _xml(target._p.pPr) == _xml(ref._p.pPr)
    ref_rpr = ref.runs[0]._r.rPr if ref.runs else None
    assert _xml(target.runs[0]._r.rPr) == _xml(ref_rpr)
