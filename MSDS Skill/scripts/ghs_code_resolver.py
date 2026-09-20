# -*- coding: utf-8 -*-
"""GHS Precautionary and Hazard Code Reverse Resolver.

Maps natural language statements to standard GHS alphanumeric codes and canonical text.
"""
import re

PRECAUTIONARY_RULES = [
    # Prevention
    {
        "code": "P280",
        "group": "prevention",
        "patterns": [r"防护用品", r"手套", r"防护镜", r"工作服", r"protective"],
        "zh": "P280 穿戴防护手套/防护服/防护眼镜/防护面罩。",
        "en": "P280 Wear protective gloves/protective clothing/eye protection/face protection."
    },
    {
        "code": "P264",
        "group": "prevention",
        "patterns": [r"清洗身体接触部位", r"彻底清洗", r"洗手", r"wash.*thoroughly"],
        "zh": "P264 作业后彻底清洗身体接触部位。",
        "en": "P264 Wash hands and skin thoroughly after handling."
    },
    {
        "code": "P270",
        "group": "prevention",
        "patterns": [r"不得进食", r"饮水或吸烟", r"eat.*drink.*smoke"],
        "zh": "P270 使用本品时不得进食、饮水或吸烟。",
        "en": "P270 Do not eat, drink or smoke when using this product."
    },
    {
        "code": "P271",
        "group": "prevention",
        "patterns": [r"室外或通风良好", r"通风良好处", r"outdoors.*ventilated"],
        "zh": "P271 只能在室外或通风良好处操作。",
        "en": "P271 Use only outdoors or in a well-ventilated area."
    },
    # Response
    {
        "code": "P304+P340",
        "group": "response",
        "patterns": [r"吸入.*就医", r"吸入.*新鲜空气", r"inhaled"],
        "zh": "P304+P340 如吸入：将受害人转移到空气新鲜处，保持呼吸舒适的体位。如有不适，就医。",
        "en": "P304+P340 IF INHALED: Remove person to fresh air and keep comfortable for breathing. Call a doctor if you feel unwell."
    },
    {
        "code": "P305+P351+P338",
        "group": "response",
        "patterns": [r"眼睛接触", r"冲洗眼睛", r"清水.*清洗.*就医", r"in eyes"],
        "zh": "P305+P351+P338 如进入眼睛：用水小心冲洗几分钟。如戴隐形眼镜并可方便取出，取出隐形眼镜。继续冲洗。如有不适感，就医。",
        "en": "P305+P351+P338 IF IN EYES: Rinse cautiously with water for several minutes. Remove contact lenses, if present and easy to do. Continue rinsing. If eye irritation persists: Get medical advice/attention."
    },
    {
        "code": "P302+P352",
        "group": "response",
        "patterns": [r"皮肤接触.*清洗", r"肥皂.*清洗", r"on skin"],
        "zh": "P302+P352 如皮肤沾染：用大量肥皂和水清洗。如有不适感，就医。",
        "en": "P302+P352 IF ON SKIN: Wash with plenty of soap and water. If skin irritation occurs: Get medical advice/attention."
    },
    {
        "code": "P301+P330+P331",
        "group": "response",
        "patterns": [r"误服", r"食入.*漱口", r"禁止催吐", r"swallowed"],
        "zh": "P301+P330+P331 如误吞咽：漱口。不要催吐。立即就医。",
        "en": "P301+P330+P331 IF SWALLOWED: Rinse mouth. Do NOT induce vomiting. Immediately call a doctor."
    },
    {
        "code": "P391",
        "group": "response",
        "patterns": [r"收集泄漏物", r"泄露.*收集", r"collect spillage"],
        "zh": "P391 收集泄漏物。",
        "en": "P391 Collect spillage."
    },
    {
        "code": "P370+P378",
        "group": "response",
        "patterns": [r"灭火", r"火灾时.*干粉", r"fire"],
        "zh": "P370+P378 火灾时：使用干粉、泡沫、二氧化碳灭火。",
        "en": "P370+P378 In case of fire: Use dry powder, foam, or carbon dioxide to extinguish."
    },
    # Storage
    {
        "code": "P403+P235",
        "group": "storage",
        "patterns": [r"避光.*阴凉", r"阴凉干燥", r"存储温度.*5-35", r"keep cool", r"ventilated"],
        "zh": "P403+P235 存放在通风良好的地方。保持阴凉。存储温度保持在5-35℃，避免霜冻。",
        "en": "P403+P235 Store in a well-ventilated place. Keep cool. Maintain storage temperature at 5-35°C, protect from freezing."
    },
    # Disposal
    {
        "code": "P501",
        "group": "disposal",
        "patterns": [r"空桶", r"包装物.*处置", r"法规规定", r"dispose"],
        "zh": "P501 按照国家和地方相关法律法规规定处置内装物和容器。",
        "en": "P501 Dispose of contents/container in accordance with national and local regulations."
    },
]


def resolve_precautionary_statements(raw_lines: list[str]) -> dict:
    full_text = " ".join(raw_lines)
    resolved_groups = {
        "prevention": {"heading_zh": "预防措施：", "heading_en": "Prevention:", "statements": []},
        "response": {"heading_zh": "事故响应：", "heading_en": "Response:", "statements": []},
        "storage": {"heading_zh": "安全储存：", "heading_en": "Storage:", "statements": []},
        "disposal": {"heading_zh": "废弃处置：", "heading_en": "Disposal:", "statements": []},
    }

    seen_codes = set()
    for rule in PRECAUTIONARY_RULES:
        code = rule["code"]
        if code in seen_codes:
            continue
        matched = False
        for pat in rule["patterns"]:
            if re.search(pat, full_text, re.IGNORECASE):
                matched = True
                break
        if matched:
            seen_codes.add(code)
            group_key = rule["group"]
            resolved_groups[group_key]["statements"].append({
                "code": code,
                "zh": rule["zh"],
                "en": rule["en"]
            })

    return resolved_groups


def format_precautionary_text(resolved_groups: dict, language: str) -> str:
    is_en = language.lower() in {"en", "en-us"}
    lines = []
    for g_key in ["prevention", "response", "storage", "disposal"]:
        grp = resolved_groups[g_key]
        stmts = grp["statements"]
        if not stmts:
            continue
        heading = grp["heading_en"] if is_en else grp["heading_zh"]
        lines.append(heading)
        for s in stmts:
            lines.append(s["en"] if is_en else s["zh"])
    return "\n".join(lines)
