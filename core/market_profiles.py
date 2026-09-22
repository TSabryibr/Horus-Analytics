from __future__ import annotations
"""
Shared EGX market profile definitions.

This module starts as contract scaffolding for the microstructure rollout.
Later work packages will tighten the parameters and wire them into routing and
execution logic.
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class MarketProfile:
    """Describe a reusable EGX market-behavior profile."""

    name: str
    max_adv_participation: float
    light_participation_threshold: float
    light_slippage_pct: float
    heavy_slippage_pct: float
    volume_confirmation_threshold: float
    sector_rs_minimum: float
    turnover_floor: float
    holding_horizon_days: int
    stop_style: str
    trap_risk_tolerance: str = "shadow"


EGX30_TREND_PROFILE = MarketProfile(
    name="EGX30_TREND_PROFILE",
    max_adv_participation=0.05,
    light_participation_threshold=0.01,
    light_slippage_pct=0.5,
    heavy_slippage_pct=3.0,
    volume_confirmation_threshold=1.5,
    sector_rs_minimum=0.0,
    turnover_floor=1_000.0,
    holding_horizon_days=20,
    stop_style="trend",
    trap_risk_tolerance="medium",
)
EGX70_TACTICAL_PROFILE = MarketProfile(
    name="EGX70_TACTICAL_PROFILE",
    max_adv_participation=0.03,
    light_participation_threshold=0.01,
    light_slippage_pct=0.75,
    heavy_slippage_pct=3.5,
    volume_confirmation_threshold=1.5,
    sector_rs_minimum=0.0,
    turnover_floor=2_000.0,
    holding_horizon_days=8,
    stop_style="tactical",
    trap_risk_tolerance="low",
)
ILLIQUID_NO_TRADE_PROFILE = MarketProfile(
    name="ILLIQUID_NO_TRADE_PROFILE",
    max_adv_participation=0.0,
    light_participation_threshold=0.0,
    light_slippage_pct=0.0,
    heavy_slippage_pct=0.0,
    volume_confirmation_threshold=99.0,
    sector_rs_minimum=0.0,
    turnover_floor=float("inf"),
    holding_horizon_days=0,
    stop_style="blocked",
    trap_risk_tolerance="none",
)

DEFAULT_ROUTE_PROFILE_NAMES = (
    EGX30_TREND_PROFILE.name,
    EGX70_TACTICAL_PROFILE.name,
    ILLIQUID_NO_TRADE_PROFILE.name,
    "UNROUTED",
)
