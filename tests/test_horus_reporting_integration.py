import datetime

import pandas as pd

from database import Portfolio, Position, SignalDelivery, SignalRecommendation, SignalRun, Trade
from routes import ai_report, analysis_reports


def test_ai_report_portfolio_snapshot_defaults_to_horus():
    my_portfolio = Portfolio.create(name="My Portfolio", type="USER")
    horus = Portfolio.create(name="Horus", type="USER")

    Position.create(
        portfolio=my_portfolio,
        ticker="SWDY",
        shares=50,
        entry_price=20.0,
        stop_loss=18.0,
        target_price=24.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 4, 1, 10, 0, 0),
    )
    Position.create(
        portfolio=horus,
        ticker="COMI",
        shares=100,
        entry_price=80.0,
        stop_loss=76.0,
        target_price=88.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 4, 1, 10, 0, 0),
    )

    snapshot = ai_report._collect_portfolio_snapshot(None)

    assert snapshot["portfolio_id"] == horus.id
    assert snapshot["portfolio_name"] == "Horus"
    assert snapshot["open_positions"] == 1
    assert snapshot["top_positions"][0]["ticker"] == "COMI"


def test_analysis_report_defaults_to_horus_and_uses_portfolio_scoped_trade_metrics(monkeypatch):
    analysis_reports._ANALYSIS_REPORT_CACHE.clear()

    my_portfolio = Portfolio.create(name="My Portfolio", type="USER")
    horus = Portfolio.create(name="Horus", type="USER")
    run_date = datetime.date(2026, 4, 8)

    run = SignalRun.create(
        run_date=run_date,
        scan_type="DAILY",
        run_key="2026-04-08:DAILY",
        status="COMPLETED",
        universe_count=100,
        signals_count=4,
        completed_at=datetime.datetime(2026, 4, 8, 15, 0, 0),
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=96.0,
        target_price=110.0,
        score=8.5,
        confidence=80.0,
        regime="BULLISH",
        state="ACTIVE",
    )
    SignalDelivery.create(run=run, portfolio=horus, channel="TELEGRAM", status="SENT")
    SignalDelivery.create(run=run, portfolio=my_portfolio, channel="TELEGRAM", status="SENT")

    Trade.create(
        portfolio=horus,
        ticker="COMI",
        shares=100,
        entry_price=100.0,
        exit_price=108.0,
        entry_date=datetime.datetime(2026, 4, 8, 11, 0, 0),
        exit_date=datetime.datetime(2026, 4, 8, 13, 0, 0),
        pnl=800.0,
        pnl_pct=8.0,
        reason="TARGET",
    )
    Trade.create(
        portfolio=my_portfolio,
        ticker="COMI",
        shares=100,
        entry_price=100.0,
        exit_price=95.0,
        entry_date=datetime.datetime(2026, 4, 8, 11, 0, 0),
        exit_date=datetime.datetime(2026, 4, 8, 13, 0, 0),
        pnl=-500.0,
        pnl_pct=-5.0,
        reason="STOP_LOSS",
    )

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {"Date": [(run_date - datetime.timedelta(days=1)).isoformat(), run_date.isoformat()], "Close": [1000.0, 1010.0]}
        ),
    )

    payload = analysis_reports.build_analysis_report(period="weekly", period_end=run_date.isoformat(), force_refresh=True)

    assert payload["portfolio"]["id"] == horus.id
    assert payload["portfolio"]["name"] == "Horus"
    assert payload["signal_review"]["closed_outcomes"] == 1
    assert payload["signal_review"]["avg_pnl_pct"] == 8.0
    assert payload["signal_review"]["win_rate_pct"] == 100.0
    assert payload["recommendations"][0]["ticker"] == rec.ticker


def test_analysis_report_cache_is_scoped_by_resolved_portfolio(monkeypatch):
    analysis_reports._ANALYSIS_REPORT_CACHE.clear()

    my_portfolio = Portfolio.create(name="My Portfolio", type="USER")
    horus = Portfolio.create(name="Horus", type="USER")
    run_date = datetime.date(2026, 4, 8)

    run = SignalRun.create(
        run_date=run_date,
        scan_type="DAILY",
        run_key="2026-04-08:DAILY",
        status="COMPLETED",
        universe_count=100,
        signals_count=2,
        completed_at=datetime.datetime(2026, 4, 8, 15, 0, 0),
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=96.0,
        target_price=110.0,
        score=8.5,
        confidence=80.0,
        regime="BULLISH",
        state="ACTIVE",
    )
    SignalDelivery.create(run=run, portfolio=horus, channel="TELEGRAM", status="SENT")
    SignalDelivery.create(run=run, portfolio=my_portfolio, channel="TELEGRAM", status="SENT")

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {"Date": [(run_date - datetime.timedelta(days=1)).isoformat(), run_date.isoformat()], "Close": [1000.0, 1010.0]}
        ),
    )

    analysis_reports.build_analysis_report(period="weekly", period_end=run_date.isoformat(), force_refresh=True)
    analysis_reports.build_analysis_report(period="weekly", period_end=run_date.isoformat(), portfolio_id=my_portfolio.id, force_refresh=True)

    assert any(key.endswith(f":{horus.id}") for key in analysis_reports._ANALYSIS_REPORT_CACHE)
    assert any(key.endswith(f":{my_portfolio.id}") for key in analysis_reports._ANALYSIS_REPORT_CACHE)
