import datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from core import TelegramBot_Alerts
from core import subscriptions


router = APIRouter(tags=["subscriptions"])


class SubscriberCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    subscription_tier: str = subscriptions.SIGNALS_ONLY
    telegram_chat_id: Optional[str] = None
    report_language: Optional[str] = None
    risk_profile: str = "BALANCED"
    default_currency: str = "EGP"
    paid_until: Optional[datetime.date] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    portfolio_id: Optional[int] = Field(None, ge=1)
    create_portfolio: bool = False


class SubscriberUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1)
    subscription_tier: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    report_language: Optional[str] = None
    risk_profile: Optional[str] = None
    default_currency: Optional[str] = None
    paid_until: Optional[datetime.date] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PortfolioLinkRequest(BaseModel):
    portfolio_id: int = Field(..., ge=1)


class AdvisorySendRequest(BaseModel):
    portfolio_id: int = Field(..., ge=1)


@router.get("/api/v1/subscribers")
def list_subscribers():
    return subscriptions.list_subscribers_payload()


@router.get("/api/v1/subscribers/deliveries")
def list_subscription_deliveries(
    client_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=500),
):
    return subscriptions.list_deliveries_payload(client_id=client_id, limit=limit)


@router.post("/api/v1/subscribers/deliveries/{delivery_id}/retry")
def retry_subscription_delivery(delivery_id: int):
    payload = subscriptions.retry_subscription_delivery(
        delivery_id,
        send_message_fn=TelegramBot_Alerts.send_message,
    )
    if payload.get("status") == "failed":
        return JSONResponse(status_code=502, content=payload)
    return payload


@router.post("/api/v1/subscribers")
def create_subscriber(req: SubscriberCreateRequest):
    client = subscriptions.provision_subscriber(
        name=req.name,
        subscription_tier=req.subscription_tier,
        telegram_chat_id=req.telegram_chat_id,
        report_language=req.report_language,
        paid_until=req.paid_until,
        risk_profile=req.risk_profile,
        default_currency=req.default_currency,
        notes=req.notes,
        description=req.description,
        is_active=req.is_active,
        portfolio_id=req.portfolio_id,
        create_portfolio=req.create_portfolio,
    )
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_CREATED",
        client=client,
        message="Subscriber record created.",
        details={
            "subscription_tier": client.subscription_tier,
            "portfolio_id": req.portfolio_id,
            "create_portfolio": req.create_portfolio,
        },
    )
    return {"status": "created", "subscriber": subscriptions.serialize_client(client)}


@router.get("/api/v1/subscribers/{client_id}")
def get_subscriber(client_id: int):
    return {"subscriber": subscriptions.serialize_client(subscriptions._client_by_id(client_id))}


@router.patch("/api/v1/subscribers/{client_id}")
def update_subscriber(client_id: int, req: SubscriberUpdateRequest):
    updates = req.model_dump(exclude_unset=True)
    client = subscriptions.update_subscriber(client_id, updates)
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_UPDATED",
        client=client,
        message="Subscriber record updated.",
        details={"updated_fields": sorted(updates.keys())},
    )
    return {"status": "updated", "subscriber": subscriptions.serialize_client(client)}


@router.post("/api/v1/subscribers/{client_id}/archive")
def archive_subscriber(client_id: int):
    client = subscriptions.archive_subscriber(client_id)
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_ARCHIVED",
        client=client,
        message="Subscriber archived without deleting delivery history.",
        details={"is_active": False},
    )
    return {"status": "archived", "subscriber": subscriptions.serialize_client(client)}


@router.post("/api/v1/subscribers/{client_id}/portfolios")
def link_subscriber_portfolio(client_id: int, req: PortfolioLinkRequest):
    client = subscriptions.link_portfolio(client_id, req.portfolio_id)
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_PORTFOLIO_LINKED",
        client=client,
        message="Subscriber linked to portfolio.",
        details={"portfolio_id": req.portfolio_id},
    )
    return {"status": "linked", "subscriber": subscriptions.serialize_client(client)}


@router.delete("/api/v1/subscribers/{client_id}/portfolios/{portfolio_id}")
def unlink_subscriber_portfolio(client_id: int, portfolio_id: int):
    client = subscriptions.unlink_portfolio(client_id, portfolio_id)
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_PORTFOLIO_UNLINKED",
        client=client,
        message="Subscriber unlinked from portfolio.",
        details={"portfolio_id": portfolio_id},
    )
    return {"status": "unlinked", "subscriber": subscriptions.serialize_client(client)}


@router.post("/api/v1/subscribers/{client_id}/telegram-test/send")
def send_subscriber_telegram_test(client_id: int):
    delivery = subscriptions.send_telegram_chat_test(
        client_id,
        send_message_fn=TelegramBot_Alerts.send_message,
    )
    payload = {
        "status": "sent" if delivery.status == "SENT" else "failed",
        "delivery": subscriptions.serialize_delivery(delivery),
    }
    if delivery.status == "FAILED":
        return JSONResponse(status_code=502, content=payload)
    return payload


@router.get("/api/v1/subscribers/{client_id}/advisory-report")
def generate_advisory_report(
    client_id: int,
    portfolio_id: int = Query(..., ge=1),
):
    report = subscriptions.build_portfolio_advisory_report(client_id, portfolio_id)
    preview = subscriptions.format_advisory_report_for_telegram(report)
    subscriptions.emit_subscription_audit(
        event_type="SUBSCRIPTION_ADVISORY_GENERATED",
        client=subscriptions._client_by_id(client_id),
        message="Subscriber advisory report generated.",
        details={"portfolio_id": portfolio_id, "action_items": report.get("summary", {}).get("action_items", 0)},
    )
    return {"report": report, "telegram_preview": preview}


@router.post("/api/v1/subscribers/{client_id}/advisory-report/send")
def send_advisory_report(client_id: int, req: AdvisorySendRequest):
    report, delivery = subscriptions.send_advisory_report(
        client_id,
        req.portfolio_id,
        send_message_fn=TelegramBot_Alerts.send_message,
    )
    payload = {
        "status": "sent" if delivery.status == "SENT" else "failed",
        "report": report,
        "delivery": subscriptions.serialize_delivery(delivery),
    }
    if delivery.status == "FAILED":
        return JSONResponse(status_code=502, content=payload)
    return payload


@router.post("/api/v1/subscribers/managed-advisory/process")
def process_managed_advisory(limit: int = Query(25, ge=1, le=200)):
    return subscriptions.process_managed_advisory_reports(
        send_message_fn=TelegramBot_Alerts.send_message,
        limit=limit,
    )
