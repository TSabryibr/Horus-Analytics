from __future__ import annotations

import hashlib
import re
from typing import Any

from ..capabilities import (
    _strip_pine_comments,
    collect_supported_nodes,
    detect_blocked_reasons,
    normalize_execution_mode,
)
from ..expression_nodes import (
    call,
    literal,
    series_ref,
    variable_ref,
)
from .lexer import (
    _ENTRY_PATTERNS,
    _EXIT_PATTERNS,
    _INDICATOR_ENTRY_CANDIDATES,
    _INDICATOR_EXIT_CANDIDATES,
    _RUNTIME_SUPPORT_MESSAGE,
    _detect_directionality,
    _detect_matches,
    _detect_script_type,
)
from .conditions import (
    _normalize_request_security_passthrough_wrappers,
)
from .statements import (
    _collect_capability_errors,
    _collect_reachable_definition_names,
    _extract_indicator_descriptor,
    _extract_unique_lengths,
    _parse_script_plan,
    _resolve_expression,
    _validate_variable_references,
)


def _extract_strategy_spec_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    definitions = dict(plan.get("definitions") or {})
    entry_expression = plan.get("entry_expression")
    exit_expression = plan.get("exit_expression")
    if not entry_expression or not exit_expression:
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)

    resolved_entry = _resolve_expression(entry_expression, definitions)
    resolved_exit = _resolve_expression(exit_expression, definitions)
    if resolved_entry.get("node_type") != "CALL" or resolved_exit.get("node_type") != "CALL":
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)
    if resolved_entry.get("name") != "ta.crossover" or resolved_exit.get("name") != "ta.crossunder":
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)

    entry_args = list(resolved_entry.get("args") or [])
    exit_args = list(resolved_exit.get("args") or [])
    if len(entry_args) != 2 or len(exit_args) != 2:
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)

    left_descriptor = _extract_indicator_descriptor(entry_args[0], definitions)
    right_descriptor = _extract_indicator_descriptor(entry_args[1], definitions)
    exit_left_descriptor = _extract_indicator_descriptor(exit_args[0], definitions)
    exit_right_descriptor = _extract_indicator_descriptor(exit_args[1], definitions)

    if left_descriptor != exit_left_descriptor or right_descriptor != exit_right_descriptor:
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)

    if left_descriptor is None or right_descriptor is None:
        raise ValueError(_RUNTIME_SUPPORT_MESSAGE)

    if left_descriptor.get("kind") == "PRICE" and right_descriptor.get("kind") in {"SMA", "EMA"}:
        return {
            "strategy_kind": f"PRICE_{right_descriptor['kind']}_CROSSOVER",
            "signal_family": right_descriptor["kind"],
            "signal_length": right_descriptor["length"],
        }

    if left_descriptor.get("kind") in {"SMA", "EMA"} and right_descriptor.get("kind") == left_descriptor.get("kind"):
        return {
            "strategy_kind": f"{left_descriptor['kind']}_CROSSOVER",
            "signal_family": left_descriptor["kind"],
            "fast_length": left_descriptor["length"],
            "slow_length": right_descriptor["length"],
        }

    raise ValueError(_RUNTIME_SUPPORT_MESSAGE)


def _build_validated_execution_plan(parsed_plan: dict[str, Any]) -> dict[str, Any]:
    definitions = dict(parsed_plan.get("definitions") or {})
    entry_expression = parsed_plan.get("entry_expression")
    exit_expression = parsed_plan.get("exit_expression")
    reachable_definition_names = _collect_reachable_definition_names(entry_expression, definitions)
    reachable_definition_names.update(_collect_reachable_definition_names(exit_expression, definitions))
    validation_errors = _validate_variable_references(entry_expression, definitions)
    validation_errors.extend(_validate_variable_references(exit_expression, definitions))
    if validation_errors:
        raise ValueError(validation_errors[0])
    capability_errors = _collect_capability_errors(entry_expression, definitions)
    capability_errors.extend(_collect_capability_errors(exit_expression, definitions))
    for definition_name in sorted(reachable_definition_names):
        capability_errors.extend(_collect_capability_errors(definitions[definition_name], definitions))
    if capability_errors:
        raise ValueError(capability_errors[0])
    if entry_expression is not None and exit_expression is not None:
        try:
            strategy_spec = _extract_strategy_spec_from_plan(parsed_plan)
        except ValueError:
            parsed_plan["strategy_kind"] = "EXPRESSION_PLAN"
            parsed_plan["signal_family"] = "EXPRESSION"
        else:
            parsed_plan["strategy_kind"] = strategy_spec["strategy_kind"]
            parsed_plan["signal_family"] = strategy_spec["signal_family"]
        return parsed_plan
    raise ValueError(_RUNTIME_SUPPORT_MESSAGE)


def _extract_indicator_signal_plan(source: str) -> tuple[dict[str, Any] | None, str | None, str | None]:
    try:
        parsed_plan = _parse_script_plan(source)
    except Exception:
        return None, None, None
    if parsed_plan is None:
        return None, None, None
    if parsed_plan.get("entry_expression") is not None or parsed_plan.get("exit_expression") is not None:
        return None, None, None

    definitions = dict(parsed_plan.get("definitions") or {})
    entry_candidates = [name for name in _INDICATOR_ENTRY_CANDIDATES if name in definitions]
    exit_candidates = [name for name in _INDICATOR_EXIT_CANDIDATES if name in definitions]
    if not entry_candidates or not exit_candidates:
        return None, None, None

    for entry_name in entry_candidates:
        for exit_name in exit_candidates:
            promoted_plan = {
                "execution_mode": "LONG_ONLY",
                "definitions": definitions,
                "entry_expression": variable_ref(entry_name),
                "exit_expression": variable_ref(exit_name),
            }
            try:
                return _build_validated_execution_plan(promoted_plan), entry_name, exit_name
            except ValueError:
                continue
    return None, None, None


def extract_supported_strategy_spec(script_source: str) -> dict[str, Any]:
    source = _normalize_request_security_passthrough_wrappers(str(script_source or ""))
    plan = _parse_script_plan(source)
    if plan is not None:
        try:
            return _extract_strategy_spec_from_plan(plan)
        except ValueError:
            pass

    has_crossover = bool(re.search(r"\bta\.crossover\s*\(", source, flags=re.IGNORECASE))
    has_crossunder = bool(re.search(r"\bta\.crossunder\s*\(", source, flags=re.IGNORECASE))
    sma_lengths = _extract_unique_lengths(source, "sma")
    ema_lengths = _extract_unique_lengths(source, "ema")

    def build_spec(lengths: list[int], ma_name: str) -> dict[str, Any] | None:
        normalized = ma_name.upper()
        if has_crossover and has_crossunder and len(lengths) >= 2:
            return {
                "strategy_kind": f"{normalized}_CROSSOVER",
                "signal_family": normalized,
                "fast_length": lengths[0],
                "slow_length": lengths[1],
            }
        if has_crossover and has_crossunder and len(lengths) == 1:
            return {
                "strategy_kind": f"PRICE_{normalized}_CROSSOVER",
                "signal_family": normalized,
                "signal_length": lengths[0],
            }
        return None

    if not ema_lengths:
        sma_spec = build_spec(sma_lengths, "sma")
        if sma_spec:
            return sma_spec

    if not sma_lengths:
        ema_spec = build_spec(ema_lengths, "ema")
        if ema_spec:
            return ema_spec

    raise ValueError(_RUNTIME_SUPPORT_MESSAGE)


def build_pine_execution_plan(script_source: str) -> dict[str, Any]:
    source = _normalize_request_security_passthrough_wrappers(str(script_source or ""))
    parsed_plan = _parse_script_plan(source)
    if parsed_plan is not None:
        entry_expression = parsed_plan.get("entry_expression")
        exit_expression = parsed_plan.get("exit_expression")
        if entry_expression is not None and exit_expression is not None:
            return _build_validated_execution_plan(parsed_plan)

    strategy_spec = extract_supported_strategy_spec(source)
    signal_family = str(strategy_spec.get("signal_family", "SMA")).upper()

    if strategy_spec["strategy_kind"] in {"SMA_CROSSOVER", "EMA_CROSSOVER"}:
        fast_name = "fast"
        slow_name = "slow"
        indicator_name = f"ta.{signal_family.lower()}"
        return {
            "execution_mode": "LONG_ONLY",
            "strategy_kind": strategy_spec["strategy_kind"],
            "signal_family": signal_family,
            "definitions": {
                fast_name: call(indicator_name, series_ref("close"), literal(strategy_spec["fast_length"])),
                slow_name: call(indicator_name, series_ref("close"), literal(strategy_spec["slow_length"])),
            },
            "entry_expression": call("ta.crossover", variable_ref(fast_name), variable_ref(slow_name)),
            "exit_expression": call("ta.crossunder", variable_ref(fast_name), variable_ref(slow_name)),
        }

    signal_name = "signal"
    indicator_name = f"ta.{signal_family.lower()}"
    return {
        "execution_mode": "LONG_ONLY",
        "strategy_kind": strategy_spec["strategy_kind"],
        "signal_family": signal_family,
        "definitions": {
            signal_name: call(indicator_name, series_ref("close"), literal(strategy_spec["signal_length"])),
        },
        "entry_expression": call("ta.crossover", series_ref("close"), variable_ref(signal_name)),
        "exit_expression": call("ta.crossunder", series_ref("close"), variable_ref(signal_name)),
    }


def preflight_pine_script(script_source: str, timeframe: str | None = None) -> dict[str, Any]:
    source = str(script_source or "").strip()
    runtime_source = _normalize_request_security_passthrough_wrappers(source)
    stripped_source = _strip_pine_comments(source)
    analysis_source = _normalize_request_security_passthrough_wrappers(stripped_source)
    script_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    script_type = _detect_script_type(analysis_source)
    directionality = _detect_directionality(analysis_source)
    detected_entries = _detect_matches(analysis_source, _ENTRY_PATTERNS)
    detected_exits = _detect_matches(analysis_source, _EXIT_PATTERNS)
    supported_nodes = collect_supported_nodes(stripped_source)
    blocked_reasons = detect_blocked_reasons(
        runtime_source,
        base_timeframe=timeframe,
        include_unsupported_functions=False,
    )
    unsupported_features: list[str] = []
    messages: list[str] = []
    plan: dict[str, Any] | None = None
    promoted_entry_name: str | None = None
    promoted_exit_name: str | None = None

    if script_type == "UNKNOWN":
        unsupported_features.append("Could not detect a Pine strategy() or indicator() declaration.")

    if script_type == "STRATEGY" and not detected_entries:
        unsupported_features.append("Strategy script is missing a supported entry construct.")

    if script_type == "STRATEGY" and not detected_exits:
        unsupported_features.append("Strategy script is missing a supported exit construct.")

    if script_type == "STRATEGY" and detected_entries and detected_exits:
        if blocked_reasons:
            unsupported_features.extend(reason for reason in blocked_reasons if reason not in unsupported_features)
        else:
            try:
                plan = build_pine_execution_plan(runtime_source)
            except ValueError as exc:
                blocked_reasons.append(str(exc))
                unsupported_features.append(str(exc))
    elif script_type == "INDICATOR" and not detected_entries and not detected_exits:
        if blocked_reasons:
            unsupported_features.extend(reason for reason in blocked_reasons if reason not in unsupported_features)
        else:
            try:
                plan, promoted_entry_name, promoted_exit_name = _extract_indicator_signal_plan(runtime_source)
            except ValueError as exc:
                blocked_reasons.append(str(exc))
                unsupported_features.append(str(exc))
            if plan is None:
                unsupported_features.append("Indicator script does not expose executable entry and exit behavior.")
            else:
                detected_entries = [f"indicator.signal.{promoted_entry_name}"]
                detected_exits = [f"indicator.signal.{promoted_exit_name}"]

    readiness = "READY" if not unsupported_features and detected_entries and detected_exits else "BLOCKED"
    compatibility_score = 92 if readiness == "READY" else 0

    if readiness == "READY":
        messages.append("Pine strategy matches the current Horus runtime support rules.")
    else:
        messages.append("Pine script is blocked until unsupported or ambiguous behavior is resolved.")

    return {
        "status": "success",
        "script_hash": script_hash,
        "script_type": script_type,
        "directionality": directionality,
        "execution_mode": normalize_execution_mode(directionality),
        "detected_entries": detected_entries,
        "detected_exits": detected_exits,
        "supported_nodes": supported_nodes,
        "blocked_reasons": blocked_reasons,
        "plan": plan,
        "unsupported_features": unsupported_features,
        "compatibility_score": compatibility_score,
        "readiness": readiness,
        "messages": messages,
    }
