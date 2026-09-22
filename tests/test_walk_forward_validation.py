from core.settings import settings
import numpy as np
import pandas as pd

from core import WalkForwardValidation
from core.simulation import Optimizer


def _make_price_frame(start="2024-01-01", periods=500):
    idx = pd.date_range(start=start, periods=periods, freq="D")
    close = np.linspace(100.0, 140.0, periods)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(periods, 250000.0),
        },
        index=idx,
    )


def test_run_forge_collects_rolling_history(monkeypatch):
    df = _make_price_frame()

    def fake_run_brute_force(*args, **kwargs):
        return {
            "LOOKBACK": 20,
            "VOL_SPIKE": 1.5,
            "MOMENTUM": 1.0,
            "RSI_MIN": 45,
            "RSI_MAX": 85,
            "SL_PCT": 1.5,
            "TP1_PCT": 4.0,
            "MIN_TURNOVER": 2000000,
        }

    def fake_add_indicators(frame, lookback=30):
        enriched = frame.copy()
        enriched[f"Res_{lookback}"] = enriched["Close"] - 1.0
        enriched["RSI"] = 60.0
        enriched["Rel_Vol"] = 2.0
        enriched["Move"] = 2.0
        enriched["Avg_Turnover"] = 3000000.0
        return enriched

    def fake_vectorize_signals(frame, settings, resistance_col="Res_30"):
        mask = np.zeros(len(frame), dtype=bool)
        mask[::5] = True
        return mask

    monkeypatch.setattr(WalkForwardValidation.Optimizer, "run_brute_force", fake_run_brute_force)
    monkeypatch.setattr(WalkForwardValidation.DataManager, "get_stock_data", staticmethod(lambda ticker, include_live=False: df.copy()))
    monkeypatch.setattr(WalkForwardValidation.SignalEngine, "add_indicators", fake_add_indicators)
    monkeypatch.setattr(WalkForwardValidation.SignalEngine, "vectorize_signals", fake_vectorize_signals)

    forge = WalkForwardValidation.WalkForwardForge("TEST", train_months=6, val_months=1)
    history = forge.run_forge("2024-01-01", "2025-06-01")

    assert len(history) > 0
    assert history[0]["params"] is not None
    assert history[0]["val_perf"]["reason"] in {"ok", "validation_loss_blocked"}
    assert history[0]["val_perf"]["trades"] > 0


def test_apply_evolved_params_updates_global_settings(monkeypatch):
    class DummyForge:
        def __init__(self, *args, **kwargs):
            self.best_params_history = []

        def run_forge(self, *args, **kwargs):
            self.best_params_history = [
                {
                    "params": {
                        "LOOKBACK": 20,
                        "VOL_SPIKE": 2.1,
                        "MOMENTUM": 1.2,
                        "RSI_MIN": 44,
                        "RSI_MAX": 82,
                        "SL_PCT": 1.1,
                        "TP1_PCT": 5.5,
                        "MIN_TURNOVER": 2500000,
                    },
                    "val_perf": {
                        "total_return_pct": 4.2,
                        "trade_allowed": True,
                        "reason": "ok",
                    },
                }
            ]
            return self.best_params_history

        @property
        def latest_params(self):
            return self.best_params_history[-1]["params"]

        @property
        def latest_cycle(self):
            return self.best_params_history[-1]

        @staticmethod
        def _merge_with_global_defaults(settings):
            merged = dict(settings)
            merged.setdefault("TRICKSTER_RSI_MAX", 30.0)
            merged.setdefault("TRICKSTER_REL_VOL_MIN", 1.2)
            merged.setdefault("TRICKSTER_STRETCH_ATR", 2.0)
            return merged

        def save_history(self, path=None):
            return "data/wfa/test_history.json"

    saved_calls = []

    def fake_save_settings(preset_name="default"):
        saved_calls.append(preset_name)
        return True

    monkeypatch.setattr(WalkForwardValidation, "WalkForwardForge", DummyForge)
    monkeypatch.setattr(WalkForwardValidation.settings, "save_settings", fake_save_settings)

    keys = ["LOOKBACK", "VOL_SPIKE", "MOMENTUM", "RSI_MIN", "RSI_MAX", "SL_PCT", "TP1_PCT", "MIN_TURNOVER"]
    original = {k: getattr(settings, k) for k in keys}

    try:
        result = WalkForwardValidation.apply_evolved_params(
            ticker="TEST",
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert result["applied"] is True
        assert settings.VOL_SPIKE == 2.1
        assert settings.LOOKBACK == 20
        assert saved_calls and saved_calls[-1] == "WFA_TEST"
    finally:
        for key, value in original.items():
            setattr(settings, key, value)


def test_optimizer_run_brute_force_returns_best_params(monkeypatch):
    def fake_load_and_prepare_data(*args, **kwargs):
        return [{"ticker": "TEST", "length": 200}]

    def fake_vectorized_backtest_single(params):
        score = float(params["VOL_SPIKE"])
        return {
            "params": params,
            "trades": 10,
            "win_rate": 60.0 + score,
            "avg_return": 1.0,
            "score": score,
        }

    grid = {
        "VOL_SPIKE": [1.0, 2.5],
        "MOMENTUM": [1.0],
        "RSI_MIN": [40],
        "RSI_MAX": [80],
        "SL_PCT": [1.0],
        "TP1_PCT": [3.0],
        "LOOKBACK": [20],
    }

    monkeypatch.setattr(Optimizer, "load_and_prepare_data", fake_load_and_prepare_data)
    monkeypatch.setattr(Optimizer, "vectorized_backtest_single", fake_vectorized_backtest_single)

    result = Optimizer.run_brute_force("TEST", param_grid=grid, min_rows=1)
    assert result is not None
    assert result["VOL_SPIKE"] == 2.5
    assert "MIN_TURNOVER" in result


def test_optimizer_vectorized_resolves_named_universe_before_loading(monkeypatch):
    captured = {}

    monkeypatch.setattr(Optimizer.MarketLists, "get_market_list", lambda choice: {"AAA", "BBB"})

    def fake_load_and_prepare_data(*, allowed_tickers=None, **kwargs):
        captured["allowed_tickers"] = allowed_tickers
        return []

    monkeypatch.setattr(Optimizer, "load_and_prepare_data", fake_load_and_prepare_data)

    result = Optimizer.optimize_strategy_vectorized(
        tickers="ALL",
        param_grid={
            "VOL_SPIKE": [1.5],
            "MOMENTUM": [2.5],
            "RSI_MIN": [55],
            "RSI_MAX": [85],
            "SL_PCT": [1.5],
            "TP1_PCT": [4.0],
            "LOOKBACK": [30],
        },
        max_workers=1,
    )

    assert result == []
    assert captured["allowed_tickers"] == {"AAA", "BBB"}


def test_optimizer_api_results_include_strategy_defaults(monkeypatch):
    old_grid = Optimizer.PARAM_GRID
    grid = {
        "VOL_SPIKE": [1.5],
        "MOMENTUM": [2.5],
        "RSI_MIN": [55],
        "RSI_MAX": [85],
        "SL_PCT": [1.5],
        "TP1_PCT": [4.0],
        "LOOKBACK": [30],
    }

    def fake_vectorized_backtest_single(params):
        return {
            "params": dict(params),
            "trades": 10,
            "win_rate": 55.0,
            "avg_return": 1.0,
            "score": 5.0,
        }

    class DummyIntradayValidator:
        def validate_trade(self, *args, **kwargs):
            return {"outcome": "FLAT"}

    monkeypatch.setattr(Optimizer, "PARAM_GRID", grid)
    monkeypatch.setattr(Optimizer, "load_and_prepare_data", lambda *args, **kwargs: [{"ticker": "TEST", "length": 200}])
    monkeypatch.setattr(Optimizer, "vectorized_backtest_single", fake_vectorized_backtest_single)
    monkeypatch.setattr(Optimizer, "IntradayValidator", DummyIntradayValidator)

    try:
        result = Optimizer.run_optimization_api("ALL", {})
    finally:
        Optimizer.PARAM_GRID = old_grid

    assert result[0]["params"]["MIN_TURNOVER"] == settings.MIN_TURNOVER
    assert result[0]["params"]["TRAILING_STOP_TYPE"] == settings.TRAILING_STOP_TYPE


def test_dynamic_windows_shorten_when_atr_is_high(monkeypatch):
    df = _make_price_frame()

    def fake_add_indicators(frame, lookback=30):
        enriched = frame.copy()
        enriched[f"Res_{lookback}"] = enriched["Close"] - 1.0
        enriched["RSI"] = 60.0
        enriched["Rel_Vol"] = 2.0
        enriched["Move"] = 2.0
        enriched["Avg_Turnover"] = 3000000.0
        # ATR/Close ~= 5%
        enriched["ATR"] = enriched["Close"] * 0.05
        return enriched

    def fake_vectorize_signals(frame, settings, resistance_col="Res_30"):
        mask = np.zeros(len(frame), dtype=bool)
        mask[::7] = True
        return mask

    def fake_run_brute_force(*args, **kwargs):
        return {
            "LOOKBACK": 20,
            "VOL_SPIKE": 1.8,
            "MOMENTUM": 2.0,
            "RSI_MIN": 45,
            "RSI_MAX": 85,
            "SL_PCT": 1.5,
            "TP1_PCT": 4.0,
            "MIN_TURNOVER": 2000000,
        }

    monkeypatch.setattr(WalkForwardValidation.DataManager, "get_stock_data", staticmethod(lambda ticker, include_live=False: df.copy()))
    monkeypatch.setattr(WalkForwardValidation.SignalEngine, "add_indicators", fake_add_indicators)
    monkeypatch.setattr(WalkForwardValidation.SignalEngine, "vectorize_signals", fake_vectorize_signals)
    monkeypatch.setattr(WalkForwardValidation.Optimizer, "run_brute_force", fake_run_brute_force)

    forge = WalkForwardValidation.WalkForwardForge(
        "TEST",
        train_months=6,
        val_months=1,
        dynamic_windows=True,
        chaos_factor=0.5,
        atr_chaos_threshold=0.03,
    )
    history = forge.run_forge("2024-01-01", "2025-06-01")

    assert len(history) > 0
    assert any(h["chaos_mode"] for h in history)
    assert history[0]["train_days"] < 180
    assert history[0]["val_days"] < 30


def test_apply_evolved_params_blocks_ticker_when_validation_loses(monkeypatch, tmp_path):
    class DummyForge:
        def __init__(self, *args, **kwargs):
            self.best_params_history = []

        def run_forge(self, *args, **kwargs):
            self.best_params_history = [
                {
                    "params": {
                        "LOOKBACK": 20,
                        "VOL_SPIKE": 2.1,
                        "MOMENTUM": 1.2,
                        "RSI_MIN": 44,
                        "RSI_MAX": 82,
                    },
                    "val_perf": {
                        "total_return_pct": -3.5,
                        "trade_allowed": False,
                        "reason": "validation_loss_blocked",
                    },
                }
            ]
            return self.best_params_history

        @property
        def latest_params(self):
            return self.best_params_history[-1]["params"]

        @property
        def latest_cycle(self):
            return self.best_params_history[-1]

        @staticmethod
        def _merge_with_global_defaults(settings):
            return dict(settings)

        def save_history(self, path=None):
            return "data/wfa/test_history.json"

    monkeypatch.setattr(WalkForwardValidation, "WalkForwardForge", DummyForge)

    gate_file = tmp_path / "trade_gate.json"
    result = WalkForwardValidation.apply_evolved_params(
        ticker="TEST",
        start_date="2024-01-01",
        end_date="2024-12-31",
        gate_path=str(gate_file),
    )
    assert result["applied"] is False
    assert result["reason"] == "validation_loss_blocked"

    gate = WalkForwardValidation.get_trade_permission("TEST", path=str(gate_file))
    assert gate["allowed"] is False


def test_get_trade_permission_fail_closed_on_corrupt_gate_file(tmp_path):
    gate_file = tmp_path / "broken_gate.json"
    gate_file.write_text("{invalid_json", encoding="utf-8")

    blocked = WalkForwardValidation.get_trade_permission("TEST", path=str(gate_file), fail_closed=True)
    assert blocked["allowed"] is False
    assert blocked["reason"] == "gate_unreadable"
