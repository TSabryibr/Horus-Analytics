from core.settings import settings
from core.exclusions import add_exclusion, remove_exclusion, save_exclusions
from fastapi.testclient import TestClient
from peewee import fn

from api import app
from database import (
    Portfolio,
    Position,
    Trade,
    Signal,
    SignalRun,
    SignalRecommendation,
    SignalOutcome,
    TickerStrategyMetrics,
)
from core import TimeUtils
client = TestClient(app, raise_server_exceptions=False)


def test_get_settings_returns_all_keys():
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    body = res.json()
    expected_keys = {
        "LOOKBACK",
        "VOL_SPIKE",
        "MOMENTUM",
        "RSI_MIN",
        "RSI_MAX",
        "SL_PCT",
        "TP1_PCT",
        "TRICKSTER_RSI_MAX",
        "TRICKSTER_REL_VOL_MIN",
        "TRICKSTER_STRETCH_ATR",
        "MIN_SIGNAL_SCORE",
        "MIN_SIGNAL_CONFIDENCE",
        "MAX_DAILY_TRADES",
        "MAX_PORTFOLIO_HEAT",
        "PENDING_ENTRY_MAX_GAP_PCT",
        "TRAILING_STOP_ENABLED",
        "TRAILING_STOP_TYPE",
        "TRAILING_STOP_VALUE",
        "SECTOR_LIMIT_ENABLED",
        "MAX_PER_SECTOR",
        "OLLAMA_API_KEY",
        "OLLAMA_API_KEY_CONFIGURED",
        "OLLAMA_BASE_URL",
        "AI_REPORT_OLLAMA_MODEL",
        "PINE_IMPORT_TRANSLATION_PROVIDER",
        "HISTORICAL_BACKFILL_TRADING_DAYS",
        "HEAT_PROTECTION_ENABLED",
        "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS",
        "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES",
        "PORTFOLIO_MGMT_TP2_PCT",
        "TELEGRAM_REPORT_LANGUAGE",
        "SIGNAL_AUTO_EXECUTION_ENABLED",
    }
    assert expected_keys.issubset(set(body.keys()))
    assert "AI_REPORT_PROVIDER" not in body
    assert "OPENAI_API_KEY" not in body
    assert "GEMINI_API_KEY" not in body
    assert "OPENROUTER_API_KEY" not in body


def test_get_settings_redacts_sensitive_runtime_values(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "1234567890:telegram-secret", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-1001234567890", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "987654321:test-secret", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_TEST_CHAT_ID", "-100999999", raising=False)
    monkeypatch.setattr(settings, "OLLAMA_API_KEY", "ollama-secret-key", raising=False)

    res = client.get("/api/v1/settings")

    assert res.status_code == 200
    body = res.json()
    for key in [
        "TELEGRAM_TOKEN",
        "CHAT_ID",
        "TELEGRAM_TEST_BOT_TOKEN",
        "TELEGRAM_TEST_CHAT_ID",
        "OLLAMA_API_KEY",
    ]:
        assert body[key] == ""
        assert "secret" not in str(body)

    assert body["TELEGRAM_TOKEN_CONFIGURED"] is True
    assert body["CHAT_ID_CONFIGURED"] is True
    assert body["TELEGRAM_TEST_BOT_TOKEN_CONFIGURED"] is True
    assert body["TELEGRAM_TEST_CHAT_ID_CONFIGURED"] is True
    assert body["OLLAMA_API_KEY_CONFIGURED"] is True
    assert body["TELEGRAM_TOKEN_PREVIEW"].startswith("1234")
    assert body["CHAT_ID_PREVIEW"].endswith("7890")


def test_update_settings_preserves_redacted_secret_fields(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "existing-main-token", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-1001234567890", raising=False)
    monkeypatch.setattr(settings, "OLLAMA_API_KEY", "existing-ollama-key", raising=False)

    def _capture(payload):
        captured.update(payload)
        return True

    monkeypatch.setattr(settings, "update", _capture)

    res = client.post(
        "/api/v1/settings",
        json={
            "LOOKBACK": 44,
            "TELEGRAM_TOKEN": "",
            "TELEGRAM_TOKEN_CONFIGURED": True,
            "CHAT_ID": "",
            "CHAT_ID_CONFIGURED": True,
            "OLLAMA_API_KEY": "",
            "OLLAMA_API_KEY_CONFIGURED": True,
        },
    )

    assert res.status_code == 200
    assert captured["LOOKBACK"] == 44
    assert "TELEGRAM_TOKEN" not in captured
    assert "CHAT_ID" not in captured
    assert "OLLAMA_API_KEY" not in captured


def test_get_settings_uses_mubasher_case_metastock_paths():
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    body = res.json()

    expected_history = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\History\CASE"
    expected_intraday = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE"

    assert body["METASTOCK_DAT_HISTORY_FOLDER"] == expected_history
    assert body["METASTOCK_DAT_INTRADAY_FOLDER"] == expected_intraday
    assert body["METASTOCK_INTRADAY_FOLDER"] == expected_intraday


def test_get_settings_reports_mubasher_stream_readiness(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    user_root = mubasher_root / "UserData" / "847857994"
    history_db = user_root / "History" / "CASE" / "history.db"
    intraday_db = user_root / "Intraday" / "CASE" / "INTRADAY_MASTER.db"
    historical_trade_dir = user_root / "HistoricalTrade" / "CASE"
    history_db.parent.mkdir(parents=True)
    intraday_db.parent.mkdir(parents=True)
    historical_trade_dir.mkdir(parents=True)
    history_db.touch()
    intraday_db.touch()
    (historical_trade_dir / "20260601.db").touch()

    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)

    res = client.get("/api/v1/settings")

    assert res.status_code == 200
    body = res.json()
    assert body["MUBASHER_ROOT_DIR"] == str(mubasher_root)
    assert body["MUBASHER_USER_ID"] == "847857994"
    assert body["MUBASHER_HISTORY_DB_PATH"] == str(history_db)
    assert body["MUBASHER_HISTORY_DB_AVAILABLE"] is True
    assert body["MUBASHER_INTRADAY_DB_PATH"] == str(intraday_db)
    assert body["MUBASHER_INTRADAY_DB_AVAILABLE"] is True
    assert body["MUBASHER_HISTORICAL_TRADE_FOLDER"] == str(historical_trade_dir)
    assert body["MUBASHER_HISTORICAL_TRADE_AVAILABLE"] is True
    assert body["MUBASHER_HISTORICAL_TRADE_DB_COUNT"] == 1
    assert body["MUBASHER_HISTORICAL_TRADE_LATEST_DATE"] == "20260601"


def test_update_settings_success(monkeypatch):
    monkeypatch.setattr(settings, "update", lambda payload: True)

    res = client.post("/api/v1/settings", json={"LOOKBACK": 45})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "updated"
    assert "settings" in body


def test_update_settings_accepts_pine_import_translation_provider(monkeypatch):
    captured = {}

    def _capture(payload):
        captured.update(payload)
        return True

    monkeypatch.setattr(settings, "update", _capture)

    res = client.post("/api/v1/settings", json={"PINE_IMPORT_TRANSLATION_PROVIDER": "OLLAMA"})

    assert res.status_code == 200
    assert captured["PINE_IMPORT_TRANSLATION_PROVIDER"] == "OLLAMA"


def test_update_settings_bad_value_returns_400(monkeypatch):
    monkeypatch.setattr(
        settings,
        "update",
        lambda payload: (_ for _ in ()).throw(ValueError("Invalid")),
    )

    res = client.post("/api/v1/settings", json={"LOOKBACK": -999})
    assert res.status_code == 400


def test_update_settings_rejects_invalid_signal_thresholds():
    res = client.post("/api/v1/settings", json={"MIN_SIGNAL_SCORE": 11})
    assert res.status_code == 400
    assert "MIN_SIGNAL_SCORE" in str(res.json().get("detail"))

    res = client.post("/api/v1/settings", json={"MIN_SIGNAL_CONFIDENCE": 101})
    assert res.status_code == 400
    assert "MIN_SIGNAL_CONFIDENCE" in str(res.json().get("detail"))


def test_get_telegram_config():
    res = client.get("/api/v1/telegram/config")
    assert res.status_code == 200
    body = res.json()
    assert "configured" in body
    assert "auto_ai_daily_report" in body
    assert "auto_weekly_report" in body
    assert "auto_monthly_report" in body
    assert body["report_language"] in {"EN", "AR"}


def test_update_telegram_config(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", False, raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT", False, raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT", False, raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN", raising=False)
    monkeypatch.setattr(settings, "save_settings", lambda *args, **kwargs: True)

    res = client.post(
        "/api/v1/telegram/config",
        json={
            "token": "abc123",
            "chat_id": "999",
            "auto_ai_daily_report": True,
            "auto_weekly_report": True,
            "auto_monthly_report": True,
            "report_language": "AR",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert settings.TELEGRAM_AUTO_BROADCAST_AI_REPORT is True
    assert settings.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT is True
    assert settings.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT is True
    assert settings.TELEGRAM_REPORT_LANGUAGE == "AR"


def test_update_telegram_config_rejects_invalid_report_language(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN", raising=False)

    res = client.post("/api/v1/telegram/config", json={"report_language": "FR"})

    assert res.status_code == 400
    assert "report_language must be EN or AR" in str(res.json()["detail"])
    assert settings.TELEGRAM_REPORT_LANGUAGE == "EN"


def test_get_exclusions():
    res = client.get("/api/v1/exclusions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_add_and_remove_exclusion(monkeypatch):
    added = set()
    removed = set()
    monkeypatch.setattr("routes.settings.add_exclusion", lambda t: added.add(t))
    monkeypatch.setattr("routes.settings.remove_exclusion", lambda t: removed.add(t))

    res_add = client.post("/api/v1/exclusions", json={"ticker": "test_ticker"})
    assert res_add.status_code == 200
    assert "TEST_TICKER" in added

    res_del = client.delete("/api/v1/exclusions/TEST_TICKER")
    assert res_del.status_code == 200
    assert "TEST_TICKER" in removed


def test_update_exclusions_purges_existing_blacklisted_rows(monkeypatch):
    monkeypatch.setattr("routes.settings.save_exclusions", lambda tickers: True)

    p = Portfolio.create(name="Settings Purge Portfolio", type="USER")
    Position.create(
        portfolio=p.id,
        ticker="Comi",
        shares=10,
        entry_price=10.0,
        stop_loss=9.0,
        target_price=11.0,
        current_price=10.0,
        status="OPEN",
    )
    Trade.create(
        portfolio=p.id,
        ticker="COMI",
        shares=10,
        entry_price=10.0,
        exit_price=11.0,
        entry_date=TimeUtils.now(),
        exit_date=TimeUtils.now(),
        pnl=10.0,
        pnl_pct=10.0,
    )
    Signal.create(ticker="comi", signal_type="BUY", price=10.0, score=8, source="Test")
    run = SignalRun.create(run_date=TimeUtils.today(), scan_type="DAILY", status="COMPLETED")
    rec = SignalRecommendation.create(
        run=run,
        ticker="CoMi",
        side="BUY",
        entry_price=10.0,
        stop_loss=9.0,
        target_price=11.0,
        score=8.0,
        confidence=80.0,
    )
    SignalOutcome.create(recommendation=rec, run=run, ticker="COMI")
    TickerStrategyMetrics.create(
        ticker="comi",
        window_days=90,
        total_signals=10,
        win_rate_pct=55.0,
        avg_gain_pct=2.0,
    )

    res = client.post("/api/v1/settings/exclusions", json=[" comi "])
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert body["tickers"] == ["COMI"]

    assert Position.select().where(fn.Upper(Position.ticker) == "COMI").count() == 0
    assert Trade.select().where(fn.Upper(Trade.ticker) == "COMI").count() == 0
    assert Signal.select().where(fn.Upper(Signal.ticker) == "COMI").count() == 0
    assert SignalRecommendation.select().where(fn.Upper(SignalRecommendation.ticker) == "COMI").count() == 0
    assert SignalOutcome.select().where(fn.Upper(SignalOutcome.ticker) == "COMI").count() == 0
    assert TickerStrategyMetrics.select().where(fn.Upper(TickerStrategyMetrics.ticker) == "COMI").count() == 0


def test_add_exclusion_purges_rows(monkeypatch):
    monkeypatch.setattr("routes.settings.add_exclusion", lambda ticker: True)

    p = Portfolio.create(name="Add Exclusion Purge Portfolio", type="USER")
    Position.create(
        portfolio=p.id,
        ticker="COMI",
        shares=5,
        entry_price=20.0,
        stop_loss=18.0,
        target_price=24.0,
        current_price=20.0,
        status="OPEN",
    )
    Position.create(
        portfolio=p.id,
        ticker="FWRY",
        shares=5,
        entry_price=20.0,
        stop_loss=18.0,
        target_price=24.0,
        current_price=20.0,
        status="OPEN",
    )

    res = client.post("/api/v1/exclusions", json={"ticker": "comi"})
    assert res.status_code == 200
    body = res.json()
    assert body["ticker"] == "COMI"

    assert Position.select().where(Position.ticker == "COMI").count() == 0
    assert Position.select().where(Position.ticker == "FWRY").count() == 1
