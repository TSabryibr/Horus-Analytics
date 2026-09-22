from __future__ import annotations

import datetime
import inspect
import json
from typing import Any, Callable, Optional

from fastapi import HTTPException
from core import TimeUtils
from core.settings import settings
from database import (
    Client,
    Portfolio,
    SignalAuditEvent,
    SubscriptionDelivery,
)

from .tiers import (
    ADVISORY_TIERS,
    MANAGED_ADVISORY,
    MANAGED_TIERS,
    SIGNALS_ONLY,
    SIGNALS_PLUS_PORTFOLIO_RECS,
    _default_report_language,
    _increment,
    _json_object,
    normalize_report_language,
    normalize_tier,
    subscription_benefits,
    subscription_error,
    subscription_plan_label,
)
from .entitlements import (
    _client_by_id,
    _portfolio_by_id,
    ensure_advisory_entitlement,
    linked_portfolios,
    subscription_state,
)
from .advisory import (
    build_portfolio_advisory_report,
    format_advisory_report_for_telegram,
    latest_completed_signal_run,
)


def _callable_accepts_keyword(fn: Callable[..., dict], keyword: str) -> bool:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return False
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True
    return keyword in signature.parameters


def last_subscription_delivery(client: Client) -> Optional[SubscriptionDelivery]:
    return (
        SubscriptionDelivery.select()
        .where(SubscriptionDelivery.client == client)
        .order_by(SubscriptionDelivery.created_at.desc(), SubscriptionDelivery.id.desc())
        .first()
    )


def serialize_delivery(delivery: Optional[SubscriptionDelivery]) -> Optional[dict[str, Any]]:
    if delivery is None:
        return None
    return {
        "id": delivery.id,
        "client_id": delivery.client.id if delivery.client else None,
        "portfolio_id": delivery.portfolio.id if delivery.portfolio else None,
        "run_id": delivery.run.id if delivery.run else None,
        "delivery_type": delivery.delivery_type,
        "subscription_tier": delivery.subscription_tier,
        "channel": delivery.channel,
        "status": delivery.status,
        "chat_id": delivery.chat_id,
        "provider_message_id": delivery.provider_message_id,
        "message_preview": delivery.message_preview,
        "last_error": delivery.last_error,
        "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
        "created_at": delivery.created_at.isoformat() if delivery.created_at else None,
        "details": _json_object(delivery.details_json),
        "diagnosis": delivery_failure_diagnosis(delivery),
    }


def subscriber_delivery_token_for_chat(chat_id: str) -> Optional[str]:
    normalized_chat_id = str(chat_id or "").strip()
    if not normalized_chat_id or normalized_chat_id.startswith("-"):
        return None
    token = str(getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "") or "").strip()
    return token or None


def _subscriber_send_kwargs(send_message_fn: Callable[..., dict], chat_id: str) -> dict[str, str]:
    kwargs = {"chat_id": chat_id}
    token = subscriber_delivery_token_for_chat(chat_id)
    if token and _callable_accepts_keyword(send_message_fn, "token"):
        kwargs["token"] = token
    return kwargs


def _date_label(value: Any) -> str:
    if value is None:
        return "Not set"
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def format_subscriber_welcome_message(client: Client, language: Optional[str] = None) -> str:
    normalized_language = normalize_report_language(
        language or getattr(client, "report_language", None) or _default_report_language()
    )
    tier = normalize_tier(client.subscription_tier)
    benefits = "\n".join(f"- {benefit}" for benefit in subscription_benefits(tier, normalized_language))
    if normalized_language == "AR":
        return (
            "مرحباً بك في حورس\n"
            "\n"
            f"أهلاً {client.name},\n"
            "اشتراكك في حورس نشط.\n"
            "\n"
            "تفاصيل الاشتراك\n"
            f"المشترك: {client.name}\n"
            f"الخطة: {subscription_plan_label(tier, normalized_language)}\n"
            f"تاريخ البداية: {_date_label(client.created_at)}\n"
            f"تاريخ النهاية: {_date_label(client.paid_until)}\n"
            "\n"
            "المزايا المضمنة\n"
            f"{benefits}\n"
            "\n"
            "التسليم\n"
            "- سيتم إرسال إشارات السوق والرسائل الاستشارية إلى هذه المحادثة على تيليجرام.\n"
            "\n"
            "للاستشارة فقط. حورس لا ينفذ الصفقات تلقائياً."
        )
    return (
        "WELCOME TO HORUS\n"
        "\n"
        f"Hello {client.name},\n"
        "Your Horus subscription is active.\n"
        "\n"
        "Subscription Details\n"
        f"Subscriber: {client.name}\n"
        f"Plan: {subscription_plan_label(tier, normalized_language)}\n"
        f"Start Date: {_date_label(client.created_at)}\n"
        f"End Date: {_date_label(client.paid_until)}\n"
        "\n"
        "Included Benefits\n"
        f"{benefits}\n"
        "\n"
        "Delivery\n"
        "- Market signals and advisory messages will be sent to this Telegram chat.\n"
        "\n"
        "Advisory only. Horus does not execute trades automatically."
    )


def send_advisory_report(
    client_id: int,
    portfolio_id: int,
    *,
    send_message_fn: Callable[..., dict],
) -> tuple[dict[str, Any], SubscriptionDelivery]:
    client = _client_by_id(client_id)
    portfolio = _portfolio_by_id(portfolio_id)
    ensure_advisory_entitlement(client, portfolio)
    chat_id = str(client.telegram_chat_id or "").strip()
    if not chat_id:
        raise subscription_error(
            400,
            "missing_telegram_chat_id",
            "Subscriber Telegram chat ID is required before sending a private report.",
            client_id=client.id,
        )
    report = build_portfolio_advisory_report(client.id, portfolio.id)
    report_language = normalize_report_language(getattr(client, "report_language", None) or _default_report_language())
    message = format_advisory_report_for_telegram(report, language=report_language)
    delivery = SubscriptionDelivery.create(
        client=client,
        portfolio=portfolio,
        run=latest_completed_signal_run(),
        delivery_type="PORTFOLIO_ADVISORY",
        subscription_tier=normalize_tier(client.subscription_tier),
        channel="TELEGRAM",
        status="PENDING",
        chat_id=chat_id,
        message_preview=message[:1000],
        details_json=json.dumps(
            {
                "action_items": report.get("summary", {}).get("action_items", 0),
                "report_language": report_language,
            }
        ),
    )
    delivery = _send_delivery_message(delivery, message, send_message_fn=send_message_fn, chat_id=chat_id)
    emit_subscription_audit(
        event_type="SUBSCRIPTION_ADVISORY_SENT" if delivery.status == "SENT" else "SUBSCRIPTION_ADVISORY_FAILED",
        severity="INFO" if delivery.status == "SENT" else "WARN",
        client=client,
        portfolio=portfolio,
        message="Subscriber advisory report delivery attempted.",
        details={
            "delivery_id": delivery.id,
            "status": delivery.status,
            "last_error": delivery.last_error,
        },
    )
    return report, delivery


def send_telegram_chat_test(
    client_id: int,
    *,
    send_message_fn: Callable[..., dict],
) -> SubscriptionDelivery:
    client = _client_by_id(client_id)
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

    chat_id = str(client.telegram_chat_id or "").strip()
    if not chat_id:
        raise subscription_error(
            400,
            "missing_telegram_chat_id",
            "Subscriber Telegram chat ID is required before sending a test message.",
            client_id=client.id,
        )

    report_language = normalize_report_language(getattr(client, "report_language", None) or _default_report_language())
    message = format_subscriber_welcome_message(client, language=report_language)
    delivery = SubscriptionDelivery.create(
        client=client,
        portfolio=None,
        run=None,
        delivery_type="TELEGRAM_CHAT_TEST",
        subscription_tier=normalize_tier(client.subscription_tier),
        channel="TELEGRAM",
        status="PENDING",
        chat_id=chat_id,
        message_preview=message[:1000],
        details_json=json.dumps({"purpose": "welcome_message", "report_language": report_language}),
    )
    delivery = _send_delivery_message(delivery, message, send_message_fn=send_message_fn, chat_id=chat_id)
    emit_subscription_audit(
        event_type="SUBSCRIPTION_CHAT_TEST_SENT" if delivery.status == "SENT" else "SUBSCRIPTION_CHAT_TEST_FAILED",
        severity="INFO" if delivery.status == "SENT" else "WARN",
        client=client,
        message="Subscriber welcome message delivery attempted.",
        details={
            "delivery_id": delivery.id,
            "status": delivery.status,
            "last_error": delivery.last_error,
        },
    )
    return delivery


def retry_subscription_delivery(
    delivery_id: int,
    *,
    send_message_fn: Callable[..., dict],
) -> dict[str, Any]:
    previous = SubscriptionDelivery.get_or_none(SubscriptionDelivery.id == delivery_id)
    if previous is None:
        raise subscription_error(404, "delivery_not_found", "Subscription delivery was not found.", delivery_id=delivery_id)
    if previous.status != "FAILED":
        raise subscription_error(
            400,
            "delivery_not_failed",
            "Only failed subscription deliveries can be retried.",
            delivery_id=delivery_id,
            status=previous.status,
        )

    delivery_type = str(previous.delivery_type or "").upper()
    if delivery_type == "PORTFOLIO_ADVISORY":
        if not previous.portfolio:
            raise subscription_error(
                400,
                "delivery_missing_portfolio",
                "Failed advisory delivery cannot be retried because it is not linked to a portfolio.",
                delivery_id=delivery_id,
            )
        report, delivery = send_advisory_report(
            previous.client.id,
            previous.portfolio.id,
            send_message_fn=send_message_fn,
        )
        return {
            "status": "sent" if delivery.status == "SENT" else "failed",
            "retried_delivery_id": previous.id,
            "report": report,
            "delivery": serialize_delivery(delivery),
        }

    if delivery_type == "TELEGRAM_CHAT_TEST":
        delivery = send_telegram_chat_test(previous.client.id, send_message_fn=send_message_fn)
        return {
            "status": "sent" if delivery.status == "SENT" else "failed",
            "retried_delivery_id": previous.id,
            "delivery": serialize_delivery(delivery),
        }

    raise subscription_error(
        400,
        "delivery_type_not_retryable",
        "Subscription delivery type is not retryable.",
        delivery_id=delivery_id,
        delivery_type=previous.delivery_type,
    )


def _send_delivery_message(
    delivery: SubscriptionDelivery,
    message: str,
    *,
    send_message_fn: Callable[..., dict],
    chat_id: str,
) -> SubscriptionDelivery:
    try:
        response = send_message_fn(message, **_subscriber_send_kwargs(send_message_fn, chat_id))
    except Exception as exc:
        response = {"ok": False, "description": str(exc) or type(exc).__name__}

    if isinstance(response, dict) and response.get("ok"):
        delivery.status = "SENT"
        message_id = (response.get("result") or {}).get("message_id")
        delivery.provider_message_id = str(message_id) if message_id is not None else None
        delivery.sent_at = TimeUtils.now()
        delivery.last_error = None
    else:
        delivery.status = "FAILED"
        delivery.last_error = (
            response.get("description", "Unknown delivery error")
            if isinstance(response, dict)
            else "Unknown delivery error"
        )
    delivery.save()
    return delivery


def list_deliveries_payload(client_id: Optional[int] = None, limit: int = 100) -> dict[str, Any]:
    query = SubscriptionDelivery.select().order_by(
        SubscriptionDelivery.created_at.desc(),
        SubscriptionDelivery.id.desc(),
    )
    if client_id is not None:
        query = query.where(SubscriptionDelivery.client == client_id)
    deliveries = list(query.limit(max(1, min(int(limit or 100), 500))))
    return {"count": len(deliveries), "deliveries": [serialize_delivery(row) for row in deliveries]}


def delivery_failure_diagnosis(delivery: Optional[SubscriptionDelivery]) -> Optional[dict[str, str]]:
    if delivery is None or str(getattr(delivery, "status", "") or "").upper() != "FAILED":
        return None
    error = str(getattr(delivery, "last_error", "") or "").lower()
    chat_id = str(getattr(delivery, "chat_id", "") or "")
    if "can't initiate conversation" in error or "bot can't initiate" in error:
        return {
            "action_code": "SUBSCRIBER_MUST_START_BOT",
            "severity": "BLOCKED",
            "operator_action": "Ask subscriber to open the bot and press Start, then retry delivery.",
            "technical_reason": "Telegram blocks bots from initiating private conversations with users.",
        }
    if "chat not found" in error:
        if chat_id and not chat_id.startswith("-"):
            return {
                "action_code": "PRIVATE_CHAT_NOT_FOUND",
                "severity": "BLOCKED",
                "operator_action": "Ask subscriber to open the same Horus bot, press Start, then recheck the private chat ID and retry.",
                "technical_reason": "Telegram could not resolve this private user chat for the configured bot.",
            }
        return {
            "action_code": "CHAT_ID_NOT_FOUND",
            "severity": "BLOCKED",
            "operator_action": "Verify the stored Telegram chat ID and ensure the bot is a member of that chat or channel.",
            "technical_reason": "Telegram could not resolve the target chat ID.",
        }
    if "bot was blocked by the user" in error or "user is deactivated" in error or ("blocked" in error and "bot" in error):
        return {
            "action_code": "SUBSCRIBER_BLOCKED_BOT",
            "severity": "BLOCKED",
            "operator_action": "Subscriber has blocked the bot or deactivated their account. Contact subscriber via secondary channel or pause subscription.",
            "technical_reason": "Telegram returned 403 Forbidden (bot was blocked by user or user deactivated).",
        }
    if "forbidden" in error:
        if chat_id.startswith("-100"):
            return {
                "action_code": "BOT_NOT_ALLOWED_IN_CHANNEL",
                "severity": "BLOCKED",
                "operator_action": "Add the bot to the channel or group and grant posting permission, then retry delivery.",
                "technical_reason": "Telegram rejected the bot for this channel or group destination.",
            }
        return {
            "action_code": "SUBSCRIBER_FORBIDDEN",
            "severity": "BLOCKED",
            "operator_action": "Subscriber destination access was rejected by Telegram (403 Forbidden). Verify chat ID and bot permissions.",
            "technical_reason": "Telegram returned 403 Forbidden for this recipient destination.",
        }
    if "not found" in error or "unauthorized" in error or "401" in error:
        return {
            "action_code": "BOT_TOKEN_INVALID",
            "severity": "BLOCKED",
            "operator_action": "Update the Telegram bot token in settings and send a chat test before retrying reports.",
            "technical_reason": "Telegram did not accept the configured bot token.",
        }
    if "max retries" in error or "timeout" in error or "connection" in error:
        return {
            "action_code": "TELEGRAM_NETWORK_RETRY",
            "severity": "RETRYABLE",
            "operator_action": "Retry delivery after verifying network access to Telegram.",
            "technical_reason": "Telegram delivery failed after retry attempts or network timeout.",
        }
    return {
        "action_code": "TELEGRAM_DELIVERY_FAILED",
        "severity": "REVIEW",
        "operator_action": "Review the Telegram error and verify token, chat ID, and bot permissions before retrying.",
        "technical_reason": "Telegram returned an unclassified delivery failure.",
    }


def process_managed_advisory_reports(
    *,
    send_message_fn: Callable[..., dict],
    limit: int = 25,
) -> dict[str, Any]:
    summary = {"sent": 0, "failed": 0, "skipped": 0, "skip_reasons": {}}
    clients = (
        Client.select()
        .where((Client.subscription_tier == MANAGED_ADVISORY) & (Client.is_active == True))
        .order_by(Client.name.asc())
        .limit(max(1, min(int(limit or 25), 200)))
    )
    for client in clients:
        for portfolio in linked_portfolios(client):
            try:
                report = build_portfolio_advisory_report(client.id, portfolio.id)
                if int(report.get("summary", {}).get("action_items", 0) or 0) <= 0:
                    _increment(summary["skip_reasons"], "no_action_items")
                    summary["skipped"] += 1
                    continue
                _, delivery = send_advisory_report(client.id, portfolio.id, send_message_fn=send_message_fn)
                if delivery.status == "SENT":
                    summary["sent"] += 1
                else:
                    summary["failed"] += 1
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                _increment(summary["skip_reasons"], str(detail.get("error_reason") or "blocked"))
                summary["skipped"] += 1
            except Exception:
                _increment(summary["skip_reasons"], "unexpected_error")
                summary["failed"] += 1
    return {"status": "completed", "summary": summary}


def emit_subscription_audit(
    *,
    event_type: str,
    severity: str = "INFO",
    client: Optional[Client] = None,
    portfolio: Optional[Portfolio] = None,
    message: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    try:
        SignalAuditEvent.create(
            event_type=event_type,
            severity=severity,
            actor_type="ADMIN" if severity != "INFO" else "SYSTEM",
            client=client,
            portfolio=portfolio,
            entity_type="SUBSCRIPTION",
            entity_id=str(client.id) if client else None,
            message=message,
            details_json=json.dumps(details or {}),
        )
    except Exception:
        return
