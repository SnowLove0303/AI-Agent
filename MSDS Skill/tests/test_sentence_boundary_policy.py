import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sentence_boundary_policy import normalize_semantic_linebreaks, audit_semantic_linebreaks

s='操作时遵守预防措施。避免接触；保持通风。'
assert normalize_semantic_linebreaks(s) == '操作时遵守预防措施。\n避免接触；\n保持通风。'
# Do not split decimal periods / ordinary ASCII periods automatically.
s2='LD50: > 2,000 mg/kg. pH 7.5; keep ventilated.'
out=normalize_semantic_linebreaks(s2)
assert '7.5' in out
assert out == 'LD50: > 2,000 mg/kg. pH 7.5;\nkeep ventilated.'
# Existing blank lines collapse.
assert normalize_semantic_linebreaks('甲。\n\n乙； 丙') == '甲。\n乙；\n丙'
assert audit_semantic_linebreaks('甲。乙')
assert not audit_semantic_linebreaks('甲。\n乙')
print('sentence boundary policy tests: PASS')
