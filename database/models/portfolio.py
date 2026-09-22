"""
DATABASE PORTFOLIO MODELS
=========================
Peewee ORM models for Portfolios, Positions, Trades, Orders, and Snapshots.
"""

from __future__ import annotations

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from core import TimeUtils
from .base import BaseModel


class Portfolio(BaseModel):
    name = CharField(unique=True)
    type = CharField(default="USER")  # SYSTEM, USER, ADMIN, STRATEGY
    auto_manage = BooleanField(default=False)
    description = TextField(null=True)
    cash_egp = FloatField(default=0.0)
    cash_usd = FloatField(default=0.0)
    created_at = DateTimeField(default=TimeUtils.now)


class PortfolioDefaultState(BaseModel):
    name = CharField(unique=True, default="GLOBAL_DEFAULT")
    portfolio = ForeignKeyField(Portfolio, backref='default_states', null=True, on_delete='SET NULL')
    updated_at = DateTimeField(default=TimeUtils.now)


class Position(BaseModel):
    portfolio = ForeignKeyField(Portfolio, backref='positions', null=True)
    ticker = CharField()
    shares = IntegerField()
    entry_price = FloatField()
    stop_loss = FloatField()
    target_price = FloatField()
    target_price_2 = FloatField(null=True)
    tp1_hit = BooleanField(default=False)
    current_price = FloatField(null=True)
    entry_date = DateTimeField(default=TimeUtils.now)
    status = CharField(default="OPEN")
    currency = CharField(default="EGP")
    entry_usd_rate = FloatField(null=True)
    sector = CharField(null=True)
    notes = TextField(null=True)
    risk_amount = FloatField(null=True)
    slippage_bps = FloatField(null=True)
    execution_latency_ms = IntegerField(null=True)
    signal_id = CharField(null=True, index=True)


class Trade(BaseModel):
    portfolio = ForeignKeyField(Portfolio, backref='trades', null=True)
    ticker = CharField()
    shares = IntegerField()
    entry_price = FloatField()
    exit_price = FloatField()
    entry_date = DateTimeField()
    exit_date = DateTimeField(default=TimeUtils.now)
    pnl = FloatField()
    pnl_pct = FloatField()
    reason = CharField(default="MANUAL")
    currency = CharField(default="EGP")
    entry_usd_rate = FloatField(null=True)
    exit_usd_rate = FloatField(null=True)
    slippage_bps = FloatField(null=True)
    execution_latency_ms = IntegerField(null=True)
    signal_id = CharField(null=True, index=True)


class BrokerOrder(BaseModel):
    portfolio = ForeignKeyField(Portfolio, backref='broker_orders', null=True)
    symbol = CharField()
    side = CharField()  # BUY, SELL
    quantity = IntegerField()
    price = FloatField()
    state = CharField(default="PENDING")  # PENDING, SUBMITTED, FILLED, REJECTED
    broker_order_id = CharField(null=True)
    filled_price = FloatField(null=True)
    slippage_bps = IntegerField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)
    updated_at = DateTimeField(default=TimeUtils.now)


class PortfolioSnapshot(BaseModel):
    portfolio = ForeignKeyField(Portfolio, backref='snapshots', on_delete='CASCADE')
    date = DateField(default=TimeUtils.today)
    equity_egp = FloatField()
    equity_usd = FloatField()
    cash_egp = FloatField()
    cash_usd = FloatField()
    position_count = IntegerField()

    class Meta:
        indexes = ((('portfolio', 'date'), True),)
