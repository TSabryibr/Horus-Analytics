"""
DATABASE ACCOUNTS & CLIENT MODELS
=================================
Peewee ORM models for Clients, API Keys, Entitlements, Subscription Deliveries, and Audit Events.
"""

from __future__ import annotations

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from core import TimeUtils
from .base import BaseModel
from .portfolio import Portfolio
from .signals import SignalRun


class Client(BaseModel):
    name = CharField(unique=True)
    is_active = BooleanField(default=True)
    subscription_tier = CharField(default="SIGNALS_ONLY")
    telegram_chat_id = CharField(null=True)
    report_language = CharField(default="EN")
    risk_profile = CharField(default="BALANCED")
    default_currency = CharField(default="EGP")
    paid_until = DateField(null=True)
    notes = TextField(null=True)
    description = TextField(null=True)
    delivery_paused = BooleanField(default=False)
    delivery_fail_count = IntegerField(default=0)
    created_at = DateTimeField(default=TimeUtils.now)
    updated_at = DateTimeField(default=TimeUtils.now)


class ClientApiKey(BaseModel):
    client = ForeignKeyField(Client, backref='api_keys', on_delete='CASCADE')
    key_hash = CharField(unique=True)
    key_prefix = CharField()
    is_active = BooleanField(default=True)
    last_used_at = DateTimeField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)


class ClientEntitlement(BaseModel):
    client = ForeignKeyField(Client, backref='entitlements', on_delete='CASCADE')
    portfolio = ForeignKeyField(Portfolio, backref='client_entitlements', on_delete='CASCADE')
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = ((('client', 'portfolio'), True),)


class SubscriptionDelivery(BaseModel):
    client = ForeignKeyField(Client, backref='subscription_deliveries', on_delete='CASCADE')
    portfolio = ForeignKeyField(Portfolio, backref='subscription_deliveries', null=True, on_delete='SET NULL')
    run = ForeignKeyField(SignalRun, backref='subscription_deliveries', null=True, on_delete='SET NULL')
    delivery_type = CharField(default="PORTFOLIO_ADVISORY")
    subscription_tier = CharField(default="SIGNALS_ONLY")
    channel = CharField(default="TELEGRAM")
    status = CharField(default="PENDING")
    chat_id = CharField(null=True)
    provider_message_id = CharField(null=True)
    message_preview = TextField(null=True)
    last_error = TextField(null=True)
    details_json = TextField(default="{}")
    sent_at = DateTimeField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('client', 'created_at'), False),
            (('portfolio', 'created_at'), False),
            (('status', 'created_at'), False),
        )


class SignalAuditEvent(BaseModel):
    event_type = CharField()
    severity = CharField(default="INFO")  # INFO, WARN, ERROR
    actor_type = CharField(default="SYSTEM")  # SYSTEM, ADMIN, CLIENT_API_KEY
    actor_id = CharField(null=True)
    client = ForeignKeyField(Client, backref='audit_events', null=True, on_delete='SET NULL')
    run = ForeignKeyField(SignalRun, backref='audit_events', null=True, on_delete='SET NULL')
    portfolio = ForeignKeyField(Portfolio, backref='audit_events', null=True, on_delete='SET NULL')
    entity_type = CharField(null=True)
    entity_id = CharField(null=True)
    message = TextField(null=True)
    details_json = TextField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('event_type', 'created_at'), False),
            (('severity', 'created_at'), False),
            (('client', 'created_at'), False),
            (('run', 'created_at'), False),
            (('portfolio', 'created_at'), False),
        )
