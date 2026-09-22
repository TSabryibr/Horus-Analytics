"""
DATABASE MARKET & SYSTEM MODELS
===============================
Peewee ORM models for Holidays, Provisioning, Sovereign state, Strategy profiles, and AI Reports.
"""

from __future__ import annotations

from peewee import (
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    TextField,
)

from core import TimeUtils
from .base import BaseModel


class Holiday(BaseModel):
    date = DateField(unique=True)
    description = CharField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)


class ProvisioningState(BaseModel):
    name = CharField(unique=True, default="HISTORICAL_SIGNAL_PROVISIONING")
    target_trading_days = IntegerField(default=252)
    completed_trading_days = IntegerField(default=0)
    status = CharField(default="IDLE")  # IDLE, RUNNING, COMPLETED, COMPLETED_WITH_WARNINGS, ERROR
    mode = CharField(default="AUTOMATIC")  # AUTOMATIC, MANUAL
    backfill_universe_choice = CharField(default="EGX30")
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    last_error = TextField(null=True)
    updated_at = DateTimeField(default=TimeUtils.now)


class SovereignState(BaseModel):
    ticker = CharField(unique=True)
    trap_type = CharField()
    confidence = CharField(default="HIGH")
    message = TextField(null=True)
    created_at = DateTimeField(default=TimeUtils.now)


class ScannerStrategyProfile(BaseModel):
    profile_name = CharField(unique=True)
    source_type = CharField(default="PINE")
    script_source = TextField()
    script_hash = CharField(unique=True)
    market = CharField(default="EGX30")
    timeframe = CharField(default="1D")
    profile_state = CharField(default="DRAFT")
    backtest_summary_json = TextField(default="{}")
    compatibility_summary_json = TextField(default="{}")
    ranking_summary_json = TextField(default="{}")
    ready_at = DateTimeField(null=True)
    activated_at = DateTimeField(null=True)
    activation_count = IntegerField(default=0)
    activation_history_json = TextField(default="[]")
    import_rule_spec_json = TextField(default="{}")
    created_at = DateTimeField(default=TimeUtils.now)


class AssetAiReport(BaseModel):
    ticker = CharField()
    generated_at = DateTimeField(default=TimeUtils.now)
    payload_json = TextField()  # Full synthesis output
    source_module = CharField(default="OLLAMA")
    confidence_score = FloatField(default=0.0)

    class Meta:
        indexes = ((('ticker', 'generated_at'), False),)
