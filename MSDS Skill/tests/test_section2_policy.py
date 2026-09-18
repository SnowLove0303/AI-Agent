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
grouped_source = (
    "\u9884\u9632\u63aa\u65bd\uff1a\n"
    "P210 \u8fdc\u79bb\u70ed\u6e90\u3002\n"
    "P280 \u6234\u9632\u62a4\u624b\u5957\u3002\n"
    "\u4e8b\u6545\u54cd\u5e94\uff1a\n"
    "P304+P340 \u5982\u679c\u5438\u5165\uff1a\u5c06\u4eba\u5458\u79fb\u5230\u7a7a\u6c14\u65b0\u9c9c\u5904\u3002\n"
    "\u5b89\u5168\u50a8\u5b58\uff1a\n"
    "\u5e9f\u5f03\u5904\u7f6e\uff1a\n"
    "P501 \u6309\u7167\u5730\u65b9\u89c4\u5b9a\u5904\u7f6e\u3002"
)
group_tokens = hp.split_precautionary_statements(grouped_source)
assert [token["kind"] for token in group_tokens] == [
    "group_heading", "p_statement", "p_statement",
    "group_heading", "p_statement", "group_heading", "group_heading",
    "p_statement",
]
assert [token.get("group_key") for token in group_tokens if token["kind"] == "group_heading"] == [
    "prevention", "response", "storage", "disposal",
]
assert hp.render_precautionary_groups([
    {"group_key": "prevention", "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a", "statements": [{"text": "P210"}]},
    {"group_key": "storage", "source_heading": "\u5b89\u5168\u50a8\u5b58\uff1a", "statements": []},
], "zh") == "\u9884\u9632\u63aa\u65bd\uff1a\nP210"
assert hp.render_precautionary_groups([
    {"group_key": "prevention", "source_heading": "\u9884\u9632\u63aa\u65bd\uff1a", "statements": [{"text": "P210"}]},
], "en") == "Prevention:\nP210"
print("section2 policy tests: PASS")
