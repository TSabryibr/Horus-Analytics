from __future__ import annotations

from typing import Any


def series_ref(name: str) -> dict[str, Any]:
    return {
        "node_type": "SERIES_REF",
        "name": name,
    }


def variable_ref(name: str) -> dict[str, Any]:
    return {
        "node_type": "VARIABLE_REF",
        "name": name,
    }


def history_ref(source: dict[str, Any], bars_ago: int) -> dict[str, Any]:
    return {
        "node_type": "HISTORY_REF",
        "source": source,
        "bars_ago": bars_ago,
    }


def if_expr(condition: dict[str, Any], when_true: dict[str, Any], when_false: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "IF_EXPR",
        "condition": condition,
        "when_true": when_true,
        "when_false": when_false,
    }


def literal(value: str | int | float | bool) -> dict[str, Any]:
    return {
        "node_type": "LITERAL",
        "value": value,
    }


def call(name: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "CALL",
        "name": name,
        "args": list(args),
    }


def bool_op(operator: str, *operands: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "BOOL_OP",
        "operator": operator,
        "operands": list(operands),
    }


def unary_op(operator: str, operand: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "UNARY_OP",
        "operator": operator,
        "operand": operand,
    }


def compare(operator: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "COMPARE",
        "operator": operator,
        "left": left,
        "right": right,
    }


def binary_op(operator: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "BINARY_OP",
        "operator": operator,
        "left": left,
        "right": right,
    }


def tuple_item(source: dict[str, Any], index: int, label: str | None = None) -> dict[str, Any]:
    return {
        "node_type": "TUPLE_ITEM",
        "source": source,
        "index": index,
        "label": label,
    }


def state_var(initial: dict[str, Any], updates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "node_type": "STATE_VAR",
        "initial": initial,
        "updates": updates,
    }
