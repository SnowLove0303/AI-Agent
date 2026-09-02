from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from company_profile_policy import PROFILES, audit_guocai_text, expected_footer, output_filename

p=PROFILES['国彩']
assert p.supplier_name == '英德市国彩精细化工有限公司'
assert p.supplier_address == '广东省英德市白沙镇太平村更古坑凯迪工业园区'
assert p.phone == '86-763-2811205'
assert p.fax == '86-763-2811024'
assert expected_footer('国彩','EP-1704') == '英德市国彩精细化工有限公司 EP-1704-MSDS'
assert output_filename('EP-1704','冠志') == 'EP-1704_MSDS_CN_冠志.docx'
assert output_filename('EP-1704','国彩') == 'EP-1704_MSDS_CN_国彩.docx'
good='英德市国彩精细化工有限公司 广东省英德市白沙镇太平村更古坑凯迪工业园区 86-763-2811205 86-763-2811024'
assert audit_guocai_text(good)==[]
bad=good+' 广州冠志新材料科技有限公司'
assert audit_guocai_text(bad)
print('company profile policy tests: PASS')
