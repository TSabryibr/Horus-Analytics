"""
AI REPORT GENERATION PACKAGE
============================
Modular LLM prompting, market scoring, execution profiling, Ollama client,
and rule-based synthesis.
"""

from core.settings import settings
from ..boundary import (
    bool_env,
    float_env,
    dedupe_recommendations,
    dedupe_report_sections,
    dedupe_strings,
    ollama_model_candidates,
    remove_overlaps,
    rule_engine_instruction_text,
    _RULE_ENGINE_THINKING_CONTRACT,
)
from .scoring import (
    _build_promotion_context,
    _build_rule_based_recommendations,
    _compute_rr_ratio,
    _derive_local_execution_profile,
    _score_market_direction,
    _strategy_regime_bias,
)
from .templates import (
    _RULE_ENGINE_REASONING_PROFILE,
    _build_llm_prompts,
)
from .ollama_client import (
    _call_ollama_report,
    _maybe_generate_llm_report,
    _normalize_llm_report,
    _repair_llm_json,
    _safe_recommendations,
    _safe_string_list,
    _strip_code_fences,
    _test_ollama_endpoint,
    logger,
)
from .synthesis import (
    _generate_rule_based_report,
)

__all__ = [
    "bool_env",
    "float_env",
    "dedupe_recommendations",
    "dedupe_report_sections",
    "dedupe_strings",
    "ollama_model_candidates",
    "remove_overlaps",
    "rule_engine_instruction_text",
    "_RULE_ENGINE_THINKING_CONTRACT",
    "_strategy_regime_bias",
    "_score_market_direction",
    "_derive_local_execution_profile",
    "_compute_rr_ratio",
    "_build_rule_based_recommendations",
    "_build_promotion_context",
    "_RULE_ENGINE_REASONING_PROFILE",
    "_build_llm_prompts",
    "_strip_code_fences",
    "_repair_llm_json",
    "_safe_string_list",
    "_safe_recommendations",
    "_normalize_llm_report",
    "_call_ollama_report",
    "_test_ollama_endpoint",
    "_maybe_generate_llm_report",
    "_generate_rule_based_report",
    "logger",
    "settings",
]
