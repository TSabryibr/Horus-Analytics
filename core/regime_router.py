from __future__ import annotations
"""
EGX regime routing and sector-relative strength helpers.

This seam keeps EGX30/EGX70 classification and sector gating in one place so
scanner and later runtime paths do not drift.
"""


from typing import Any, Mapping

import pandas as pd

from core.market import MarketLists
from core.market_profiles import (
    EGX30_TREND_PROFILE,
    EGX70_TACTICAL_PROFILE,
    ILLIQUID_NO_TRADE_PROFILE,
)


def calculate_sector_relative_strength(
    universe_df: pd.DataFrame,
    lookback: int = 14,
    sector_map: Mapping[str, str] | None = None,
    benchmark_tickers: set[str] | None = None,
) -> dict[str, float]:
    """Return sector returns relative to the EGX30 benchmark basket."""

    if universe_df is None or universe_df.empty:
        return {}

    if not isinstance(universe_df.index, pd.MultiIndex):
        raise ValueError("universe_df must use a [Ticker, Date] MultiIndex")

    sector_lookup = sector_map or MarketLists.SECTOR_MAP
    benchmark_members = set(benchmark_tickers or MarketLists.EGX_30)

    close = universe_df["Close"].astype(float)
    returns_14 = close.groupby(level=0).transform(lambda series: series / series.shift(lookback) - 1.0)
    latest_returns = returns_14.groupby(level=0).last().dropna()
    if latest_returns.empty:
        return {}

    benchmark_series = latest_returns[latest_returns.index.isin(benchmark_members)]
    benchmark_return = float(benchmark_series.mean()) if not benchmark_series.empty else 0.0

    sector_buckets: dict[str, list[float]] = {}
    for ticker, value in latest_returns.items():
        sector = sector_lookup.get(ticker, "Unknown")
        sector_buckets.setdefault(sector, []).append(float(value))

    return {
        sector: (sum(values) / len(values)) - benchmark_return
        for sector, values in sector_buckets.items()
        if values
    }


def route_candidate(
    ticker: str,
    row: pd.Series,
    sector_rs_map: Mapping[str, float],
    sector: str | None = None,
    egx30_tickers: set[str] | None = None,
    egx70_tickers: set[str] | None = None,
) -> dict[str, Any]:
    """Route a candidate into an EGX profile and return allow/block metadata."""

    resolved_sector = sector or MarketLists.get_sector(ticker)
    sector_rs_14 = float(sector_rs_map.get(resolved_sector, 0.0))
    liquidity_tier = classify_liquidity_tier(row)
    egx30_members = egx30_tickers if egx30_tickers is not None else MarketLists.EGX_30
    egx70_members = egx70_tickers if egx70_tickers is not None else MarketLists.EGX_70

    if liquidity_tier == "ILLIQUID":
        return _route_response(
            profile_name=ILLIQUID_NO_TRADE_PROFILE.name,
            allowed=False,
            routing_reason="illiquid",
            liquidity_tier=liquidity_tier,
            sector=resolved_sector,
            sector_rs_14=sector_rs_14,
        )

    if sector_rs_14 <= 0:
        return _route_response(
            profile_name=ILLIQUID_NO_TRADE_PROFILE.name,
            allowed=False,
            routing_reason="negative_sector_rs",
            liquidity_tier=liquidity_tier,
            sector=resolved_sector,
            sector_rs_14=sector_rs_14,
        )

    if ticker in egx30_members:
        return _route_response(
            profile_name=EGX30_TREND_PROFILE.name,
            allowed=True,
            routing_reason="egx30_trend",
            liquidity_tier=liquidity_tier,
            sector=resolved_sector,
            sector_rs_14=sector_rs_14,
        )

    if ticker in egx70_members:
        return _route_response(
            profile_name=EGX70_TACTICAL_PROFILE.name,
            allowed=True,
            routing_reason="egx70_tactical",
            liquidity_tier=liquidity_tier,
            sector=resolved_sector,
            sector_rs_14=sector_rs_14,
        )

    # Non-index tickers in FULL universe mode are treated as EGX70 tactical
    return _route_response(
        profile_name=EGX70_TACTICAL_PROFILE.name,
        allowed=True,
        routing_reason="non_index_tactical",
        liquidity_tier=liquidity_tier,
        sector=resolved_sector,
        sector_rs_14=sector_rs_14,
    )


def classify_liquidity_tier(row: pd.Series) -> str:
    """Classify a row into simple liquidity buckets using notional turnover."""

    adv_notional = float(row.get("adv_10_notional") or row.get("Avg_Turnover") or row.get("Turnover") or 0.0)
    if adv_notional >= 1_000_000:
        return "LIQUID"
    if adv_notional >= 250_000:
        return "TRADABLE"
    return "ILLIQUID"


def _route_response(
    profile_name: str,
    allowed: bool,
    routing_reason: str,
    liquidity_tier: str,
    sector: str,
    sector_rs_14: float,
) -> dict[str, Any]:
    """Build the standard routing payload shape."""

    return {
        "route_profile": profile_name,
        "allowed": allowed,
        "routing_reason": routing_reason,
        "liquidity_tier": liquidity_tier,
        "sector": sector,
        "sector_rs_14": sector_rs_14,
    }
