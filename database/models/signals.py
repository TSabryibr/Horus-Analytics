"""
DATABASE SIGNALS & EXECUTION MODELS
===================================
Peewee ORM models for Signals, Runs, Recommendations, Deliveries, Outcomes, Lifecycles, and Desk state.
"""

from __future__ import annotations

import datetime
from typing import Optional
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
from .portfolio import Portfolio


class Signal(BaseModel):
    ticker = CharField()
    date = DateField(default=TimeUtils.today)
    signal_type = CharField()
    price = FloatField()
    score = FloatField(default=0.0)
    source = CharField(default="Scanner")
    processed = BooleanField(default=False)
    rationale = TextField(null=True)

    class Meta:
        indexes = ((('ticker', 'date', 'signal_type', 'source'), True),)


class BackfillIntradayCheckpoint(BaseModel):
    session_date = DateField(default=TimeUtils.today)
    checkpoint_at = DateTimeField(default=TimeUtils.now)
    ticker = CharField()
    signal_type = CharField()
    source = CharField(default="BackfillIntraday")
    universe_choice = CharField(default="EGX30")
    price = FloatField()
    score = FloatField(default=0.0)
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('session_date', 'checkpoint_at', 'ticker', 'signal_type', 'source'), True),
            (('session_date', 'source'), False),
            (('ticker', 'checkpoint_at'), False),
        )


class SignalRun(BaseModel):
    run_date = DateField(default=TimeUtils.today)
    scan_type = CharField(default="DAILY")  # DAILY, INTRADAY, PRE_CLOSE
    run_key = CharField(unique=True, null=True)
    status = CharField(default="PENDING")   # PENDING, RUNNING, COMPLETED, BLOCKED, ERROR
    started_at = DateTimeField(default=TimeUtils.now)
    completed_at = DateTimeField(null=True)
    universe_count = IntegerField(default=0)
    signals_count = IntegerField(default=0)
    published_count = IntegerField(default=0)
    model_version = CharField(null=True)
    error = TextField(null=True)

    class Meta:
        indexes = ((('run_key',), True),)


class SignalRecommendation(BaseModel):
    run = ForeignKeyField(SignalRun, backref='recommendations', on_delete='CASCADE')
    ticker = CharField()
    side = CharField(default="BUY")
    entry_price = FloatField()
    stop_loss = FloatField()
    target_price = FloatField()
    score = FloatField(default=0.0)
    confidence = FloatField(default=0.0)
    rationale_json = TextField(null=True)
    invalidation_rule = TextField(null=True)
    horizon_days = IntegerField(default=5)
    regime = CharField(null=True)
    data_cutoff_at = DateTimeField(null=True)
    state = CharField(default="ACTIVE")
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = ((('run', 'ticker', 'side'), True),)


class SignalDelivery(BaseModel):
    run = ForeignKeyField(SignalRun, backref='deliveries', on_delete='CASCADE')
    portfolio = ForeignKeyField(Portfolio, backref='signal_deliveries', null=True, on_delete='SET NULL')
    channel = CharField(default="TELEGRAM")
    service_tier = CharField(default="SIGNALS_ONLY")
    destination_type = CharField(default="PORTFOLIO")
    destination_id = CharField(null=True)
    destination_name = CharField(null=True)
    destination_chat_id = CharField(null=True)
    status = CharField(default="PENDING")  # PENDING, SENT, FAILED, DRY_RUN, SKIPPED
    provider_message_id = CharField(null=True)
    attempts = IntegerField(default=0)
    last_error = TextField(null=True)
    sent_at = DateTimeField(null=True)
    latency_ms = FloatField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('run', 'portfolio', 'channel'), False),
            (('run', 'channel', 'destination_type', 'destination_id'), True),
            (('destination_type', 'status'), False),
            (('service_tier', 'status'), False),
        )


class SignalOutcome(BaseModel):
    recommendation = ForeignKeyField(
        SignalRecommendation,
        backref='outcome',
        unique=True,
        on_delete='CASCADE'
    )
    run = ForeignKeyField(SignalRun, backref='outcomes', on_delete='CASCADE')
    ticker = CharField()
    outcome_status = CharField(default="NO_TRADE")  # NO_TRADE, OPEN, CLOSED
    entry_date = DateTimeField(null=True)
    exit_date = DateTimeField(null=True)
    entry_price = FloatField(null=True)
    exit_price = FloatField(null=True)
    pnl = FloatField(null=True)
    pnl_pct = FloatField(null=True)
    max_adverse_excursion = FloatField(null=True)
    max_favorable_excursion = FloatField(null=True)
    holding_days = IntegerField(null=True)
    computed_at = DateTimeField(default=TimeUtils.now)
    notes = TextField(null=True)


class PublishedSignalLifecycle(BaseModel):
    recommendation: SignalRecommendation = ForeignKeyField(
        SignalRecommendation,
        backref='published_lifecycles',
        on_delete='CASCADE'
    )
    run: SignalRun = ForeignKeyField(SignalRun, backref='published_lifecycles', on_delete='CASCADE')
    delivery: SignalDelivery = ForeignKeyField(SignalDelivery, backref='published_lifecycles', on_delete='CASCADE')
    portfolio: Optional[Portfolio] = ForeignKeyField(Portfolio, backref='published_signal_lifecycles', null=True, on_delete='SET NULL')
    ticker: str = CharField()
    side: str = CharField(default="BUY")
    lane: str = CharField(default="SWING")
    source_module: Optional[str] = CharField(null=True)
    operating_mode: str = CharField(default="MANUAL")
    channel: str = CharField(default="TELEGRAM")
    published_message_id: Optional[str] = CharField(null=True)
    state: str = CharField(default="PUBLISHED")
    resolution_source: str = CharField(default="AUTO")
    published_at: datetime.datetime = DateTimeField(default=TimeUtils.now)
    expires_at: Optional[datetime.datetime] = DateTimeField(null=True)
    opened_at: Optional[datetime.datetime] = DateTimeField(null=True)
    tp1_hit_at: Optional[datetime.datetime] = DateTimeField(null=True)
    closed_at: Optional[datetime.datetime] = DateTimeField(null=True)
    entry_price_planned: Optional[float] = FloatField(null=True)
    entry_price_filled: Optional[float] = FloatField(null=True)
    stop_loss_initial: Optional[float] = FloatField(null=True)
    stop_loss_active: Optional[float] = FloatField(null=True)
    target_price_1: Optional[float] = FloatField(null=True)
    target_price_2: Optional[float] = FloatField(null=True)
    close_price: Optional[float] = FloatField(null=True)
    close_reason: Optional[str] = CharField(null=True)
    override_notes: Optional[str] = TextField(null=True)
    last_market_event_at: Optional[datetime.datetime] = DateTimeField(null=True)
    details_json: str = TextField(default="{}")
    created_at: datetime.datetime = DateTimeField(default=TimeUtils.now)
    updated_at: datetime.datetime = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('delivery', 'recommendation'), True),
            (('state', 'published_at'), False),
            (('lane', 'state'), False),
            (('portfolio', 'state'), False),
        )


class PublishedSignalLifecycleEvent(BaseModel):
    lifecycle: PublishedSignalLifecycle = ForeignKeyField(
        PublishedSignalLifecycle,
        backref='events',
        on_delete='CASCADE',
    )
    event_type: str = CharField()
    from_state: Optional[str] = CharField(null=True)
    to_state: Optional[str] = CharField(null=True)
    event_source: str = CharField(default="AUTO")
    actor_type: str = CharField(default="SYSTEM")
    actor_id: Optional[str] = CharField(null=True)
    event_time: datetime.datetime = DateTimeField(default=TimeUtils.now)
    price_context_json: str = TextField(default="{}")
    notes: Optional[str] = TextField(null=True)
    created_at: datetime.datetime = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('lifecycle', 'event_time'), False),
            (('event_type', 'event_time'), False),
            (('event_source', 'event_time'), False),
        )


class PublishedSignalFollowUp(BaseModel):
    lifecycle = ForeignKeyField(
        PublishedSignalLifecycle,
        backref='follow_ups',
        on_delete='CASCADE',
    )
    recommendation = ForeignKeyField(
        SignalRecommendation,
        backref='published_follow_ups',
        null=True,
        on_delete='SET NULL',
    )
    run = ForeignKeyField(SignalRun, backref='published_follow_ups', null=True, on_delete='SET NULL')
    delivery = ForeignKeyField(SignalDelivery, backref='published_follow_ups', null=True, on_delete='SET NULL')
    portfolio = ForeignKeyField(Portfolio, backref='published_signal_follow_ups', null=True, on_delete='SET NULL')
    ticker = CharField()
    side = CharField(default="BUY")
    lane = CharField(default="SWING")
    source_module = CharField(null=True)
    operating_mode = CharField(default="MANUAL")
    channel = CharField(default="TELEGRAM")
    service_tier = CharField(default="SIGNALS_ONLY")
    destination_type = CharField(default="PORTFOLIO")
    destination_id = CharField(null=True)
    destination_name = CharField(null=True)
    destination_chat_id = CharField(null=True)
    trigger_state = CharField()
    message_type = CharField(default="UPDATE")
    queue_state = CharField(default="PENDING")
    draft_message = TextField(null=True)
    telegram_message_id = CharField(null=True)
    retry_count = IntegerField(default=0)
    last_attempted_at = DateTimeField(null=True)
    ready_at = DateTimeField(null=True)
    sent_at = DateTimeField(null=True)
    suppressed_at = DateTimeField(null=True)
    suppression_reason = TextField(null=True)
    last_error = TextField(null=True)
    details_json = TextField(default="{}")
    created_at = DateTimeField(default=TimeUtils.now)
    updated_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('lifecycle', 'trigger_state'), False),
            (('lifecycle', 'trigger_state', 'destination_type', 'destination_id'), True),
            (('queue_state', 'created_at'), False),
            (('portfolio', 'queue_state'), False),
            (('trigger_state', 'created_at'), False),
            (('destination_type', 'queue_state'), False),
            (('service_tier', 'queue_state'), False),
        )


class HorusExecution(BaseModel):
    portfolio: Portfolio = ForeignKeyField(Portfolio, backref='horus_executions', on_delete='CASCADE')
    run: Optional[SignalRun] = ForeignKeyField(SignalRun, backref='horus_executions', null=True, on_delete='SET NULL')
    recommendation: Optional[SignalRecommendation] = ForeignKeyField(
        SignalRecommendation,
        backref='horus_executions',
        null=True,
        on_delete='SET NULL',
    )
    ticker: str = CharField()
    state: str = CharField(default="PENDING_OPEN")  # PENDING_OPEN, OPEN, UPDATED, CLOSED, SKIPPED, FAILED
    trigger_source: str = CharField(default="INTRADAY")  # INTRADAY, PRE_CLOSE, DAILY_NEXT_OPEN
    planned_entry_price: Optional[float] = FloatField(null=True)
    actual_entry_price: Optional[float] = FloatField(null=True)
    gap_pct: Optional[float] = FloatField(null=True)
    gap_adjusted: bool = BooleanField(default=False)
    active_stop_loss: Optional[float] = FloatField(null=True)
    active_target_price: Optional[float] = FloatField(null=True)
    trailing_state: Optional[str] = TextField(null=True)
    close_reason: Optional[str] = CharField(null=True)
    position_id: Optional[int] = IntegerField(null=True)
    trade_id: Optional[int] = IntegerField(null=True)
    open_message_id: Optional[str] = CharField(null=True)
    update_message_id: Optional[str] = CharField(null=True)
    close_message_id: Optional[str] = CharField(null=True)
    skip_message_id: Optional[str] = CharField(null=True)
    details_json: Optional[str] = TextField(null=True)
    created_at: datetime.datetime = DateTimeField(default=TimeUtils.now)
    updated_at: datetime.datetime = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('portfolio', 'ticker', 'state'), False),
            (('portfolio', 'recommendation'), False),
            (('portfolio', 'run', 'trigger_source'), False),
            (('portfolio', 'open_message_id'), False),
            (('portfolio', 'update_message_id'), False),
            (('portfolio', 'close_message_id'), False),
            (('portfolio', 'skip_message_id'), False),
        )


class SignalExecutionAttribution(BaseModel):
    execution: HorusExecution = ForeignKeyField(
        HorusExecution,
        backref='attribution',
        unique=True,
        on_delete='CASCADE',
    )
    execution_portfolio: Portfolio = ForeignKeyField(
        Portfolio,
        backref='execution_attributions',
        on_delete='CASCADE',
    )
    strategy_portfolio: Optional[Portfolio] = ForeignKeyField(
        Portfolio,
        backref='strategy_attributions',
        null=True,
        on_delete='SET NULL',
    )
    recommendation: Optional[SignalRecommendation] = ForeignKeyField(
        SignalRecommendation,
        backref='execution_attributions',
        null=True,
        on_delete='SET NULL',
    )
    run: Optional[SignalRun] = ForeignKeyField(
        SignalRun,
        backref='execution_attributions',
        null=True,
        on_delete='SET NULL',
    )
    lane: str = CharField(default="SWING")  # INTRADAY, SWING, POSITION
    scan_type: Optional[str] = CharField(null=True)
    strategy_profile_name: Optional[str] = CharField(null=True)
    strategy_source_type: Optional[str] = CharField(null=True)
    signal_side: Optional[str] = CharField(null=True)
    signal_state: Optional[str] = CharField(null=True)
    details_json: str = TextField(default="{}")
    created_at: datetime.datetime = DateTimeField(default=TimeUtils.now)
    updated_at: datetime.datetime = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = (
            (('execution_portfolio', 'lane'), False),
            (('strategy_portfolio', 'lane'), False),
            (('strategy_profile_name', 'lane'), False),
            (('run', 'scan_type'), False),
        )


class SignalValidationRun(BaseModel):
    run_date = DateField(default=TimeUtils.today)
    window_days = IntegerField(default=90)
    closed_signals = IntegerField(default=0)
    win_rate_pct = FloatField(default=0.0)
    avg_pnl_pct = FloatField(default=0.0)
    status = CharField(default="PASS")  # PASS, FAIL
    degradation_reason = TextField(null=True)
    details_json = TextField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)


class TickerStrategyMetrics(BaseModel):
    ticker = CharField()
    window_days = IntegerField()
    total_signals = IntegerField()
    win_rate_pct = FloatField()
    avg_gain_pct = FloatField()
    sharpe_ratio = FloatField(default=0.0)
    max_drawdown = FloatField(default=0.0)
    expectancy = FloatField(default=0.0)
    updated_at = DateTimeField(default=TimeUtils.now)

    class Meta:
        indexes = ((('ticker', 'window_days'), True),)


class LegacySignalOutcome(BaseModel):
    signal = ForeignKeyField(Signal, backref='outcomes', null=True)
    ticker = CharField()
    signal_date = DateField(default=TimeUtils.today)
    entry_price = FloatField()
    max_price = FloatField()
    min_price = FloatField()
    current_price = FloatField()
    max_gain_pct = FloatField(default=0.0)
    max_drawdown_pct = FloatField(default=0.0)
    realized_pnl_pct = FloatField(default=0.0)
    target_1_hit = BooleanField(default=False)
    target_2_hit = BooleanField(default=False)
    stop_loss_hit = BooleanField(default=False)
    outcome_status = CharField(default="ACTIVE")  # ACTIVE, WIN_TP1, WIN_TP2, LOSS_SL, EXPIRED
    updated_at = DateTimeField(default=TimeUtils.now)


class SignalSuppressionLog(BaseModel):
    ticker = CharField()
    price = FloatField()
    score = IntegerField(default=0)
    suppression_tag = CharField()
    kill_reason = TextField()
    created_at = DateTimeField(default=TimeUtils.now)


class SignalGuardState(BaseModel):
    name = CharField(unique=True, default="PUBLISH")
    is_blocked = BooleanField(default=False)
    reason = TextField(null=True)
    source = CharField(null=True)
    details_json = TextField(null=True)
    updated_at = DateTimeField(default=TimeUtils.now)


class SignalDeskState(BaseModel):
    name = CharField(unique=True, default="PRIMARY")
    operating_mode = CharField(default="MANUAL")  # MANUAL, AI_ASSIST, AUTOPILOT
    autopilot_armed = BooleanField(default=False)
    autopilot_status = CharField(default="IDLE")  # IDLE, READY, RUNNING, BLOCKED, COMPLETED, FAILED
    last_autopilot_run_id = IntegerField(null=True)
    last_autopilot_attempted_at = DateTimeField(null=True)
    last_autopilot_published_at = DateTimeField(null=True)
    last_autopilot_error = TextField(null=True)
    autopilot_summary_json = TextField(default="{}")
    publish_policy_json = TextField(default="{}")
    lane_preferences_json = TextField(default="{}")
    manual_queue_json = TextField(default="{}")
    updated_at = DateTimeField(default=TimeUtils.now)


class SignalStateArchive(BaseModel):
    ticker = CharField()
    timestamp = DateTimeField(default=TimeUtils.now)
    final_status = CharField()
    signal_score = IntegerField()
    filter_snapshot_json = TextField()  # Snapshots of ATR, Rel_Vol, Spread, Sentiment, USD Slope, Hurdle Rate
    kill_reason = TextField(null=True)
    signal_id = CharField(unique=True, index=True)

    class Meta:
        indexes = (
            (('ticker', 'timestamp'), False),
            (('signal_id',), True),
        )
