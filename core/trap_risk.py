from __future__ import annotations
"""
Shared trap-risk metadata contract helpers.

The first rollout is shadow-only, so this module begins with a stable payload
shape and neutral defaults that downstream consumers can depend on safely.
"""


from typing import Any


TRAP_RISK_METADATA_FIELDS = (
    "trap_risk_score",
    "trap_risk_band",
    "trap_risk_reason",
    "trap_risk_components",
)


def build_shadow_threshold_analysis() -> dict[str, Any]:
    """Return zeroed shadow threshold-analysis counters."""

    return {
        "rollout_mode": "shadow",
        "would_review_count": 0,
        "would_block_count": 0,
        "top_block_reasons": {},
    }


def build_trap_risk_defaults() -> dict[str, Any]:
    """Return neutral trap-risk metadata for shadow-mode consumers."""

    return {
        "trap_risk_score": None,
        "trap_risk_band": "UNKNOWN",
        "trap_risk_reason": "not_computed",
        "trap_risk_components": None,
    }


def assess_trap_risk(
    ticker: str,
    liquidity_tier: str,
    sector_rs_14: float | int | None,
    vsa_valid: bool | None,
    whale_alignment: str,
    bull_traps: list[dict[str, Any]] | None,
    bear_traps: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Return a deterministic shadow-only trap-risk assessment."""

    components = {
        "liquidity_risk": _liquidity_risk(liquidity_tier),
        "sector_risk": _sector_risk(sector_rs_14),
        "volume_quality_risk": _volume_quality_risk(vsa_valid),
        "whale_conflict_risk": _whale_conflict_risk(whale_alignment),
        "trap_context_risk": _trap_context_risk(ticker, bull_traps),
    }
    raw_score = sum(components.values())
    supportive_offset = _supportive_offset(whale_alignment, sector_rs_14, vsa_valid, liquidity_tier)
    score = max(0, min(100, raw_score - supportive_offset))
    band = _trap_risk_band(score)
    reason = _primary_trap_risk_reason(components, score)

    return {
        "trap_risk_score": int(score),
        "trap_risk_band": band,
        "trap_risk_reason": reason,
        "trap_risk_components": components,
    }


def analyze_shadow_thresholds(rows: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Summarize how future trap/whale gates would behave in shadow mode."""

    analysis = build_shadow_threshold_analysis()

    for row in rows or []:
        trap_risk_band = str(
            row.get("trap_risk_band", row.get("Trap_Risk_Band", "UNKNOWN"))
        ).strip().upper()
        whale_alignment = str(
            row.get("whale_alignment", row.get("Whale_Alignment", "NEUTRAL"))
        ).strip().upper()
        trap_risk_reason = str(
            row.get("trap_risk_reason", row.get("Trap_Risk_Reason", ""))
        ).strip()

        should_review = trap_risk_band in {"HIGH", "SEVERE"} or whale_alignment == "CONFLICT"
        should_block = trap_risk_band == "SEVERE" or (
            trap_risk_band == "HIGH" and whale_alignment == "CONFLICT"
        )

        if should_review:
            analysis["would_review_count"] += 1
        if should_block:
            analysis["would_block_count"] += 1
            if trap_risk_reason:
                analysis["top_block_reasons"][trap_risk_reason] = (
                    int(analysis["top_block_reasons"].get(trap_risk_reason, 0)) + 1
                )

    return analysis


def _liquidity_risk(liquidity_tier: str) -> int:
    tier = str(liquidity_tier or "").strip().upper()
    if tier == "ILLIQUID":
        return 50
    if tier == "TRADABLE":
        return 10
    return 0


def _sector_risk(sector_rs_14: float | int | None) -> int:
    sector_rs = float(sector_rs_14 or 0.0)
    if sector_rs <= 0:
        return 20
    if sector_rs < 0.05:
        return 10
    return 0


def _volume_quality_risk(vsa_valid: bool | None) -> int:
    if vsa_valid is False:
        return 20
    return 0


def _whale_conflict_risk(whale_alignment: str) -> int:
    alignment = str(whale_alignment or "").strip().upper()
    if alignment == "CONFLICT":
        return 30
    return 0


def _trap_context_risk(
    ticker: str,
    bull_traps: list[dict[str, Any]] | None,
) -> int:
    if not bull_traps:
        return 0

    normalized_ticker = str(ticker or "").upper()
    ticker_match = any(str(row.get("Ticker", "")).upper() == normalized_ticker for row in bull_traps)
    if ticker_match:
        return 25
    if len(bull_traps) >= 3:
        return 15
    return 0


def _supportive_offset(
    whale_alignment: str,
    sector_rs_14: float | int | None,
    vsa_valid: bool | None,
    liquidity_tier: str,
) -> int:
    offset = 0
    if str(whale_alignment or "").strip().upper() == "SUPPORTIVE":
        offset += 15
    if float(sector_rs_14 or 0.0) >= 0.1:
        offset += 5
    if vsa_valid is True:
        offset += 5
    if str(liquidity_tier or "").strip().upper() == "LIQUID":
        offset += 5
    return offset


def _trap_risk_band(score: int) -> str:
    if score >= 75:
        return "SEVERE"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def _primary_trap_risk_reason(components: dict[str, int], score: int) -> str:
    if components["whale_conflict_risk"] >= 30:
        return "distribution_against_breakout"
    if components["liquidity_risk"] >= 35:
        return "illiquid_breakout"
    if score <= 24:
        return "low_risk_alignment"
    if components["trap_context_risk"] >= 15:
        return "bull_trap_pressure"
    if components["sector_risk"] > 0:
        return "weak_sector_breakout"
    return "elevated_trap_risk"
