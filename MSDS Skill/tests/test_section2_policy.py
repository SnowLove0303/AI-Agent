from pathlib import Path
import importlib.util

p = Path(__file__).resolve().parents[1] / "scripts" / "section2_hp_policy.py"
spec = importlib.util.spec_from_file_location("hp", p)
hp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hp)

# Missing-data markers disappear.
for x in ["无数据", "无数据资料。", "暂无数据", "无可用资料", "无适用资料"]:
    assert hp.is_missing_data_value(x), x

# Substantive conclusions remain displayable.
for x in ["不适用", "无刺激", "无危险反应", "非危险品", "初沸点以下无闪点", "无"]:
    assert not hp.is_missing_data_value(x), x

assert hp.split_h_statements("H315 造成皮肤刺激。 H319 造成严重眼刺激。") == [
    "H315 造成皮肤刺激。", "H319 造成严重眼刺激。"
]
assert hp.split_h_statements("H412 对水生生物有害并具有长期持续影响。") == [
    "H412 对水生生物有害并具有长期持续影响。"
]
assert hp.split_p_statements("P273 禁止排入环境。 P501 将本品或其容器送至有资质的废物处理厂处置。") == [
    "P273 禁止排入环境。", "P501 将本品或其容器送至有资质的废物处理厂处置。"
]
assert hp.split_p_statements("预防措施： P210 远离热源。 P280 戴防护手套。") == [
    "预防措施：", "P210 远离热源。", "P280 戴防护手套。"
]
assert hp.split_p_statements("P301+P310 如误吞咽：立即呼叫解毒中心/医生。 P331 不得诱导呕吐。") == [
    "P301+P310 如误吞咽：立即呼叫解毒中心/医生。", "P331 不得诱导呕吐。"
]
print("section2 policy tests: PASS")
