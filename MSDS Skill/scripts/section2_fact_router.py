"""Fail-closed semantic routing for Section 2 source facts.

Visible Section 2 numbers are presentation and may change after an approved
missing-row suppression.  This module therefore audits stable semantic targets
and keeps the source fact boundary separate from the template's visible labels.
The default is one source fact to one Section 2 target.  Reuse is possible only
when the reviewed routing record explicitly declares a shared exception.
"""
from __future__ import annotations

import re
import unicodedata


ROUTER_VERSION = "1.2.0"
SECTION2_TARGETS = (
    "emergency_overview",
    "ghs_classes",
    "label_elements",
    "signal_word",
    "hazard_statements",
    "precautionary_statements",
    "physical_chemical_hazards",
    "health_hazards.inhalation",
    "health_hazards.ingestion",
    "health_hazards.skin",
    "health_hazards.eyes",
    "health_hazards.symptoms_signs",
    "health_hazards",
    "environmental_hazards",
    "other_hazards",
)
_TARGET_SET = set(SECTION2_TARGETS)
_PRECAUTIONARY_GROUP_EN = {
    "prevention": "Prevention:",
    "response": "Response:",
    "storage": "Storage:",
    "disposal": "Disposal:",
}

_HEALTH_ROUTE_TARGETS = (
    "health_hazards.inhalation",
    "health_hazards.ingestion",
    "health_hazards.skin",
    "health_hazards.eyes",
    "health_hazards.symptoms_signs",
)
_H_CODE_ROUTE_MAP = {
    "inhalation": (330, 331, 332, 334, 335),
    "ingestion": (300, 301, 302, 303, 304),
    "skin": (310, 311, 312, 313, 314, 315, 316, 317),
    "eyes": (314, 318, 319),
}
_ROUTE_TEXT_PATTERNS = {
    "inhalation": re.compile(r"吸入|呼吸道|吸入后|inhal(?:ation|ed)|respiratory", re.I),
    "ingestion": re.compile(r"食入|摄入|吞食|经口|口服|swallow(?:ed)?|ingest(?:ion|ed)?|oral", re.I),
    "skin": re.compile(r"皮肤|经皮|skin|dermal", re.I),
    "eyes": re.compile(r"眼睛|眼部|眼|eye|ocular", re.I),
    "symptoms_signs": re.compile(r"症状|体征|symptoms?|signs?", re.I),
}


def health_routes_covered_by_h_statements(statements) -> set[str]:
    """Return only exposure routes explicitly covered by Section 2.5 H text."""
    covered: set[str] = set()
    text = "\n".join(_text(item) for item in (statements or []) if _text(item))
    for code in re.findall(r"(?<![A-Za-z0-9])H(\d{3})[A-Za-z]{0,3}\b", text, re.I):
        number = int(code)
        for route, numbers in _H_CODE_ROUTE_MAP.items():
            if number in numbers:
                covered.add(f"health_hazards.{route}")
    for route, pattern in _ROUTE_TEXT_PATTERNS.items():
        if pattern.search(text):
            covered.add(f"health_hazards.{route}")
    return covered

_TARGET_ALIASES = {
    "emergency_overview": ("emergency_overview", "emergency", "紧急情况概述", "紧急概述"),
    "ghs_classes": ("ghs_classes", "ghs_class", "ghs危险性类别", "危险性类别"),
    "label_elements": ("label_elements", "label_element", "ghs标签要素", "标签要素"),
    "signal_word": ("signal_word", "signal", "信号词"),
    "hazard_statements": ("hazard_statements", "h_statements", "hstatement", "危险性说明"),
    "precautionary_statements": (
        "precautionary_statements", "p_statements", "pstatement", "防范说明",
    ),
    "physical_chemical_hazards": (
        "physical_chemical_hazards", "physical_chemical_hazard", "物理和化学危险",
        "物理化学危险",
    ),
    "health_hazards.inhalation": (
        "health_hazards.inhalation", "health hazard inhalation", "inhalation",
        "吸入", "呼吸道",
    ),
    "health_hazards.ingestion": (
        "health_hazards.ingestion", "health hazard ingestion", "ingestion",
        "oral", "食入", "摄入", "吞食",
    ),
    "health_hazards.skin": (
        "health_hazards.skin", "health hazard skin", "skin", "皮肤",
    ),
    "health_hazards.eyes": (
        "health_hazards.eyes", "health hazard eyes", "eye", "eyes", "眼睛", "眼部",
    ),
    "health_hazards.symptoms_signs": (
        "health_hazards.symptoms_signs", "symptoms_signs", "symptoms and signs",
        "signs and symptoms", "症状和体征", "症状及体征", "症状与体征",
    ),
    "health_hazards": ("health_hazards", "health_hazard", "健康危害"),
    "environmental_hazards": (
        "environmental_hazards", "environmental_hazard", "环境危害",
    ),
    "other_hazards": ("other_hazards", "other_hazard", "其他危害", "其他危险"),
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _canonical(value: object) -> str:
    text = unicodedata.normalize("NFKC", _text(value)).casefold()
    text = text.replace("：", ":").replace("－", "-")
    return re.sub(r"[\s_\-.:\[\]（）()]+", "", text)


def _has_alias(text: str, alias: str) -> bool:
    return _canonical(alias) in _canonical(text)


def semantic_target(value: object) -> str | None:
    """Resolve a reviewed slot/label to one stable Section 2 semantic target.

    Generic positional names such as ``s2.row[1]`` intentionally return None;
    they are ambiguous after omission and must not be used for release.
    """
    text = _text(value)
    compact = _canonical(text)
    if not compact:
        return None
    # Route aliases must win over numeric 2.8.  The visible number is
    # presentation-only and repeated 2.8 rows are otherwise indistinguishable
    # after empty-row suppression.
    route_targets = (
        "health_hazards.inhalation",
        "health_hazards.ingestion",
        "health_hazards.skin",
        "health_hazards.eyes",
        "health_hazards.symptoms_signs",
    )
    for target in route_targets:
        aliases = sorted(_TARGET_ALIASES[target], key=len, reverse=True)
        if any(_has_alias(compact, alias) for alias in aliases):
            return target
    numeric = re.search(r"(?:^|s)2\.(\d+)(?:$|[^0-9])", text.casefold())
    if numeric:
        number = int(numeric.group(1))
        numeric_targets = {
            1: "emergency_overview",
            2: "ghs_classes",
            3: "label_elements",
            4: "signal_word",
            5: "hazard_statements",
            6: "precautionary_statements",
            7: "physical_chemical_hazards",
            8: "health_hazards",
            9: "environmental_hazards",
            10: "other_hazards",
        }
        if number in numeric_targets:
            return numeric_targets[number]
    # Prefer specific targets before short aliases such as ``signal``.
    for target in SECTION2_TARGETS:
        aliases = sorted(_TARGET_ALIASES[target], key=len, reverse=True)
        if any(_has_alias(compact, alias) for alias in aliases):
            return target
    return None


def _is_overall_classification_fact(mapping: dict, fact: dict) -> bool:
    """Return true for a classification conclusion being reused as a route."""
    source_locator = _text(mapping.get("source_locator"))
    target_slot = _text(mapping.get("target_slot"))
    source_text = _text(mapping.get("source_text") or fact.get("source_text"))
    classification_locator = bool(re.search(
        r"(?:ghs[_ .-]*class|classification|危险性分类|危险性)",
        source_locator + " " + target_slot,
        re.I,
    ))
    overall_conclusion = bool(re.search(
        r"(?:未被分类|未分类|不属于危险|not\s+classified|not\s+hazardous|non[- ]?hazardous)",
        source_text,
        re.I,
    ))
    return classification_locator and overall_conclusion


def _row_value(row: object) -> str:
    if isinstance(row, dict):
        return _text(row.get("value"))
    if not isinstance(row, (list, tuple)):
        return ""
    if len(row) <= 1:
        return ""
    return "\n".join(_text(value) for value in row[1:] if _text(value))


def _iter_section2_rows(layer: object, language: str):
    rows = layer.get("s2") if isinstance(layer, dict) else None
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows, start=1):
        label = _text(row.get("label")) if isinstance(row, dict) else (
            _text(row[0]) if isinstance(row, (list, tuple)) and row else ""
        )
        target = semantic_target(label)
        value = _row_value(row)
        if target and value:
            yield language, index, target, value


def _mapping_items(facts: dict) -> tuple[dict[str, dict], list[str]]:
    by_fact: dict[str, dict] = {}
    errors: list[str] = []
    mapping = facts.get("source_mapping")
    if not isinstance(mapping, dict):
        return by_fact, ["Section 2 routing: source_mapping is missing"]
    items = mapping.get("items")
    if not isinstance(items, list):
        return by_fact, ["Section 2 routing: source_mapping.items is missing"]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not _text(item.get("fact_id")):
            continue
        if item.get("decision") != "mapped":
            continue
        fact_id = _text(item.get("fact_id"))
        if fact_id in by_fact:
            errors.append(f"Section 2 routing: fact {fact_id} is mapped more than once")
        by_fact[fact_id] = item
        if item.get("target_section") == "s2":
            target = semantic_target(item.get("target_slot"))
            if target is None:
                errors.append(
                    f"Section 2 routing: mapping item {index} has ambiguous target_slot "
                    f"{item.get('target_slot')!r}"
                )
            elif item.get("source_section") != "s2" and not (
                item.get("cross_section_route") is True and target == "ghs_classes"
            ):
                errors.append(
                    f"Section 2 routing: fact {fact_id} comes from "
                    f"{item.get('source_section')!r} but targets {target}"
                )
    return by_fact, errors


def _trace_items(facts: dict) -> tuple[list[dict], list[str]]:
    trace = facts.get("output_traceability")
    if not isinstance(trace, dict):
        return [], ["Section 2 routing: output_traceability is missing"]
    items = trace.get("items")
    if not isinstance(items, list):
        return [], ["Section 2 routing: output_traceability.items is missing"]
    errors: list[str] = []
    s2_items: list[dict] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("target_section") != "s2":
            continue
        target = semantic_target(item.get("target_slot"))
        if target is None:
            errors.append(
                f"Section 2 routing: trace item {index} has ambiguous target_slot "
                f"{item.get('target_slot')!r}"
            )
        else:
            item = dict(item)
            item["_semantic_target"] = target
            s2_items.append(item)
    return s2_items, errors


def _routing_items(facts: dict) -> tuple[dict[str, dict], list[str]]:
    routing = facts.get("section2_routing")
    if not isinstance(routing, dict):
        return {}, ["Section 2 routing: section2_routing is required"]
    errors: list[str] = []
    if routing.get("version") != ROUTER_VERSION:
        errors.append(
            f"Section 2 routing: version must be {ROUTER_VERSION}, found {routing.get('version')!r}"
        )
    if routing.get("status") != "reviewed":
        errors.append("Section 2 routing: status must be reviewed")
    items = routing.get("items")
    if not isinstance(items, list):
        return {}, errors + ["Section 2 routing: items is required"]
    by_fact: dict[str, dict] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"Section 2 routing: item {index} is not an object")
            continue
        fact_id = _text(item.get("fact_id"))
        target = _text(item.get("semantic_target"))
        usage = item.get("usage", "exclusive")
        if not fact_id or fact_id in by_fact:
            errors.append(f"Section 2 routing: item {index} has duplicate/missing fact_id")
            continue
        if target not in _TARGET_SET:
            errors.append(f"Section 2 routing: item {index} has invalid semantic_target")
        if usage not in {"exclusive", "shared"}:
            errors.append(f"Section 2 routing: item {index} has invalid usage {usage!r}")
        if usage == "shared":
            approved_targets = item.get("approved_targets")
            if not isinstance(approved_targets, list) or len(approved_targets) < 2:
                errors.append(
                    f"Section 2 routing: shared fact {fact_id} needs approved_targets"
                )
            elif any(value not in _TARGET_SET for value in approved_targets):
                errors.append(f"Section 2 routing: shared fact {fact_id} has invalid approved_targets")
            if not _text(item.get("reason")):
                errors.append(f"Section 2 routing: shared fact {fact_id} needs a reason")
        elif item.get("approved_targets") not in (None, [], [target]):
            errors.append(
                f"Section 2 routing: exclusive fact {fact_id} cannot claim multiple targets"
            )
        item = dict(item)
        item["_usage"] = usage
        item["_semantic_target"] = target
        by_fact[fact_id] = item
    return by_fact, errors


def _audit_precautionary_groups(
    facts: dict,
    ledger: dict[str, dict],
    routing_by_fact: dict[str, dict],
    trace_items: list[dict],
) -> list[str]:
    """Require source-present precautionary groups to survive reviewed output."""
    errors: list[str] = []
    mapping_items = (facts.get("source_mapping") or {}).get("items") or []
    mappings = {
        _text(item.get("fact_id")): item
        for item in mapping_items
        if isinstance(item, dict) and _text(item.get("fact_id"))
    }
    for fact_id, fact in ledger.items():
        if fact.get("source_kind") != "precautionary_group":
            continue
        mapping = mappings.get(fact_id)
        if mapping is None:
            errors.append(
                f"Section 2 routing: precautionary group fact {fact_id} has no mapping"
            )
            continue
        decision = mapping.get("decision")
        has_statements = bool(fact.get("has_statements"))
        if decision == "duplicate":
            errors.append(
                f"Section 2 routing: precautionary group fact {fact_id} cannot be silently marked duplicate"
            )
            continue
        if has_statements:
            target = semantic_target(mapping.get("target_slot"))
            if decision != "mapped" or target != "precautionary_statements":
                errors.append(
                    f"Section 2 routing: source-present precautionary group fact {fact_id} "
                    "must map to precautionary_statements"
                )
            route = routing_by_fact.get(fact_id)
            if route is None or route.get("_semantic_target") != "precautionary_statements":
                errors.append(
                    f"Section 2 routing: precautionary group fact {fact_id} lacks reviewed "
                    "precautionary_statements routing"
                )
            traces = [
                item for item in trace_items
                if item.get("decision") in {"written", "merged"}
                and fact_id in (item.get("source_fact_ids") or [])
            ]
            if not traces:
                errors.append(
                    f"Section 2 routing: source-present precautionary group fact {fact_id} "
                    "has no output trace"
                )
                continue
            key = _text(fact.get("group_key"))
            expected = {
                "zh": _text(fact.get("source_heading")),
                "en": _PRECAUTIONARY_GROUP_EN.get(key, ""),
            }
            for language, heading in expected.items():
                if not heading:
                    errors.append(
                        f"Section 2 routing: precautionary group fact {fact_id} has no "
                        f"controlled {language} heading"
                    )
                    continue
                heading_key = _canonical(heading)
                present = any(
                    any(_canonical(line) == heading_key
                        for line in _text(item.get("output_values", {}).get(language)).splitlines())
                    for item in traces
                    if isinstance(item.get("output_values"), dict)
                )
                if not present:
                    errors.append(
                        f"Section 2 routing: {language} output loses precautionary group "
                        f"{key or heading} from fact {fact_id}"
                    )
        elif decision == "mapped":
            errors.append(
                f"Section 2 routing: orphan precautionary group fact {fact_id} cannot be mapped"
            )
    return errors


def expected_precautionary_group_keys(facts: dict) -> list[str]:
    """Return source-present, reviewed group keys in source/ledger order."""
    mapping_items = (facts.get("source_mapping") or {}).get("items") or []
    mapped = {
        _text(item.get("fact_id")): item
        for item in mapping_items
        if isinstance(item, dict) and _text(item.get("fact_id"))
    }
    keys: list[str] = []
    for fact in facts.get("fact_ledger") or []:
        if not isinstance(fact, dict) or fact.get("source_kind") != "precautionary_group":
            continue
        if not fact.get("has_statements"):
            continue
        fact_id = _text(fact.get("fact_id"))
        if mapped.get(fact_id, {}).get("decision") != "mapped":
            continue
        key = _text(fact.get("group_key"))
        if key:
            keys.append(key)
    return keys


def audit(facts: dict) -> dict:
    """Return all Section 2 routing blockers without mutating ``facts``."""
    errors: list[str] = []
    mapping_by_fact, mapping_errors = _mapping_items(facts)
    errors.extend(mapping_errors)
    routing_by_fact, routing_errors = _routing_items(facts)
    errors.extend(routing_errors)
    ledger = {
        _text(item.get("fact_id")): item
        for item in (facts.get("fact_ledger") or [])
        if isinstance(item, dict) and _text(item.get("fact_id"))
    }

    s2_mapped = {
        fact_id: item for fact_id, item in mapping_by_fact.items()
        if item.get("target_section") == "s2"
    }
    for fact_id, mapping in s2_mapped.items():
        route = semantic_target(mapping.get("target_slot"))
        route_item = routing_by_fact.get(fact_id)
        if route_item is None:
            errors.append(f"Section 2 routing: mapped fact {fact_id} has no routing item")
            continue
        if route and route_item.get("_semantic_target") != route:
            errors.append(
                f"Section 2 routing: fact {fact_id} mapping target {route} disagrees with "
                f"routing target {route_item.get('_semantic_target')!r}"
            )
        source_section = mapping.get("source_section")
        if source_section != "s2" and not (
            mapping.get("cross_section_route") is True and route == "ghs_classes"
        ):
            errors.append(f"Section 2 routing: fact {fact_id} is not sourced from s2")
        fact = ledger.get(fact_id, {})
        if route in {
            "health_hazards.inhalation",
            "health_hazards.ingestion",
            "health_hazards.skin",
            "health_hazards.eyes",
            "health_hazards.symptoms_signs",
        } and _is_overall_classification_fact(mapping, fact):
            errors.append(
                f"Section 2 routing: overall classification fact {fact_id} cannot be used "
                f"as route target {route}"
            )
        if route == "emergency_overview":
            locator = _text(mapping.get("source_locator"))
            if not re.search(r"(?:s2[.:_ -]*1|emergency|overview|紧急情况概述|紧急概述)", locator, re.I):
                errors.append(
                    f"Section 2 routing: emergency_overview fact {fact_id} lacks an explicit "
                    f"emergency source locator: {locator!r}"
                )
            if fact.get("evidence_type") == "derived":
                errors.append(
                    f"Section 2 routing: emergency_overview fact {fact_id} cannot be derived"
                )

    trace_items, trace_errors = _trace_items(facts)
    errors.extend(trace_errors)
    errors.extend(_audit_precautionary_groups(
        facts, ledger, routing_by_fact, trace_items
    ))

    # H statements suppress only the same exposure route. A route not covered
    # by Section 2.5 must remain available from the source Section 2.7/2.8
    # health-hazard block; blanket suppression would lose source facts.
    for language in ("zh", "en"):
        h_values = []
        route_values: dict[str, list[str]] = {}
        for _, _, target, value in _iter_section2_rows(facts.get(language), language) or ():
            if target == "hazard_statements":
                h_values.append(value)
            elif target in _HEALTH_ROUTE_TARGETS and _text(value):
                route_values.setdefault(target, []).append(value)
        covered = health_routes_covered_by_h_statements(h_values)
        for target in sorted(covered.intersection(route_values)):
            errors.append(
                f"Section 2 routing: {language} {target} repeats a route already "
                "covered by Section 2.5 hazard statements"
            )
    traces_by_fact: dict[str, list[tuple[str, dict]]] = {}
    for index, item in enumerate(trace_items, start=1):
        decision = item.get("decision")
        if decision not in {"written", "merged"}:
            continue
        target = item.get("_semantic_target")
        fact_ids = item.get("source_fact_ids")
        if not isinstance(fact_ids, list) or not fact_ids:
            errors.append(f"Section 2 routing: written trace item {index} has no source_fact_ids")
            continue
        for fact_id in fact_ids:
            fact_id = _text(fact_id)
            mapping = mapping_by_fact.get(fact_id)
            if mapping is None:
                errors.append(f"Section 2 routing: trace item {index} references unknown/unmapped fact {fact_id}")
                continue
            route_item = routing_by_fact.get(fact_id)
            mapping_target = semantic_target(mapping.get("target_slot"))
            shared_target = bool(
                route_item
                and route_item.get("_usage") == "shared"
                and target in set(route_item.get("approved_targets") or [])
            )
            if mapping.get("target_section") != "s2" or (
                mapping_target != target and not shared_target
            ):
                errors.append(
                    f"Section 2 routing: trace item {index} places fact {fact_id} in {target}, "
                    "but reviewed mapping assigns another destination"
                )
            if mapping.get("source_section") != "s2" and not (
                mapping.get("cross_section_route") is True and target == "ghs_classes"
            ):
                errors.append(f"Section 2 routing: trace item {index} uses non-s2 fact {fact_id}")
            traces_by_fact.setdefault(fact_id, []).append((target, item))

    for fact_id, entries in traces_by_fact.items():
        targets = {target for target, _ in entries}
        route_item = routing_by_fact.get(fact_id)
        if len(targets) > 1:
            if not route_item or route_item.get("_usage") != "shared":
                errors.append(
                    f"Section 2 routing: fact {fact_id} is duplicated across targets "
                    f"{sorted(targets)} without a reviewed shared exception"
                )
            else:
                approved = set(route_item.get("approved_targets") or [])
                if targets != approved:
                    errors.append(
                        f"Section 2 routing: shared fact {fact_id} targets {sorted(targets)} "
                        f"do not equal approved_targets {sorted(approved)}"
                    )

    # Every non-empty semantic CN/EN value must have a matching trace item.  The
    # comparison is whitespace/line-break tolerant but remains target-specific.
    for language in ("zh", "en"):
        for _, row_index, target, value in _iter_section2_rows(facts.get(language), language) or ():
            matching = [
                item for item in trace_items
                if item.get("_semantic_target") == target
                and isinstance(item.get("output_values"), dict)
                and _text(item["output_values"].get(language))
            ]
            normalized = _canonical(value)
            if not matching or not any(
                normalized in _canonical(item["output_values"].get(language))
                or _canonical(item["output_values"].get(language)) in normalized
                for item in matching
            ):
                errors.append(
                    f"Section 2 routing: {language}.s2 row {row_index} value has no "
                    f"target-specific reviewed trace for {target}"
                )

    return {
        "status": "passed" if not errors else "failed",
        "version": ROUTER_VERSION,
        "errors": errors,
        "mapped_section2_fact_count": len(s2_mapped),
        "traced_section2_fact_count": len(traces_by_fact),
    }


def validate(facts: dict) -> list[str]:
    return audit(facts).get("errors", [])


__all__ = [
    "ROUTER_VERSION", "SECTION2_TARGETS", "audit", "expected_precautionary_group_keys",
    "semantic_target", "validate",
]
