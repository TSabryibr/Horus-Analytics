from __future__ import annotations

import re


SUPPORTED_FUNCTIONS = {
    "horus.supertrend",
    "math.abs",
    "math.floor",
    "request.security",
    "ta.atr",
    "ta.highest",
    "ta.lowest",
    "ta.sma",
    "ta.ema",
    "ta.rsi",
    "ta.stdev",
    "ta.macd",
    "ta.linreg",
    "ta.wma",
    "ta.vwma",
    "ta.alma",
    "ta.crossover",
    "ta.crossunder",
}

BLOCKED_SHORT_MESSAGE = "Blocked: strategy.short is not supported in this phase."
BLOCKED_STRATEGY_EXIT_MESSAGE = "Blocked: strategy.exit stop/limit execution is not available in this phase."
BLOCKED_REQUEST_SECURITY_SAME_SYMBOL_MESSAGE = "Blocked: request.security only supports same-symbol imports in this phase."
BLOCKED_REQUEST_SECURITY_HIGHER_TIMEFRAME_MESSAGE = "Blocked: request.security only supports same-timeframe or higher-timeframe imports in this phase."
BLOCKED_REQUEST_SECURITY_INTRADAY_ONLY_MESSAGE = "Blocked: request.security lower-timeframe imports are only supported for intraday strategies in this phase."
BLOCKED_REQUEST_SECURITY_REPAINT_MESSAGE = "Blocked: request.security lookahead/repaint behavior is not supported in this phase."
BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE = "Blocked: wrapped request.security helper patterns are not supported in this phase."
BLOCKED_REQUEST_SECURITY_RUNTIME_MESSAGE = "Blocked: request.security deterministic MTF runtime is not available yet."
UNSUPPORTED_FUNCTION_TEMPLATE = "Blocked: {name}() is not supported by the Horus Pine runtime."

_TIMEFRAME_RANKS = {
    "1D": 1,
    "D": 1,
    "DAILY": 1,
    "1W": 2,
    "W": 2,
    "WEEKLY": 2,
    "1M": 3,
    "M": 3,
    "1MO": 3,
    "MONTHLY": 3,
}


def _normalize_timeframe_config(value: str | None) -> tuple[str, int, bool] | None:
    token = str(value or "").strip().upper()
    if token in _TIMEFRAME_RANKS:
        if token in {"1D", "D", "DAILY"}:
            return ("D", 1440, False)
        if token in {"1W", "W", "WEEKLY"}:
            return ("W-FRI", 10080, False)
        return ("ME", 43200, False)
    if re.fullmatch(r"\d+", token):
        minutes = int(token)
        if minutes < 1:
            return None
        return (f"{minutes}min", minutes, True)
    return None


def _strip_pine_comments(source: str) -> str:
    text = str(source or "")
    stripped: list[str] = []
    in_string: str | None = None
    in_block_comment = False
    escape = False
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            if char in "\r\n":
                stripped.append(char)
            index += 1
            continue

        if in_string is not None:
            stripped.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_string:
                in_string = None
            index += 1
            continue

        if char in {'"', "'"}:
            in_string = char
            stripped.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        stripped.append(char)
        index += 1

    return "".join(stripped)


def _extract_function_calls(source: str, function_name: str) -> list[str]:
    lowered_source = source.lower()
    lowered_name = function_name.lower()
    calls: list[str] = []
    search_from = 0

    while True:
        position = lowered_source.find(lowered_name, search_from)
        if position < 0:
            break
        after_name = position + len(lowered_name)
        if position > 0 and (source[position - 1].isalnum() or source[position - 1] == "_"):
            search_from = after_name
            continue

        cursor = after_name
        while cursor < len(source) and source[cursor].isspace():
            cursor += 1
        if cursor >= len(source) or source[cursor] != "(":
            search_from = after_name
            continue

        depth = 0
        in_string: str | None = None
        escape = False
        end = cursor
        while end < len(source):
            char = source[end]
            if in_string is not None:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == in_string:
                    in_string = None
            else:
                if char in {'"', "'"}:
                    in_string = char
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        calls.append(source[position:end + 1])
                        search_from = end + 1
                        break
            end += 1
        else:
            search_from = after_name

    return calls


def _split_call_args(call_source: str) -> list[str]:
    start = call_source.find("(")
    end = call_source.rfind(")")
    if start < 0 or end <= start:
        return []

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


def _is_string_literal(value: str) -> bool:
    text = str(value or "").strip()
    while len(text) >= 2 and text.startswith("(") and text.endswith(")"):
        inner = text[1:-1].strip()
        if not inner:
            break
        text = inner
    return len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}


def _parse_timeframe_literal(value: str) -> str | None:
    text = str(value or "").strip()
    while len(text) >= 2 and text.startswith("(") and text.endswith(")"):
        inner = text[1:-1].strip()
        if not inner:
            break
        text = inner
    if not _is_string_literal(text):
        return None
    normalized = text[1:-1].strip().upper()
    return normalized or None


def _extract_literal_assignments(source: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for raw_line in str(source or "").splitlines():
        stripped = raw_line.strip()
        assign_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", stripped)
        if not assign_match:
            continue

        name, expression = assign_match.groups()
        normalized_expression = expression.strip()
        if _is_string_literal(normalized_expression):
            assignments[name] = normalized_expression
            continue

        if re.match(r"^input(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(", normalized_expression, flags=re.IGNORECASE):
            args = _split_call_args(normalized_expression)
            default_arg: str | None = None
            for arg in args:
                if "=" not in arg:
                    if default_arg is None:
                        default_arg = arg.strip()
                    continue
                key, value = arg.split("=", 1)
                if key.strip().lower() == "defval":
                    default_arg = value.strip()
                    break
            if default_arg is not None and _is_string_literal(default_arg):
                assignments[name] = default_arg
    return assignments


def _detect_request_security_blocked_reasons(source: str, *, base_timeframe: str | None = None) -> list[str]:
    blocked: list[str] = []
    literal_assignments = _extract_literal_assignments(source)
    for call_source in _extract_function_calls(source, "request.security"):
        lowered_call = call_source.lower()
        if "lookahead_on" in lowered_call or "barstate.isrealtime" in lowered_call:
            if BLOCKED_REQUEST_SECURITY_REPAINT_MESSAGE not in blocked:
                blocked.append(BLOCKED_REQUEST_SECURITY_REPAINT_MESSAGE)

        args = _split_call_args(call_source)
        if len(args) < 3:
            if BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE not in blocked:
                blocked.append(BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE)
            continue

        raw_symbol_arg = str(args[0] or "").strip()
        raw_timeframe_arg = str(args[1] or "").strip()
        symbol_arg = literal_assignments.get(raw_symbol_arg, raw_symbol_arg).strip().lower()
        timeframe_arg = literal_assignments.get(raw_timeframe_arg, raw_timeframe_arg).strip()
        requested_timeframe = _parse_timeframe_literal(timeframe_arg)

        if symbol_arg != "syminfo.tickerid":
            if _is_string_literal(raw_symbol_arg) or _is_string_literal(literal_assignments.get(raw_symbol_arg, "")):
                if BLOCKED_REQUEST_SECURITY_SAME_SYMBOL_MESSAGE not in blocked:
                    blocked.append(BLOCKED_REQUEST_SECURITY_SAME_SYMBOL_MESSAGE)
            else:
                if BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE not in blocked:
                    blocked.append(BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE)
            continue

        if not _is_string_literal(timeframe_arg):
            if BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE not in blocked:
                blocked.append(BLOCKED_REQUEST_SECURITY_WRAPPER_MESSAGE)
            continue

        requested_config = _normalize_timeframe_config(requested_timeframe)
        base_config = _normalize_timeframe_config(base_timeframe)
        if requested_config is None or base_config is None:
            if BLOCKED_REQUEST_SECURITY_RUNTIME_MESSAGE not in blocked and BLOCKED_REQUEST_SECURITY_REPAINT_MESSAGE not in blocked:
                blocked.append(BLOCKED_REQUEST_SECURITY_RUNTIME_MESSAGE)
            continue

        _, requested_rank, requested_intraday = requested_config
        _, base_rank, base_intraday = base_config
        if requested_rank < base_rank:
            if not (requested_intraday and base_intraday):
                if BLOCKED_REQUEST_SECURITY_INTRADAY_ONLY_MESSAGE not in blocked:
                    blocked.append(BLOCKED_REQUEST_SECURITY_INTRADAY_ONLY_MESSAGE)
            continue

        if requested_rank == base_rank and requested_timeframe != str(base_timeframe or "").strip().upper():
            if BLOCKED_REQUEST_SECURITY_HIGHER_TIMEFRAME_MESSAGE not in blocked:
                blocked.append(BLOCKED_REQUEST_SECURITY_HIGHER_TIMEFRAME_MESSAGE)

    return blocked


def collect_supported_nodes(script_source: str) -> list[str]:
    source = str(script_source or "")
    nodes: list[str] = []
    for function_name in sorted(SUPPORTED_FUNCTIONS):
        if re.search(rf"\b{re.escape(function_name)}\s*\(", source, flags=re.IGNORECASE):
            nodes.append(function_name)
    if re.search(r"\bclose\b", source, flags=re.IGNORECASE):
        nodes.append("close")
    return nodes


def detect_blocked_reasons(
    script_source: str,
    *,
    base_timeframe: str | None = None,
    include_unsupported_functions: bool = True,
) -> list[str]:
    source = _strip_pine_comments(script_source)
    blocked: list[str] = []

    if re.search(r"\bstrategy\.short\b", source, flags=re.IGNORECASE):
        blocked.append(BLOCKED_SHORT_MESSAGE)

    if re.search(r"\bstrategy\.exit\s*\(", source, flags=re.IGNORECASE):
        blocked.append(BLOCKED_STRATEGY_EXIT_MESSAGE)

    blocked.extend(reason for reason in _detect_request_security_blocked_reasons(source, base_timeframe=base_timeframe) if reason not in blocked)

    if include_unsupported_functions:
        seen_functions: set[str] = set()
        for function_name in re.findall(r"\b(ta\.[A-Za-z_][A-Za-z0-9_]*)\s*\(", source, flags=re.IGNORECASE):
            normalized = function_name.lower()
            if normalized in SUPPORTED_FUNCTIONS or normalized in seen_functions:
                continue
            blocked.append(UNSUPPORTED_FUNCTION_TEMPLATE.format(name=normalized))
            seen_functions.add(normalized)

    return blocked


def normalize_execution_mode(directionality: str) -> str:
    if str(directionality or "").upper() == "LONG_ONLY":
        return "LONG_ONLY"
    return "LONG_ONLY"
