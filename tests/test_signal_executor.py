from core.settings import settings
import json

from database import (
    HorusExecution,
    Portfolio,
    Position,
    SignalAuditEvent,
    SignalExecutionAttribution,
    SignalRecommendation,
    SignalRun,
    Trade,
)


def test_signal_executor_execute_run_opens_intraday_recommendation(monkeypatch, caplog):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:00",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": 115.0, "source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._run_risk_gates", lambda portfolio, run, rec: (True, "allowed", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda signal_type: ("STRONG_BULL", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)

    add_calls = {}
    def _add_position(**kwargs):
        add_calls["payload"] = kwargs
        return True

    monkeypatch.setattr(
        "core.signals.executor.PositionTracker.add_position",
        _add_position,
    )
    monkeypatch.setattr("core.signals.executor.build_open_message", lambda portfolio, rec, shares, execution: "open")
    monkeypatch.setattr(
        "core.signals.executor.TelegramBot_Alerts.send_message",
        lambda message: {"ok": True, "result": {"message_id": 501}},
    )

    with caplog.at_level("INFO", logger="SignalExecutor"):
        result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 1, "updated": 0, "failed": 0, "skipped": 0, "pending": 0}
    assert add_calls["payload"]["ticker"] == "COMI"
    assert add_calls["payload"]["shares"] == 200
    assert add_calls["payload"]["portfolio_id"] is not None

    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    assert execution.state == "OPEN"
    assert execution.open_message_id == "501"
    attribution = SignalExecutionAttribution.get(SignalExecutionAttribution.execution == execution.id)
    assert attribution.execution_portfolio_id == execution.portfolio_id
    assert attribution.lane == "INTRADAY"
    assert attribution.strategy_portfolio_id is None
    assert Position.select().count() == 0
    assert f"execute_run start run_id={run.id}" in caplog.text
    assert f"ticker={rec.ticker} action=OPEN_NEW" in caplog.text
    assert f"ticker={rec.ticker} action=OPENED execution_id={execution.id}" in caplog.text


def test_signal_executor_suppresses_main_channel_open_when_signal_level_none(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:05",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": 115.0, "source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none", raising=False)
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._run_risk_gates", lambda portfolio, run, rec: (True, "allowed", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda signal_type: ("STRONG_BULL", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)
    monkeypatch.setattr("core.signals.executor.PositionTracker.add_position", lambda **kwargs: True)
    monkeypatch.setattr("core.signals.executor.build_open_message", lambda portfolio, rec, shares, execution: "open")
    monkeypatch.setattr(
        "core.signals.executor.TelegramBot_Alerts.send_message",
        lambda message: (_ for _ in ()).throw(AssertionError("main channel open alert should not be sent")),
    )

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"]["opened"] == 1
    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    assert execution.state == "OPEN"
    assert execution.open_message_id is None


def test_signal_executor_skips_cross_portfolio_duplicate_signal(monkeypatch, caplog):
    from core.signals.executor import SignalExecutor

    intraday = Portfolio.get(Portfolio.name == "Intraday Signals")
    swing = Portfolio.get(Portfolio.name == "Swing Signals")
    Position.create(
        portfolio=swing,
        ticker="BONY",
        shares=1000,
        entry_price=5.21,
        stop_loss=5.21,
        target_price=5.6015,
        target_price_2=5.8256,
        tp1_hit=True,
        status="OPEN",
    )
    run = SignalRun.create(
        run_date="2026-05-25",
        scan_type="INTRADAY",
        run_key="2026-05-25:INTRADAY:12:53",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="BONY",
        side="BUY",
        entry_price=5.62,
        stop_loss=5.296,
        target_price=6.052,
        score=9,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._run_risk_gates", lambda portfolio, run, rec: (True, "allowed", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)
    monkeypatch.setattr(
        "core.signals.executor.PositionTracker.add_position",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("duplicate signal opened a new position")),
    )

    with caplog.at_level("INFO", logger="SignalExecutor"):
        result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 0, "updated": 0, "failed": 0, "skipped": 1, "pending": 0}
    assert Position.select().where((Position.portfolio == intraday) & (Position.ticker == "BONY")).count() == 0

    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    assert execution.state == "SKIPPED"
    details = json.loads(execution.details_json)
    assert details["reason"] == "cross_portfolio_duplicate_open"
    assert details["existing_portfolio"] == "Swing Signals"
    assert "cross_portfolio_duplicate_open" in caplog.text


def test_signal_executor_skips_update_for_tp1_managed_position(monkeypatch, caplog):
    from core.signals.executor import SignalExecutor

    intraday = Portfolio.get(Portfolio.name == "Intraday Signals")
    position = Position.create(
        portfolio=intraday,
        ticker="BONY",
        shares=9542,
        entry_price=5.14,
        stop_loss=5.14,
        target_price=5.6015,
        target_price_2=5.8256,
        tp1_hit=True,
        status="OPEN",
    )
    run = SignalRun.create(
        run_date="2026-05-25",
        scan_type="INTRADAY",
        run_key="2026-05-25:INTRADAY:12:48",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="BONY",
        side="BUY",
        entry_price=5.62,
        stop_loss=5.296,
        target_price=6.052,
        score=9,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": 6.2941, "source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._run_risk_gates", lambda portfolio, run, rec: (True, "allowed", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)
    monkeypatch.setattr(
        "core.signals.executor.PositionTracker.update_position",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("managed position should not be rewritten")),
    )

    with caplog.at_level("INFO", logger="SignalExecutor"):
        result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 0, "updated": 0, "failed": 0, "skipped": 1, "pending": 0}

    position = Position.get_by_id(position.id)
    assert position.stop_loss == 5.14
    assert position.target_price == 5.6015

    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    details = json.loads(execution.details_json)
    assert execution.state == "SKIPPED"
    assert details["reason"] == "existing_position_already_managed_after_tp1"
    assert details["previous"]["stop_loss"] == 5.14
    assert details["requested"]["stop_loss"] == 5.296
    assert "existing_position_already_managed_after_tp1" in caplog.text


def test_signal_executor_execute_run_skips_when_live_guard_not_armed(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:30",
        status="COMPLETED",
    )
    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_ARM_GUARD_ENABLED", True, raising=False)
    SignalExecutor._HEAT_BLOCK_LOG_STATE.clear()
    settings.disarm_live_execution()

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "skipped"
    assert "not armed" in result["message"].lower()


def test_signal_executor_suppresses_repeated_live_guard_warning_noise(monkeypatch, caplog):
    from core.signals.executor import SignalExecutor

    first_run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:40",
        status="COMPLETED",
    )
    second_run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:45",
        status="COMPLETED",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_ARM_GUARD_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "core.signals.executor.TimeUtils.today",
        lambda: __import__("datetime").date(2026, 5, 2),
    )
    settings.disarm_live_execution()
    SignalExecutor._LIVE_GUARD_LOG_STATE.clear()

    with caplog.at_level("INFO", logger="SignalExecutor"):
        SignalExecutor.execute_run(first_run.id)
        SignalExecutor.execute_run(second_run.id)
        SignalExecutor.execute_pending_entries()
        SignalExecutor.execute_pending_entries()

    warning_messages = [record.getMessage() for record in caplog.records if record.levelname == "WARNING"]
    assert sum("Live execution guard blocked" in msg for msg in warning_messages) == 1
    assert sum("Pending entries blocked by live execution guard" in msg for msg in warning_messages) == 1
    assert "repeat_count=2" in caplog.text


def test_signal_executor_execute_run_skips_invalid_buy_risk_reward(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:32",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=101.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )
    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.MIN_RISK_REWARD", 1.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"]["skipped"] == 1
    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    assert execution.state == "SKIPPED"
    details = json.loads(execution.details_json or "{}")
    assert details.get("reason") == "invalid_risk_reward"


def test_signal_executor_execute_run_allows_when_live_guard_armed(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:35",
        status="COMPLETED",
    )
    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_ARM_GUARD_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.TimeUtils.today", lambda: __import__("datetime").date(2026, 5, 2))
    settings.arm_live_execution(__import__("datetime").date(2026, 5, 2))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 0, "updated": 0, "failed": 0, "skipped": 0, "pending": 0}


def test_signal_executor_market_open_delegates_to_settings(monkeypatch):
    from core.signals.executor import SignalExecutor

    monkeypatch.setattr("core.signals.executor.settings.is_market_open", lambda: False, raising=False)
    assert SignalExecutor._is_market_open() is False
    monkeypatch.setattr("core.signals.executor.settings.is_market_open", lambda: True, raising=False)
    assert SignalExecutor._is_market_open() is True


def test_signal_executor_correlation_check_failure_blocks(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    monkeypatch.setattr(
        "core.signals.executor.RiskManager.check_new_trade_correlation",
        lambda open_tickers, ticker: (_ for _ in ()).throw(RuntimeError("corr down")),
    )

    allowed, reason, data = SignalExecutor._check_correlation(portfolio, "COMI")

    assert allowed is False
    assert reason == "check_failed"
    assert "corr down" in str(data.get("error", ""))


def test_signal_executor_macro_lookup_failure_blocks_buy(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:33",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_entry_gate", lambda ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_whale_trap", lambda rec: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sovereign_confluence", lambda ticker, side: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_correlation", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_velocity_limit", lambda portfolio: (True, "ok"))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda side: ("UNKNOWN", {"error": "market data unavailable"}))
    monkeypatch.setattr("core.signals.executor.settings.REGIME_FILTER_ENABLED", True, raising=False)

    allowed, reason, data = SignalExecutor._run_risk_gates(portfolio, run, rec)

    assert allowed is False
    assert reason == "macro_regime_unavailable"
    assert "market data unavailable" in str(data.get("error", ""))


def test_signal_executor_allows_choppy_buy_when_regime_filter_disabled(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:34",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )
    monkeypatch.setattr("core.signals.executor.settings.REGIME_FILTER_ENABLED", False, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_nonzero_cost_assumptions", lambda: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_entry_gate", lambda ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_whale_trap", lambda rec: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sovereign_confluence", lambda ticker, side: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_correlation", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sector_limit", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_velocity_limit", lambda portfolio: (True, "ok"))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda side: ("CHOPPY_OR_BEAR", {"close": 90}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_live_risk_contract", lambda **kwargs: (True, "ok", {}))

    allowed, reason, data = SignalExecutor._run_risk_gates(portfolio, run, rec)

    assert allowed is True
    assert reason == "allowed"
    assert data == {}


def test_signal_executor_blocks_choppy_buy_when_regime_filter_enabled(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:35",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )
    monkeypatch.setattr("core.signals.executor.settings.REGIME_FILTER_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_nonzero_cost_assumptions", lambda: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_entry_gate", lambda ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_whale_trap", lambda rec: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sovereign_confluence", lambda ticker, side: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_correlation", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sector_limit", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_velocity_limit", lambda portfolio: (True, "ok"))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda side: ("CHOPPY_OR_BEAR", {"close": 90}))

    allowed, reason, data = SignalExecutor._run_risk_gates(portfolio, run, rec)

    assert allowed is False
    assert reason == "macro_regime_blocked"
    assert data["close"] == 90


def test_signal_executor_invalid_risk_distance_returns_zero_shares():
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    shares = SignalExecutor._calculate_shares(
        portfolio=portfolio,
        price=100.0,
        sl=100.0,
        regime="STRONG_BULL",
        signal_type="BUY",
    )
    assert shares == 0


def test_signal_executor_pending_entry_uses_funded_portfolio_when_global_balance_is_zero(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")
    portfolio.cash_egp = 500000.0
    portfolio.save()
    run = SignalRun.create(
        run_date="2026-05-04",
        scan_type="DAILY",
        run_key="2026-05-04:DAILY",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": 115.0, "source": "BUY"}),
        state="ACTIVE",
    )
    execution = HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=rec,
        ticker=rec.ticker,
        state="PENDING_OPEN",
        trigger_source="DAILY_NEXT_OPEN",
        planned_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
        details_json=json.dumps({"trigger_source": "DAILY_NEXT_OPEN"}),
    )
    SignalExecutionAttribution.create(
        execution=execution,
        execution_portfolio=portfolio,
        strategy_portfolio=None,
        recommendation=rec,
        run=run,
        lane="SWING",
        scan_type="DAILY",
        signal_side="BUY",
        signal_state="PENDING_OPEN",
        details_json="{}",
    )

    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 0.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr("core.signals.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda signal_type: ("STRONG_BULL", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._get_next_open_price", lambda ticker: (100.0, "2026-05-04T10:00:00"))

    add_calls = {}

    def _add_position(**kwargs):
        add_calls["payload"] = kwargs
        return True

    monkeypatch.setattr("core.signals.executor.PositionTracker.add_position", _add_position)
    monkeypatch.setattr("core.signals.executor.build_open_message", lambda portfolio, rec, shares, execution: "open")
    monkeypatch.setattr(
        "core.signals.executor.TelegramBot_Alerts.send_message",
        lambda message: {"ok": True, "result": {"message_id": 502}},
    )

    result = SignalExecutor.execute_pending_entries()

    assert result["summary"] == {"opened": 1, "skipped": 0, "failed": 0}
    assert add_calls["payload"]["shares"] == 1000
    assert add_calls["payload"]["portfolio_id"] == portfolio.id
    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "OPEN"
    assert execution.open_message_id == "502"
    attribution = SignalExecutionAttribution.get(SignalExecutionAttribution.execution == execution.id)
    assert attribution.execution_portfolio_id == portfolio.id
    assert attribution.lane == "SWING"
    assert attribution.signal_state == "OPEN"


def test_signal_executor_pending_entries_skip_when_cash_capacity_exceeded(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")
    portfolio.cash_egp = 100.0
    portfolio.save()
    run = SignalRun.create(
        run_date="2026-05-04",
        scan_type="DAILY",
        run_key="2026-05-04:DAILY",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": 115.0, "source": "BUY"}),
        state="ACTIVE",
    )
    execution = HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=rec,
        ticker=rec.ticker,
        state="PENDING_OPEN",
        trigger_source="DAILY_NEXT_OPEN",
        planned_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
        details_json=json.dumps({"trigger_source": "DAILY_NEXT_OPEN"}),
    )

    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 500000.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda signal_type: ("STRONG_BULL", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._get_next_open_price", lambda ticker: (100.0, "2026-05-04T10:00:00"))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_live_risk_contract", lambda **kwargs: (True, "ok", {}))
    monkeypatch.setattr(
        "core.signals.executor.PositionTracker.add_position",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("cash-blocked pending entry must not open")),
    )

    result = SignalExecutor.execute_pending_entries()

    assert result["summary"] == {"opened": 0, "skipped": 1, "failed": 0}
    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "SKIPPED"
    details = json.loads(execution.details_json or "{}")
    assert details["reason"] == "cash_capacity_limit"
    assert details["capacity"]["available_cash"] == 100.0


def test_signal_executor_suppresses_repeated_heat_alert_noise(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:05",
        status="COMPLETED",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr(
        "core.signals.executor.SignalExecutor._check_portfolio_heat",
        lambda portfolio: (False, "heat_limit_reached", 7.96),
    )
    monkeypatch.setattr(
        "core.signals.executor.TimeUtils.today",
        lambda: __import__("datetime").date(2026, 5, 2),
    )

    critical_logs = []
    warning_logs = []
    alerts = []
    monkeypatch.setattr("core.signals.executor.logger.critical", lambda msg: critical_logs.append(msg))
    monkeypatch.setattr("core.signals.executor.logger.warning", lambda msg: warning_logs.append(msg))
    monkeypatch.setattr("core.signals.executor.AlertManager.broadcast_alert", lambda msg: alerts.append(msg) or {"ok": True})
    SignalExecutor._HEAT_BLOCK_LOG_STATE.clear()

    first = SignalExecutor.execute_run(run.id)
    second = SignalExecutor.execute_run(run.id)

    assert first["status"] == "blocked"
    assert second["status"] == "blocked"
    assert len(critical_logs) == 1
    assert len(warning_logs) == 1
    assert "repeat_count=2" in warning_logs[0]
    assert len(alerts) == 1


def test_signal_executor_blocks_heat_alert_from_type_1_main_channel(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")

    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(
        "core.signals.executor.TimeUtils.today",
        lambda: __import__("datetime").date(2026, 6, 3),
    )

    alerts = []
    monkeypatch.setattr("core.signals.executor.AlertManager.broadcast_alert", lambda msg: alerts.append(msg) or {"ok": True})
    SignalExecutor._HEAT_BLOCK_LOG_STATE.clear()

    SignalExecutor._record_heat_block(portfolio, "portfolio_heat_limit", 6.94)

    assert alerts == []


def test_signal_executor_allows_heat_alert_for_type_3_main_channel(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")

    monkeypatch.setattr("core.signals.executor.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr(
        "core.signals.executor.TimeUtils.today",
        lambda: __import__("datetime").date(2026, 6, 3),
    )

    alerts = []
    monkeypatch.setattr("core.signals.executor.AlertManager.broadcast_alert", lambda msg: alerts.append(msg) or {"ok": True})
    SignalExecutor._HEAT_BLOCK_LOG_STATE.clear()

    SignalExecutor._record_heat_block(portfolio, "portfolio_heat_limit", 6.94)

    assert len(alerts) == 1
    assert "PORTFOLIO HEAT LIMIT REACHED" in alerts[0]


def test_signal_executor_keeps_lane_execution_and_adds_strategy_attribution(monkeypatch):
    from core.signals.executor import SignalExecutor

    strategy_portfolio = Portfolio.create(
        name="EGX Breakout Pine",
        type="STRATEGY",
        auto_manage=True,
        description="Auto-managed strategy profile portfolio",
    )
    intraday_portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    run = SignalRun.create(
        run_date="2026-05-02",
        scan_type="INTRADAY",
        run_key="2026-05-02:INTRADAY:11:10",
        status="COMPLETED",
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps(
            {
                "target_price_2": 115.0,
                "source": "BUY",
                "strategy_profile_name": "EGX Breakout Pine",
            }
        ),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._run_risk_gates", lambda portfolio, run, rec: (True, "allowed", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_macro_regime", lambda signal_type: ("STRONG_BULL", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._is_market_open", lambda: True)
    monkeypatch.setattr("core.signals.executor.build_open_message", lambda portfolio, rec, shares, execution: "open")
    monkeypatch.setattr(
        "core.signals.executor.TelegramBot_Alerts.send_message",
        lambda message: {"ok": True, "result": {"message_id": 503}},
    )

    add_calls = {}

    def _add_position(**kwargs):
        add_calls["payload"] = kwargs
        return True

    monkeypatch.setattr("core.signals.executor.PositionTracker.add_position", _add_position)

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert add_calls["payload"]["portfolio_id"] == intraday_portfolio.id

    execution = HorusExecution.select().order_by(HorusExecution.id.desc()).first()
    attribution = SignalExecutionAttribution.get(SignalExecutionAttribution.execution == execution.id)
    assert attribution.execution_portfolio_id == intraday_portfolio.id
    assert attribution.strategy_portfolio_id == strategy_portfolio.id
    assert attribution.strategy_profile_name == "EGX Breakout Pine"


def test_signal_executor_skips_portfolio_heat_when_protection_disabled(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")

    monkeypatch.setattr("core.signals.executor.settings.HEAT_PROTECTION_ENABLED", False, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.MAX_PORTFOLIO_HEAT", 6.0, raising=False)
    monkeypatch.setattr(
        "core.signals.executor.RiskManager.calculate_portfolio_heat",
        lambda heat_input, account_size: 99.0,
    )

    allowed, reason, heat = SignalExecutor._check_portfolio_heat(portfolio)

    assert allowed is True
    assert reason == "heat_protection_disabled"
    assert heat == 0.0


def test_signal_executor_blocks_when_execution_cost_assumptions_are_zero(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-03",
        scan_type="INTRADAY",
        run_key="2026-05-03:INTRADAY:11:00",
        status="COMPLETED",
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=7.5,
        confidence=75.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.COMMISSION_PCT", 0.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.SLIPPAGE_PCT", 0.1, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"]["skipped"] == 1
    execution = HorusExecution.select().order_by(HorusExecution.id.desc()).first()
    details = json.loads(execution.details_json or "{}")
    assert "cost_commission_non_positive" in str(details.get("reason", ""))


def test_signal_executor_live_risk_contract_blocks_daily_loss_breach(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    Trade.create(
        portfolio=portfolio,
        ticker="COMI",
        shares=100,
        entry_price=100.0,
        exit_price=80.0,
        entry_date=__import__("datetime").datetime(2026, 5, 3, 10, 0, 0),
        exit_date=__import__("datetime").datetime(2026, 5, 3, 11, 0, 0),
        pnl=-2000.0,
        pnl_pct=-20.0,
        reason="STOP_LOSS",
    )
    monkeypatch.setattr("core.signals.executor.TimeUtils.now", lambda: __import__("datetime").datetime(2026, 5, 3, 12, 0, 0))
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.COMMISSION_PCT", 0.05, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.SLIPPAGE_PCT", 0.1, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_MAX_DAILY_LOSS_PCT", 1.0, raising=False)

    allowed, reason, data = SignalExecutor._check_live_risk_contract(
        portfolio=portfolio,
        ticker="COMI",
        entry_price=100.0,
        stop_loss=95.0,
        shares=100,
    )

    assert allowed is False
    assert reason == "daily_loss_limit"
    assert float(data.get("daily_loss_pct", 0.0)) >= 1.0


def test_signal_executor_operator_lockout_blocks_after_manual_override_abuse(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    monkeypatch.setattr("core.signals.executor.settings.LIVE_MAX_DAILY_LOSS_PCT", 99.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_MAX_CONSECUTIVE_LOSSES", 99, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.LIVE_MAX_MANUAL_OVERRIDES_PER_DAY", 1, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.ACCOUNT_BALANCE", 100000.0, raising=False)
    SignalAuditEvent.create(
        event_type="OPERATOR_MANUAL_OVERRIDE",
        severity="INFO",
        actor_type="OPERATOR",
        portfolio=portfolio,
        message="manual override test event",
        details_json="{}",
    )

    allowed, reason, data = SignalExecutor._check_operator_lockout(portfolio)

    assert allowed is False
    assert reason == "manual_override_abuse"
    assert data["manual_override_state"]["manual_override_lockout"] is True


def test_signal_executor_pending_entries_uses_settings_gap_threshold(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")
    run = SignalRun.create(
        run_date="2026-05-05",
        scan_type="DAILY",
        run_key="2026-05-05:DAILY",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )
    execution = HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=rec,
        ticker=rec.ticker,
        state="PENDING_OPEN",
        trigger_source="DAILY_NEXT_OPEN",
        planned_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
        details_json=json.dumps({"trigger_source": "DAILY_NEXT_OPEN"}),
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.PENDING_ENTRY_MAX_GAP_PCT", 0.5, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._get_next_open_price", lambda ticker: (101.0, "2026-05-05T10:00:00"))
    monkeypatch.setattr("core.signals.executor.TelegramBot_Alerts.send_message", lambda message: {"ok": True})

    result = SignalExecutor.execute_pending_entries()

    assert result["status"] == "completed"
    assert result["summary"]["skipped"] == 1
    updated = HorusExecution.get_by_id(execution.id)
    assert updated.state == "SKIPPED"
    details = json.loads(updated.details_json or "{}")
    assert details.get("reason") == "gap_threshold_exceeded"


def test_signal_executor_run_risk_gates_blocks_sector_limit(monkeypatch):
    from core.signals.executor import SignalExecutor

    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    run = SignalRun.create(
        run_date="2026-05-06",
        scan_type="INTRADAY",
        run_key="2026-05-06:INTRADAY:11:11",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_nonzero_cost_assumptions", lambda: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_entry_gate", lambda ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_whale_trap", lambda rec: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sovereign_confluence", lambda ticker, side: True)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_correlation", lambda portfolio, ticker: (True, "ok", {}))
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_sector_limit", lambda portfolio, ticker: (False, "limit_exceeded", {"warning": "Sector Limit Exceeded"}))

    allowed, reason, data = SignalExecutor._run_risk_gates(portfolio, run, rec)

    assert allowed is False
    assert reason == "sector_limit_exceeded"
    assert "warning" in data


def test_signal_executor_execute_run_skips_when_signal_score_below_threshold(monkeypatch):
    from core.signals.executor import SignalExecutor

    run = SignalRun.create(
        run_date="2026-05-07",
        scan_type="INTRADAY",
        run_key="2026-05-07:INTRADAY:12:00",
        status="COMPLETED",
    )
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=7.0,
        confidence=80.0,
        rationale_json=json.dumps({"source": "BUY"}),
        state="ACTIVE",
    )

    monkeypatch.setattr("core.signals.executor.settings.AUTO_TRADE_ENABLED", True, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.MIN_SIGNAL_SCORE", 8.0, raising=False)
    monkeypatch.setattr("core.signals.executor.settings.MIN_SIGNAL_CONFIDENCE", 0.0, raising=False)
    monkeypatch.setattr("core.signals.executor.SignalExecutor._check_portfolio_heat", lambda portfolio: (True, "ok", 0.0))

    result = SignalExecutor.execute_run(run.id)

    assert result["status"] == "completed"
    assert result["summary"]["skipped"] == 1
    execution = HorusExecution.get(HorusExecution.recommendation == rec)
    details = json.loads(execution.details_json or "{}")
    assert details.get("reason") == "below_min_signal_score"
