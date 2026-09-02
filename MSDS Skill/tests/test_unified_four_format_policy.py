import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from output_matrix import output_names
from sentence_boundary_policy import normalize_semantic_linebreaks
from structured_toxicology_policy import split_structured_lines,audit_field_value_integrity
from four_variant_policy import allowed_difference

def test_default_four_outputs():
    assert output_names('HPU-7710') == [
        'HPU-7710_MSDS_CN_冠志.docx','HPU-7710_MSDS_CN_国彩.docx',
        'HPU-7710_MSDS_EN_冠志.docx','HPU-7710_MSDS_EN_国彩.docx']

def test_language_filter():
    assert len(output_names('X','CN'))==2 and len(output_names('X','EN'))==2

def test_section11_not_punctuation_split():
    s='评估：此物质无急性皮肤毒性；对类似产品的研究。'
    assert normalize_semantic_linebreaks(s,section=11)==s

def test_structured_fields_keep_value():
    lines=split_structured_lines('物种：家兔 结果：轻微刺激 分类：无皮肤刺激 方法：OECD 404')
    assert lines==['物种：家兔','结果：轻微刺激','分类：无皮肤刺激','方法：OECD 404']
    assert not audit_field_value_integrity(lines)

def test_company_whitelist():
    assert allowed_difference('CN','guanzhi','CN','guocai','supplier_name')
    assert not allowed_difference('CN','guanzhi','CN','guocai','toxicity')
