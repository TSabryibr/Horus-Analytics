import pandas as pd
import pytest

from core.regime_router import calculate_sector_relative_strength, route_candidate


def _universe_frame() -> pd.DataFrame:
    dates = pd.date_range('2025-01-01', periods=15, freq='D')
    rows = []
    for i, date in enumerate(dates):
        rows.append(('COMI', date, 100 + i * 2.0))
        rows.append(('CIB', date, 90 + i * 2.0))
        rows.append(('FWRY', date, 80 + i * 0.5))
        rows.append(('SWDY', date, 70 - i * 0.2))
    frame = pd.DataFrame(rows, columns=['Ticker', 'Date', 'Close'])
    frame['Open'] = frame['Close']
    frame['High'] = frame['Close']
    frame['Low'] = frame['Close']
    frame['Volume'] = 1000.0
    return frame.set_index(['Ticker', 'Date']).sort_index()


def test_calculate_sector_relative_strength_compares_sector_baskets_to_egx30_benchmark():
    sector_map = {
        'COMI': 'Banks',
        'CIB': 'Banks',
        'FWRY': 'Tech',
        'SWDY': 'Retail',
    }
    sector_rs = calculate_sector_relative_strength(
        _universe_frame(),
        lookback=14,
        sector_map=sector_map,
        benchmark_tickers={'COMI', 'CIB'},
    )

    assert sector_rs['Banks'] == pytest.approx(0.0)
    assert sector_rs['Tech'] < 0.0
    assert sector_rs['Retail'] < sector_rs['Tech']


def test_route_candidate_assigns_egx30_trend_profile_when_sector_is_supportive():
    route = route_candidate(
        ticker='COMI',
        row=pd.Series({'Avg_Turnover': 2_500_000.0, 'adv_10_notional': 2_000_000.0}),
        sector='Banks',
        sector_rs_map={'Banks': 0.08},
        egx30_tickers={'COMI'},
        egx70_tickers=set(),
    )

    assert route['allowed'] is True
    assert route['route_profile'] == 'EGX30_TREND_PROFILE'
    assert route['routing_reason'] == 'egx30_trend'
    assert route['liquidity_tier'] == 'LIQUID'


def test_route_candidate_assigns_egx70_tactical_profile_when_sector_is_supportive():
    route = route_candidate(
        ticker='FWRY',
        row=pd.Series({'Avg_Turnover': 400_000.0, 'adv_10_notional': 350_000.0}),
        sector='Tech',
        sector_rs_map={'Tech': 0.05},
        egx30_tickers=set(),
        egx70_tickers={'FWRY'},
    )

    assert route['allowed'] is True
    assert route['route_profile'] == 'EGX70_TACTICAL_PROFILE'
    assert route['routing_reason'] == 'egx70_tactical'
    assert route['liquidity_tier'] == 'TRADABLE'


def test_route_candidate_downgrades_to_no_trade_when_sector_or_liquidity_is_weak():
    route = route_candidate(
        ticker='SWDY',
        row=pd.Series({'Avg_Turnover': 20_000.0, 'adv_10_notional': 20_000.0}),
        sector='Retail',
        sector_rs_map={'Retail': -0.10},
        egx30_tickers={'SWDY'},
        egx70_tickers=set(),
    )

    assert route['allowed'] is False
    assert route['route_profile'] == 'ILLIQUID_NO_TRADE_PROFILE'
    assert route['routing_reason'] in {'negative_sector_rs', 'illiquid'}
    assert route['liquidity_tier'] == 'ILLIQUID'
