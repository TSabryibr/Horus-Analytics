from __future__ import annotations

import ast
import re
from typing import Any

from ..expression_nodes import (
    binary_op,
    bool_op,
    call,
    compare,
    history_ref,
    if_expr,
    literal,
    series_ref,
    unary_op,
    variable_ref,
)
from .lexer import (
    _extract_function_call_spans,
    _split_call_args,
    _strip_wrapping_parentheses,
)


def _extract_passthrough_request_security_helpers(source: str) -> tuple[str, dict[str, tuple[str, str, str]]]:
    retained_lines: list[str] = []
    helpers: dict[str, tuple[str, str, str]] = {}

    for raw_line in str(source or "").splitlines():
        stripped = raw_line.strip()
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=>\s*(.+)$", stripped)
        if not match:
            retained_lines.append(raw_line)
            continue

        helper_name, raw_params, body = match.groups()
        params = [param.strip() for param in raw_params.split(",") if param.strip()]
        if len(params) != 3:
            retained_lines.append(raw_line)
            continue

        body_stripped = body.strip()
        call_spans = _extract_function_call_spans(body_stripped, "request.security")
        if len(call_spans) != 1:
            retained_lines.append(raw_line)
            continue

        _, _, call_source = call_spans[0]
        if call_source.strip() != body_stripped:
            retained_lines.append(raw_line)
            continue

        args = _split_call_args(call_source)
        normalized_args = [str(arg or "").strip() for arg in args]
        if len(normalized_args) != 3 or [arg.lower() for arg in normalized_args] != [param.lower() for param in params]:
            retained_lines.append(raw_line)
            continue

        helpers[helper_name.lower()] = (params[0], params[1], params[2])

    return "\n".join(retained_lines), helpers


def _substitute_identifier_references(expression: str, replacements: dict[str, str]) -> str:
    substituted = str(expression or "")
    for name, replacement in replacements.items():
        substituted = re.sub(rf"\b{re.escape(name)}\b", f"({replacement})", substituted)
    return substituted


def _normalize_known_supertrend_helpers(source: str) -> str:
    lines = str(source or "").splitlines()
    retained_lines: list[str] = []
    index = 0
    helper_names: set[str] = set()

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*src\s*,\s*factor\s*,\s*atrLen\s*\)\s*=>\s*$", stripped)
        if not match:
            retained_lines.append(raw_line)
            index += 1
            continue

        helper_name = match.group(1)
        body_lines: list[str] = []
        body_index = index + 1
        while body_index < len(lines):
            candidate = lines[body_index]
            if candidate.startswith((" ", "\t")):
                if candidate.strip():
                    body_lines.append(candidate.strip())
                body_index += 1
                continue
            break

        body_text = "\n".join(body_lines)
        if all(
            marker in body_text
            for marker in (
                "atr = ta.atr(atrLen)",
                "upperBand = src + factor * atr",
                "lowerBand = src - factor * atr",
                "[superTrend, direction]",
            )
        ):
            helper_names.add(helper_name.lower())
            index = body_index
            continue

        retained_lines.append(raw_line)
        retained_lines.extend(lines[index + 1:body_index])
        index = body_index

    normalized_source = "\n".join(retained_lines)
    for helper_name in helper_names:
        spans = _extract_function_call_spans(normalized_source, helper_name)
        replacements: list[tuple[int, int, str]] = []
        for start, end, call_source in spans:
            args = _split_call_args(call_source)
            if len(args) != 3:
                continue
            replacements.append((start, end, f"horus.supertrend({args[0]}, {args[1]}, {args[2]})"))
        for start, end, replacement in reversed(replacements):
            normalized_source = normalized_source[:start] + replacement + normalized_source[end:]

    return normalized_source


def _extract_multiline_expression_helpers(source: str) -> tuple[str, dict[str, tuple[list[str], list[tuple[str, str]], str]]]:
    lines = str(source or "").splitlines()
    retained_lines: list[str] = []
    helpers: dict[str, tuple[list[str], list[tuple[str, str]], str]] = {}
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=>\s*$", stripped)
        if not match:
            retained_lines.append(raw_line)
            index += 1
            continue

        helper_name, raw_params = match.groups()
        params = [param.strip() for param in raw_params.split(",") if param.strip()]
        body_lines: list[str] = []
        body_index = index + 1
        while body_index < len(lines):
            candidate = lines[body_index]
            if candidate.startswith((" ", "\t")):
                candidate_stripped = candidate.strip()
                if candidate_stripped:
                    body_lines.append(candidate_stripped)
                body_index += 1
                continue
            break

        if not body_lines:
            retained_lines.append(raw_line)
            index += 1
            continue

        assignments: list[tuple[str, str]] = []
        final_expression = body_lines[-1]
        is_supported = True
        for statement in body_lines[:-1]:
            assign_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", statement)
            if not assign_match:
                is_supported = False
                break
            local_name, local_expression = assign_match.groups()
            assignments.append((local_name, local_expression.strip()))

        if is_supported:
            helper_body_text = " ".join(body_lines).lower()
            if any(token in helper_body_text for token in (" lookahead_on", " barstate.isrealtime", "request.security_lower_tf")):
                is_supported = False

        if is_supported:
            helpers[helper_name.lower()] = (params, assignments, final_expression.strip())
            index = body_index
            continue

        retained_lines.append(raw_line)
        retained_lines.extend(lines[index + 1:body_index])
        index = body_index

    return "\n".join(retained_lines), helpers


def _expand_multiline_expression_helpers(source: str) -> str:
    normalized_source, helpers = _extract_multiline_expression_helpers(source)
    if not helpers:
        return source

    changed = True
    while changed:
        changed = False
        for helper_name, (params, assignments, final_expression) in helpers.items():
            spans = _extract_function_call_spans(normalized_source, helper_name)
            if not spans:
                continue

            replacements: list[tuple[int, int, str]] = []
            for start, end, call_source in spans:
                call_args = _split_call_args(call_source)
                if len(call_args) != len(params):
                    continue

                scope = {param: arg.strip() for param, arg in zip(params, call_args)}
                for local_name, local_expression in assignments:
                    expanded_local_expression = _substitute_identifier_references(local_expression, scope)
                    scope[local_name] = expanded_local_expression

                expanded = _substitute_identifier_references(final_expression, scope)
                replacements.append((start, end, f"({expanded})"))

            if not replacements:
                continue

            changed = True
            for start, end, replacement in reversed(replacements):
                normalized_source = normalized_source[:start] + replacement + normalized_source[end:]

    return normalized_source


def _normalize_request_security_passthrough_wrappers(source: str) -> str:
    expanded_source = _normalize_known_supertrend_helpers(source)
    expanded_source = _expand_multiline_expression_helpers(expanded_source)
    normalized_source, helpers = _extract_passthrough_request_security_helpers(expanded_source)
    if not helpers:
        return expanded_source

    for helper_name in helpers:
        spans = _extract_function_call_spans(normalized_source, helper_name)
        if not spans:
            continue
        replacements: list[tuple[int, int, str]] = []
        for start, end, call_source in spans:
            args = _split_call_args(call_source)
            if len(args) != 3:
                continue
            replacements.append((start, end, f"request.security({args[0]}, {args[1]}, {args[2]})"))

        for start, end, replacement in reversed(replacements):
            normalized_source = normalized_source[:start] + replacement + normalized_source[end:]

    return normalized_source


def _call_name_from_ast(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name_from_ast(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _split_top_level_ternary(expression: str) -> tuple[str, str, str] | None:
    source = str(expression or "")
    in_string: str | None = None
    escape = False
    paren_depth = 0
    ternary_depth = 0
    question_index = -1

    for index, char in enumerate(source):
        if in_string is not None:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_string:
                in_string = None
            continue

        if char in {'"', "'"}:
            in_string = char
            continue

        if char in "([{":
            paren_depth += 1
            continue
        if char in ")]}":
            paren_depth = max(0, paren_depth - 1)
            continue

        if paren_depth != 0:
            continue

        if char == "?" and question_index < 0:
            question_index = index
            continue

        if question_index >= 0:
            if char == "?":
                ternary_depth += 1
                continue
            if char == ":":
                if ternary_depth == 0:
                    condition = source[:question_index].strip()
                    when_true = source[question_index + 1:index].strip()
                    when_false = source[index + 1:].strip()
                    if condition and when_true and when_false:
                        return condition, when_true, when_false
                    return None
                ternary_depth -= 1

    return None


def _normalize_embedded_ternaries(expression: str) -> str:
    source = str(expression or "")
    stack: list[int] = []
    replacements: list[tuple[int, int, str]] = []
    in_string: str | None = None
    escape = False

    for index, char in enumerate(source):
        if in_string is not None:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_string:
                in_string = None
            continue

        if char in {'"', "'"}:
            in_string = char
            continue
        if char == "(":
            stack.append(index)
            continue
        if char == ")" and stack:
            start = stack.pop()
            inner = source[start + 1:index]
            if "?" in inner and ":" in inner:
                replacements.append((start, index + 1, f"({_normalize_pine_expression(inner)})"))

    normalized = source
    for start, end, replacement in reversed(replacements):
        normalized = normalized[:start] + replacement + normalized[end:]
    return normalized


def _normalize_pine_expression(expression: str) -> str:
    normalized = _strip_wrapping_parentheses(expression)
    normalized = _normalize_embedded_ternaries(normalized)
    ternary_parts = _split_top_level_ternary(normalized)
    if ternary_parts is not None:
        condition, when_true, when_false = ternary_parts
        normalized = (
            f"({_normalize_pine_expression(when_true)} if {_normalize_pine_expression(condition)} "
            f"else {_normalize_pine_expression(when_false)})"
        )
    return normalized


def _parse_expression_node(expression: str) -> dict[str, Any]:
    parsed = ast.parse(_normalize_pine_expression(expression), mode="eval")

    def convert(node: ast.AST) -> dict[str, Any]:
        if isinstance(node, ast.Attribute):
            return literal(_call_name_from_ast(node))

        if isinstance(node, ast.Name):
            if node.id == "true":
                return literal(True)
            if node.id == "false":
                return literal(False)
            if node.id == "na":
                return literal(None)
            if node.id in {"open", "high", "low", "close", "volume"}:
                return series_ref(node.id)
            return variable_ref(node.id)

        if isinstance(node, ast.Subscript):
            slice_node = node.slice
            if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, int):
                return history_ref(convert(node.value), literal(int(slice_node.value)))
            return history_ref(convert(node.value), convert(slice_node))

        if isinstance(node, ast.Constant):
            return literal(node.value)

        if isinstance(node, ast.IfExp):
            return if_expr(convert(node.test), convert(node.body), convert(node.orelse))

        if isinstance(node, ast.Call):
            return call(_call_name_from_ast(node.func), *(convert(arg) for arg in node.args))

        if isinstance(node, ast.BoolOp):
            operator = "and" if isinstance(node.op, ast.And) else "or"
            return bool_op(operator, *(convert(value) for value in node.values))

        if isinstance(node, ast.BinOp):
            operator = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/",
            }.get(type(node.op))
            if operator is None:
                raise ValueError(f"Unsupported binary operator in expression: {expression}")
            return binary_op(operator, convert(node.left), convert(node.right))

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return unary_op("not", convert(node.operand))
            if isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
                return literal(-node.operand.value)
            if isinstance(node.op, ast.UAdd) and isinstance(node.operand, ast.Constant):
                return literal(+node.operand.value)

        if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
            op = node.ops[0]
            operator = {
                ast.Gt: ">",
                ast.GtE: ">=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Eq: "==",
                ast.NotEq: "!=",
            }.get(type(op))
            if operator is None:
                raise ValueError(f"Unsupported comparison operator in expression: {expression}")
            return compare(operator, convert(node.left), convert(node.comparators[0]))

        raise ValueError(f"Unsupported Pine expression node: {expression}")

    return convert(parsed.body)


def _parse_input_default_literal(expression: str) -> dict[str, Any] | None:
    stripped = str(expression or "").strip()
    if not re.match(r"^input(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(", stripped, flags=re.IGNORECASE):
        return None

    args = _split_call_args(stripped)
    default_arg: str | None = None
    for arg in args:
        if "=" not in arg:
            if default_arg is None:
                default_arg = arg.strip()
            continue

        name, value = arg.split("=", 1)
        if name.strip().lower() == "defval":
            default_arg = value.strip()
            break

    if default_arg is None:
        return None

    try:
        return _parse_expression_node(default_arg)
    except Exception:
        return None
