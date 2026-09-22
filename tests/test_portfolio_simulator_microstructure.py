from __future__ import annotations
from core.settings import settings

import pandas as pd
import pytest

from core.simulation import BacktestReporting
from core.simulation import PortfolioSimulator
from core import SignalEngine


class _DummyExcelWriter:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture()
def clean_simulator_side_effects(monkeypatch, tmp_path):
    monkeypatch.setattr(PortfolioSimulator, 'COMMISSION_PCT', 0.0)
    monkeypatch.setattr(PortfolioSimulator.pd, 'ExcelWriter', _DummyExcelWriter)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None)
    monkeypatch.setattr(
        BacktestReporting,
        'calculate_metrics',
        lambda trades_df, daily_df, starting_capital: {
            'Total Return %': 0.0,
            'Final Equity': float(daily_df['value'].iloc[-1]) if not daily_df.empty else float(starting_capital),
        },
    )
    monkeypatch.setattr(BacktestReporting, 'generate_markdown_report', lambda metrics, trades_df, save_path=None: 'report')
    monkeypatch.setattr(PortfolioSimulator.settings, 'REPORTS_DIR', str(tmp_path))


def _make_stock_frame(rows: list[dict[str, float]], dates: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, index=pd.to_datetime(dates))
    frame.index.name = 'Date'
    return frame


def _patch_signal_dates(monkeypatch, *signal_dates: str):
    active_dates = {pd.Timestamp(date) for date in signal_dates}

    def fake_vectorize_signals(frame, settings, resistance_col="Res_30"):
        return pd.Series(frame.index.isin(active_dates), index=frame.index)

    monkeypatch.setattr(SignalEngine, 'vectorize_signals', fake_vectorize_signals)


def test_run_simulation_enters_on_next_bar_open(clean_simulator_side_effects, monkeypatch):
    dates = ['2025-01-01', '2025-01-02', '2025-01-03']
    stock = _make_stock_frame(
        [
            {'Open': 95.0, 'High': 100.0, 'Low': 95.0, 'Close': 100.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 1000000.0},
            {'Open': 102.0, 'High': 102.5, 'Low': 101.5, 'Close': 102.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 1020000.0},
            {'Open': 103.0, 'High': 103.0, 'Low': 103.0, 'Close': 103.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 1030000.0},
        ],
        dates,
    )

    monkeypatch.setattr(PortfolioSimulator, 'load_all_stocks', lambda allowed_tickers=None, params=None: {'COMI': stock})
    _patch_signal_dates(monkeypatch, '2025-01-01')
    monkeypatch.setattr(PortfolioSimulator, 'check_exit', lambda *args, **kwargs: None)

    result = PortfolioSimulator.run_simulation(
        cap=6000,
        start_date='2025-01-01',
        end_date='2025-01-03',
        index_choice='EGX30',
        max_positions=1,
    )

    assert result['trades'] == []
    assert result['daily_values'][1]['positions'] == 1
    assert result['final_value'] == pytest.approx(6028.42)


def test_run_simulation_caps_entry_size_and_updates_shadow_diagnostics(clean_simulator_side_effects, monkeypatch):
    dates = ['2025-01-01', '2025-01-02', '2025-01-03']
    stock = _make_stock_frame(
        [
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 1000.0, 'adv_10_shares': 1000.0, 'adv_10_notional': 10000.0},
            {'Open': 10.0, 'High': 10.5, 'Low': 9.5, 'Close': 10.0, 'Volume': 1000.0, 'adv_10_shares': 1000.0, 'adv_10_notional': 10000.0},
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 1000.0, 'adv_10_shares': 1000.0, 'adv_10_notional': 10000.0},
        ],
        dates,
    )

    monkeypatch.setattr(PortfolioSimulator, 'load_all_stocks', lambda allowed_tickers=None, params=None: {'COMI': stock})
    _patch_signal_dates(monkeypatch, '2025-01-01')
    monkeypatch.setattr(PortfolioSimulator, 'check_exit', lambda *args, **kwargs: None)

    result = PortfolioSimulator.run_simulation(
        cap=100000,
        start_date='2025-01-01',
        end_date='2025-01-03',
        index_choice='EGX30',
        max_positions=1,
    )

    diagnostics = result['microstructure']['diagnostics']
    assert result['trades'] == []
    assert result['daily_values'][1]['positions'] == 1
    assert diagnostics['liquidity_cap_hits'] == 1
    assert diagnostics['rejected_notional'] == pytest.approx(99500.0)
    assert diagnostics['slippage_bucket_usage']['capped'] == 1
    assert diagnostics['unliquidated_shares'] == 50
    assert diagnostics['unliquidated_notional'] == pytest.approx(500.0)


def test_run_simulation_applies_exit_side_liquidity_constraints(clean_simulator_side_effects, monkeypatch):
    dates = ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04']
    stock = _make_stock_frame(
        [
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 100000.0},
            {'Open': 15.0, 'High': 15.0, 'Low': 15.0, 'Close': 15.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 150000.0},
            {'Open': 12.0, 'High': 12.0, 'Low': 12.0, 'Close': 12.0, 'Volume': 1000.0, 'adv_10_shares': 1000.0, 'adv_10_notional': 10000.0},
            {'Open': 12.0, 'High': 12.0, 'Low': 12.0, 'Close': 12.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 120000.0},
        ],
        dates,
    )

    monkeypatch.setattr(PortfolioSimulator, 'load_all_stocks', lambda allowed_tickers=None, params=None: {'COMI': stock})
    _patch_signal_dates(monkeypatch, '2025-01-01')
    monkeypatch.setattr(
        PortfolioSimulator,
        'check_exit',
        lambda df, entry_date, entry_price, stop_loss, target1, target2, params=None: {
            'exit_date': pd.Timestamp('2025-01-03'),
            'exit_price': 12.0,
            'reason': 'TARGET1',
        },
    )

    result = PortfolioSimulator.run_simulation(
        cap=6000,
        start_date='2025-01-01',
        end_date='2025-01-04',
        index_choice='EGX30',
        max_positions=1,
    )

    assert len(result['trades']) == 2
    assert result['trades'][0]['shares'] == 41
    assert result['trades'][0]['exit_rejected_shares'] == 347
    assert result['trades'][0]['reason'] == 'TARGET1'
    assert result['trades'][1]['shares'] == 347
    assert result['trades'][1]['reason'] == 'TARGET1'
    assert result['microstructure']['diagnostics']['liquidity_cap_hits'] == 1


def test_run_simulation_applies_per_run_cost_assumptions(clean_simulator_side_effects, monkeypatch):
    dates = ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04']
    stock = _make_stock_frame(
        [
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 100000.0, 'adv_10_shares': 100000.0, 'adv_10_notional': 1000000.0},
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 100000.0, 'adv_10_shares': 100000.0, 'adv_10_notional': 1000000.0},
            {'Open': 12.0, 'High': 12.0, 'Low': 12.0, 'Close': 12.0, 'Volume': 100000.0, 'adv_10_shares': 100000.0, 'adv_10_notional': 1200000.0},
            {'Open': 12.0, 'High': 12.0, 'Low': 12.0, 'Close': 12.0, 'Volume': 100000.0, 'adv_10_shares': 100000.0, 'adv_10_notional': 1200000.0},
        ],
        dates,
    )

    monkeypatch.setattr(PortfolioSimulator, 'load_all_stocks', lambda allowed_tickers=None, params=None: {'COMI': stock})
    _patch_signal_dates(monkeypatch, '2025-01-01')
    monkeypatch.setattr(
        PortfolioSimulator,
        'check_exit',
        lambda df, entry_date, entry_price, stop_loss, target1, target2, params=None: {
            'exit_date': pd.Timestamp('2025-01-03'),
            'exit_price': 12.0,
            'reason': 'TARGET1',
        },
    )

    result = PortfolioSimulator.run_simulation(
        cap=6000,
        start_date='2025-01-01',
        end_date='2025-01-04',
        index_choice='EGX30',
        max_positions=1,
        params={'COMMISSION_PCT': 1.0, 'SLIPPAGE_PCT': 2.0},
    )

    assert len(result['trades']) == 1
    trade = result['trades'][0]
    gross_pnl = (trade['exit_price'] - trade['entry_price']) * trade['shares']
    expected_fees = (trade['entry_price'] * trade['shares'] + trade['exit_price'] * trade['shares']) * 0.01
    assert trade['entry_slippage_pct'] == pytest.approx(2.0)
    assert trade['exit_slippage_pct'] == pytest.approx(2.0)
    assert trade['pnl'] == pytest.approx(gross_pnl - expected_fees)


def test_run_simulation_tracks_unliquidated_inventory_when_final_bar_cannot_fill(clean_simulator_side_effects, monkeypatch):
    dates = ['2025-01-01', '2025-01-02', '2025-01-03']
    stock = _make_stock_frame(
        [
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 100000.0},
            {'Open': 10.0, 'High': 10.0, 'Low': 10.0, 'Close': 10.0, 'Volume': 10000.0, 'adv_10_shares': 10000.0, 'adv_10_notional': 100000.0},
            {'Open': 12.0, 'High': 12.0, 'Low': 12.0, 'Close': 12.0, 'Volume': 0.0, 'adv_10_shares': 0.0, 'adv_10_notional': 0.0},
        ],
        dates,
    )

    monkeypatch.setattr(PortfolioSimulator, 'load_all_stocks', lambda allowed_tickers=None, params=None: {'COMI': stock})
    _patch_signal_dates(monkeypatch, '2025-01-01')
    monkeypatch.setattr(PortfolioSimulator, 'check_exit', lambda *args, **kwargs: None)

    result = PortfolioSimulator.run_simulation(
        cap=6000,
        start_date='2025-01-01',
        end_date='2025-01-03',
        index_choice='EGX30',
        max_positions=1,
    )

    diagnostics = result['microstructure']['diagnostics']
    assert result['trades'] == []
    assert diagnostics['unliquidated_shares'] == 500
    assert diagnostics['unliquidated_notional'] == pytest.approx(6000.0)
    assert result['final_value'] == pytest.approx(6850.0)
