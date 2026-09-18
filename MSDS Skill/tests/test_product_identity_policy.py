import importlib.util
import sys
from pathlib import Path

mod_path = Path(__file__).parents[1] / 'scripts' / 'product_identity_policy.py'
spec = importlib.util.spec_from_file_location('identity', mod_path)
identity = importlib.util.module_from_spec(spec); sys.modules['identity']=identity; spec.loader.exec_module(identity)

def test_ep1704_expected_identity():
    x = identity.expected_identity('水性环氧乳液', 'EP-1704')
    assert x.product_name_value == ''
    assert x.chinese_name_value == '水性环氧乳液 EP-1704'

def test_reject_model_in_product_name():
    errs = identity.audit_identity(chinese_name='水性环氧乳液', model='EP-1704',
        product_name_value='EP-1704', chinese_name_value='水性环氧乳液 EP-1704',
        header_text='EP-1704', footer_text='EP-1704-MSDS')
    assert any('产品名称' in e for e in errs)

def test_no_duplicate_model():
    x = identity.expected_identity('水性环氧乳液 EP-1704', 'EP-1704')
    assert x.chinese_name_value == '水性环氧乳液 EP-1704'

def test_no_duplicate_model_when_source_name_has_compact_suffix():
    x = identity.expected_identity('脂肪族水性聚氨酯接着树脂PU-1001', 'PU-1001')
    assert x.chinese_name_value == '脂肪族水性聚氨酯接着树脂PU-1001'

def test_compact_model_suffix_match_is_case_insensitive_and_whitespace_tolerant():
    x = identity.expected_identity('水性环氧乳液 p u - 1 7 0 4', 'PU-1704')
    assert x.chinese_name_value == '水性环氧乳液 p u - 1 7 0 4'
