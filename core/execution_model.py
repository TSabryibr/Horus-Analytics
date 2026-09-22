from __future__ import annotations
"""
Shared EGX microstructure execution contract helpers.

The first rollout keeps these helpers intentionally small so simulator,
scanner, and later runtime paths can agree on one vocabulary before any
enforcement logic is activated.
"""


from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Any

import pandas as pd

from core.market_profiles import DEFAULT_ROUTE_PROFILE_NAMES, MarketProfile


MICROSTRUCTURE_METADATA_FIELDS = (
    "route_profile",
    "liquidity_tier",
    "adv_10_shares",
    "adv_10_notional",
    "volume_mult_20",
    "sector_rs_14",
    "vsa_valid",
    "trap_risk",
    "expected_slippage_pct",
    "execution_cap_shares",
)


def build_candidate_microstructure_defaults() -> dict[str, Any]:
    """Return the default metadata payload carried by a candidate signal."""

    return {
        "route_profile": "UNROUTED",
        "liquidity_tier": "UNKNOWN",
        "adv_10_shares": None,
        "adv_10_notional": None,
        "volume_mult_20": None,
        "sector_rs_14": None,
        "vsa_valid": None,
        "trap_risk": None,
        "expected_slippage_pct": None,
        "execution_cap_shares": None,
    }


def build_shadow_diagnostics() -> dict[str, Any]:
    """Return zeroed microstructure counters for shadow-mode rollout."""

    return {
        "rollout_mode": "shadow",
        "liquidity_cap_hits": 0,
        "rejected_notional": 0.0,
        "unliquidated_shares": 0,
        "unliquidated_notional": 0.0,
        "vsa_veto_count": 0,
        "sector_rs_veto_count": 0,
        "slippage_bucket_usage": {
            "light": 0,
            "heavy": 0,
            "capped": 0,
        },
        "route_counts": {name: 0 for name in DEFAULT_ROUTE_PROFILE_NAMES},
    }


def build_microstructure_contract(
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the shared payload shape exposed by simulator and scanner paths."""

    shadow_diagnostics = diagnostics or build_shadow_diagnostics()
    return {
        "metadata_fields": list(MICROSTRUCTURE_METADATA_FIELDS),
        "diagnostics": deepcopy(shadow_diagnostics),
    }


@dataclass(frozen=True)
class ExecutionEstimate:
    """Describe the liquidity-constrained fill estimate for one order."""

    desired_shares: int
    fillable_shares: int
    rejected_shares: int
    execution_cap_shares: int
    participation_rate: float
    slippage_pct: float
    slippage_bucket: str
    effective_fill_price: float
    rejected_notional: float
    liquidity_warning: str | None
    side: str


def prepare_adv_metrics(frame: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Add rolling share and notional ADV columns to a price frame."""

    enriched = frame.copy()
    turnover = enriched["Close"].astype(float) * enriched["Volume"].astype(float)
    enriched["adv_10_shares"] = enriched["Volume"].rolling(window, min_periods=window).mean()
    enriched["adv_10_notional"] = turnover.rolling(window, min_periods=window).mean()
    return enriched


def estimate_fill(
    desired_shares: int,
    reference_price: float,
    adv_10_shares: float | None,
    adv_10_notional: float | None,
    profile: MarketProfile,
    side: str = "buy",
    slippage_floor_pct: float | None = None,
) -> ExecutionEstimate:
    """Estimate a fill under profile-driven EGX liquidity constraints."""

    normalized_side = side.lower()
    if normalized_side not in {"buy", "sell"}:
        raise ValueError(f"Unsupported side: {side}")

    safe_desired_shares = max(int(desired_shares), 0)
    safe_price = float(reference_price)
    cap_shares = _calculate_cap_shares(
        reference_price=safe_price,
        adv_10_shares=adv_10_shares,
        adv_10_notional=adv_10_notional,
        max_adv_participation=profile.max_adv_participation,
    )

    fillable_shares = min(safe_desired_shares, cap_shares)
    rejected_shares = max(safe_desired_shares - fillable_shares, 0)
    fill_notional = fillable_shares * safe_price
    participation_rate = _calculate_participation_rate(
        fill_notional=fill_notional,
        fillable_shares=fillable_shares,
        adv_10_notional=adv_10_notional,
        adv_10_shares=adv_10_shares,
    )

    if rejected_shares > 0:
        slippage_bucket = "capped"
        slippage_pct = profile.heavy_slippage_pct
        liquidity_warning = "Liquidity Cap Reached"
    elif participation_rate < profile.light_participation_threshold:
        slippage_bucket = "light"
        slippage_pct = profile.light_slippage_pct
        liquidity_warning = None
    else:
        slippage_bucket = "heavy"
        slippage_pct = profile.heavy_slippage_pct
        liquidity_warning = None

    if slippage_floor_pct is not None:
        slippage_pct = max(slippage_pct, float(slippage_floor_pct))

    effective_fill_price = _apply_slippage(
        reference_price=safe_price,
        slippage_pct=slippage_pct,
        side=normalized_side,
    )

    return ExecutionEstimate(
        desired_shares=safe_desired_shares,
        fillable_shares=fillable_shares,
        rejected_shares=rejected_shares,
        execution_cap_shares=cap_shares,
        participation_rate=participation_rate,
        slippage_pct=slippage_pct,
        slippage_bucket=slippage_bucket,
        effective_fill_price=effective_fill_price,
        rejected_notional=rejected_shares * safe_price,
        liquidity_warning=liquidity_warning,
        side=normalized_side,
    )


def _calculate_cap_shares(
    reference_price: float,
    adv_10_shares: float | None,
    adv_10_notional: float | None,
    max_adv_participation: float,
) -> int:
    """Return the maximum shares allowed by the available ADV metrics."""

    if reference_price <= 0 or max_adv_participation <= 0:
        return 0

    candidate_caps: list[int] = []
    if adv_10_notional is not None and not pd.isna(adv_10_notional) and adv_10_notional > 0:
        candidate_caps.append(
            int(math.floor((adv_10_notional * max_adv_participation) / reference_price))
        )
    if adv_10_shares is not None and not pd.isna(adv_10_shares) and adv_10_shares > 0:
        candidate_caps.append(int(math.floor(adv_10_shares * max_adv_participation)))

    if not candidate_caps:
        return 0

    return max(min(candidate_caps), 0)


def _calculate_participation_rate(
    fill_notional: float,
    fillable_shares: int,
    adv_10_notional: float | None,
    adv_10_shares: float | None,
) -> float:
    """Compute order participation using notional ADV first, then shares."""

    if adv_10_notional is not None and not pd.isna(adv_10_notional) and adv_10_notional > 0:
        return float(fill_notional / adv_10_notional)
    if adv_10_shares is not None and not pd.isna(adv_10_shares) and adv_10_shares > 0:
        return float(fillable_shares / adv_10_shares)
    return 0.0


def _apply_slippage(reference_price: float, slippage_pct: float, side: str) -> float:
    """Apply slippage in the direction of market impact."""

    if side == "buy":
        return reference_price * (1 + (slippage_pct / 100))
    return reference_price * (1 - (slippage_pct / 100))
