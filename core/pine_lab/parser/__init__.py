"""
PINE LAB PARSER PACKAGE
=======================
Modular lexing, security wrapper normalization, ternary resolution, AST expression conversion,
variable validation, and execution plan transpilation for Pine Script scripts.
"""

from .lexer import (
    _CYCLIC_REFERENCE_TEMPLATE,
    _ENTRY_PATTERNS,
    _EXIT_PATTERNS,
    _INDICATOR_ENTRY_CANDIDATES,
    _INDICATOR_EXIT_CANDIDATES,
    _RUNTIME_SUPPORT_MESSAGE,
    _UNRESOLVED_REFERENCE_TEMPLATE,
    _UNSUPPORTED_CALL_TEMPLATE,
    _detect_directionality,
    _detect_matches,
    _detect_script_type,
    _extract_function_call_spans,
    _normalize_line_continuations,
    _paren_balance_delta,
    _split_call_args,
    _strip_wrapping_parentheses,
)
from .conditions import (
    _call_name_from_ast,
    _expand_multiline_expression_helpers,
    _extract_multiline_expression_helpers,
    _extract_passthrough_request_security_helpers,
    _normalize_embedded_ternaries,
    _normalize_known_supertrend_helpers,
    _normalize_pine_expression,
    _normalize_request_security_passthrough_wrappers,
    _parse_expression_node,
    _parse_input_default_literal,
    _split_top_level_ternary,
    _substitute_identifier_references,
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
from .transpiler import (
    _build_validated_execution_plan,
    _extract_indicator_signal_plan,
    _extract_strategy_spec_from_plan,
    build_pine_execution_plan,
    extract_supported_strategy_spec,
    preflight_pine_script,
)

__all__ = [
    # Lexer
    "_ENTRY_PATTERNS",
    "_EXIT_PATTERNS",
    "_RUNTIME_SUPPORT_MESSAGE",
    "_UNRESOLVED_REFERENCE_TEMPLATE",
    "_CYCLIC_REFERENCE_TEMPLATE",
    "_UNSUPPORTED_CALL_TEMPLATE",
    "_INDICATOR_ENTRY_CANDIDATES",
    "_INDICATOR_EXIT_CANDIDATES",
    "_paren_balance_delta",
    "_extract_function_call_spans",
    "_split_call_args",
    "_strip_wrapping_parentheses",
    "_normalize_line_continuations",
    "_detect_matches",
    "_detect_script_type",
    "_detect_directionality",
    # Conditions
    "_extract_passthrough_request_security_helpers",
    "_substitute_identifier_references",
    "_normalize_known_supertrend_helpers",
    "_extract_multiline_expression_helpers",
    "_expand_multiline_expression_helpers",
    "_normalize_request_security_passthrough_wrappers",
    "_call_name_from_ast",
    "_split_top_level_ternary",
    "_normalize_embedded_ternaries",
    "_normalize_pine_expression",
    "_parse_expression_node",
    "_parse_input_default_literal",
    # Statements
    "_extract_unique_lengths",
    "_collect_capability_errors",
    "_collect_reachable_definition_names",
    "_validate_variable_references",
    "_resolve_expression",
    "_extract_indicator_descriptor",
    "_parse_script_plan",
    # Transpiler
    "_extract_strategy_spec_from_plan",
    "_build_validated_execution_plan",
    "_extract_indicator_signal_plan",
    "extract_supported_strategy_spec",
    "build_pine_execution_plan",
    "preflight_pine_script",
]
