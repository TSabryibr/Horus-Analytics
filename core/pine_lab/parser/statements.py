from __future__ import annotations

import re
from typing import Any

from ..capabilities import SUPPORTED_FUNCTIONS, _strip_pine_comments
from ..expression_nodes import (
    literal,
    state_var,
    tuple_item,
)
from .lexer import (
    _CYCLIC_REFERENCE_TEMPLATE,
    _RUNTIME_SUPPORT_MESSAGE,
    _UNRESOLVED_REFERENCE_TEMPLATE,
    _UNSUPPORTED_CALL_TEMPLATE,
    _normalize_line_continuations,
    _paren_balance_delta,
)
from .conditions import (
    _parse_expression_node,
    _parse_input_default_literal,
)


def _extract_unique_lengths(source: str, ma_name: str) -> list[int]:
    lengths = [
        int(length)
        for length in re.findall(
            rf"ta\.{ma_name}\s*\(\s*close\s*,\s*(\d+)\s*\)",
            source,
            flags=re.IGNORECASE,
        )
    ]
    unique_lengths: list[int] = []
    for length in lengths:
        if length not in unique_lengths:
            unique_lengths.append(length)
    return unique_lengths


def _collect_capability_errors(
    expression: dict[str, Any] | None,
    definitions: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> list[str]:
    if expression is None:
        return []

    node_type = expression.get("node_type")
    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name in definitions and name not in stack:
            return _collect_capability_errors(definitions[name], definitions, (*stack, name))
        return []

    if node_type == "CALL":
        call_name = str(expression.get("name") or "").lower()
        errors: list[str] = []
        if call_name not in SUPPORTED_FUNCTIONS:
            errors.append(_UNSUPPORTED_CALL_TEMPLATE.format(name=call_name))
        for arg in expression.get("args", []):
            errors.extend(_collect_capability_errors(arg, definitions, stack))
        return errors

    if node_type == "TUPLE_ITEM":
        return _collect_capability_errors(expression.get("source"), definitions, stack)

    if node_type == "HISTORY_REF":
        return _collect_capability_errors(expression.get("source"), definitions, stack) + _collect_capability_errors(
            expression.get("bars_ago"), definitions, stack
        )

    if node_type == "STATE_VAR":
        errors = _collect_capability_errors(expression.get("initial"), definitions, stack)
        for update in expression.get("updates", []):
            errors.extend(_collect_capability_errors(update.get("condition"), definitions, stack))
            errors.extend(_collect_capability_errors(update.get("value"), definitions, stack))
        return errors

    if node_type == "IF_EXPR":
        return (
            _collect_capability_errors(expression.get("condition"), definitions, stack)
            + _collect_capability_errors(expression.get("when_true"), definitions, stack)
            + _collect_capability_errors(expression.get("when_false"), definitions, stack)
        )

    if node_type == "BOOL_OP":
        errors = []
        for operand in expression.get("operands", []):
            errors.extend(_collect_capability_errors(operand, definitions, stack))
        return errors

    if node_type == "UNARY_OP":
        return _collect_capability_errors(expression.get("operand"), definitions, stack)

    if node_type == "COMPARE":
        return _collect_capability_errors(expression.get("left"), definitions, stack) + _collect_capability_errors(
            expression.get("right"), definitions, stack
        )

    if node_type == "BINARY_OP":
        return _collect_capability_errors(expression.get("left"), definitions, stack) + _collect_capability_errors(
            expression.get("right"), definitions, stack
        )

    return []


def _collect_reachable_definition_names(
    expression: dict[str, Any] | None,
    definitions: dict[str, dict[str, Any]],
    *,
    reachable: set[str] | None = None,
    stack: tuple[str, ...] = (),
) -> set[str]:
    reachable = reachable if reachable is not None else set()
    if expression is None:
        return reachable

    node_type = expression.get("node_type")
    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name in definitions and name not in stack:
            reachable.add(name)
            _collect_reachable_definition_names(definitions[name], definitions, reachable=reachable, stack=(*stack, name))
        return reachable

    if node_type == "CALL":
        for arg in expression.get("args", []):
            _collect_reachable_definition_names(arg, definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "TUPLE_ITEM":
        _collect_reachable_definition_names(expression.get("source"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "HISTORY_REF":
        _collect_reachable_definition_names(expression.get("source"), definitions, reachable=reachable, stack=stack)
        _collect_reachable_definition_names(expression.get("bars_ago"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "STATE_VAR":
        _collect_reachable_definition_names(expression.get("initial"), definitions, reachable=reachable, stack=stack)
        for update in expression.get("updates", []):
            _collect_reachable_definition_names(update.get("condition"), definitions, reachable=reachable, stack=stack)
            _collect_reachable_definition_names(update.get("value"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "IF_EXPR":
        _collect_reachable_definition_names(expression.get("condition"), definitions, reachable=reachable, stack=stack)
        _collect_reachable_definition_names(expression.get("when_true"), definitions, reachable=reachable, stack=stack)
        _collect_reachable_definition_names(expression.get("when_false"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "BOOL_OP":
        for operand in expression.get("operands", []):
            _collect_reachable_definition_names(operand, definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "UNARY_OP":
        _collect_reachable_definition_names(expression.get("operand"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "COMPARE":
        _collect_reachable_definition_names(expression.get("left"), definitions, reachable=reachable, stack=stack)
        _collect_reachable_definition_names(expression.get("right"), definitions, reachable=reachable, stack=stack)
        return reachable

    if node_type == "BINARY_OP":
        _collect_reachable_definition_names(expression.get("left"), definitions, reachable=reachable, stack=stack)
        _collect_reachable_definition_names(expression.get("right"), definitions, reachable=reachable, stack=stack)
        return reachable

    return reachable


def _validate_variable_references(
    expression: dict[str, Any] | None,
    definitions: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> list[str]:
    if expression is None:
        return []

    node_type = expression.get("node_type")
    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name not in definitions:
            return [_UNRESOLVED_REFERENCE_TEMPLATE.format(name=name)]
        if name in stack:
            return [_CYCLIC_REFERENCE_TEMPLATE.format(name=name)]
        return _validate_variable_references(definitions[name], definitions, (*stack, name))

    if node_type == "CALL":
        errors = []
        for arg in expression.get("args", []):
            errors.extend(_validate_variable_references(arg, definitions, stack))
        return errors

    if node_type == "HISTORY_REF":
        return _validate_variable_references(expression.get("source"), definitions, stack) + _validate_variable_references(
            expression.get("bars_ago"), definitions, stack
        )

    if node_type == "TUPLE_ITEM":
        return _validate_variable_references(expression.get("source"), definitions, stack)

    if node_type == "STATE_VAR":
        errors = _validate_variable_references(expression.get("initial"), definitions, stack)
        for update in expression.get("updates", []):
            errors.extend(_validate_variable_references(update.get("condition"), definitions, stack))
            errors.extend(_validate_variable_references(update.get("value"), definitions, stack))
        return errors

    if node_type == "IF_EXPR":
        return (
            _validate_variable_references(expression.get("condition"), definitions, stack)
            + _validate_variable_references(expression.get("when_true"), definitions, stack)
            + _validate_variable_references(expression.get("when_false"), definitions, stack)
        )

    if node_type == "BOOL_OP":
        errors = []
        for operand in expression.get("operands", []):
            errors.extend(_validate_variable_references(operand, definitions, stack))
        return errors

    if node_type == "UNARY_OP":
        return _validate_variable_references(expression.get("operand"), definitions, stack)

    if node_type == "COMPARE":
        return _validate_variable_references(expression.get("left"), definitions, stack) + _validate_variable_references(
            expression.get("right"), definitions, stack
        )

    if node_type == "BINARY_OP":
        return _validate_variable_references(expression.get("left"), definitions, stack) + _validate_variable_references(
            expression.get("right"), definitions, stack
        )

    return []


def _resolve_expression(
    expression: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    node_type = expression.get("node_type")
    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name in definitions and name not in stack:
            return _resolve_expression(definitions[name], definitions, (*stack, name))
        return expression
    return expression


def _extract_indicator_descriptor(
    expression: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    resolved = _resolve_expression(expression, definitions)
    node_type = resolved.get("node_type")
    if node_type == "SERIES_REF" and resolved.get("name") == "close":
        return {"kind": "PRICE"}
    if node_type != "CALL":
        return None
    call_name = str(resolved.get("name") or "")
    if call_name not in {"ta.sma", "ta.ema"}:
        return None
    args = list(resolved.get("args") or [])
    if len(args) != 2:
        return None
    source_arg, length_arg = args
    if source_arg.get("node_type") != "SERIES_REF" or source_arg.get("name") != "close":
        return None
    if length_arg.get("node_type") != "LITERAL":
        return None
    try:
        length = int(length_arg.get("value"))
    except (TypeError, ValueError):
        return None
    return {
        "kind": call_name.split(".")[-1].upper(),
        "length": length,
    }


def _parse_script_plan(source: str) -> dict[str, Any] | None:
    source = _normalize_line_continuations(_strip_pine_comments(source))
    definitions: dict[str, dict[str, Any]] = {}
    state_updates: dict[str, list[dict[str, Any]]] = {}
    entry_expression: dict[str, Any] | None = None
    exit_expression: dict[str, Any] | None = None
    pending_if: str | None = None
    declaration_depth = 0
    statement_buffer: list[str] = []
    statement_depth = 0

    for raw_line in list(str(source or "").splitlines()) + [""]:
        stripped = raw_line.strip()
        if statement_buffer:
            statement_buffer.append(raw_line)
            statement_depth += _paren_balance_delta(raw_line)
            if statement_depth > 0:
                continue
            stripped = " ".join(part.strip() for part in statement_buffer).strip()
            raw_line = statement_buffer[0]
            statement_buffer = []
            statement_depth = 0

        if not stripped or stripped.startswith("//"):
            continue
        lowered = stripped.lower()
        if declaration_depth > 0:
            declaration_depth += _paren_balance_delta(stripped)
            if declaration_depth < 0:
                declaration_depth = 0
            continue
        if lowered.startswith("strategy(") or lowered.startswith("indicator("):
            declaration_depth = max(0, _paren_balance_delta(stripped))
            continue

        if _paren_balance_delta(stripped) > 0:
            statement_buffer = [raw_line]
            statement_depth = _paren_balance_delta(raw_line)
            continue

        inline_entry_match = re.match(r"^if\s+(.+?)\s+strategy\.entry\s*\(", stripped, flags=re.IGNORECASE)
        if inline_entry_match:
            entry_expression = _parse_expression_node(inline_entry_match.group(1).strip())
            pending_if = None
            continue

        inline_exit_match = re.match(r"^if\s+(.+?)\s+strategy\.(?:close|close_all)\s*\(", stripped, flags=re.IGNORECASE)
        if inline_exit_match:
            exit_expression = _parse_expression_node(inline_exit_match.group(1).strip())
            pending_if = None
            continue

        if_match = re.match(r"^if\s+(.+)$", stripped, flags=re.IGNORECASE)
        if if_match:
            pending_if = if_match.group(1).strip()
            continue

        if pending_if:
            if re.search(r"\bstrategy\.entry\s*\(", stripped, flags=re.IGNORECASE):
                entry_expression = _parse_expression_node(pending_if)
                pending_if = None
                continue
            if re.search(r"\bstrategy\.(?:close|close_all)\s*\(", stripped, flags=re.IGNORECASE):
                exit_expression = _parse_expression_node(pending_if)
                pending_if = None
                continue
            state_assign_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:=\s*(.+)$", stripped)
            if state_assign_match and raw_line.startswith((" ", "\t")):
                name, expression = state_assign_match.groups()
                try:
                    state_updates.setdefault(name, []).append(
                        {
                            "condition": _parse_expression_node(pending_if),
                            "value": _parse_expression_node(expression.strip()),
                        }
                    )
                except Exception:
                    pass
                pending_if = None
                continue
            if not raw_line.startswith((" ", "\t")):
                pending_if = None

        tuple_assign_match = re.match(
            r"^\[\s*([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)+)\s*\]\s*=\s*(.+)$",
            stripped,
        )
        if tuple_assign_match:
            raw_names, expression = tuple_assign_match.groups()
            names = [name.strip() for name in raw_names.split(",")]
            try:
                source_node = _parse_expression_node(expression.strip())
            except Exception:
                continue
            for index, name in enumerate(names):
                definitions[name] = tuple_item(source_node, index=index, label=name)
            continue

        assign_match = re.match(
            r"^(?:var\s+)?(?:(?:int|float|bool|string)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$",
            stripped,
        )
        if assign_match:
            name, expression = assign_match.groups()
            try:
                parsed_input_default = _parse_input_default_literal(expression.strip())
                definitions[name] = parsed_input_default if parsed_input_default is not None else _parse_expression_node(expression.strip())
            except Exception:
                continue

    for name, updates in state_updates.items():
        initial = definitions.get(name, literal(None))
        definitions[name] = state_var(initial, updates)

    if entry_expression is None and exit_expression is None and not definitions:
        return None

    return {
        "execution_mode": "LONG_ONLY",
        "definitions": definitions,
        "entry_expression": entry_expression,
        "exit_expression": exit_expression,
    }
