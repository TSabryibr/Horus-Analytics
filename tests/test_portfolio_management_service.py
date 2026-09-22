from core.settings import settings
from core.exclusions import is_excluded_ticker, assert_ticker_allowed
from fastapi.testclient import TestClient

from api import app
from database import Portfolio, Position, Trade

client = TestClient(app, raise_server_exceptions=False)


def test_portfolio_management_intake_and_report_builds_tp2(monkeypatch):
    monkeypatch.setenv("SIGNAL_TP2_PCT", "4")
    monkeypatch.setattr(
        "routes.portfolio.WalkForwardValidation.get_trade_permission",
        lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
    )
    monkeypatch.setattr("routes.portfolio.is_excluded_ticker", lambda x: False)

    p = Portfolio.create(name="Managed Service A", type="USER")
    intake = client.post(
        "/api/v1/portfolio/management/intake",
        json={
            "portfolio_id": p.id,
            "holdings": [
                {
                    "ticker": "COMI",
                    "shares": 100,
                    "entry_price": 10.0,
                    "stop_loss": 9.5,
                    "target_price": 11.0,
                    "notes": "VIP client intake",
                }
            ],
        },
    )
    assert intake.status_code == 200
    body = intake.json()
    assert body["status"] == "completed", body
    assert body["created"] == 1, body
    assert body["updated"] == 0, body

    report = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}")
    assert report.status_code == 200
    r = report.json()
    assert r["portfolio"]["id"] == p.id
    assert r["summary"]["open_positions"] == 1
    assert len(r["positions"]) == 1
    pos = r["positions"][0]
    assert pos["ticker"] == "COMI"
    assert pos["target_price_2"] > pos["target_price"]


def test_portfolio_management_intake_supports_total_cost(monkeypatch):
    monkeypatch.setenv("SIGNAL_TP2_PCT", "4")
    monkeypatch.setattr(
        "routes.portfolio.WalkForwardValidation.get_trade_permission",
        lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
    )
    monkeypatch.setattr("routes.portfolio.is_excluded_ticker", lambda x: False)
    p = Portfolio.create(name="Managed Service B", type="USER")

    intake = client.post(
        "/api/v1/portfolio/management/intake",
        json={
            "portfolio_id": p.id,
            "holdings": [
                {
                    "ticker": "FWRY",
                    "shares": 200,
                    "total_cost": 1000.0,
                }
            ],
        },
    )
    assert intake.status_code == 200
    pos = Position.get(Position.ticker == "FWRY", Position.portfolio == p.id, Position.status == "OPEN")
    assert abs(float(pos.entry_price) - 5.0) < 1e-9
    assert int(pos.shares) == 200


def test_portfolio_management_tp2_uses_settings_control(monkeypatch):
    monkeypatch.setattr("routes.portfolio.settings.PORTFOLIO_MGMT_TP2_PCT", 12.0, raising=False)
    monkeypatch.setattr(
        "routes.portfolio.WalkForwardValidation.get_trade_permission",
        lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
    )
    monkeypatch.setattr("routes.portfolio.is_excluded_ticker", lambda x: False)

    p = Portfolio.create(name="Managed Service TP2", type="USER")
    intake = client.post(
        "/api/v1/portfolio/management/intake",
        json={
            "portfolio_id": p.id,
            "holdings": [
                {
                    "ticker": "ETEL",
                    "shares": 100,
                    "entry_price": 10.0,
                    "target_price": 11.0,
                }
            ],
        },
    )
    assert intake.status_code == 200

    report = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}&refresh_prices=false")
    assert report.status_code == 200
    pos = report.json()["positions"][0]
    assert abs(float(pos["target_price_2"]) - 12.32) < 1e-9


def test_portfolio_management_report_send_telegram(monkeypatch):
    p = Portfolio.create(name="Managed Service C", type="USER")
    Position.create(
        portfolio=p.id,
        ticker="ACAMD",
        shares=50,
        entry_price=20.0,
        stop_loss=19.0,
        target_price=22.0,
        current_price=21.0,
        status="OPEN",
        currency="EGP",
    )

    sent_payloads = []

    def _fake_send(message, chat_id=None, token=None):
        sent_payloads.append({"message": message, "chat_id": chat_id})
        return {"ok": True, "result": {"message_id": 999}}

    monkeypatch.setattr("routes.portfolio.TelegramBot_Alerts.send_message", _fake_send)

    resp = client.post(
        "/api/v1/portfolio/management/report/send",
        json={"portfolio_id": p.id, "include_positions": 10, "chat_id": "-100123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "sent"
    assert body["chunks_total"] >= 1
    assert body["chunks_failed"] == 0
    assert len(sent_payloads) >= 1
    assert "PORTFOLIO MANAGEMENT REPORT" in sent_payloads[0]["message"]
    assert "TP2" in sent_payloads[0]["message"]


def test_portfolio_management_report_send_rejects_non_positive_portfolio_id(monkeypatch):
    monkeypatch.setattr(
        "routes.portfolio.TelegramBot_Alerts.send_message",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("telegram send should not be called")),
    )

    zero_response = client.post(
        "/api/v1/portfolio/management/report/send",
        json={"portfolio_id": 0, "include_positions": 10},
    )
    negative_response = client.post(
        "/api/v1/portfolio/management/report/send",
        json={"portfolio_id": -1, "include_positions": 10},
    )

    assert zero_response.status_code == 422
    assert negative_response.status_code == 422


def test_portfolio_add_blocks_gated_manual_trade(monkeypatch):
    p = Portfolio.create(name="Managed Service D", type="USER")
    monkeypatch.setattr(
        "routes.portfolio.WalkForwardValidation.get_trade_permission",
        lambda ticker, fail_closed=True: {"allowed": False, "reason": "validation_loss_blocked"},
    )
    monkeypatch.setattr("routes.portfolio.assert_ticker_allowed", lambda x: None)

    resp = client.post(
        "/api/v1/portfolio/add",
        json={
            "portfolio_id": p.id,
            "ticker": "COMI",
            "shares": 100,
            "price": 10.0,
            "type": "NEW",
        },
    )
    assert resp.status_code == 403
    assert "WFA gate blocked" in resp.json()["detail"]


def test_portfolio_management_intake_skips_blocked_ticker(monkeypatch):
    p = Portfolio.create(name="Managed Service E", type="USER")

    def _gate(ticker, fail_closed=True):
        if str(ticker).upper() == "COMI":
            return {"allowed": False, "reason": "validation_loss_blocked"}
        return {"allowed": True, "reason": "ok"}

    monkeypatch.setattr("routes.portfolio.WalkForwardValidation.get_trade_permission", _gate)
    monkeypatch.setattr("routes.portfolio.is_excluded_ticker", lambda x: False)

    intake = client.post(
        "/api/v1/portfolio/management/intake",
        json={
            "portfolio_id": p.id,
            "holdings": [
                {"ticker": "COMI", "shares": 100, "entry_price": 10.0},
                {"ticker": "FWRY", "shares": 50, "entry_price": 5.0},
            ],
        },
    )
    assert intake.status_code == 200
    body = intake.json()
    assert body["status"] == "partial", body
    assert body["created"] == 1, body
    assert any("COMI" in err and "WFA gate blocked" in err for err in body["errors"]), body

    assert Position.select().where(Position.portfolio == p.id, Position.status == "OPEN", Position.ticker == "COMI").count() == 0
    assert Position.select().where(Position.portfolio == p.id, Position.status == "OPEN", Position.ticker == "FWRY").count() == 1


def test_portfolio_management_intake_rejects_non_positive_portfolio_id(monkeypatch):
    monkeypatch.setattr(
        "routes.portfolio.WalkForwardValidation.get_trade_permission",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("WFA gate should not be called")),
    )
    monkeypatch.setattr("routes.portfolio.is_excluded_ticker", lambda x: False)

    payload = {
        "holdings": [
            {"ticker": "COMI", "shares": 100, "entry_price": 10.0},
        ],
    }
    zero_response = client.post(
        "/api/v1/portfolio/management/intake",
        json={"portfolio_id": 0, **payload},
    )
    negative_response = client.post(
        "/api/v1/portfolio/management/intake",
        json={"portfolio_id": -1, **payload},
    )

    assert zero_response.status_code == 422
    assert negative_response.status_code == 422


def test_portfolio_close_without_shares_closes_full_position():
    p = Portfolio.create(name="Managed Service F", type="USER")
    Position.create(
        portfolio=p.id,
        ticker="AMOC",
        shares=120,
        entry_price=10.0,
        stop_loss=9.0,
        target_price=12.0,
        current_price=11.0,
        status="OPEN",
        currency="EGP",
    )

    resp = client.post(
        "/api/v1/portfolio/close",
        json={
            "portfolio_id": p.id,
            "ticker": "AMOC",
            "price": 11.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"

    assert Position.select().where(Position.portfolio == p.id, Position.ticker == "AMOC", Position.status == "OPEN").count() == 0
    trade = Trade.get(Trade.portfolio == p.id, Trade.ticker == "AMOC")
    assert int(trade.shares) == 120
