from core.settings import settings
import datetime

from fastapi.testclient import TestClient

from api import app
from core.subscriptions import format_advisory_report_for_telegram, format_subscriber_welcome_message
from database import (
    Client,
    ClientEntitlement,
    Portfolio,
    Position,
    SignalAuditEvent,
    SignalRecommendation,
    SignalRun,
    SubscriptionDelivery,
)


client = TestClient(app, raise_server_exceptions=False)


def _portfolio(name: str = "VIP Portfolio", *, cash_egp: float = 100000.0) -> Portfolio:
    return Portfolio.create(name=name, type="USER", cash_egp=cash_egp)


def _latest_signal_run() -> SignalRun:
    run = SignalRun.create(
        run_date=datetime.date(2026, 5, 20),
        scan_type="DAILY",
        status="COMPLETED",
        completed_at=datetime.datetime(2026, 5, 20, 15, 30),
        signals_count=2,
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=10.0,
        stop_loss=9.0,
        target_price=12.0,
        score=8.5,
        confidence=82.0,
        horizon_days=5,
    )
    SignalRecommendation.create(
        run=run,
        ticker="FWRY",
        side="BUY",
        entry_price=5.0,
        stop_loss=4.5,
        target_price=6.2,
        score=7.9,
        confidence=76.0,
        horizon_days=5,
    )
    return run


def test_admin_can_create_subscriber_and_link_user_portfolio():
    portfolio = _portfolio("Subscriber Link Portfolio")

    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Alpha Subscriber",
            "subscription_tier": "SIGNALS_PLUS_PORTFOLIO_RECS",
            "telegram_chat_id": "-100111",
            "paid_until": "2027-06-20",
            "notes": "Manual billing",
            "report_language": "AR",
        },
    )

    assert create.status_code == 200, create.text
    subscriber = create.json()["subscriber"]
    assert subscriber["name"] == "Alpha Subscriber"
    assert subscriber["subscription_tier"] == "SIGNALS_PLUS_PORTFOLIO_RECS"
    assert subscriber["subscription_state"] == "ACTIVE"
    assert subscriber["report_language"] == "AR"

    link = client.post(
        f"/api/v1/subscribers/{subscriber['id']}/portfolios",
        json={"portfolio_id": portfolio.id},
    )

    assert link.status_code == 200, link.text
    linked = link.json()["subscriber"]
    assert linked["linked_portfolios"][0]["id"] == portfolio.id
    assert ClientEntitlement.select().where(
        (ClientEntitlement.client == subscriber["id"])
        & (ClientEntitlement.portfolio == portfolio.id)
        & (ClientEntitlement.is_active == True)
    ).exists()
    assert Client.get_by_id(subscriber["id"]).report_language == "AR"


def test_subscriber_report_language_rejects_unknown_values():
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Invalid Language Client",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "-100909",
            "paid_until": "2027-06-20",
            "report_language": "FR",
        },
    )

    assert create.status_code == 422
    assert create.json()["detail"]["error_reason"] == "invalid_report_language"


def test_type_three_subscriber_creation_can_create_and_link_user_portfolio():
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Auto Portfolio Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "telegram_chat_id": "1822794531",
            "paid_until": "2027-06-20",
            "create_portfolio": True,
        },
    )

    assert create.status_code == 200, create.text
    subscriber = create.json()["subscriber"]
    linked = subscriber["linked_portfolios"]
    assert linked[0]["name"] == "Auto Portfolio Client"
    assert "NO_LINKED_PORTFOLIO" not in subscriber["warnings"]
    portfolio = Portfolio.get_by_id(linked[0]["id"])
    assert portfolio.type == "USER"
    assert ClientEntitlement.select().where(
        (ClientEntitlement.client == subscriber["id"])
        & (ClientEntitlement.portfolio == portfolio.id)
        & (ClientEntitlement.is_active == True)
    ).exists()


def test_admin_can_archive_subscriber_without_erasing_delivery_history():
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Archive Candidate",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "-100999",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    SubscriptionDelivery.create(
        client=subscriber_id,
        delivery_type="TELEGRAM_CHAT_TEST",
        subscription_tier="SIGNALS_ONLY",
        channel="TELEGRAM",
        status="SENT",
        chat_id="-100999",
        provider_message_id="991",
        message_preview="old delivery proof",
    )

    response = client.post(f"/api/v1/subscribers/{subscriber_id}/archive")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "archived"
    assert body["subscriber"]["is_active"] is False
    assert body["subscriber"]["subscription_state"] == "INACTIVE"
    assert bool(Client.get_by_id(subscriber_id).is_active) is False

    history = client.get("/api/v1/subscribers/deliveries", params={"client_id": subscriber_id})
    assert history.status_code == 200
    assert history.json()["deliveries"][0]["status"] == "SENT"
    assert SubscriptionDelivery.select().where(SubscriptionDelivery.client == subscriber_id).count() == 1
    assert SignalAuditEvent.select().where(
        (SignalAuditEvent.client == subscriber_id)
        & (SignalAuditEvent.event_type == "SUBSCRIPTION_ARCHIVED")
    ).exists()


def test_signals_only_subscriber_is_blocked_from_portfolio_advisory():
    portfolio = _portfolio("Signals Only Portfolio")
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Signals Only Client",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "-100222",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})

    response = client.get(
        f"/api/v1/subscribers/{subscriber_id}/advisory-report",
        params={"portfolio_id": portfolio.id},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error_reason"] == "tier_not_entitled"


def test_portfolio_advisory_matches_open_positions_and_cash_aware_new_entries():
    portfolio = _portfolio("Managed Advisory Portfolio", cash_egp=20000.0)
    Position.create(
        portfolio=portfolio,
        ticker="COMI",
        shares=100,
        entry_price=9.8,
        stop_loss=8.8,
        target_price=11.2,
        target_price_2=12.0,
        current_price=10.1,
        status="OPEN",
        currency="EGP",
    )
    _latest_signal_run()
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Managed Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "telegram_chat_id": "-100333",
            "paid_until": "2027-06-20",
            "risk_profile": "BALANCED",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})

    response = client.get(
        f"/api/v1/subscribers/{subscriber_id}/advisory-report",
        params={"portfolio_id": portfolio.id},
    )

    assert response.status_code == 200, response.text
    report = response.json()["report"]
    actions = {item["ticker"]: item for item in report["actions"]}
    assert "NO_LINKED_PORTFOLIO" not in report["subscriber"]["warnings"]
    assert actions["COMI"]["action"] == "HOLD_WITH_SIGNAL"
    assert actions["COMI"]["signal_match"] is True
    assert actions["FWRY"]["action"] == "NEW_ENTRY"
    assert actions["FWRY"]["recommended_shares"] > 0
    assert "advisory only" in response.json()["telegram_preview"].lower()


def test_portfolio_advisory_flags_overweight_position_for_resize():
    portfolio = _portfolio("Concentrated Advisory Portfolio", cash_egp=0.0)
    Position.create(
        portfolio=portfolio,
        ticker="COMI",
        shares=10000,
        entry_price=10.0,
        stop_loss=9.0,
        target_price=12.0,
        current_price=10.0,
        status="OPEN",
        currency="EGP",
    )
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Resize Client",
            "subscription_tier": "SIGNALS_PLUS_PORTFOLIO_RECS",
            "telegram_chat_id": "-100555",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})

    response = client.get(
        f"/api/v1/subscribers/{subscriber_id}/advisory-report",
        params={"portfolio_id": portfolio.id},
    )

    assert response.status_code == 200, response.text
    action = response.json()["report"]["actions"][0]
    assert action["action"] == "REDUCE_SIZE"
    assert action["recommended_shares"] < 10000


def test_telegram_advisory_copy_clarifies_resize_and_no_cash_signals():
    report_payload = {
        "subscriber": {"name": "Tamer Sabry", "subscription_tier": "MANAGED_ADVISORY"},
        "portfolio": {"id": 9, "name": "Tamer Sabry"},
        "run": {"scan_type": "PRE_CLOSE", "run_date": "2026-05-28"},
        "generated_at": "2026-05-29T01:34:24",
        "summary": {
            "open_positions": 5,
            "latest_recommendations": 3,
            "action_items": 2,
            "risk_status": "HEALTHY",
            "risk_score": 75,
        },
        "actions": [
            {
                "ticker": "ACAP",
                "action": "REDUCE_SIZE",
                "shares": 25000,
                "recommended_shares": 19603,
                "position_weight_pct": 25.5,
                "max_position_weight_pct": 20.0,
                "reason": "Position weight is above the configured subscriber risk cap.",
            },
            {
                "ticker": "GTEX",
                "action": "EXIT_NOW",
                "shares": 10000,
                "current_price": 0.7,
                "stop_loss": 0.72,
                "reason": "Current price is at or below the stored stop loss.",
            },
            {
                "ticker": "ICID",
                "action": "NO_ACTION",
                "signal_match": True,
                "recommended_shares": 0,
                "reason": "Fresh Horus signal exists but cash or risk distance does not support a new position.",
                "entry_price": 8.25,
                "stop_loss": 7.9,
                "target_price": 9.1,
            },
        ],
    }
    text = format_advisory_report_for_telegram(report_payload)

    assert "Target holding: 19,603 shares" in text
    assert "Reduce by: 5,397 shares" in text
    assert "Price/SL: 0.7 / 0.72" in text
    assert "No new entry: cash/risk rules blocked this signal" in text
    assert "Size: 0" not in text
    assert "Confirm live prices before acting" in text

    arabic_text = format_advisory_report_for_telegram(report_payload, language="AR")
    assert "تقرير حورس الاستشاري للمحفظة" in arabic_text
    assert "هورس" not in arabic_text
    assert "المشترك: Tamer Sabry" in arabic_text
    assert "الإجراءات ذات الأولوية" in arabic_text
    assert "الاحتفاظ المستهدف: 19,603 سهم" in arabic_text
    assert "راجع الخروج الكامل" in arabic_text
    assert "تأكيد الأسعار الحية قبل اتخاذ القرار" in arabic_text
    assert "HORUS PORTFOLIO ADVISORY REPORT" not in arabic_text


def test_subscriber_welcome_message_uses_client_report_language():
    client_row = Client.create(
        name="Arabic Welcome Client",
        subscription_tier="MANAGED_ADVISORY",
        telegram_chat_id="-100444",
        paid_until=datetime.date(2026, 6, 20),
        report_language="AR",
    )

    message = format_subscriber_welcome_message(client_row)

    assert "مرحباً بك في حورس" in message
    assert "اشتراكك في حورس نشط." in message
    assert "هورس" not in message
    assert "المشترك: Arabic Welcome Client" in message
    assert "الخطة: النوع 3" in message
    assert "WELCOME TO HORUS" not in message


def test_expired_or_missing_chat_subscribers_cannot_send_private_report(monkeypatch):
    portfolio = _portfolio("Expired Advisory Portfolio")
    _latest_signal_run()
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Expired Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "paid_until": "2026-01-01",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})

    sent = client.post(
        f"/api/v1/subscribers/{subscriber_id}/advisory-report/send",
        json={"portfolio_id": portfolio.id},
    )

    assert sent.status_code == 403
    assert sent.json()["detail"]["error_reason"] == "subscription_expired"


def test_private_report_send_persists_delivery_attempt(monkeypatch):
    portfolio = _portfolio("Delivery Advisory Portfolio")
    _latest_signal_run()
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Delivery Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "telegram_chat_id": "-100444",
            "paid_until": "2027-06-20",
            "report_language": "AR",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})

    monkeypatch.setattr(
        "routes.subscriptions.TelegramBot_Alerts.send_message",
        lambda message, chat_id=None: {"ok": False, "description": "telegram down"},
    )

    sent = client.post(
        f"/api/v1/subscribers/{subscriber_id}/advisory-report/send",
        json={"portfolio_id": portfolio.id},
    )

    assert sent.status_code == 502
    body = sent.json()
    assert body["delivery"]["status"] == "FAILED"
    assert body["delivery"]["last_error"] == "telegram down"
    assert body["delivery"]["details"]["report_language"] == "AR"
    assert "تقرير حورس الاستشاري للمحفظة" in body["delivery"]["message_preview"]
    assert "هورس" not in body["delivery"]["message_preview"]

    history = client.get("/api/v1/subscribers/deliveries", params={"client_id": subscriber_id})
    assert history.status_code == 200
    assert history.json()["deliveries"][0]["status"] == "FAILED"


def test_admin_can_send_subscriber_welcome_message(monkeypatch):
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Welcome Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "telegram_chat_id": "-100777",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    sent_messages = []
    monkeypatch.setattr(
        "routes.subscriptions.TelegramBot_Alerts.send_message",
        lambda message, chat_id=None: sent_messages.append((message, chat_id))
        or {"ok": True, "result": {"message_id": 991}},
    )

    response = client.post(f"/api/v1/subscribers/{subscriber_id}/telegram-test/send")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["delivery"]["status"] == "SENT"
    assert body["delivery"]["delivery_type"] == "TELEGRAM_CHAT_TEST"
    assert body["delivery"]["provider_message_id"] == "991"
    assert sent_messages[0][1] == "-100777"
    welcome_message = sent_messages[0][0]
    assert "WELCOME TO HORUS" in welcome_message
    assert "Subscriber: Welcome Client" in welcome_message
    assert "Plan: Type 3 - Market Signals + Managed Advisory" in welcome_message
    assert "Start Date:" in welcome_message
    assert "End Date: 2027-06-20" in welcome_message
    assert "Premium market signals on Telegram" in welcome_message
    assert "Proactive portfolio advisory reports" in welcome_message
    assert "Cash-aware position sizing" in welcome_message
    assert "HORUS TELEGRAM CHAT TEST" not in welcome_message


def test_private_subscriber_chat_test_uses_private_bot_token(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "private-token", raising=False)
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Private Bot Client",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "1822794531",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    sent_messages = []

    def fake_send(message, token=None, chat_id=None):
        sent_messages.append({"message": message, "token": token, "chat_id": chat_id})
        return {"ok": True, "result": {"message_id": 992}}

    monkeypatch.setattr("routes.subscriptions.TelegramBot_Alerts.send_message", fake_send)

    response = client.post(f"/api/v1/subscribers/{subscriber_id}/telegram-test/send")

    assert response.status_code == 200, response.text
    assert sent_messages[0]["chat_id"] == "1822794531"
    assert sent_messages[0]["token"] == "private-token"


def test_delivery_diagnosis_explains_private_chat_start_required(monkeypatch):
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Private Chat Client",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "1822794531",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    monkeypatch.setattr(
        "routes.subscriptions.TelegramBot_Alerts.send_message",
        lambda message, chat_id=None: {
            "ok": False,
            "error_code": 403,
            "description": "Forbidden: bot can't initiate conversation with a user",
        },
    )

    response = client.post(f"/api/v1/subscribers/{subscriber_id}/telegram-test/send")

    assert response.status_code == 502
    delivery = response.json()["delivery"]
    assert delivery["status"] == "FAILED"
    assert delivery["diagnosis"]["action_code"] == "SUBSCRIBER_MUST_START_BOT"
    assert "open the bot" in delivery["diagnosis"]["operator_action"]


def test_delivery_diagnosis_explains_private_chat_not_found(monkeypatch):
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Private Chat Not Found Client",
            "subscription_tier": "SIGNALS_ONLY",
            "telegram_chat_id": "1822794531",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    monkeypatch.setattr(
        "routes.subscriptions.TelegramBot_Alerts.send_message",
        lambda message, chat_id=None: {
            "ok": False,
            "error_code": 400,
            "description": "Bad Request: chat not found",
        },
    )

    response = client.post(f"/api/v1/subscribers/{subscriber_id}/telegram-test/send")

    assert response.status_code == 502
    delivery = response.json()["delivery"]
    assert delivery["status"] == "FAILED"
    assert delivery["diagnosis"]["action_code"] == "PRIVATE_CHAT_NOT_FOUND"
    assert "press Start" in delivery["diagnosis"]["operator_action"]


def test_admin_can_retry_failed_subscription_delivery(monkeypatch):
    portfolio = _portfolio("Retry Advisory Portfolio")
    _latest_signal_run()
    create = client.post(
        "/api/v1/subscribers",
        json={
            "name": "Retry Client",
            "subscription_tier": "MANAGED_ADVISORY",
            "telegram_chat_id": "-100888",
            "paid_until": "2027-06-20",
        },
    )
    subscriber_id = create.json()["subscriber"]["id"]
    client.post(f"/api/v1/subscribers/{subscriber_id}/portfolios", json={"portfolio_id": portfolio.id})
    failed = SubscriptionDelivery.create(
        client=subscriber_id,
        portfolio=portfolio.id,
        delivery_type="PORTFOLIO_ADVISORY",
        subscription_tier="MANAGED_ADVISORY",
        channel="TELEGRAM",
        status="FAILED",
        chat_id="-100888",
        message_preview="old failed advisory",
        last_error="telegram down",
    )
    monkeypatch.setattr(
        "routes.subscriptions.TelegramBot_Alerts.send_message",
        lambda message, chat_id=None: {"ok": True, "result": {"message_id": 992}},
    )

    response = client.post(f"/api/v1/subscribers/deliveries/{failed.id}/retry")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["retried_delivery_id"] == failed.id
    assert body["delivery"]["id"] != failed.id
    assert body["delivery"]["status"] == "SENT"
    assert body["delivery"]["provider_message_id"] == "992"


def test_commercial_routes_require_api_key_when_auth_enabled(monkeypatch):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.setenv("HORUS_ADMIN_API_KEY", "secret-admin-key")

    blocked = client.get("/api/v1/signals/recommendations")
    assert blocked.status_code == 401
    assert blocked.json()["detail"]["error_reason"] == "api_key_missing"

    allowed = client.get("/api/v1/subscribers", headers={"x-api-key": "secret-admin-key"})
    assert allowed.status_code == 200
    assert allowed.json()["summary"]["total"] == 0
