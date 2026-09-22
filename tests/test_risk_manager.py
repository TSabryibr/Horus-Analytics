from core.settings import settings
import pytest
from unittest.mock import patch

from core import RiskManager
from database import Portfolio, Position
def test_portfolio_heat_calculation():
    positions = [
        {"ticker": "COMI", "entry": 50.0, "sl": 48.0, "shares": 100},
        {"ticker": "FWRY", "entry": 10.0, "sl": 9.0, "shares": 200},
    ]
    # Risk: (50-48)*100 + (10-9)*200 = 200 + 200 = 400
    # Heat: 400 / 100000 * 100 = 0.4%
    heat = RiskManager.calculate_portfolio_heat(positions, account_balance=100_000)
    assert heat == 0.4


def test_portfolio_heat_zero_balance():
    positions = [{"ticker": "COMI", "entry": 50.0, "sl": 48.0, "shares": 100}]
    heat = RiskManager.calculate_portfolio_heat(positions, account_balance=0)
    assert heat == 0.0


def test_portfolio_heat_empty_positions():
    heat = RiskManager.calculate_portfolio_heat([], account_balance=100_000)
    assert heat == 0.0


def test_check_sector_exposure_under_limit(monkeypatch):
    monkeypatch.setattr(settings, "SECTOR_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "MAX_PER_SECTOR", 3)
    monkeypatch.setattr("core.RiskManager.MarketLists.get_sector", lambda t: "Banks")

    allowed, msg = RiskManager.check_sector_exposure("NEW_BANK", ["BANK_A", "BANK_B"])
    assert allowed is True
    assert msg is None


def test_check_sector_exposure_at_limit(monkeypatch):
    monkeypatch.setattr(settings, "SECTOR_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "MAX_PER_SECTOR", 2)
    monkeypatch.setattr("core.RiskManager.MarketLists.get_sector", lambda t: "Banks")

    allowed, msg = RiskManager.check_sector_exposure("NEW_BANK", ["BANK_A", "BANK_B"])
    assert allowed is False
    assert "Sector Limit Exceeded" in msg


def test_correlation_matrix_returns_dataframe(monkeypatch):
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2025-01-01", periods=120, freq="B")
    base = 100 + np.cumsum(np.random.randn(120) * 0.5)

    def fake_get_stock_data(ticker, include_live=False, **kwargs):
        noise = np.random.randn(120) * 0.3
        return pd.DataFrame(
            {"Close": base + noise, "Open": base, "High": base + 1, "Low": base - 1, "Volume": [1000] * 120},
            index=dates,
        )

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)

    result = RiskManager.get_correlation_matrix(["A", "B", "C"])
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert result.shape == (3, 3)


def test_check_new_trade_correlation_safe(monkeypatch):
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2025-01-01", periods=120, freq="B")

    def fake_get_stock_data(ticker, include_live=False, **kwargs):
        np.random.seed(hash(ticker) % 2**31)
        prices = 100 + np.cumsum(np.random.randn(120) * 2)
        return pd.DataFrame(
            {"Close": prices, "Open": prices, "High": prices + 1, "Low": prices - 1, "Volume": [1000] * 120},
            index=dates,
        )

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)

    result = RiskManager.check_new_trade_correlation(["EXISTING_A"], "NEW_TICKER")
    assert "is_safe" in result
    assert isinstance(result["is_safe"], bool)


def test_correlation_matrix_uses_bulk_universe_data_when_available(monkeypatch):
    import pandas as pd

    dates = pd.date_range("2025-01-01", periods=120, freq="B")
    rows = []
    index = []
    for idx, date in enumerate(dates):
        rows.append(
            {
                "Open": 100.0 + idx,
                "High": 101.0 + idx,
                "Low": 99.0 + idx,
                "Close": 100.0 + (idx * 1.1),
                "Volume": 1000 + idx,
                "Ticker": "A",
            }
        )
        index.append(("A", date))
        rows.append(
            {
                "Open": 200.0 + idx,
                "High": 201.0 + idx,
                "Low": 199.0 + idx,
                "Close": 200.0 + (idx * 1.3),
                "Volume": 2000 + idx,
                "Ticker": "B",
            }
        )
        index.append(("B", date))

    universe_df = pd.DataFrame(
        rows,
        index=pd.MultiIndex.from_tuples(index, names=["Ticker", "Date"]),
    )

    monkeypatch.setattr(
        "core.DataManager.DataManager.get_universe_data",
        lambda tickers, include_live=False: universe_df if tickers == ["A", "B"] and include_live is False else None,
    )
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_stock_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("bulk universe data should satisfy correlation")),
    )

    result = RiskManager.get_correlation_matrix(["A", "B"])
    assert result is not None
    assert list(result.columns) == ["A", "B"]


def test_stock_beta_uses_read_only_history(monkeypatch):
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2025-01-01", periods=120, freq="B")
    prices = 100 + np.cumsum(np.random.randn(120))
    df = pd.DataFrame(
        {"Close": prices, "Open": prices, "High": prices + 1, "Low": prices - 1, "Volume": [1000] * 120},
        index=dates,
    )
    calls = []

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        calls.append({"ticker": ticker, "include_live": include_live})
        return df.copy()

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)

    result = RiskManager.get_stock_beta("COMI", benchmark="EGX30")

    assert isinstance(result, float)
    assert calls == [
        {"ticker": "COMI", "include_live": False},
        {"ticker": "EGX30", "include_live": False},
    ]


def test_analyze_portfolio_uses_settings_heat_threshold(monkeypatch):
    portfolio = Portfolio.create(name="Risk Heat Threshold Portfolio", type="USER")
    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=400,
        entry_price=100.0,
        stop_loss=92.0,
        target_price=115.0,
        current_price=100.0,
        status="OPEN",
    )
    portfolio.cash_egp = 10000.0
    portfolio.cash_usd = 0.0
    portfolio.save()

    monkeypatch.setattr(settings, "MAX_PORTFOLIO_HEAT", 10.0)
    relaxed = RiskManager.analyze_portfolio(portfolio.id)
    relaxed_titles = [item.get("title") for item in (relaxed.get("recommendations") or [])]
    assert "High Portfolio Heat" not in relaxed_titles

    monkeypatch.setattr(settings, "MAX_PORTFOLIO_HEAT", 6.0)
    strict = RiskManager.analyze_portfolio(portfolio.id)
    strict_titles = [item.get("title") for item in (strict.get("recommendations") or [])]
    assert "High Portfolio Heat" in strict_titles
