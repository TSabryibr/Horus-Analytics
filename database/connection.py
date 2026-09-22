"""
DATABASE CONNECTION & INITIALIZATION
====================================
Database engine resolution, initialization, and table seeding.
"""

from __future__ import annotations

import datetime
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from peewee import PostgresqlDatabase, SqliteDatabase

from core import TimeUtils
from core.settings import settings

from .migrations import run_auto_migrations
from .models import (
    AssetAiReport,
    BackfillIntradayCheckpoint,
    BrokerOrder,
    Client,
    ClientApiKey,
    ClientEntitlement,
    Holiday,
    HorusExecution,
    LegacySignalOutcome,
    Portfolio,
    PortfolioDefaultState,
    PortfolioSnapshot,
    Position,
    ProvisioningState,
    PublishedSignalFollowUp,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    ScannerStrategyProfile,
    Signal,
    SignalAuditEvent,
    SignalDelivery,
    SignalDeskState,
    SignalExecutionAttribution,
    SignalGuardState,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
    SignalStateArchive,
    SignalSuppressionLog,
    SignalValidationRun,
    SovereignState,
    SubscriptionDelivery,
    TickerStrategyMetrics,
    Trade,
    db,
)


def get_db_instance():
    db_type = os.getenv("HORUS_DB_TYPE", "sqlite").strip().lower()

    # If standard Postgres variables are present, prefer Postgres
    pg_host = os.getenv("POSTGRES_HOST")
    if pg_host:
        db_type = "postgres"

    if db_type == "postgres":
        pg_db = os.getenv("POSTGRES_DB", "horus")
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD", "")
        pg_port = int(os.getenv("POSTGRES_PORT", "5432"))

        return PostgresqlDatabase(
            pg_db,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port,
            autorollback=True,
        )
    else:
        _DEFAULT_DB_FILE = settings.get_persistent_path("horus.db")
        DB_FILE = os.getenv("HORUS_DB_FILE", _DEFAULT_DB_FILE)
        DB_JOURNAL_MODE = os.getenv("HORUS_DB_JOURNAL_MODE", "wal").strip().lower() or "wal"
        DB_SYNCHRONOUS = os.getenv("HORUS_DB_SYNCHRONOUS", "normal").strip().lower() or "normal"

        return SqliteDatabase(
            DB_FILE,
            pragmas={
                'journal_mode': DB_JOURNAL_MODE,
                'cache_size': -1024 * 64,
                'foreign_keys': 1,
                'synchronous': DB_SYNCHRONOUS,
                'busy_timeout': 30000,
            },
            timeout=30,
        )


real_db = get_db_instance()
db.initialize(real_db)


@contextmanager
def atomic_write_retry(max_retries: int = 3, base_delay: float = 0.1):
    """
    Context manager for Peewee write transactions with exponential backoff
    to gracefully mitigate SQLite write lock contention during peak market hours.
    """
    for attempt in range(max_retries):
        try:
            with db.atomic():
                yield
            return
        except Exception as exc:
            msg = str(exc).lower()
            if ("locked" in msg or "busy" in msg) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            raise


def _seed_market_holidays() -> None:
    candidates = []
    for resolver in (
        settings.get_resource_path,
        settings.get_persistent_path,
    ):
        try:
            candidates.append(Path(resolver("config/egx_holidays.json")))
        except Exception:
            pass
    candidates.append(Path("config/egx_holidays.json"))

    seen_paths = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        if not path.exists():
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            items = raw.get("holidays", raw) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                return
            for item in items:
                if not isinstance(item, dict):
                    continue
                date_text = str(item.get("date") or "").strip()
                if not date_text:
                    continue
                holiday_date = datetime.date.fromisoformat(date_text)
                description = str(item.get("description") or "EGX market holiday")
                Holiday.get_or_create(
                    date=holiday_date,
                    defaults={"description": description},
                )
            return
        except Exception as e:
            print(f"Market holiday seed error: {e}")
            return


def initialize_db():
    db.connect(reuse_if_open=True)
    db.create_tables(
        [
            Portfolio,
            PortfolioDefaultState,
            Position,
            Trade,
            BrokerOrder,
            Signal,
            BackfillIntradayCheckpoint,
            SignalRun,
            SignalRecommendation,
            SignalDelivery,
            SignalOutcome,
            PublishedSignalLifecycle,
            PublishedSignalLifecycleEvent,
            PublishedSignalFollowUp,
            HorusExecution,
            SignalExecutionAttribution,
            SignalValidationRun,
            TickerStrategyMetrics,
            SignalGuardState,
            SignalDeskState,
            ProvisioningState,
            Client,
            ClientApiKey,
            ClientEntitlement,
            SubscriptionDelivery,
            SignalAuditEvent,
            SignalStateArchive,
            PortfolioSnapshot,
            Holiday,
            SovereignState,
            ScannerStrategyProfile,
            AssetAiReport,
            SignalSuppressionLog,
            LegacySignalOutcome,
        ],
        safe=True,
    )
    _seed_market_holidays()
    run_auto_migrations(real_db)

    # Ensure default USER portfolios exist
    if not Portfolio.select().where(Portfolio.id == 1).exists():
        try:
            Portfolio.create(id=1, name="My Portfolio", type="USER", auto_manage=False)
        except Exception:
            if not Portfolio.select().where(Portfolio.type == "USER").exists():
                Portfolio.create(name="My Portfolio", type="USER", auto_manage=False)
    if not Portfolio.select().where(Portfolio.name == "Horus").exists():
        Portfolio.create(name="Horus", type="USER", auto_manage=False)

    # Canonical Signal-type System Model Fleets (Read-Only Algorithmic Benchmarks)
    if not Portfolio.select().where(Portfolio.name == "Intraday Signals").exists():
        Portfolio.create(name="Intraday Signals", type="SYSTEM", auto_manage=True, cash_egp=500000.0)
    if not Portfolio.select().where(Portfolio.name == "Swing Signals").exists():
        Portfolio.create(name="Swing Signals", type="SYSTEM", auto_manage=True, cash_egp=500000.0)
    if not Portfolio.select().where(Portfolio.name == "Position Signals").exists():
        Portfolio.create(name="Position Signals", type="SYSTEM", auto_manage=True, cash_egp=500000.0)

    # Normalize legacy auto-managed strategy portfolios created before STRATEGY type.
    try:
        strategy_profile_names = [
            row.profile_name
            for row in ScannerStrategyProfile.select(ScannerStrategyProfile.profile_name)
            if str(row.profile_name or "").strip()
        ]
        if strategy_profile_names:
            (
                Portfolio.update(type="STRATEGY", auto_manage=True)
                .where(
                    (Portfolio.name.in_(strategy_profile_names)) &
                    (Portfolio.auto_manage == True) &
                    (Portfolio.type != "STRATEGY")
                )
                .execute()
            )
    except Exception as e:
        print(f"Strategy portfolio normalization error: {e}")

    default_state, _ = PortfolioDefaultState.get_or_create(name="GLOBAL_DEFAULT")
    if default_state.portfolio_id is None:
        default_system_portfolio = (
            Portfolio.get_or_none((Portfolio.name == "Intraday Signals") & (Portfolio.type == "SYSTEM"))
            or Portfolio.get_or_none(Portfolio.type == "SYSTEM")
        )
        if default_system_portfolio is not None:
            default_state.portfolio = default_system_portfolio
            default_state.updated_at = TimeUtils.now()
            default_state.save()
    SignalDeskState.get_or_create(name="PRIMARY")
    db.close()
