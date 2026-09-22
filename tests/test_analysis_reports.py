from core.settings import settings
import datetime

import pandas as pd
from fastapi.testclient import TestClient

from api import app
from core import TimeUtils
from database import Portfolio, PublishedSignalFollowUp, PublishedSignalLifecycle, Signal, SignalDelivery, SignalOutcome, SignalRecommendation, SignalRun
from routes.analysis_reports import _ANALYSIS_REPORT_CACHE

client = TestClient(app, raise_server_exceptions=False)


def _seed_signal_run_with_outcome(run_date: datetime.date):
    run = SignalRun.create(
        run_date=run_date,
        scan_type="DAILY",
        status="COMPLETED",
        universe_count=100,
        signals_count=8,
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=96.0,
        target_price=108.0,
        score=8.5,
        confidence=74.0,
        regime="CAUTIOUS",
    )
    SignalOutcome.create(
        recommendation=rec,
        run=run,
        ticker="COMI",
        outcome_status="CLOSED",
        pnl_pct=2.5,
    )
    return run


def test_get_weekly_analysis_report(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=3)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1020.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["period_type"] == "WEEKLY"
    assert body["period_end"] == run_date.isoformat()
    assert "market_summary" in body
    assert "signal_review" in body
    assert body["signal_review"]["run_count"] >= 1


def test_broadcast_monthly_analysis_report(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=10)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1015.0],
            }
        ),
    )
    monkeypatch.setattr(
        "core.TelegramBot_Alerts.send_message",
        lambda msg: {"ok": True, "result": {"message_id": 1}},
    )

    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "12345", raising=False)

    response = client.post(
        "/api/v1/reports/analysis/broadcast",
        json={"period": "monthly", "period_end": run_date.isoformat(), "force_refresh": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "sent"
    assert body["period_type"] == "MONTHLY"


def test_broadcast_partial_analysis_report_includes_warning_section(monkeypatch):
    run_date = datetime.date(2024, 10, 31)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(),
    )

    sent_messages = []
    monkeypatch.setattr(
        "core.TelegramBot_Alerts.send_message",
        lambda msg: sent_messages.append(msg) or {"ok": True, "result": {"message_id": 2}},
    )
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "12345", raising=False)

    response = client.post(
        "/api/v1/reports/analysis/broadcast",
        json={"period": "monthly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "sent"
    assert len(sent_messages) == 1
    assert "*Warnings*" in sent_messages[0]
    assert "benchmark context is unavailable" in sent_messages[0].lower()


def test_analysis_report_falls_back_to_legacy_signal_activity(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    Signal.create(
        ticker="COMI",
        date=run_date,
        signal_type="BUY",
        price=101.0,
        score=7.3,
        source="Scanner",
    )

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=2)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1005.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["signal_review"]["run_count"] >= 1
    assert body["signal_review"]["signals_generated"] >= 1
    assert any("legacy Signal table" in note for note in body.get("notes", []))


def test_analysis_report_returns_partial_when_benchmark_context_is_missing(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["signal_review"]["run_count"] >= 1
    assert any("Benchmark market return/volatility data is unavailable" in note for note in body.get("notes", []))
    assert any("benchmark context" in warning.lower() for warning in body.get("warnings", []))


def test_partial_analysis_report_is_cached_with_same_partial_status(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )

    calls = {"count": 0}

    def _missing_market_data(ticker, limit=520):
        calls["count"] += 1
        return pd.DataFrame()

    monkeypatch.setattr("routes.analysis_reports.DataManager.get_stock_data", _missing_market_data)

    first = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )
    second = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat()},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["status"] == "partial"
    assert second_body["status"] == "partial"
    assert second_body["cached"] is True
    assert calls["count"] == 1


def test_monthly_analysis_report_returns_partial_when_benchmark_context_is_missing(monkeypatch):
    run_date = datetime.date(2024, 10, 31)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "monthly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period_type"] == "MONTHLY"
    assert body["status"] == "partial"
    assert body["signal_review"]["run_count"] >= 1
    assert any("Benchmark market return/volatility data is unavailable" in note for note in body.get("notes", []))
    assert any("benchmark context" in warning.lower() for warning in body.get("warnings", []))


def test_partial_monthly_analysis_report_is_cached_with_same_partial_status(monkeypatch):
    run_date = datetime.date(2024, 10, 31)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )

    calls = {"count": 0}

    def _missing_market_data(ticker, limit=520):
        calls["count"] += 1
        return pd.DataFrame()

    monkeypatch.setattr("routes.analysis_reports.DataManager.get_stock_data", _missing_market_data)

    first = client.get(
        "/api/v1/reports/analysis",
        params={"period": "monthly", "period_end": run_date.isoformat(), "force_refresh": True},
    )
    second = client.get(
        "/api/v1/reports/analysis",
        params={"period": "monthly", "period_end": run_date.isoformat()},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["status"] == "partial"
    assert second_body["status"] == "partial"
    assert second_body["cached"] is True
    assert calls["count"] == 1


def test_analysis_report_stays_success_when_period_end_only_needs_trading_day_adjustment(monkeypatch):
    run_date = datetime.date(2024, 10, 17)
    _ANALYSIS_REPORT_CACHE.clear()
    for day in (
        datetime.date(2024, 10, 13),
        datetime.date(2024, 10, 14),
        datetime.date(2024, 10, 15),
        datetime.date(2024, 10, 16),
        run_date,
    ):
        _seed_signal_run_with_outcome(day)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=3)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1020.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": "2024-10-18", "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period_end"] == "2024-10-17"
    assert body["period_complete"] is True
    assert body["status"] == "success"
    assert any("period_end adjusted" in note for note in body.get("notes", []))


def test_monthly_analysis_report_returns_partial_when_daily_replay_coverage_is_thin(monkeypatch):
    run_date = datetime.date(2024, 10, 31)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=10)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1015.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "monthly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period_type"] == "MONTHLY"
    assert body["period_complete"] is True
    assert body["signal_review"]["run_count"] == 1
    assert body["status"] == "partial"
    assert any("daily replay coverage" in warning.lower() for warning in body.get("warnings", []))
    assert not any("benchmark context" in warning.lower() for warning in body.get("warnings", []))


def test_weekly_analysis_report_avoids_nan_volatility_for_single_return_window(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=1)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1010.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    volatility_context = body["market_summary"]["volatility_context"]
    assert "nan" not in volatility_context.lower()
    assert "limited benchmark history" in volatility_context.lower()


def test_broadcast_message_avoids_nan_volatility_for_single_return_window(monkeypatch):
    run_date = datetime.date(2024, 10, 16)
    _ANALYSIS_REPORT_CACHE.clear()
    _seed_signal_run_with_outcome(run_date)

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=1)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1010.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={"period": "weekly", "period_end": run_date.isoformat(), "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    from routes.analysis_reports import build_analysis_report_telegram_message

    message = build_analysis_report_telegram_message(body)
    assert "nan" not in message.lower()
    assert "limited benchmark history; volatility estimate unavailable." in message.lower()

    arabic_message = build_analysis_report_telegram_message(body, language="AR")
    assert "*تقرير حورس التحليلي الأسبوعي*" in arabic_message
    assert "هورس" not in arabic_message
    assert "*ملخص السوق*" in arabic_message
    assert "*مراجعة الإشارات*" in arabic_message
    assert "*HORUS WEEKLY ANALYSIS REPORT*" not in arabic_message


def test_portfolio_analysis_report_prefers_published_signal_lifecycle_metrics(monkeypatch):
    run_date = datetime.date(2026, 4, 8)
    _ANALYSIS_REPORT_CACHE.clear()

    horus = Portfolio.create(name="Horus", type="USER")
    run = SignalRun.create(
        run_date=run_date,
        scan_type="DAILY",
        run_key="2026-04-08:DAILY",
        status="COMPLETED",
        universe_count=120,
        signals_count=6,
        completed_at=datetime.datetime(2026, 4, 8, 15, 0, 0),
    )
    rec_win = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=108.0,
        score=9.1,
        confidence=82.0,
        regime="BULLISH",
    )
    rec_open = SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=50.0,
        stop_loss=47.5,
        target_price=56.0,
        score=8.8,
        confidence=76.0,
        regime="BULLISH",
    )
    rec_expired = SignalRecommendation.create(
        run=run,
        ticker="ORWE",
        side="BUY",
        entry_price=20.0,
        stop_loss=19.0,
        target_price=22.5,
        score=7.9,
        confidence=68.0,
        regime="CAUTIOUS",
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=horus,
        channel="TELEGRAM",
        status="SENT",
        sent_at=datetime.datetime(2026, 4, 8, 10, 0, 0),
    )

    PublishedSignalLifecycle.create(
        recommendation=rec_win,
        run=run,
        delivery=delivery,
        portfolio=horus,
        ticker="COMI",
        side="BUY",
        lane="SWING",
        source_module="SCANNER",
        operating_mode="AUTOPILOT",
        state="TP2_HIT",
        published_at=datetime.datetime(2026, 4, 8, 10, 0, 0),
        opened_at=datetime.datetime(2026, 4, 8, 12, 0, 0),
        tp1_hit_at=datetime.datetime(2026, 4, 8, 15, 0, 0),
        closed_at=datetime.datetime(2026, 4, 8, 20, 0, 0),
        entry_price_planned=100.0,
        entry_price_filled=100.0,
        stop_loss_initial=95.0,
        stop_loss_active=100.0,
        target_price_1=104.0,
        target_price_2=110.0,
        close_price=110.0,
        close_reason="TP2_HIT",
    )
    PublishedSignalLifecycle.create(
        recommendation=rec_open,
        run=run,
        delivery=delivery,
        portfolio=horus,
        ticker="HRHO",
        side="BUY",
        lane="INTRADAY",
        source_module="ORACLE",
        operating_mode="AI_ASSIST",
        state="OPEN",
        published_at=datetime.datetime(2026, 4, 8, 10, 30, 0),
        opened_at=datetime.datetime(2026, 4, 8, 11, 30, 0),
        entry_price_planned=50.0,
        entry_price_filled=50.0,
        stop_loss_initial=47.5,
        stop_loss_active=47.5,
        target_price_1=53.0,
        target_price_2=56.0,
    )
    PublishedSignalLifecycle.create(
        recommendation=rec_expired,
        run=run,
        delivery=delivery,
        portfolio=horus,
        ticker="ORWE",
        side="BUY",
        lane="POSITION",
        source_module="ANALYTICS",
        operating_mode="MANUAL",
        state="EXPIRED",
        published_at=datetime.datetime(2026, 4, 8, 9, 45, 0),
        expires_at=datetime.datetime(2026, 4, 9, 9, 45, 0),
        closed_at=datetime.datetime(2026, 4, 9, 9, 45, 0),
        entry_price_planned=20.0,
        stop_loss_initial=19.0,
        stop_loss_active=19.0,
        target_price_1=21.0,
        target_price_2=22.5,
        close_reason="EXPIRED",
    )
    PublishedSignalFollowUp.create(
        lifecycle=PublishedSignalLifecycle.get(PublishedSignalLifecycle.ticker == "COMI"),
        recommendation=rec_win,
        run=run,
        delivery=delivery,
        portfolio=horus,
        ticker="COMI",
        side="BUY",
        lane="SWING",
        source_module="SCANNER",
        operating_mode="AUTOPILOT",
        trigger_state="TP1_HIT",
        message_type="UPDATE",
        queue_state="SENT",
        retry_count=0,
        created_at=datetime.datetime(2026, 4, 8, 15, 0, 0),
        sent_at=datetime.datetime(2026, 4, 8, 15, 1, 0),
    )
    PublishedSignalFollowUp.create(
        lifecycle=PublishedSignalLifecycle.get(PublishedSignalLifecycle.ticker == "ORWE"),
        recommendation=rec_expired,
        run=run,
        delivery=delivery,
        portfolio=horus,
        ticker="ORWE",
        side="BUY",
        lane="POSITION",
        source_module="ANALYTICS",
        operating_mode="MANUAL",
        trigger_state="EXPIRED",
        message_type="CLOSE",
        queue_state="FAILED",
        retry_count=1,
        last_error="transport down",
        created_at=datetime.datetime(2026, 4, 8, 16, 0, 0),
    )

    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )
    monkeypatch.setattr(
        "routes.analysis_reports.DataManager.get_stock_data",
        lambda ticker, limit=520: pd.DataFrame(
            {
                "Date": [
                    (run_date - datetime.timedelta(days=1)).isoformat(),
                    run_date.isoformat(),
                ],
                "Close": [1000.0, 1010.0],
            }
        ),
    )

    response = client.get(
        "/api/v1/reports/analysis",
        params={
            "period": "weekly",
            "period_end": run_date.isoformat(),
            "portfolio_id": horus.id,
            "force_refresh": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    review = body["signal_review"]
    assert review["review_source"] == "PUBLISHED_LIFECYCLE"
    assert review["signals_generated"] == 3
    assert review["published_signals"] == 3
    assert review["closed_outcomes"] == 1
    assert review["open_outcomes"] == 1
    assert review["no_trade_outcomes"] == 1
    assert review["fill_rate_pct"] == 66.67
    assert review["tp1_hit_rate_pct"] == 33.33
    assert review["full_win_rate_pct"] == 33.33
    assert review["expiry_rate_pct"] == 33.33
    assert review["avg_time_to_open_hours"] == 1.5
    assert review["avg_time_to_resolution_hours"] == 17.0
    assert review["avg_pnl_pct"] == 10.0
    assert review["expectancy_pct"] == 3.3333
    assert review["followup_total"] == 2
    assert review["followup_sent_rate_pct"] == 50.0
    assert review["followup_failure_rate_pct"] == 50.0
    assert review["followup_avg_retry_count"] == 0.5
    assert review["followup_pending_count"] == 0
    assert review["followup_suppressed_count"] == 0
    assert review["lane_breakdown"][0]["key"] == "INTRADAY"
    assert any(item["key"] == "AUTOPILOT" for item in review["operating_mode_breakdown"])
    assert any("published Horus lifecycle records" in note for note in body.get("notes", []))
    assert any("lifecycle follow-up jobs" in note for note in body.get("notes", []))
