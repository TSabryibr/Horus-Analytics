from __future__ import annotations

import datetime
from typing import Any, Callable, Optional

from peewee import fn
from core import TimeUtils
from database import (
    Client,
    ClientEntitlement,
    Portfolio,
    SubscriptionDelivery,
    db,
)

from .tiers import (
    ADVISORY_TIERS,
    MANAGED_TIERS,
    SIGNALS_ONLY,
    _clean_optional,
    _default_report_language,
    _safe_int_setting,
    normalize_report_language,
    normalize_risk_profile,
    normalize_tier,
    subscription_error,
)


def subscription_state(client: Client, *, today_fn: Callable[[], datetime.date] = TimeUtils.today) -> str:
    if not bool(client.is_active):
        return "INACTIVE"
    paid_until = getattr(client, "paid_until", None)
    if paid_until is None:
        return "ACTIVE"
    today = today_fn()
    if paid_until < today:
        return "EXPIRED"
    renewal_window_days = _safe_int_setting("SUBSCRIPTION_RENEWAL_DUE_DAYS", 7)
    if paid_until <= today + datetime.timedelta(days=renewal_window_days):
        return "RENEWAL_DUE"
    return "ACTIVE"


def _client_by_id(client_id: int) -> Client:
    client = Client.get_or_none(Client.id == client_id)
    if not client:
        raise subscription_error(404, "subscriber_not_found", "Subscriber not found.", client_id=client_id)
    return client


def _portfolio_by_id(portfolio_id: int) -> Portfolio:
    portfolio = Portfolio.get_or_none((Portfolio.id == portfolio_id) & (Portfolio.type == "USER"))
    if not portfolio:
        raise subscription_error(
            404,
            "user_portfolio_not_found",
            "USER portfolio not found.",
            portfolio_id=portfolio_id,
        )
    return portfolio


def linked_portfolios(client: Client) -> list[Portfolio]:
    rows = (
        ClientEntitlement.select(ClientEntitlement, Portfolio)
        .join(Portfolio)
        .where((ClientEntitlement.client == client) & (ClientEntitlement.is_active == True))
        .order_by(Portfolio.name.asc())
    )
    return [row.portfolio for row in rows if row.portfolio and row.portfolio.type == "USER"]


def serialize_portfolio(portfolio: Portfolio) -> dict[str, Any]:
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "type": portfolio.type,
        "cash_egp": round(float(portfolio.cash_egp or 0.0), 2),
        "cash_usd": round(float(portfolio.cash_usd or 0.0), 2),
    }


def serialize_client(client: Client, *, include_portfolios: bool = True) -> dict[str, Any]:
    from .delivery import last_subscription_delivery, serialize_delivery

    tier = normalize_tier(client.subscription_tier)
    state = subscription_state(client)
    portfolios = linked_portfolios(client) if include_portfolios else []
    warnings = []
    if state == "EXPIRED":
        warnings.append("SUBSCRIPTION_EXPIRED")
    elif state == "RENEWAL_DUE":
        warnings.append("RENEWAL_DUE")
    if not str(client.telegram_chat_id or "").strip():
        warnings.append("MISSING_CHAT")
    if include_portfolios and tier in ADVISORY_TIERS and not portfolios:
        warnings.append("NO_LINKED_PORTFOLIO")

    return {
        "id": client.id,
        "name": client.name,
        "is_active": bool(client.is_active),
        "subscription_tier": tier,
        "subscription_state": state,
        "telegram_chat_id": client.telegram_chat_id,
        "report_language": normalize_report_language(getattr(client, "report_language", None) or _default_report_language()),
        "risk_profile": client.risk_profile or "BALANCED",
        "default_currency": client.default_currency or "EGP",
        "paid_until": client.paid_until.isoformat() if client.paid_until else None,
        "notes": client.notes or client.description,
        "description": client.description,
        "warnings": warnings,
        "linked_portfolios": [serialize_portfolio(portfolio) for portfolio in portfolios],
        "last_delivery": serialize_delivery(last_subscription_delivery(client)),
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "updated_at": client.updated_at.isoformat() if getattr(client, "updated_at", None) else None,
    }


def list_subscribers_payload() -> dict[str, Any]:
    subscribers = [serialize_client(row) for row in Client.select().order_by(Client.name.asc())]
    summary = {
        "total": len(subscribers),
        "active": sum(1 for row in subscribers if row["subscription_state"] == "ACTIVE"),
        "renewal_due": sum(1 for row in subscribers if row["subscription_state"] == "RENEWAL_DUE"),
        "expired": sum(1 for row in subscribers if row["subscription_state"] == "EXPIRED"),
        "inactive": sum(1 for row in subscribers if row["subscription_state"] == "INACTIVE"),
        "missing_chat": sum(1 for row in subscribers if "MISSING_CHAT" in row["warnings"]),
        "advisory_enabled": sum(1 for row in subscribers if row["subscription_tier"] in ADVISORY_TIERS),
        "managed": sum(1 for row in subscribers if row["subscription_tier"] in MANAGED_TIERS),
    }
    return {"summary": summary, "subscribers": subscribers}


def upsert_subscriber(
    *,
    name: str,
    subscription_tier: str = SIGNALS_ONLY,
    telegram_chat_id: Optional[str] = None,
    report_language: Optional[str] = None,
    paid_until: Optional[datetime.date] = None,
    risk_profile: Optional[str] = None,
    default_currency: Optional[str] = "EGP",
    notes: Optional[str] = None,
    description: Optional[str] = None,
    is_active: bool = True,
) -> Client:
    clean_name = str(name or "").strip()
    if not clean_name:
        raise subscription_error(422, "subscriber_name_required", "Subscriber name is required.")
    existing = Client.get_or_none(fn.Lower(Client.name) == clean_name.lower())
    if existing:
        raise subscription_error(
            400,
            "subscriber_name_exists",
            "Subscriber name already exists.",
            name=clean_name,
        )
    now = TimeUtils.now()
    return Client.create(
        name=clean_name,
        is_active=bool(is_active),
        subscription_tier=normalize_tier(subscription_tier),
        telegram_chat_id=_clean_optional(telegram_chat_id),
        report_language=normalize_report_language(report_language or _default_report_language()),
        paid_until=paid_until,
        risk_profile=normalize_risk_profile(risk_profile),
        default_currency=str(default_currency or "EGP").upper().strip(),
        notes=_clean_optional(notes),
        description=_clean_optional(description),
        created_at=now,
        updated_at=now,
    )


def subscriber_portfolio_name(client: Client) -> str:
    return str(client.name or "").strip()


def create_or_link_subscriber_portfolio(client: Client) -> Portfolio:
    portfolio_name = subscriber_portfolio_name(client)
    if not portfolio_name:
        raise subscription_error(422, "subscriber_name_required", "Subscriber name is required.")
    portfolio, _ = Portfolio.get_or_create(
        name=portfolio_name,
        defaults={"type": "USER", "auto_manage": False},
    )
    if portfolio.type != "USER":
        raise subscription_error(
            400,
            "subscriber_portfolio_name_conflict",
            "A non-user portfolio already uses this subscriber name.",
            client_id=client.id,
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
        )
    link_portfolio(client.id, portfolio.id)
    return portfolio


def provision_subscriber(
    *,
    name: str,
    subscription_tier: str = SIGNALS_ONLY,
    telegram_chat_id: Optional[str] = None,
    report_language: Optional[str] = None,
    paid_until: Optional[datetime.date] = None,
    risk_profile: Optional[str] = None,
    default_currency: Optional[str] = "EGP",
    notes: Optional[str] = None,
    description: Optional[str] = None,
    is_active: bool = True,
    portfolio_id: Optional[int] = None,
    create_portfolio: bool = False,
) -> Client:
    with db.atomic():
        client = upsert_subscriber(
            name=name,
            subscription_tier=subscription_tier,
            telegram_chat_id=telegram_chat_id,
            report_language=report_language,
            paid_until=paid_until,
            risk_profile=risk_profile,
            default_currency=default_currency,
            notes=notes,
            description=description,
            is_active=is_active,
        )
        tier = normalize_tier(client.subscription_tier)
        if portfolio_id:
            link_portfolio(client.id, int(portfolio_id))
        elif create_portfolio and tier in ADVISORY_TIERS:
            create_or_link_subscriber_portfolio(client)
    return client


def update_subscriber(client_id: int, updates: dict[str, Any]) -> Client:
    client = _client_by_id(client_id)
    allowed = {
        "name",
        "is_active",
        "subscription_tier",
        "telegram_chat_id",
        "report_language",
        "paid_until",
        "risk_profile",
        "default_currency",
        "notes",
        "description",
    }
    for key, value in updates.items():
        if key not in allowed:
            continue
        if key == "subscription_tier":
            value = normalize_tier(value)
        elif key == "report_language":
            value = normalize_report_language(value)
        elif key == "risk_profile":
            value = normalize_risk_profile(value)
        elif key in {"telegram_chat_id", "notes", "description"}:
            value = _clean_optional(value)
        elif key == "default_currency":
            value = str(value or "EGP").upper().strip()
        elif key == "name":
            value = str(value or "").strip()
            if not value:
                raise subscription_error(422, "subscriber_name_required", "Subscriber name is required.")
            duplicate = Client.get_or_none((fn.Lower(Client.name) == value.lower()) & (Client.id != client.id))
            if duplicate:
                raise subscription_error(400, "subscriber_name_exists", "Subscriber name already exists.", name=value)
        setattr(client, key, value)
    client.updated_at = TimeUtils.now()
    client.save()
    return client


def archive_subscriber(client_id: int) -> Client:
    client = _client_by_id(client_id)
    client.is_active = False
    client.updated_at = TimeUtils.now()
    client.save()
    return client


def link_portfolio(client_id: int, portfolio_id: int) -> Client:
    client = _client_by_id(client_id)
    portfolio = _portfolio_by_id(portfolio_id)
    entitlement, _ = ClientEntitlement.get_or_create(
        client=client,
        portfolio=portfolio,
        defaults={"is_active": True},
    )
    if not entitlement.is_active:
        entitlement.is_active = True
        entitlement.save()
    return client


def unlink_portfolio(client_id: int, portfolio_id: int) -> Client:
    client = _client_by_id(client_id)
    entitlement = ClientEntitlement.get_or_none(
        (ClientEntitlement.client == client_id) & (ClientEntitlement.portfolio == portfolio_id)
    )
    if entitlement:
        entitlement.is_active = False
        entitlement.save()
    return client


def ensure_advisory_entitlement(client: Client, portfolio: Portfolio) -> None:
    tier = normalize_tier(client.subscription_tier)
    if tier not in ADVISORY_TIERS:
        raise subscription_error(
            403,
            "tier_not_entitled",
            "Subscriber tier does not include portfolio advisory.",
            client_id=client.id,
            subscription_tier=tier,
        )
    state = subscription_state(client)
    if state == "EXPIRED":
        raise subscription_error(
            403,
            "subscription_expired",
            "Subscriber subscription is expired.",
            client_id=client.id,
            paid_until=client.paid_until.isoformat() if client.paid_until else None,
        )
    if state == "INACTIVE":
        raise subscription_error(403, "subscriber_inactive", "Subscriber is inactive.", client_id=client.id)
    entitlement = ClientEntitlement.get_or_none(
        (ClientEntitlement.client == client)
        & (ClientEntitlement.portfolio == portfolio)
        & (ClientEntitlement.is_active == True)
    )
    if entitlement is None:
        raise subscription_error(
            403,
            "portfolio_not_linked",
            "Subscriber is not linked to this portfolio.",
            client_id=client.id,
            portfolio_id=portfolio.id,
        )
