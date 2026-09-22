"""
Horus Analytics - Canonical SQLAlchemy 2.0 Database Layer.
Provides async & sync engine configuration, declarative models,
and thread-safe session lifecycle providers.
"""

from __future__ import annotations

import contextlib
import datetime
import os
import sys
from typing import AsyncGenerator, Generator, Optional, List

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

# -----------------------------------------------------------------------------
# Database Configuration & Engines
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("HORUS_ASYNC_DB_URL", "sqlite+aiosqlite:///horus_async.db")

# Derive synchronous SQLite URL for thread-safe background workers / scripts
SYNC_DATABASE_URL = os.getenv(
    "HORUS_SYNC_DB_URL",
    DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///"),
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False, class_=Session)


class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------
# 1. Portfolio & Execution Models
# -----------------------------------------------------------------------------
class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    type: Mapped[str] = mapped_column(String(50), default="USER")
    auto_manage: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cash_egp: Mapped[float] = mapped_column(Float, default=0.0)
    cash_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    positions: Mapped[List["Position"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    trades: Mapped[List["Trade"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    broker_orders: Mapped[List["BrokerOrder"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    snapshots: Mapped[List["PortfolioSnapshot"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioDefaultState(Base):
    __tablename__ = "portfolio_default_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, default="GLOBAL_DEFAULT")
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class Position(Base):
    __tablename__ = "position"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50), index=True)
    shares: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    target_price: Mapped[float] = mapped_column(Float)
    target_price_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tp1_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entry_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    currency: Mapped[str] = mapped_column(String(10), default="EGP")
    entry_usd_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slippage_bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    execution_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signal_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    portfolio: Mapped[Optional["Portfolio"]] = relationship(back_populates="positions")


class Trade(Base):
    __tablename__ = "trade"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50), index=True)
    shares: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    entry_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    exit_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    pnl: Mapped[float] = mapped_column(Float)
    pnl_pct: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(100), default="MANUAL")
    currency: Mapped[str] = mapped_column(String(10), default="EGP")
    entry_usd_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_usd_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slippage_bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    execution_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signal_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    portfolio: Mapped[Optional["Portfolio"]] = relationship(back_populates="trades")


class BrokerOrder(Base):
    __tablename__ = "broker_order"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(50), default="PENDING")
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    filled_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slippage_bps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    portfolio: Mapped[Optional["Portfolio"]] = relationship(back_populates="broker_orders")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    equity_egp: Mapped[float] = mapped_column(Float)
    equity_usd: Mapped[float] = mapped_column(Float)
    cash_egp: Mapped[float] = mapped_column(Float)
    cash_usd: Mapped[float] = mapped_column(Float)
    position_count: Mapped[int] = mapped_column(Integer)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="snapshots")

    __table_args__ = (
        Index("idx_portfoliosnapshot_portfolio_date", "portfolio_id", "date", unique=True),
    )


# -----------------------------------------------------------------------------
# 2. Signals & Pipeline Models
# -----------------------------------------------------------------------------
class Signal(Base):
    __tablename__ = "signal"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50))
    date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    signal_type: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(100), default="Scanner")
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_signal_ticker_date_type", "ticker", "date", "signal_type", unique=True),
    )


class BackfillIntradayCheckpoint(Base):
    __tablename__ = "backfill_intraday_checkpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    checkpoint_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    ticker: Mapped[str] = mapped_column(String(50))
    signal_type: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50), default="BackfillIntraday")
    universe_choice: Mapped[str] = mapped_column(String(50), default="EGX30")
    price: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    __table_args__ = (
        Index("idx_backfill_session_ticker_sig", "session_date", "checkpoint_at", "ticker", "signal_type", "source", unique=True),
    )


class SignalRun(Base):
    __tablename__ = "signal_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    scan_type: Mapped[str] = mapped_column(String(50), default="DAILY")
    run_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    universe_count: Mapped[int] = mapped_column(Integer, default=0)
    signals_count: Mapped[int] = mapped_column(Integer, default=0)
    published_count: Mapped[int] = mapped_column(Integer, default=0)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recommendations: Mapped[List["SignalRecommendation"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    deliveries: Mapped[List["SignalDelivery"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    outcomes: Mapped[List["SignalOutcome"]] = relationship(back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_signalrun_date_type", "run_date", "scan_type", unique=True),
    )


class SignalRecommendation(Base):
    __tablename__ = "signal_recommendation"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("signal_run.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10), default="BUY")
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    target_price: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invalidation_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=5)
    regime: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_cutoff_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    run: Mapped["SignalRun"] = relationship(back_populates="recommendations")
    outcome: Mapped[Optional["SignalOutcome"]] = relationship(back_populates="recommendation", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_signalrecommendation_run_ticker_side", "run_id", "ticker", "side", unique=True),
    )


class SignalDelivery(Base):
    __tablename__ = "signal_delivery"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("signal_run.id", ondelete="CASCADE"))
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="TELEGRAM")
    service_tier: Mapped[str] = mapped_column(String(50), default="SIGNALS_ONLY")
    destination_type: Mapped[str] = mapped_column(String(50), default="PORTFOLIO")
    destination_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    run: Mapped["SignalRun"] = relationship(back_populates="deliveries")

    __table_args__ = (
        Index("idx_signaldelivery_run_portfolio_channel", "run_id", "portfolio_id", "channel"),
        Index("idx_signaldelivery_run_channel_destination", "run_id", "channel", "destination_type", "destination_id", unique=True),
        Index("idx_signaldelivery_destination_status", "destination_type", "status"),
        Index("idx_signaldelivery_service_status", "service_tier", "status"),
    )


class SignalOutcome(Base):
    __tablename__ = "signal_outcome"

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("signal_recommendation.id", ondelete="CASCADE"), unique=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("signal_run.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(50))
    outcome_status: Mapped[str] = mapped_column(String(50), default="NO_TRADE")
    entry_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    exit_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_adverse_excursion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_favorable_excursion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    holding_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recommendation: Mapped["SignalRecommendation"] = relationship(back_populates="outcome")
    run: Mapped["SignalRun"] = relationship(back_populates="outcomes")


class PublishedSignalLifecycle(Base):
    __tablename__ = "published_signal_lifecycle"

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("signal_recommendation.id", ondelete="CASCADE"))
    run_id: Mapped[int] = mapped_column(ForeignKey("signal_run.id", ondelete="CASCADE"))
    delivery_id: Mapped[int] = mapped_column(ForeignKey("signal_delivery.id", ondelete="CASCADE"))
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10), default="BUY")
    lane: Mapped[str] = mapped_column(String(50), default="SWING")
    source_module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operating_mode: Mapped[str] = mapped_column(String(50), default="MANUAL")
    channel: Mapped[str] = mapped_column(String(50), default="TELEGRAM")
    published_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="PUBLISHED")
    resolution_source: Mapped[str] = mapped_column(String(50), default="AUTO")
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    tp1_hit_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    entry_price_planned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entry_price_filled: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss_initial: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss_active: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_price_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_price_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    override_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_market_event_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    events: Mapped[List["PublishedSignalLifecycleEvent"]] = relationship(back_populates="lifecycle", cascade="all, delete-orphan")


class PublishedSignalLifecycleEvent(Base):
    __tablename__ = "published_signal_lifecycle_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    lifecycle_id: Mapped[int] = mapped_column(ForeignKey("published_signal_lifecycle.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(100))
    from_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_source: Mapped[str] = mapped_column(String(50), default="AUTO")
    actor_type: Mapped[str] = mapped_column(String(50), default="SYSTEM")
    actor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_time: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    price_context_json: Mapped[str] = mapped_column(Text, default="{}")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    lifecycle: Mapped["PublishedSignalLifecycle"] = relationship(back_populates="events")


class PublishedSignalFollowUp(Base):
    __tablename__ = "published_signal_follow_up"

    id: Mapped[int] = mapped_column(primary_key=True)
    lifecycle_id: Mapped[int] = mapped_column(ForeignKey("published_signal_lifecycle.id", ondelete="CASCADE"))
    recommendation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_recommendation.id", ondelete="SET NULL"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_run.id", ondelete="SET NULL"), nullable=True)
    delivery_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_delivery.id", ondelete="SET NULL"), nullable=True)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10), default="BUY")
    lane: Mapped[str] = mapped_column(String(50), default="SWING")
    source_module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operating_mode: Mapped[str] = mapped_column(String(50), default="MANUAL")
    channel: Mapped[str] = mapped_column(String(50), default="TELEGRAM")
    service_tier: Mapped[str] = mapped_column(String(50), default="SIGNALS_ONLY")
    destination_type: Mapped[str] = mapped_column(String(50), default="PORTFOLIO")
    destination_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_state: Mapped[str] = mapped_column(String(50))
    message_type: Mapped[str] = mapped_column(String(50), default="UPDATE")
    queue_state: Mapped[str] = mapped_column(String(50), default="PENDING")
    draft_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telegram_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    suppressed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    suppression_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class HorusExecution(Base):
    __tablename__ = "horus_execution"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_run.id", ondelete="SET NULL"), nullable=True)
    recommendation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_recommendation.id", ondelete="SET NULL"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50))
    state: Mapped[str] = mapped_column(String(50), default="PENDING_OPEN")
    trigger_source: Mapped[str] = mapped_column(String(50), default="INTRADAY")
    planned_entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gap_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gap_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    active_stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trailing_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    close_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trade_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    open_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    update_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    close_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    skip_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalExecutionAttribution(Base):
    __tablename__ = "signal_execution_attribution"

    id: Mapped[int] = mapped_column(primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("horus_execution.id", ondelete="CASCADE"), unique=True)
    execution_portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    strategy_portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    recommendation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_recommendation.id", ondelete="SET NULL"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_run.id", ondelete="SET NULL"), nullable=True)
    lane: Mapped[str] = mapped_column(String(50), default="SWING")
    scan_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    strategy_profile_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    strategy_source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    signal_side: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    signal_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalValidationRun(Base):
    __tablename__ = "signal_validation_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    window_days: Mapped[int] = mapped_column(Integer, default=90)
    closed_signals: Mapped[int] = mapped_column(Integer, default=0)
    win_rate_pct: Mapped[float] = mapped_column(Float, default=0.0)
    avg_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="PASS")
    degradation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class TickerStrategyMetrics(Base):
    __tablename__ = "ticker_strategy_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50))
    window_days: Mapped[int] = mapped_column(Integer)
    total_signals: Mapped[int] = mapped_column(Integer)
    win_rate_pct: Mapped[float] = mapped_column(Float)
    avg_gain_pct: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown: Mapped[float] = mapped_column(Float, default=0.0)
    expectancy: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    __table_args__ = (
        Index("idx_tickerstrategymetrics_ticker_window", "ticker", "window_days", unique=True),
    )


class LegacySignalOutcome(Base):
    __tablename__ = "legacy_signal_outcome"

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal.id", ondelete="SET NULL"), nullable=True)
    ticker: Mapped[str] = mapped_column(String(50))
    signal_date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    entry_price: Mapped[float] = mapped_column(Float)
    max_price: Mapped[float] = mapped_column(Float)
    min_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    max_gain_pct: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    target_1_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    target_2_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_loss_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome_status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalSuppressionLog(Base):
    __tablename__ = "signal_suppression_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(Float)
    score: Mapped[int] = mapped_column(Integer, default=0)
    suppression_tag: Mapped[str] = mapped_column(String(100))
    kill_reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalGuardState(Base):
    __tablename__ = "signal_guard_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, default="PUBLISH")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalDeskState(Base):
    __tablename__ = "signal_desk_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, default="PRIMARY")
    operating_mode: Mapped[str] = mapped_column(String(50), default="MANUAL")
    autopilot_armed: Mapped[bool] = mapped_column(Boolean, default=False)
    autopilot_status: Mapped[str] = mapped_column(String(50), default="IDLE")
    last_autopilot_run_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_autopilot_attempted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_autopilot_published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_autopilot_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    autopilot_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    publish_policy_json: Mapped[str] = mapped_column(Text, default="{}")
    lane_preferences_json: Mapped[str] = mapped_column(Text, default="{}")
    manual_queue_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalStateArchive(Base):
    __tablename__ = "signal_state_archive"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    final_status: Mapped[str] = mapped_column(String(50))
    signal_score: Mapped[int] = mapped_column(Integer)
    filter_snapshot_json: Mapped[str] = mapped_column(Text)
    kill_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signal_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)


# -----------------------------------------------------------------------------
# 3. Market & Intelligence Models
# -----------------------------------------------------------------------------
class Holiday(Base):
    __tablename__ = "holiday"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class ProvisioningState(Base):
    __tablename__ = "provisioning_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, default="HISTORICAL_SIGNAL_PROVISIONING")
    target_trading_days: Mapped[int] = mapped_column(Integer, default=252)
    completed_trading_days: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="IDLE")
    mode: Mapped[str] = mapped_column(String(50), default="AUTOMATIC")
    backfill_universe_choice: Mapped[str] = mapped_column(String(50), default="EGX30")
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SovereignState(Base):
    __tablename__ = "sovereign_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50), unique=True)
    trap_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[str] = mapped_column(String(50), default="HIGH")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class ScannerStrategyProfile(Base):
    __tablename__ = "scanner_strategy_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_name: Mapped[str] = mapped_column(String(100), unique=True)
    source_type: Mapped[str] = mapped_column(String(50), default="PINE")
    script_source: Mapped[str] = mapped_column(Text)
    script_hash: Mapped[str] = mapped_column(String(100), unique=True)
    market: Mapped[str] = mapped_column(String(50), default="EGX30")
    timeframe: Mapped[str] = mapped_column(String(50), default="1D")
    profile_state: Mapped[str] = mapped_column(String(50), default="DRAFT")
    backtest_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    compatibility_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    ranking_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    ready_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    activated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    activation_count: Mapped[int] = mapped_column(Integer, default=0)
    activation_history_json: Mapped[str] = mapped_column(Text, default="[]")
    import_rule_spec_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class AssetAiReport(Base):
    __tablename__ = "asset_ai_report"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50))
    generated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    payload_json: Mapped[str] = mapped_column(Text)
    source_module: Mapped[str] = mapped_column(String(50), default="OLLAMA")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        Index("idx_asset_ai_report_ticker_gen", "ticker", "generated_at"),
    )


# -----------------------------------------------------------------------------
# 4. Client & Multi-Tenant Entitlement Models
# -----------------------------------------------------------------------------
class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="SIGNALS_ONLY")
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    report_language: Mapped[str] = mapped_column(String(10), default="EN")
    risk_profile: Mapped[str] = mapped_column(String(50), default="BALANCED")
    default_currency: Mapped[str] = mapped_column(String(10), default="EGP")
    paid_until: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_fail_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    api_keys: Mapped[List["ClientApiKey"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    entitlements: Mapped[List["ClientEntitlement"]] = relationship(back_populates="client", cascade="all, delete-orphan")


class ClientApiKey(Base):
    __tablename__ = "client_api_key"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    key_prefix: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    client: Mapped["Client"] = relationship(back_populates="api_keys")


class ClientEntitlement(Base):
    __tablename__ = "client_entitlement"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"))
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    client: Mapped["Client"] = relationship(back_populates="entitlements")

    __table_args__ = (
        Index("idx_cliententitlement_client_portfolio", "client_id", "portfolio_id", unique=True),
    )


class SubscriptionDelivery(Base):
    __tablename__ = "subscription_delivery"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"))
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_run.id", ondelete="SET NULL"), nullable=True)
    delivery_type: Mapped[str] = mapped_column(String(50), default="PORTFOLIO_ADVISORY")
    subscription_tier: Mapped[str] = mapped_column(String(50), default="SIGNALS_ONLY")
    channel: Mapped[str] = mapped_column(String(50), default="TELEGRAM")
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class SignalAuditEvent(Base):
    __tablename__ = "signal_audit_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50), default="INFO")
    actor_type: Mapped[str] = mapped_column(String(50), default="SYSTEM")
    actor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("client.id", ondelete="SET NULL"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("signal_run.id", ondelete="SET NULL"), nullable=True)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolio.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    __table_args__ = (
        Index("idx_signalaudit_event_created", "event_type", "created_at"),
        Index("idx_signalaudit_severity_created", "severity", "created_at"),
    )


# -----------------------------------------------------------------------------
# 5. Session Lifecycle Helpers & Dependency Providers
# -----------------------------------------------------------------------------
async def init_db() -> None:
    """Creates all database tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_sync_db() -> None:
    """Creates all database tables synchronously."""
    Base.metadata.create_all(sync_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency yielding an AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    """FastAPI sync dependency yielding a synchronous Session."""
    with SyncSessionLocal() as session:
        yield session


@contextlib.asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing commit/rollback transactional semantics."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@contextlib.contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    """Synchronous context manager providing commit/rollback transactional semantics."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
