from __future__ import annotations
"""
Shared whale-flow metadata contract helpers.

The first rollout is intentionally shadow-only. These helpers define a stable
field vocabulary and neutral defaults before scanner, AI report, and dashboard
consumers begin depending on whale-flow interpretation.
"""


from copy import deepcopy
from typing import Any

from core.trap_risk import (
    TRAP_RISK_METADATA_FIELDS,
    analyze_shadow_thresholds,
    build_shadow_threshold_analysis,
    build_trap_risk_defaults,
)


WHALE_FLOW_METADATA_FIELDS = (
    "whale_signal",
    "whale_strength",
    "whale_alignment",
    "whale_reason",
)


def build_whale_flow_defaults() -> dict[str, Any]:
    """Return neutral whale-flow metadata for shadow-mode consumers."""

    return {
        "whale_signal": "UNKNOWN",
        "whale_strength": None,
        "whale_alignment": "NEUTRAL",
        "whale_reason": "no_whale_signal",
    }


def build_whale_trap_diagnostics() -> dict[str, Any]:
    """Return zeroed whale/trap shadow diagnostics."""

    return {
        "rollout_mode": "shadow",
        "supportive_whale_alignments": 0,
        "whale_conflicts": 0,
        "high_trap_risk_count": 0,
        "severe_trap_risk_count": 0,
        "top_trap_risk_reasons": {},
        "threshold_analysis": build_shadow_threshold_analysis(),
    }


def build_whale_trap_contract(
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the shared whale/trap metadata contract."""

    resolved_diagnostics = diagnostics or build_whale_trap_diagnostics()
    return {
        "metadata_fields": [
            *WHALE_FLOW_METADATA_FIELDS,
            *TRAP_RISK_METADATA_FIELDS,
        ],
        "defaults": {
            **build_whale_flow_defaults(),
            **build_trap_risk_defaults(),
        },
        "diagnostics": deepcopy(resolved_diagnostics),
    }


def summarize_whale_trap_diagnostics(
    rows: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Roll up shadow whale/trap counters across candidate-like rows."""

    diagnostics = build_whale_trap_diagnostics()
    for row in rows or []:
        whale_alignment = str(
            row.get("whale_alignment", row.get("Whale_Alignment", ""))
        ).strip().upper()
        trap_risk_band = str(
            row.get("trap_risk_band", row.get("Trap_Risk_Band", "UNKNOWN"))
        ).strip().upper()
        trap_risk_reason = str(
            row.get("trap_risk_reason", row.get("Trap_Risk_Reason", ""))
        ).strip()

        if whale_alignment == "SUPPORTIVE":
            diagnostics["supportive_whale_alignments"] += 1
        elif whale_alignment == "CONFLICT":
            diagnostics["whale_conflicts"] += 1

        if trap_risk_band == "HIGH":
            diagnostics["high_trap_risk_count"] += 1
        elif trap_risk_band == "SEVERE":
            diagnostics["severe_trap_risk_count"] += 1

        if trap_risk_band in {"HIGH", "SEVERE"} and trap_risk_reason:
            diagnostics["top_trap_risk_reasons"][trap_risk_reason] = (
                int(diagnostics["top_trap_risk_reasons"].get(trap_risk_reason, 0)) + 1
            )

    diagnostics["threshold_analysis"] = analyze_shadow_thresholds(rows)
    return diagnostics


def evaluate_whale_flow(
    ticker: str,
    whale_candidates: list[dict[str, Any]] | None,
    candidate_side: str = "BUY",
) -> dict[str, Any]:
    """Return whale-flow metadata for one candidate ticker."""

    defaults = build_whale_flow_defaults()
    if not whale_candidates:
        return defaults

    normalized_ticker = str(ticker or "").upper()
    matched = next(
        (
            row for row in whale_candidates
            if str(row.get("Ticker", "")).upper() == normalized_ticker
        ),
        None,
    )
    if not matched:
        return defaults

    signal = _normalize_whale_signal(matched.get("Signal"))
    if signal == "UNKNOWN":
        return defaults

    max_strength = max(
        [
            float(row.get("Strength") or 0.0)
            for row in whale_candidates
            if _normalize_whale_signal(row.get("Signal")) != "UNKNOWN"
        ] or [0.0]
    )
    whale_strength = _normalize_whale_strength(matched.get("Strength"), max_strength)
    whale_alignment, whale_reason = _resolve_whale_alignment(signal, candidate_side)

    return {
        "whale_signal": signal,
        "whale_strength": whale_strength,
        "whale_alignment": whale_alignment,
        "whale_reason": whale_reason,
    }


def _normalize_whale_signal(value: Any) -> str:
    """Return a supported whale signal label or UNKNOWN."""

    normalized = str(value or "").strip().upper()
    if normalized in {"ACCUMULATION", "DISTRIBUTION", "NEUTRAL"}:
        return normalized
    return "UNKNOWN"


def _normalize_whale_strength(raw_strength: Any, max_strength: float) -> float | None:
    """Normalize raw whale strength to a compact 0..1 range."""

    strength = float(raw_strength or 0.0)
    if strength <= 0:
        return None

    baseline = max(float(max_strength or 0.0), strength, 1.0)
    return round(min(max(strength / baseline, 0.0), 1.0), 3)


def _resolve_whale_alignment(signal: str, candidate_side: str) -> tuple[str, str]:
    """Map whale signal to candidate alignment labels."""

    side = str(candidate_side or "BUY").strip().upper()
    if side == "BUY":
        if signal == "ACCUMULATION":
            return "SUPPORTIVE", "accumulation_support"
        if signal == "DISTRIBUTION":
            return "CONFLICT", "distribution_conflict"
        return "NEUTRAL", "neutral_whale_signal"

    return "NEUTRAL", "neutral_whale_signal"
