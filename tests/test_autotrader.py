from core.settings import settings
import pytest
import datetime
from unittest.mock import MagicMock, patch
import pandas as pd
from database import Portfolio, Position, Trade
from core import AutoTrader


class _QueryResult(list):
    def where(self, *args, **kwargs):
        return self

    def count(self):
        return len(self)


def _make_bullish_market_frame(periods=30):
    index = pd.date_range("2025-01-01", periods=periods, freq="D")
    close = pd.Series(range(100, 100 + periods), index=index, dtype=float)
    return pd.DataFrame({"Close": close}, index=index)


def _make_choppy_market_frame(periods=30):
    index = pd.date_range("2025-01-01", periods=periods, freq="D")
    close = pd.Series(list(range(130, 130 - periods, -1)), index=index, dtype=float)
    return pd.DataFrame({"Close": close}, index=index)


def test_autotrader_blocks_heat_alert_from_type_1_main_channel(monkeypatch):
    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.ENABLE_INTRADAY_ALERTS", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.MAX_PORTFOLIO_HEAT", 6.0, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.HEAT_PROTECTION_ENABLED", True, raising=False)
    monkeypatch.setattr("core.RiskManager.calculate_portfolio_heat", lambda heat_input, account_size: 7.0)

    alerts = []
    monkeypatch.setattr("core.AutoTrader.AlertManager.broadcast_alert", lambda message: alerts.append(message) or {"ok": True})

    with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
        AutoTrader.process_scanner_signals(
            [{"Ticker": "EGTS", "Entry_Price": 10.0, "Stop_Loss": 9.0, "Target_Price": 12.0}],
            "Swing Signals",
        )

    assert alerts == []


def test_autotrader_allows_heat_alert_for_type_3_main_channel(monkeypatch):
    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.ENABLE_INTRADAY_ALERTS", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.MAX_PORTFOLIO_HEAT", 6.0, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.HEAT_PROTECTION_ENABLED", True, raising=False)
    monkeypatch.setattr("core.RiskManager.calculate_portfolio_heat", lambda heat_input, account_size: 7.0)

    alerts = []
    monkeypatch.setattr("core.AutoTrader.AlertManager.broadcast_alert", lambda message: alerts.append(message) or {"ok": True})

    with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
        AutoTrader.process_scanner_signals(
            [{"Ticker": "EGTS", "Entry_Price": 10.0, "Stop_Loss": 9.0, "Target_Price": 12.0}],
            "Swing Signals",
        )

    assert len(alerts) == 1
    assert "PORTFOLIO HEAT LIMIT REACHED" in alerts[0]


def test_autotrader_blocks_exit_card_from_type_1_main_channel(monkeypatch):
    monkeypatch.setattr("core.AutoTrader.settings.ENABLE_INTRADAY_ALERTS", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr("core.ReportGenerator.create_exit_card", lambda *args, **kwargs: object())

    images = []
    alerts = []
    monkeypatch.setattr("core.AutoTrader.AlertManager.broadcast_image", lambda card, caption="": images.append(caption) or {"ok": True})
    monkeypatch.setattr("core.AutoTrader.AlertManager.broadcast_alert", lambda message: alerts.append(message) or {"ok": True})

    AutoTrader._notify_exit("EGTS", 19.9217, 21.69, "STOP_LOSS")

    assert images == []
    assert alerts == []


def test_autotrader_allows_exit_card_for_type_3_main_channel(monkeypatch):
    monkeypatch.setattr("core.AutoTrader.settings.ENABLE_INTRADAY_ALERTS", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr("core.ReportGenerator.create_exit_card", lambda *args, **kwargs: object())

    images = []
    monkeypatch.setattr("core.AutoTrader.AlertManager.broadcast_image", lambda card, caption="": images.append(caption) or {"ok": True})

    AutoTrader._notify_exit("EGTS", 19.9217, 21.69, "STOP_LOSS")

    assert len(images) == 1
    assert "STOP LOSS HIT" in images[0]


def test_monitor_positions_refreshes_intraday_cache_before_exit_checks(monkeypatch):
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    Position.create(
        portfolio=portfolio,
        ticker="BONY",
        shares=100,
        entry_price=5.0,
        stop_loss=4.5,
        target_price=6.0,
        entry_date=datetime.datetime(2026, 5, 25, 12, 0, 0),
        status="OPEN",
    )
    bars = pd.DataFrame(
        {
            "Open": [5.1],
            "High": [5.5],
            "Low": [5.0],
            "Close": [5.4],
            "Volume": [1000],
        },
        index=[pd.Timestamp("2026-05-25 12:30:00")],
    )
    refresh_calls = []

    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_ENABLED", False, raising=False)
    monkeypatch.setattr("core.AutoTrader.DataManager.refresh_intraday_cache_if_due", lambda: refresh_calls.append(True) or True)
    monkeypatch.setattr("core.AutoTrader.DataManager.get_intraday_data", lambda *args, **kwargs: bars)
    monkeypatch.setattr("core.ConfluenceEngine.confluence_engine.get_active_trap", lambda ticker: None)

    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    assert refresh_calls == [True]


def test_monitor_positions_uses_latest_intraday_bar_not_daily_session_low(monkeypatch):
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    position = Position.create(
        portfolio=portfolio,
        ticker="BONY",
        shares=100,
        entry_price=5.14,
        stop_loss=5.296,
        target_price=6.052,
        entry_date=datetime.datetime(2026, 5, 24, 13, 0, 0),
        status="OPEN",
    )
    bars = pd.DataFrame(
        {
            "Open": [5.63],
            "High": [5.63],
            "Low": [5.61],
            "Close": [5.62],
            "Volume": [80275],
        },
        index=[pd.Timestamp("2026-05-25 12:43:00")],
    )

    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_ENABLED", False, raising=False)
    monkeypatch.setattr("core.AutoTrader.DataManager.refresh_intraday_cache_if_due", lambda: False)
    monkeypatch.setattr("core.AutoTrader.DataManager.get_intraday_data", lambda *args, **kwargs: bars)
    monkeypatch.setattr(
        "core.AutoTrader.DataManager.get_stock_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("monitor should not use daily stock data for exits")),
    )
    monkeypatch.setattr("core.ConfluenceEngine.confluence_engine.get_active_trap", lambda ticker: None)

    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    position = Position.get_by_id(position.id)
    assert position.status == "OPEN"
    assert Trade.select().where(Trade.ticker == "BONY").count() == 0


def test_monitor_positions_marks_stop_above_entry_as_trailing_stop(monkeypatch):
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    Position.create(
        portfolio=portfolio,
        ticker="TRAIL",
        shares=100,
        entry_price=100.0,
        stop_loss=104.0,
        target_price=120.0,
        entry_date=datetime.datetime(2026, 6, 15, 10, 0, 0),
        status="OPEN",
    )
    bars = pd.DataFrame(
        {
            "Open": [105.0],
            "High": [106.0],
            "Low": [103.5],
            "Close": [104.2],
            "Volume": [1000],
        },
        index=[pd.Timestamp("2026-06-15 10:05:00")],
    )

    notifications = []
    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_ENABLED", False, raising=False)
    monkeypatch.setattr("core.AutoTrader.DataManager.refresh_intraday_cache_if_due", lambda: False)
    monkeypatch.setattr("core.AutoTrader.DataManager.get_intraday_data", lambda *args, **kwargs: bars)
    monkeypatch.setattr("core.AutoTrader.TimeUtils.now", lambda: datetime.datetime(2026, 6, 15, 10, 6, 0))
    monkeypatch.setattr("core.ConfluenceEngine.confluence_engine.get_active_trap", lambda ticker: None)
    monkeypatch.setattr("core.AutoTrader._notify_exit", lambda ticker, exit_price, entry_price, reason: notifications.append(reason))

    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    trade = Trade.get(Trade.ticker == "TRAIL")
    assert trade.reason == "TRAILING_STOP"
    assert notifications == ["TRAILING_STOP"]


@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.AlertManager.broadcast_alert")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
def test_process_scanner_signals(
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_send_msg,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    # Setup
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = True
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"
    
    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_add_position.return_value = True
    mock_position_select.return_value = _QueryResult()

    signals = [
        {
            'Ticker': 'TEST',
            'Entry_Price': 100,
            'Stop_Loss': 90,
            'Target_Price': 120,
            'Sector': 'Tech',
            'Score': 80
        }
    ]

    # Execute
    with patch("core.AutoTrader.WalkForwardValidation.get_trade_permission", return_value={"allowed": True, "reason": "ok"}):
        with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
            AutoTrader.process_scanner_signals(signals, "Test Portfolio")

    # Verify
    mock_add_position.assert_called_once()
    args, kwargs = mock_add_position.call_args
    assert kwargs['ticker'] == 'TEST'
    assert kwargs['entry_price'] == 100
    assert kwargs['portfolio_id'] == 1
    
    # Check share calculation: Risk = 2000 (2% of 100k). Risk/Share = 10. Shares = 200.
    assert kwargs['shares'] == 200


@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get_or_none")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
def test_process_scanner_signals_falls_back_when_requested_portfolio_missing(
    mock_settings,
    mock_portfolio_get,
    mock_portfolio_get_or_none,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"

    mock_portfolio_get.side_effect = Exception("missing requested portfolio")
    fallback_portfolio = MagicMock()
    fallback_portfolio.id = 99
    fallback_portfolio.name = "Swing Signals"
    mock_portfolio_get_or_none.return_value = fallback_portfolio
    mock_position_select.return_value = _QueryResult()
    mock_add_position.return_value = True

    signals = [{
        'Ticker': 'TEST',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with patch("core.AutoTrader.WalkForwardValidation.get_trade_permission", return_value={"allowed": True, "reason": "ok"}):
        with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
            AutoTrader.process_scanner_signals(signals, "Horus Core")

    mock_add_position.assert_called_once()
    _, kwargs = mock_add_position.call_args
    assert kwargs["portfolio_id"] == 99


@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_choppy_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
def test_process_scanner_signals_respects_disabled_regime_filter(
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"
    mock_settings.REGIME_FILTER_ENABLED = False

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_position_select.return_value = _QueryResult()
    mock_add_position.return_value = True

    signals = [{
        'Ticker': 'TEST',
        'Signal_Type': 'BUY',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with patch("core.AutoTrader.WalkForwardValidation.get_trade_permission", return_value={"allowed": True, "reason": "ok"}):
        with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
            AutoTrader.process_scanner_signals(signals, "Test Portfolio")

    mock_add_position.assert_called_once()


@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_choppy_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
def test_process_scanner_signals_blocks_choppy_buy_when_regime_filter_enabled(
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"
    mock_settings.REGIME_FILTER_ENABLED = True

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_position_select.return_value = _QueryResult()

    signals = [{
        'Ticker': 'TEST',
        'Signal_Type': 'BUY',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with patch("core.AutoTrader.WalkForwardValidation.get_trade_permission", return_value={"allowed": True, "reason": "ok"}):
        with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
            AutoTrader.process_scanner_signals(signals, "Test Portfolio")

    mock_add_position.assert_not_called()

@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
@patch("core.AutoTrader.WalkForwardValidation.get_trade_permission")
def test_process_scanner_signals_blocked_by_gate(
    mock_gate,
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_gate.return_value = {"allowed": False, "reason": "validation_loss_blocked"}
    mock_position_select.return_value = _QueryResult()

    signals = [{
        'Ticker': 'TEST',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
        AutoTrader.process_scanner_signals(signals, "Test Portfolio")
    mock_add_position.assert_not_called()
    assert mock_gate.called


@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=9.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.AlertManager.broadcast_alert")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
def test_process_scanner_signals_blocks_when_portfolio_heat_exceeds_limit(
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_send_msg,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_position_select.return_value = _QueryResult()

    signals = [{
        'Ticker': 'TEST',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with patch("core.AutoTrader.WalkForwardValidation.get_trade_permission", return_value={"allowed": True, "reason": "ok"}):
        with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
            AutoTrader.process_scanner_signals(signals, "Test Portfolio")

    mock_add_position.assert_not_called()


@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
@patch("core.AutoTrader.WalkForwardValidation.get_trade_permission")
def test_process_scanner_signals_fail_closed_on_gate_lookup_error(
    mock_gate,
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_gate.side_effect = RuntimeError("broken gate file")
    mock_position_select.return_value = _QueryResult()

    signals = [{
        'Ticker': 'TEST',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
        AutoTrader.process_scanner_signals(signals, "Test Portfolio")
    mock_add_position.assert_not_called()

@patch("core.ConfluenceEngine.confluence_engine.get_active_trap", return_value=None)
@patch("core.RiskManager.check_new_trade_correlation", return_value={"is_safe": True})
@patch("core.RiskManager.calculate_portfolio_heat", return_value=0.0)
@patch("core.AutoTrader.DataManager.get_stock_data", return_value=_make_bullish_market_frame())
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.PositionTracker.add_position")
@patch("core.AutoTrader.Portfolio.get")
@patch("core.AutoTrader.settings")
@patch("core.AutoTrader.WalkForwardValidation.get_trade_permission")
def test_process_scanner_signals_blocked_on_pre_execution_recheck(
    mock_gate,
    mock_settings,
    mock_portfolio_get,
    mock_add_position,
    mock_position_select,
    mock_market_data,
    mock_heat,
    mock_corr,
    mock_trap,
):
    mock_settings.AUTO_TRADE_ENABLED = True
    mock_settings.ENABLE_INTRADAY_ALERTS = False
    mock_settings.RISK_PER_TRADE = 2.0
    mock_settings.ACCOUNT_BALANCE = 100000
    mock_settings.MAX_PORTFOLIO_HEAT = 6.0
    mock_settings.MAX_DAILY_TRADES = 3
    mock_settings.METASTOCK_HISTORY_FOLDER = "data"

    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio_get.return_value = mock_portfolio
    mock_gate.side_effect = [
        {"allowed": True, "reason": "ok"},
        {"allowed": False, "reason": "midday_block"},
    ]
    mock_position_select.return_value = _QueryResult()

    signals = [{
        'Ticker': 'TEST',
        'Entry_Price': 100,
        'Stop_Loss': 90,
        'Target_Price': 120,
        'Sector': 'Tech',
        'Score': 80
    }]

    with pytest.deprecated_call(match="AutoTrader.process_scanner_signals is deprecated"):
        AutoTrader.process_scanner_signals(signals, "Test Portfolio")
    mock_add_position.assert_not_called()
    assert mock_gate.call_count == 2

@patch("core.AutoTrader.PositionTracker.close_position")
@patch("core.AutoTrader.AlertManager.broadcast_alert")
@patch("core.AutoTrader.Position.select")
def test_check_exit_conditions_sl(mock_select, mock_send_msg, mock_close_position):
    # Setup: Mock an open position with SL=90
    mock_pos = MagicMock()
    mock_pos.ticker = "TEST"
    mock_pos.stop_loss = 90
    mock_pos.target_price = 120
    mock_pos.entry_price = 100
    mock_pos.portfolio.id = 1
    
    mock_select.return_value.where.return_value = [mock_pos]
    mock_close_position.return_value = True

    # Execute: Current price 85 (below SL)
    AutoTrader.check_exit_conditions("TEST", 85)

    # Verify
    mock_close_position.assert_called_once()
    args, kwargs = mock_close_position.call_args
    assert args[0] == "TEST"
    assert args[1] == 90 # Exit at SL
    assert kwargs['reason'] == 'STOP_LOSS'

@patch("core.AutoTrader.PositionTracker.close_position")
@patch("core.AutoTrader.AlertManager.broadcast_alert")
@patch("core.AutoTrader.PositionTracker.update_position")
@patch("core.AutoTrader.Position.select")
@patch("core.AutoTrader.Position.get_or_none")
def test_check_exit_conditions_tp(mock_get_or_none, mock_select, mock_update_position, mock_send_msg, mock_close_position):
    # Setup: Mock an open position with TP=120
    mock_pos = MagicMock()
    mock_pos.ticker = "TEST"
    mock_pos.shares = 100
    mock_pos.tp1_hit = False
    mock_pos.stop_loss = 90
    mock_pos.target_price = 120
    mock_pos.entry_price = 100
    mock_pos.portfolio.id = 1
    mock_pos.target_price_2 = None
    
    mock_select.return_value.where.return_value = [mock_pos]
    mock_get_or_none.return_value = mock_pos
    mock_close_position.return_value = True

    # Execute: Current price 125 (above TP)
    AutoTrader.check_exit_conditions("TEST", 125)

    # Verify
    mock_close_position.assert_called_once()
    args, kwargs = mock_close_position.call_args
    assert args[0] == "TEST"
    assert args[1] == 120 # Exit at TP
    assert kwargs['reason'] == 'TARGET 1'
    assert kwargs['partial_shares'] == 50


def test_monitor_positions_stops_execution_on_close_and_skips_trailing_sl_update(monkeypatch):
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    position = Position.create(
        portfolio=portfolio,
        ticker="GGRN",
        shares=100,
        entry_price=1.60,
        stop_loss=1.4959,
        target_price=2.00,
        entry_date=datetime.datetime(2026, 7, 28, 10, 0, 0),
        status="OPEN",
    )
    bars = pd.DataFrame(
        {
            "Open": [1.57],
            "High": [1.58],
            "Low": [1.49], # Triggers SL at 1.4959
            "Close": [1.57], # With 2% trailing stop, potential_sl = 1.5386 -> 1.54 (> 1.4959)
            "Volume": [10000],
        },
        index=[pd.Timestamp("2026-07-28 14:03:00")],
    )

    logged_trailing_sls = []

    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_TYPE", "PERCENT", raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_VALUE", 2.0, raising=False)
    # Pin the clock so the bar is not treated as stale data.
    monkeypatch.setattr("core.AutoTrader.TimeUtils.now", lambda: datetime.datetime(2026, 7, 28, 14, 5, 0))
    monkeypatch.setattr("core.AutoTrader.DataManager.refresh_intraday_cache_if_due", lambda: False)
    monkeypatch.setattr("core.AutoTrader.DataManager.get_intraday_data", lambda *args, **kwargs: bars)
    monkeypatch.setattr("core.ConfluenceEngine.confluence_engine.get_active_trap", lambda ticker: None)

    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    assert Position.get_or_none(Position.id == position.id) is None
    trade = Trade.select().where(Trade.ticker == "GGRN").first()
    assert trade is not None
    assert trade.reason == "STOP_LOSS"


def test_monitor_positions_tp1_sets_tp1_hit_and_does_not_repeat(monkeypatch):
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    position = Position.create(
        portfolio=portfolio,
        ticker="AIHC",
        shares=100,
        entry_price=0.60,
        stop_loss=0.55,
        target_price=0.66,
        entry_date=datetime.datetime(2026, 7, 28, 10, 0, 0),
        status="OPEN",
        tp1_hit=False,
    )
    bars = pd.DataFrame(
        {
            "Open": [0.65],
            "High": [0.68], # Touches TP1 (0.66)
            "Low": [0.64],
            "Close": [0.67], # Trailing SL at 2% = 0.6566
            "Volume": [50000],
        },
        index=[pd.Timestamp("2026-07-28 10:05:00")],
    )

    exit_notifications = []
    monkeypatch.setattr("core.AutoTrader.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_ENABLED", True, raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_TYPE", "PERCENT", raising=False)
    monkeypatch.setattr("core.AutoTrader.settings.TRAILING_STOP_VALUE", 2.0, raising=False)
    monkeypatch.setattr("core.AutoTrader.TimeUtils.now", lambda: datetime.datetime(2026, 7, 28, 10, 6, 0))
    monkeypatch.setattr("core.AutoTrader.DataManager.refresh_intraday_cache_if_due", lambda: False)
    monkeypatch.setattr("core.AutoTrader.DataManager.get_intraday_data", lambda *args, **kwargs: bars)
    monkeypatch.setattr("core.ConfluenceEngine.confluence_engine.get_active_trap", lambda ticker: None)
    monkeypatch.setattr(
        "core.AutoTrader._notify_exit",
        lambda ticker, exit_price, entry_price, reason, portfolio_id=None: exit_notifications.append(
            {"ticker": ticker, "exit_price": exit_price, "reason": reason, "portfolio_id": portfolio_id}
        ),
    )

    # First monitor cycle: TP1 should trigger
    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    # Verify: 50 shares sold, 50 remaining, tp1_hit=True, stop_loss moved to entry (0.60)
    updated_pos = Position.get(Position.id == position.id)
    assert updated_pos.shares == 50
    assert updated_pos.tp1_hit is True
    assert updated_pos.stop_loss == 0.60
    assert len(exit_notifications) == 1
    assert exit_notifications[0]["reason"] == "TARGET 1"
    assert exit_notifications[0]["ticker"] == "AIHC"

    trades = list(Trade.select().where(Trade.ticker == "AIHC"))
    assert len(trades) == 1
    assert trades[0].shares == 50
    assert trades[0].reason == "TARGET 1"

    # Second monitor cycle with same/higher price: TP1 must NOT trigger again!
    with pytest.deprecated_call(match="AutoTrader.monitor_positions is deprecated"):
        AutoTrader.monitor_positions()

    # Still 50 shares, tp1_hit remains True, trailing stop can move up from breakeven
    updated_pos_2 = Position.get(Position.id == position.id)
    assert updated_pos_2.shares == 50
    assert updated_pos_2.tp1_hit is True
    assert updated_pos_2.stop_loss >= 0.60
    # No duplicate exit notification sent!
    assert len(exit_notifications) == 1
    # Still only 1 trade record!
    assert Trade.select().where(Trade.ticker == "AIHC").count() == 1

