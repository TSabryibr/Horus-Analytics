from __future__ import annotations

import datetime
import logging
import threading
from typing import Any

import pandas as pd

from core import TimeUtils
from core.DataManager import DataManager
from core.settings import settings
from database import ProvisioningState

logger = logging.getLogger("HistoricalBackfill")
_REAL_DATETIME = datetime.datetime
DEFAULT_PROVISIONING_TRADING_DAYS = 252
DEFAULT_BACKFILL_UNIVERSE_CHOICE = "EGX30"
VALID_BACKFILL_UNIVERSE_CHOICES = {"EGX30", "EGX70", "EGX100", "FULL"}
DEFAULT_BACKFILL_SIGNAL_LANES = "BOTH"
VALID_BACKFILL_SIGNAL_LANES = {"SWING", "INTRADAY", "BOTH"}

BACKFILL_STATE: dict[str, Any] = {
    "status": "IDLE",       # IDLE | RUNNING | COMPLETED | ERROR
    "current_day": None,
    "progress": 0,
    "total_days": 0,
    "signals_found": 0,
    "swing_signals_found": 0,
    "intraday_signals_found": 0,
    "intraday_checkpoint_rows": 0,
    "mode": "MANUAL",
    "target_kind": "TRADING_DAYS",
    "universe_choice": DEFAULT_BACKFILL_UNIVERSE_CHOICE,
    "signal_lanes": DEFAULT_BACKFILL_SIGNAL_LANES,
    "error": None,
}

_backfill_lock = threading.Lock()
_DB_LOCK_RETRY_ATTEMPTS = 8
_DB_LOCK_BASE_SLEEP_SECONDS = 0.05
_DB_LOCK_MAX_SLEEP_SECONDS = 0.8
_DEFAULT_BACKFILL_INTRADAY_INTERVAL_MINS = 15


def is_backfill_running() -> bool:
    return str(BACKFILL_STATE.get("status", "IDLE")).strip().upper() == "RUNNING"


def _coerce_plain_datetime(value: datetime.datetime) -> datetime.datetime:
    """Normalize datetime subclasses (e.g. frozen test clocks) before DB bind."""
    if not isinstance(value, datetime.datetime):
        raise TypeError(f"Expected datetime, got {type(value)!r}")
    return datetime.datetime(
        value.year,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second,
        value.microsecond,
        tzinfo=value.tzinfo,
    )


def _get_or_create_provisioning_row(target_trading_days: int, mode: str) -> ProvisioningState:
    row, _created = ProvisioningState.get_or_create(
        name="HISTORICAL_SIGNAL_PROVISIONING",
        defaults={
            "target_trading_days": int(target_trading_days),
            "completed_trading_days": 0,
            "status": "IDLE",
            "mode": str(mode or "MANUAL").strip().upper() or "MANUAL",
            "backfill_universe_choice": DEFAULT_BACKFILL_UNIVERSE_CHOICE,
        },
    )
    return row


def _persist_provisioning_state(
    row: ProvisioningState,
    *,
    target_trading_days: int,
    completed_trading_days: int | None = None,
    status: str,
    mode: str,
    universe_choice: str | None = None,
    started_at: datetime.datetime | None = None,
    completed_at: datetime.datetime | None = None,
    last_error: str | None = None,
) -> None:
    def _coerce_dt(value: datetime.datetime | None) -> datetime.datetime | None:
        if value is None:
            return None
        return datetime.datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=value.tzinfo,
        )

    row.target_trading_days = int(target_trading_days)
    if completed_trading_days is not None:
        row.completed_trading_days = int(completed_trading_days)
    row.status = str(status or "IDLE").strip().upper() or "IDLE"
    row.mode = str(mode or "MANUAL").strip().upper() or "MANUAL"
    if universe_choice is not None:
        row.backfill_universe_choice = normalize_backfill_universe_choice(universe_choice)
    if started_at is not None:
        row.started_at = _coerce_dt(started_at)
    if completed_at is not None:
        row.completed_at = _coerce_dt(completed_at)
    row.last_error = last_error
    row.updated_at = TimeUtils.now()
    row.save()


def _market_days_between(start: datetime.date, end: datetime.date) -> list[datetime.date]:
    """Return EGX working days (Sun-Thu) in [start, end]."""
    days: list[datetime.date] = []
    current = start
    while current <= end:
        if current.weekday() not in settings.MARKET_WEEKEND:
            days.append(current)
        current += datetime.timedelta(days=1)
    return days


def _is_market_day(day: datetime.date) -> bool:
    if day.weekday() in settings.MARKET_WEEKEND:
        return False
    try:
        return not bool(settings._is_db_holiday(day))
    except Exception:
        return True


def _recent_market_days(
    end_date: datetime.date,
    trading_days: int,
    earliest_available_date: datetime.date | None = None,
) -> list[datetime.date]:
    """Return the most recent eligible trading sessions before the live date."""
    days: list[datetime.date] = []
    candidate = end_date - datetime.timedelta(days=1)
    target = max(1, int(trading_days))

    while len(days) < target and (earliest_available_date is None or candidate >= earliest_available_date):
        if _is_market_day(candidate):
            days.append(candidate)
        candidate -= datetime.timedelta(days=1)

    days.reverse()
    return days


def _history_window_start_date(tickers: list[str]) -> datetime.date | None:
    for ticker in list(tickers or []):
        try:
            history = DataManager.get_stock_data(ticker, include_live=False)
        except Exception as exc:
            logger.debug("Backfill history preflight failed for %s: %s", ticker, exc)
            continue
        if history is None or getattr(history, "empty", True):
            continue
        try:
            oldest = history.index.min()
            if hasattr(oldest, "date"):
                return oldest.date()
        except Exception as exc:
            logger.debug("Backfill history start extraction failed for %s: %s", ticker, exc)
    return None


def _available_tickers() -> list[str]:
    try:
        return list(DataManager.list_tickers() or [])
    except Exception as exc:
        logger.warning("Backfill ticker preflight failed: %s", exc)
        return []


def _normalize_market_signal_payload(result: Any) -> tuple[list[dict], list[dict], float, Any]:
    if isinstance(result, tuple):
        parts = list(result)
    elif isinstance(result, list):
        parts = list(result)
    elif result is None:
        parts = []
    else:
        parts = [result]

    if len(parts) >= 4:
        signals, monitored, breadth, regime = parts[:4]
    elif len(parts) == 3:
        signals, monitored, breadth = parts
        regime = None
    elif len(parts) == 2:
        signals, monitored = parts
        breadth = 0.0
        regime = None
    elif len(parts) == 1:
        signals = parts[0]
        monitored = []
        breadth = 0.0
        regime = None
    else:
        signals = []
        monitored = []
        breadth = 0.0
        regime = None

    return list(signals or []), list(monitored or []), float(breadth or 0.0), regime


def normalize_backfill_universe_choice(universe_choice: str | None) -> str:
    normalized = str(universe_choice or DEFAULT_BACKFILL_UNIVERSE_CHOICE).strip().upper()
    if normalized not in VALID_BACKFILL_UNIVERSE_CHOICES:
        raise ValueError(
            f"Invalid backfill universe '{universe_choice}'. Expected one of: "
            + ", ".join(sorted(VALID_BACKFILL_UNIVERSE_CHOICES))
        )
    return normalized


def resolve_backfill_market_choice(universe_choice: str) -> str:
    normalized = normalize_backfill_universe_choice(universe_choice)
    if normalized == "FULL":
        return "ALL"
    return normalized


def normalize_backfill_signal_lanes(signal_lanes: str | None) -> str:
    normalized = str(signal_lanes or DEFAULT_BACKFILL_SIGNAL_LANES).strip().upper()
    if normalized not in VALID_BACKFILL_SIGNAL_LANES:
        raise ValueError(
            f"Invalid backfill signal_lanes '{signal_lanes}'. Expected one of: "
            + ", ".join(sorted(VALID_BACKFILL_SIGNAL_LANES))
        )
    return normalized


def _is_sqlite_lock_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "database is locked" in message
        or "database table is locked" in message
        or "database is busy" in message
    )
