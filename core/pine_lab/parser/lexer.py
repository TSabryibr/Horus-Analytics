from __future__ import annotations

import re

_ENTRY_PATTERNS = (
    r"\bstrategy\.entry\s*\(",
    r"\bstrategy\.order\s*\(",
)

_EXIT_PATTERNS = (
    r"\bstrategy\.exit\s*\(",
    r"\bstrategy\.close\s*\(",
    r"\bstrategy\.close_all\s*\(",
)

_RUNTIME_SUPPORT_MESSAGE = "Pine backtest currently supports crossover/crossunder strategies built on ta.sma(close, N) or ta.ema(close, N)."
_UNRESOLVED_REFERENCE_TEMPLATE = 'Blocked: condition depends on unresolved variable "{name}".'
_CYCLIC_REFERENCE_TEMPLATE = 'Blocked: condition "{name}" depends on itself recursively.'
_UNSUPPORTED_CALL_TEMPLATE = "Blocked: {name}() is not supported by the Horus Pine runtime."

_INDICATOR_ENTRY_CANDIDATES = (
    "longCondition",
    "entryCondition",
    "entrySignal",
    "longSignal",
    "buySignal",
    "buyCondition",
    "buyCond",
    "triggerBuy",
    "newBuySignal",
    "buy_signal",
    "entry_signal",
    "long_signal",
    "final_buy",
    "advancedBullishEntry",
)

_INDICATOR_EXIT_CANDIDATES = (
    "exitCondition",
    "exitSignal",
    "longExit",
    "sellSignal",
    "sellCondition",
    "sellCond",
    "triggerSell",
    "newSellSignal",
    "sell_signal",
    "exit_signal",
    "long_exit",
    "final_sell",
    "advancedBearishEntry",
)


def _paren_balance_delta(source: str) -> int:
    depth_delta = 0
    in_string: str | None = None
    escape = False

    for char in str(source or ""):
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
            depth_delta += 1
        elif char == ")":
            depth_delta -= 1

    return depth_delta


def _extract_function_call_spans(source: str, function_name: str) -> list[tuple[int, int, str]]:
    lowered_source = source.lower()
    lowered_name = function_name.lower()
    spans: list[tuple[int, int, str]] = []
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
                        spans.append((position, end + 1, source[position:end + 1]))
                        search_from = end + 1
                        break
            end += 1
        else:
            search_from = after_name

    return spans


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


def _strip_wrapping_parentheses(expression: str) -> str:
    normalized = str(expression or "").strip()
    while normalized.startswith("(") and normalized.endswith(")"):
        depth = 0
        in_string: str | None = None
        escape = False
        balanced = True
        for index, char in enumerate(normalized):
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
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(normalized) - 1:
                    balanced = False
                    break

        if not balanced or depth != 0:
            break
        normalized = normalized[1:-1].strip()
    return normalized


def _normalize_line_continuations(source: str) -> str:
    lines = str(source or "").splitlines()
    normalized: list[str] = []
    index = 0

    while index < len(lines):
        current = lines[index]
        stripped = current.strip()
        if re.search(r"(?:\band\b|\bor\b|[+\-*/])\s*$", stripped, flags=re.IGNORECASE):
            parts = [stripped]
            next_index = index + 1
            while next_index < len(lines) and lines[next_index].startswith((" ", "\t")):
                candidate = lines[next_index].strip()
                if candidate:
                    parts.append(candidate)
                next_index += 1
            normalized.append(" ".join(parts))
            index = next_index
            continue

        normalized.append(current)
        index += 1

    return "\n".join(normalized)


def _detect_matches(source: str, patterns: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, source, flags=re.IGNORECASE):
            token = match.group(0).strip()
            if token not in matches:
                matches.append(token)
    return matches


def _detect_script_type(source: str) -> str:
    lowered = source.lower()
    if "strategy(" in lowered:
        return "STRATEGY"
    if "indicator(" in lowered:
        return "INDICATOR"
    return "UNKNOWN"


def _detect_directionality(source: str) -> str:
    lowered = source.lower()
    if "strategy.short" in lowered:
        return "LONG_SHORT"
    if "strategy.long" in lowered:
        return "LONG_ONLY"
    return "UNKNOWN"
