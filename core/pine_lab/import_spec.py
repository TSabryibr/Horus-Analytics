from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from .expression_nodes import variable_ref
from .parser import _parse_expression_node

_TOKEN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
_DEPENDENCY_KEYWORDS = {
    "and",
    "or",
    "not",
    "if",
    "else",
    "true",
    "false",
    "na",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "ta",
    "request",
    "input",
}


def build_missing_signal() -> dict[str, Any]:
    return {
        "status": "missing",
        "source_name": None,
        "expression": None,
        "line": None,
        "depends_on": [],
        "confidence": 0.0,
    }


def _split_call_args(call_source: str) -> list[str]:
    start = call_source.find("(")
    end = call_source.rfind(")")
    if start < 0:
        return []
    if end <= start:
        end = len(call_source)

    raw = call_source[start + 1:end]
    args: list[str] = []
    current: list[str] = []
    depth = 0
    in_string: str | None = None
    escape = False

    for char in raw:
        if in_string is not None:
            current.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_string:
                in_string = None
            continue

        if char in {'"', "'"}:
            in_string = char
            current.append(char)
            continue

        if char in "([{":
            depth += 1
            current.append(char)
            continue

        if char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
            continue

        if char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue

        current.append(char)

    trailing = "".join(current).strip()
    if trailing:
        args.append(trailing)

    return args


def _parse_literal_token(token: str) -> str | int | float | bool | None:
    value = str(token or "").strip()
    if not value:
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "na":
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    try:
        if any(char in value for char in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return None


def _format_literal(value: str | int | float | bool | None) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "na"
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _extract_input_default(expression: str) -> str | int | float | bool | None:
    match = re.match(r"^input(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(", str(expression or "").strip(), flags=re.IGNORECASE)
    if not match:
        return None
    args = _split_call_args(str(expression or "").strip())
    if not args:
        fallback = re.search(r"^input(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(\s*([^,\)]+)", str(expression or "").strip(), flags=re.IGNORECASE)
        if fallback:
            return _parse_literal_token(fallback.group(1))
        return None
    return _parse_literal_token(args[0])


def _build_literal_defaults(definition_map: dict[str, dict[str, Any]]) -> dict[str, str | int | float | bool | None]:
    defaults: dict[str, str | int | float | bool | None] = {}
    for name, definition in definition_map.items():
        literal_value = _extract_input_default(str(definition.get("expression") or "").strip())
        if literal_value is not None:
            defaults[name] = literal_value
            continue
        direct_literal = _parse_literal_token(str(definition.get("expression") or "").strip())
        if direct_literal is not None:
            defaults[name] = direct_literal
    return defaults


def _replace_literal_history_offsets(expression: str, literal_defaults: dict[str, str | int | float | bool | None]) -> str:
    normalized = str(expression or "").strip()
    for name, value in literal_defaults.items():
        if not isinstance(value, int):
            continue
        normalized = re.sub(rf"\[\s*{re.escape(name)}\s*\]", f"[{value}]", normalized)
    return normalized


def _normalize_definition_expression(
    name: str,
    definition_map: dict[str, dict[str, Any]],
    literal_defaults: dict[str, str | int | float | bool | None],
    cache: dict[str, str],
) -> str:
    if name in cache:
        return cache[name]
    definition = definition_map.get(name)
    if not definition:
        raise ValueError(f'Missing definition for imported signal dependency "{name}".')

    expression = _replace_literal_history_offsets(str(definition.get("expression") or "").strip(), literal_defaults)
    input_default = _extract_input_default(expression)
    if input_default is not None:
        cache[name] = _format_literal(input_default)
        return cache[name]

    if name in literal_defaults:
        cache[name] = _format_literal(literal_defaults[name])
        return cache[name]

    if expression.startswith("variant("):
        args = _split_call_args(expression)
        if len(args) == 5:
            variant_type = args[0].strip()
            if variant_type in literal_defaults:
                variant_type = _format_literal(literal_defaults[variant_type])
            variant_kind = _parse_literal_token(variant_type)
            source_arg = _replace_literal_history_offsets(args[1], literal_defaults)
            length_arg = args[2].strip()
            off_sig_arg = args[3].strip()
            off_alma_arg = args[4].strip()
            if isinstance(variant_kind, str) and variant_kind.upper() == "ALMA":
                expression = f"ta.alma({source_arg}, {length_arg}, {off_alma_arg}, {off_sig_arg})"
            elif isinstance(variant_kind, str) and variant_kind.upper() == "EMA":
                expression = f"ta.ema({source_arg}, {length_arg})"

    if expression.startswith("reso("):
        args = _split_call_args(expression)
        if args:
            expression = _replace_literal_history_offsets(args[0], literal_defaults)

    cache[name] = expression
    return expression


def _build_normalized_definition_map(definitions_payload: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    definition_map = {
        str(item.get("name") or "").strip(): item
        for item in definitions_payload
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    literal_defaults = _build_literal_defaults(definition_map)
    normalized_cache: dict[str, str] = {}
    normalized_map: dict[str, dict[str, Any]] = {}
    known_names = set(definition_map)

    def extract_dependencies(expression: str) -> list[str]:
        dependencies: list[str] = []
        for match in _TOKEN_RE.finditer(str(expression or "")):
            token = match.group(1)
            if token in _DEPENDENCY_KEYWORDS or token not in known_names:
                continue
            start, _ = match.span(1)
            if start > 0 and expression[start - 1] == ".":
                continue
            if token not in dependencies:
                dependencies.append(token)
        return dependencies

    for name, definition in definition_map.items():
        normalized_expression = _normalize_definition_expression(name, definition_map, literal_defaults, normalized_cache)
        normalized_map[name] = {
            **definition,
            "expression": normalized_expression,
            "depends_on": extract_dependencies(normalized_expression),
        }

    return normalized_map


def _should_prefer_trigger_fallback(
    *,
    definition_map: dict[str, dict[str, Any]],
    long_entry_name: str,
    long_exit_name: str,
) -> bool:
    if "leTrigger" not in definition_map or "seTrigger" not in definition_map:
        return False
    entry_definition = definition_map.get(long_entry_name) or {}
    exit_definition = definition_map.get(long_exit_name) or {}
    entry_depends = {str(item or "").strip() for item in list(entry_definition.get("depends_on") or [])}
    exit_depends = {str(item or "").strip() for item in list(exit_definition.get("depends_on") or [])}
    entry_expression = str(entry_definition.get("expression") or "").strip()
    exit_expression = str(exit_definition.get("expression") or "").strip()

    condition_like = "condition" in entry_depends or "condition" in exit_depends
    condition_like = condition_like or "condition[" in entry_expression or "condition[" in exit_expression
    return condition_like


def _parse_execution_pair(
    *,
    definition_map: dict[str, dict[str, Any]],
    entry_name: str,
    exit_name: str,
) -> dict[str, Any]:
    parsed_definitions: dict[str, dict[str, Any]] = {}

    def visit(name: str) -> None:
        if name in parsed_definitions:
            return
        definition = definition_map.get(name)
        if not definition:
            raise ValueError(f'Missing definition for imported signal dependency "{name}".')
        parsed_definitions[name] = _parse_expression_node(str(definition.get("expression") or "").strip())
        for dependency_name in list(definition.get("depends_on") or []):
            dependency = str(dependency_name or "").strip()
            if dependency and dependency in definition_map:
                visit(dependency)

    visit(entry_name)
    visit(exit_name)

    return {
        "execution_mode": "LONG_ONLY",
        "strategy_kind": "IMPORTED_EXPRESSION_PLAN",
        "signal_family": "IMPORTED",
        "definitions": parsed_definitions,
        "entry_expression": variable_ref(entry_name),
        "exit_expression": variable_ref(exit_name),
    }


def build_execution_plan(
    *,
    definitions_payload: list[dict[str, Any]],
    signal_map: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    definition_map = _build_normalized_definition_map(definitions_payload)
    long_entry_name = str(signal_map.get("long_entry", {}).get("source_name") or "").strip()
    long_exit_name = str(signal_map.get("long_exit", {}).get("source_name") or "").strip()
    if not long_entry_name or not long_exit_name:
        return None
    if long_entry_name not in definition_map or long_exit_name not in definition_map:
        return None

    if _should_prefer_trigger_fallback(
        definition_map=definition_map,
        long_entry_name=long_entry_name,
        long_exit_name=long_exit_name,
    ):
        plan = _parse_execution_pair(
            definition_map=definition_map,
            entry_name="leTrigger",
            exit_name="seTrigger",
        )
        plan["import_fallback"] = {
            "entry_source_name": "leTrigger",
            "exit_source_name": "seTrigger",
            "original_long_entry": long_entry_name,
            "original_long_exit": long_exit_name,
            "reason": "Mapped signals depend on Pine state-machine condition tracking.",
        }
        return plan

    try:
        return _parse_execution_pair(
            definition_map=definition_map,
            entry_name=long_entry_name,
            exit_name=long_exit_name,
        )
    except ValueError as primary_error:
        fallback_entry_name = "leTrigger" if "leTrigger" in definition_map else ""
        fallback_exit_name = ""
        if "seTrigger" in definition_map:
            fallback_exit_name = "seTrigger"
        elif str(signal_map.get("short_entry", {}).get("source_name") or "").strip() in definition_map:
            fallback_exit_name = str(signal_map.get("short_entry", {}).get("source_name") or "").strip()

        if fallback_entry_name and fallback_exit_name:
            plan = _parse_execution_pair(
                definition_map=definition_map,
                entry_name=fallback_entry_name,
                exit_name=fallback_exit_name,
            )
            plan["import_fallback"] = {
                "entry_source_name": fallback_entry_name,
                "exit_source_name": fallback_exit_name,
                "original_long_entry": long_entry_name,
                "original_long_exit": long_exit_name,
                "reason": str(primary_error),
            }
            return plan
        raise


def build_rule_spec(
    *,
    script_source: str,
    script_type: str,
    parameters: list[dict[str, Any]],
    indicators: list[dict[str, Any]],
    definitions_payload: list[dict[str, Any]],
    signal_map: dict[str, dict[str, Any]],
    ignored_sections: list[dict[str, Any]],
    warnings: list[str],
    translation_mode: str,
) -> dict[str, Any]:
    signals = {
        "long_entry": signal_map.get("long_entry") or build_missing_signal(),
        "short_entry": signal_map.get("short_entry") or build_missing_signal(),
        "long_exit": signal_map.get("long_exit") or build_missing_signal(),
        "short_exit": signal_map.get("short_exit") or build_missing_signal(),
    }

    human_summary: dict[str, str] = {}
    traceability: list[dict[str, Any]] = []
    confidence_by_signal: dict[str, float] = {}

    for role, payload in signals.items():
        confidence_by_signal[role] = float(payload.get("confidence") or 0.0)
        source_name = payload.get("source_name")
        expression = payload.get("expression")
        line = payload.get("line")
        status = str(payload.get("status") or "missing")

        if source_name and expression:
            human_summary[role] = f"Derived from Pine variable `{source_name}`: {expression}"
            traceability.append(
                {
                    "role": role,
                    "source_name": source_name,
                    "expression": expression,
                    "line": line,
                }
            )
        else:
            human_summary[role] = f"No {role.replace('_', ' ')} signal was mapped in this draft."

        payload["status"] = status

    overall_confidence = 0.0
    mapped_confidences = [value for value in confidence_by_signal.values() if value > 0]
    if mapped_confidences:
        overall_confidence = round(sum(mapped_confidences) / len(mapped_confidences), 4)

    execution_plan: dict[str, Any] | None
    try:
        execution_plan = build_execution_plan(definitions_payload=definitions_payload, signal_map=signals)
    except ValueError as exc:
        execution_plan = None
        if str(exc) not in warnings:
            warnings.append(str(exc))
    else:
        fallback_meta = execution_plan.get("import_fallback") if isinstance(execution_plan, dict) else None
        if isinstance(fallback_meta, dict):
            fallback_warning = (
                "Import execution fallback: using "
                f"{fallback_meta.get('entry_source_name')} / {fallback_meta.get('exit_source_name')} "
                f"instead of {fallback_meta.get('original_long_entry')} / {fallback_meta.get('original_long_exit')} "
                "because the mapped state-machine signals are not directly executable in Horus yet."
            )
            if fallback_warning not in warnings:
                warnings.append(fallback_warning)

    return {
        "source": {
            "script_hash": hashlib.sha256(str(script_source or "").encode("utf-8")).hexdigest(),
            "script_type": script_type,
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "import_mode": "LOGIC_IMPORT",
            "translation_mode": translation_mode,
        },
        "parameters": parameters,
        "indicators": indicators,
        "signals": signals,
        "human_summary": human_summary,
        "traceability": traceability,
        "ignored_sections": ignored_sections,
        "warnings": warnings,
        "execution_plan": execution_plan,
        "confidence": {
            "overall": overall_confidence,
            "per_signal": confidence_by_signal,
        },
    }
