import pandas as pd
import pytest

from core.execution_model import estimate_fill, prepare_adv_metrics
from core.market_profiles import (
    EGX30_TREND_PROFILE,
    EGX70_TACTICAL_PROFILE,
    ILLIQUID_NO_TRADE_PROFILE,
)


def test_market_profiles_expose_distinct_egx_policy_defaults():
    assert EGX30_TREND_PROFILE.max_adv_participation == pytest.approx(0.05)
    assert EGX30_TREND_PROFILE.light_participation_threshold == pytest.approx(0.01)
    assert EGX30_TREND_PROFILE.light_slippage_pct == pytest.approx(0.5)
    assert EGX30_TREND_PROFILE.heavy_slippage_pct == pytest.approx(3.0)

    assert EGX70_TACTICAL_PROFILE.max_adv_participation == pytest.approx(0.03)
    assert EGX70_TACTICAL_PROFILE.heavy_slippage_pct > EGX30_TREND_PROFILE.heavy_slippage_pct
    assert EGX70_TACTICAL_PROFILE.volume_confirmation_threshold == EGX30_TREND_PROFILE.volume_confirmation_threshold


    assert ILLIQUID_NO_TRADE_PROFILE.max_adv_participation == pytest.approx(0.0)


def test_prepare_adv_metrics_adds_share_and_notional_adv_columns():
    frame = pd.DataFrame(
        {
            'Close': [10.0] * 10,
            'Volume': [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
        }
    )

    enriched = prepare_adv_metrics(frame, window=10)

    assert 'adv_10_shares' in enriched.columns
    assert 'adv_10_notional' in enriched.columns
    assert enriched['adv_10_shares'].iloc[-1] == pytest.approx(145.0)
    assert enriched['adv_10_notional'].iloc[-1] == pytest.approx(1450.0)


def test_estimate_fill_applies_light_slippage_below_participation_threshold():
    result = estimate_fill(
        desired_shares=50,
        reference_price=10.0,
        adv_10_shares=10000,
        adv_10_notional=100000.0,
        profile=EGX30_TREND_PROFILE,
        side='buy',
    )

    assert result.fillable_shares == 50
    assert result.rejected_shares == 0
    assert result.participation_rate == pytest.approx(0.005)
    assert result.slippage_pct == pytest.approx(0.5)
    assert result.slippage_bucket == 'light'
    assert result.effective_fill_price == pytest.approx(10.05)


def test_estimate_fill_applies_heavy_slippage_for_mid_participation():
    result = estimate_fill(
        desired_shares=300,
        reference_price=10.0,
        adv_10_shares=10000,
        adv_10_notional=100000.0,
        profile=EGX70_TACTICAL_PROFILE,
        side='buy',
    )

    assert result.fillable_shares == 300
    assert result.rejected_shares == 0
    assert result.participation_rate == pytest.approx(0.03)
    assert result.slippage_bucket == 'heavy'
    assert result.slippage_pct == pytest.approx(EGX70_TACTICAL_PROFILE.heavy_slippage_pct)


def test_estimate_fill_caps_order_size_and_rejects_remainder():
    result = estimate_fill(
        desired_shares=800,
        reference_price=10.0,
        adv_10_shares=10000,
        adv_10_notional=100000.0,
        profile=EGX30_TREND_PROFILE,
        side='buy',
    )

    assert result.fillable_shares == 500
    assert result.rejected_shares == 300
    assert result.execution_cap_shares == 500
    assert result.rejected_notional == pytest.approx(3000.0)
    assert result.slippage_bucket == 'capped'
    assert result.liquidity_warning == 'Liquidity Cap Reached'


def test_estimate_fill_applies_exit_side_slippage_for_sells():
    result = estimate_fill(
        desired_shares=300,
        reference_price=10.0,
        adv_10_shares=10000,
        adv_10_notional=100000.0,
        profile=EGX30_TREND_PROFILE,
        side='sell',
    )

    assert result.slippage_bucket == 'heavy'
    assert result.effective_fill_price == pytest.approx(9.7)
