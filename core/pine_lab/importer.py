from __future__ import annotations

import hashlib
import re
from typing import Any

from .capabilities import _strip_pine_comments
from .import_translation import build_import_translation
from .import_validator import validate_import_rule_spec
from .parser import _detect_script_type

_ASSIGNMENT_RE = re.compile(
    r"^(?:var\s+)?(?:bool|int|float|string|color|line|label|box|table|array<[^>]+>\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)\s*(.+)$"
)
_INPUT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*input(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(", re.IGNORECASE)
_INDICATOR_CALL_RE = re.compile(r"\b(ta\.[A-Za-z_][A-Za-z0-9_]*|request\.security)\s*\(", re.IGNORECASE)
_TOKEN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

_KEYWORDS = {
    "and",
    "or",
    "not",
    "if",
    "true",
    "false",
    "na",
    "color",
    "math",
    "str",
    "ta",
    "request",
    "input",
}
_SERIES_NAMES = {"open", "high", "low", "close", "volume", "hl2", "ohlc4", "bar_index"}
_ROLE_PATTERNS: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    (
        "long_entry",
        (
            re.compile(r"^longe$", re.IGNORECASE),
            re.compile(r"^longentry$", re.IGNORECASE),
            re.compile(r"^longcondition$", re.IGNORECASE),
            re.compile(r"^buysignal\d*$", re.IGNORECASE),
            re.compile(r"^buy$", re.IGNORECASE),
            re.compile(r"^letrigger$", re.IGNORECASE),
        ),
    ),
    (
        "short_entry",
        (
            re.compile(r"^shorte$", re.IGNORECASE),
            re.compile(r"^shortentry$", re.IGNORECASE),
            re.compile(r"^shortcondition$", re.IGNORECASE),
            re.compile(r"^sellsignal\d*$", re.IGNORECASE),
            re.compile(r"^sell$", re.IGNORECASE),
            re.compile(r"^setrigger$", re.IGNORECASE),
        ),
    ),
    (
        "long_exit",
        (
            re.compile(r"^longx$", re.IGNORECASE),
            re.compile(r"^exitcondition$", re.IGNORECASE),
            re.compile(r"^lxtrigger$", re.IGNORECASE),
            re.compile(r"^closelong$", re.IGNORECASE),
        ),
    ),
    (
        "short_exit",
        (
            re.compile(r"^shortx$", re.IGNORECASE),
            re.compile(r"^sxtrigger$", re.IGNORECASE),
            re.compile(r"^closeshort$", re.IGNORECASE),
        ),
    ),
]


def _extract_dependencies(expression: str, known_names: set[str]) -> list[str]:
    dependencies: list[str] = []
    for match in _TOKEN_RE.finditer(str(expression or "")):
        token = match.group(1)
        if token in _KEYWORDS or token in _SERIES_NAMES:
            continue
        if token not in known_names:
            continue
        if token not in dependencies:
            dependencies.append(token)
    return dependencies


def _extract_unresolved_references(expression: str, known_names: set[str]) -> list[str]:
    unresolved: list[str] = []
    raw_expression = str(expression or "")
    for match in _TOKEN_RE.finditer(raw_expression):
        token = match.group(1)
        start, end = match.span(1)
        if token in _KEYWORDS or token in _SERIES_NAMES:
            continue
        if token in known_names:
            continue
        previous_char = raw_expression[start - 1] if start > 0 else ""
        next_char = raw_expression[end] if end < len(raw_expression) else ""
        if previous_char == ".":
            continue
        if next_char == "(":
            continue
        if token not in unresolved:
            unresolved.append(token)
    return unresolved


def _classify_role(name: str) -> str | None:
    for role, patterns in _ROLE_PATTERNS:
        for pattern in patterns:
            if pattern.match(name):
                return role
    return None


def _classify_ignored_section(line: str) -> str | None:
    stripped = line.strip()
    lowered = stripped.lower()
    if not stripped:
        return None
    if lowered.startswith("plot(") or lowered.startswith("plotshape(") or lowered.startswith("plotchar("):
        return "plot"
    if lowered.startswith("fill("):
        return "fill"
    if lowered.startswith("alertcondition(") or lowered.startswith("alert("):
        return "alert"
    if lowered.startswith("label.") or "label.new(" in lowered:
        return "label"
    if lowered.startswith("table.") or "table.new(" in lowered:
        return "table"
    if lowered.startswith("barcolor(") or lowered.startswith("bgcolor("):
        return "style"
    return None


def _scan_script(script_source: str) -> dict[str, Any]:
    sanitized = _strip_pine_comments(str(script_source or ""))
    definitions: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    ignored_sections: list[dict[str, Any]] = []
    indicator_calls: list[str] = []

    raw_definitions: list[dict[str, Any]] = []

    for line_number, raw_line in enumerate(sanitized.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue

        ignored_kind = _classify_ignored_section(stripped)
        if ignored_kind:
            ignored_sections.append({"kind": ignored_kind, "line": line_number, "source": stripped})
            continue

        input_match = _INPUT_RE.match(stripped)
        if input_match:
            inputs.append({"name": input_match.group(1), "line": line_number})

        for call_name in _INDICATOR_CALL_RE.findall(stripped):
            normalized = str(call_name).strip()
            if normalized not in indicator_calls:
                indicator_calls.append(normalized)

        match = _ASSIGNMENT_RE.match(stripped)
        if match:
            raw_definitions.append(
                {
                    "name": match.group(1),
                    "expression": match.group(2).strip(),
                    "line": line_number,
                }
            )

    known_names = {item["name"] for item in raw_definitions}
    for item in raw_definitions:
        definitions.append(
            {
                **item,
                "depends_on": _extract_dependencies(item["expression"], known_names),
            }
        )

    definition_map = {item["name"]: item for item in definitions}
    candidate_signals: list[dict[str, Any]] = []
    unresolved_references: list[dict[str, Any]] = []
    warnings: list[str] = []
    for item in definitions:
        role = _classify_role(item["name"])
        if role is None:
            continue
        confidence = 0.72 if role in {"long_entry", "long_exit"} else 0.64
        if any(dep.endswith("trigger") for dep in item["depends_on"]):
            confidence = max(confidence, 0.78)
        candidate_signals.append(
            {
                "role": role,
                "name": item["name"],
                "expression": item["expression"],
                "line": item["line"],
                "depends_on": item["depends_on"],
                "confidence": confidence,
            }
        )
        unresolved_names = _extract_unresolved_references(item["expression"], known_names)
        if unresolved_names:
            unresolved_references.append(
                {
                    "role": role,
                    "name": item["name"],
                    "line": item["line"],
                    "expression": item["expression"],
                    "references": unresolved_names,
                }
            )
            warnings.append(
                f'Candidate signal "{item["name"]}" references unresolved names: {", ".join(unresolved_names)}.'
            )

    if not candidate_signals:
        warnings.append("No executable signal logic extracted from named Pine assignments.")

    indicators = [
        {"name": name}
        for name in indicator_calls
    ]

    return {
        "definition_map": definition_map,
        "definitions": definitions,
        "candidate_signals": candidate_signals,
        "unresolved_references": unresolved_references,
        "parameters": inputs,
        "indicators": indicators,
        "ignored_sections": ignored_sections,
        "warnings": warnings,
    }


def build_pine_import_preview(
    script_source: str,
    *,
    market: str,
    timeframe: str,
    date_from: str,
    date_to: str,
    signal_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = str(script_source or "")
    scanned = _scan_script(source)
    translation, rule_spec = build_import_translation(
        scanned,
        script_source=source,
        script_type=_detect_script_type(_strip_pine_comments(source)),
        signal_overrides=signal_overrides,
    )
    validation = validate_import_rule_spec(rule_spec, scanned)

    return {
        "status": "success",
        "import_mode": "LOGIC_IMPORT",
        "script_hash": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "market": market,
        "timeframe": timeframe,
        "date_from": date_from,
        "date_to": date_to,
        "signal_overrides": signal_overrides if isinstance(signal_overrides, dict) else {},
        "review_status": validation["review_status"],
        "translation": translation,
        "reduced_source_pack": {
            "candidate_signals": scanned["candidate_signals"],
            "definitions": scanned["definitions"],
            "unresolved_references": scanned["unresolved_references"],
            "parameters": scanned["parameters"],
            "indicators": scanned["indicators"],
            "warnings": scanned["warnings"],
        },
        "ignored_sections": scanned["ignored_sections"],
        "warnings": rule_spec["warnings"],
        "rule_spec": rule_spec,
    }
