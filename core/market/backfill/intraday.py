from __future__ import annotations

import datetime
import time
from typing import Any

import pandas as pd
from peewee import IntegrityError, OperationalError

from core.DataManager import DataManager
from core.settings import settings
from database import BackfillIntradayCheckpoint, Signal, db

from .state import (
    DEFAULT_BACKFILL_UNIVERSE_CHOICE,
    _DB_LOCK_BASE_SLEEP_SECONDS,
    _DB_LOCK_MAX_SLEEP_SECONDS,
    _DB_LOCK_RETRY_ATTEMPTS,
    _DEFAULT_BACKFILL_INTRADAY_INTERVAL_MINS,
    _coerce_plain_datetime,
    _is_sqlite_lock_error,
    logger,
    normalize_backfill_universe_choice,
)


def _normalize_simulation_cutoff_for_universe(
    universe_df,
    sim_dt: datetime.datetime,
) -> datetime.datetime:
    if universe_df is None or getattr(universe_df, "empty", True):
        return sim_dt
    try:
        if getattr(universe_df.index, "nlevels", 1) < 2:
            return sim_dt
        date_index = universe_df.index.get_level_values(1)
        tz = getattr(date_index, "tz", None)
        if tz is not None and sim_dt.tzinfo is None:
            return sim_dt.replace(tzinfo=tz)
    except Exception:
        return sim_dt
    return sim_dt


def _parse_market_times_for_day(sim_date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """Resolve market open/close for a day using active settings profile."""
    start_hhmm = str(settings._active_market_start()).zfill(4)
    end_hhmm = str(settings._active_market_end()).zfill(4)
    market_open = datetime.datetime.combine(
        sim_date,
        datetime.time(int(start_hhmm[:2]), int(start_hhmm[2:])),
    )
    market_close = datetime.datetime.combine(
        sim_date,
        datetime.time(int(end_hhmm[:2]), int(end_hhmm[2:])),
    )
    if market_close <= market_open:
        market_close = market_open + datetime.timedelta(hours=4)
    return market_open, market_close


def _backfill_intraday_interval_minutes() -> int:
    configured = getattr(
        settings,
        "HISTORICAL_BACKFILL_INTRADAY_INTERVAL_MINS",
        _DEFAULT_BACKFILL_INTRADAY_INTERVAL_MINS,
    )
    try:
        interval = int(configured)
    except Exception:
        interval = _DEFAULT_BACKFILL_INTRADAY_INTERVAL_MINS
    return max(1, min(120, interval))


def _intraday_checkpoints_for_day(sim_date: datetime.date) -> list[datetime.datetime]:
    """Build intraday simulation checkpoints for one session."""
    try:
        market_open, market_close = _parse_market_times_for_day(sim_date)
        step = datetime.timedelta(minutes=_backfill_intraday_interval_minutes())
        checkpoints: list[datetime.datetime] = []
        cursor = market_open
        while cursor <= market_close:
            checkpoints.append(cursor)
            cursor += step
        if not checkpoints:
            checkpoints = [market_open]
        elif checkpoints[-1] != market_close:
            checkpoints.append(market_close)
        return checkpoints
    except Exception:
        return [datetime.datetime(sim_date.year, sim_date.month, sim_date.day, 12, 0)]


def _resolve_intraday_entry_price(
    ticker: str,
    sim_date: datetime.date,
    cutoff_dt: datetime.datetime,
) -> float | None:
    """Resolve an intraday entry price at or before cutoff for a ticker/session."""
    try:
        intra_df = DataManager.get_intraday_data(ticker, refresh_if_stale=False)
    except Exception:
        return None
    if intra_df is None or intra_df.empty:
        return None
    if "Close" not in intra_df.columns:
        return None

    session = intra_df.loc[intra_df.index.date == sim_date]
    if session.empty:
        return None

    cutoff_ts = pd.Timestamp(cutoff_dt)
    if getattr(session.index, "tz", None) is not None and cutoff_ts.tzinfo is None:
        cutoff_ts = cutoff_ts.tz_localize(session.index.tz)

    at_or_before = session.loc[session.index <= cutoff_ts]
    chosen = at_or_before.iloc[-1] if not at_or_before.empty else session.iloc[0]
    try:
        px = float(chosen.get("Close"))
    except Exception:
        return None
    return px if px > 0 else None


def _apply_intraday_entry_prices(
    signals: list[dict],
    sim_date: datetime.date,
    cutoff_dt: datetime.datetime,
    universe_df=None,
) -> list[dict]:
    """Inject lane-specific intraday entry prices so intraday backfill diverges from swing."""
    if not signals:
        return []

    precision = int(getattr(settings, "PRICE_PRECISION", 2))

    day_open_map: dict[str, float] = {}
    if universe_df is not None and not getattr(universe_df, "empty", True):
        try:
            if getattr(universe_df.index, "nlevels", 1) >= 2:
                work = universe_df.reset_index()
                ticker_col = "Ticker" if "Ticker" in work.columns else work.columns[0]
                date_col = "Date" if "Date" in work.columns else work.columns[1]
                if "Open" in work.columns:
                    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
                    day_rows = work.loc[work[date_col].dt.date == sim_date]
                    for _, row in day_rows.iterrows():
                        t = str(row.get(ticker_col, "")).upper().strip()
                        if not t:
                            continue
                        try:
                            px = float(row.get("Open"))
                        except Exception:
                            continue
                        if px > 0:
                            day_open_map[t] = px
        except Exception:
            day_open_map = {}

    patched: list[dict] = []
    for signal in signals:
        current = dict(signal or {})
        ticker = str(current.get("Ticker", "")).strip().upper()
        if not ticker:
            patched.append(current)
            continue
        intraday_price = _resolve_intraday_entry_price(ticker, sim_date, cutoff_dt)
        if intraday_price is None:
            intraday_price = day_open_map.get(ticker)
        if intraday_price is None:
            patched.append(current)
            continue
        rounded_price = round(intraday_price, precision)
        current["Entry_Price"] = rounded_price
        current["Price"] = rounded_price
        patched.append(current)
    return patched


def _upsert_signal_once(
    *,
    ticker: str,
    sim_date: datetime.date,
    signal_type: str,
    price: float,
    score: float,
    source: str,
) -> str:
    existing = Signal.get_or_none(
        (Signal.ticker == ticker)
        & (Signal.date == sim_date)
        & (Signal.signal_type == signal_type)
        & (Signal.source == source)
    )
    if existing:
        existing_score = float(existing.score)
        existing_price = float(existing.price)
        intraday_price_fix = (
            source == "BackfillIntraday"
            and score >= existing_score
            and abs(existing_price - price) > 1e-9
        )
        if score > existing_score or intraday_price_fix:
            existing.score = score
            existing.price = price
            existing.save()
            return "updated"
        return "unchanged"

    Signal.create(
        ticker=ticker,
        date=sim_date,
        signal_type=signal_type,
        price=price,
        score=score,
        source=source,
    )
    return "inserted"


def _upsert_signal_with_retry(
    *,
    ticker: str,
    sim_date: datetime.date,
    signal_type: str,
    price: float,
    score: float,
    source: str,
) -> str:
    for attempt in range(_DB_LOCK_RETRY_ATTEMPTS):
        try:
            with db.atomic():
                return _upsert_signal_once(
                    ticker=ticker,
                    sim_date=sim_date,
                    signal_type=signal_type,
                    price=price,
                    score=score,
                    source=source,
                )
        except IntegrityError:
            with db.atomic():
                return _upsert_signal_once(
                    ticker=ticker,
                    sim_date=sim_date,
                    signal_type=signal_type,
                    price=price,
                    score=score,
                    source=source,
                )
        except OperationalError as exc:
            if not _is_sqlite_lock_error(exc):
                raise
            if attempt >= _DB_LOCK_RETRY_ATTEMPTS - 1:
                raise
            sleep_seconds = min(
                _DB_LOCK_MAX_SLEEP_SECONDS,
                _DB_LOCK_BASE_SLEEP_SECONDS * (2 ** attempt),
            )
            time.sleep(sleep_seconds)


def _store_signals_for_day(
    signals: list[dict],
    sim_date: datetime.date,
    *,
    source: str = "Backfill",
    include_diagnostics: bool = False,
) -> int | dict[str, Any]:
    summary: dict[str, Any] = {
        "input": 0,
        "stored": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "invalid_ticker": 0,
        "invalid_payload": 0,
        "errors": 0,
        "error_samples": [],
    }
    if hasattr(sim_date, "date"):
        sim_date = sim_date.date()

    for s in signals:
        summary["input"] += 1
        ticker = str(s.get("Ticker", "")).strip().upper()
        if not ticker:
            summary["invalid_ticker"] += 1
            continue

        signal_type = str(s.get("Signal_Type", s.get("Signal", "BUY"))).upper()
        try:
            price = float(s.get("Entry_Price", s.get("Price", 0.0)))
            score = float(s.get("Score", 0.0))
        except (TypeError, ValueError):
            summary["invalid_payload"] += 1
            continue

        try:
            outcome = _upsert_signal_with_retry(
                ticker=ticker,
                sim_date=sim_date,
                signal_type=signal_type,
                price=price,
                score=score,
                source=source,
            )
            if outcome == "updated":
                summary["stored"] += 1
                summary["updated"] += 1
            elif outcome == "inserted":
                summary["stored"] += 1
                summary["inserted"] += 1
            else:
                summary["unchanged"] += 1
        except Exception as exc:
            summary["errors"] += 1
            if len(summary["error_samples"]) < 3:
                summary["error_samples"].append(
                    {
                        "ticker": ticker,
                        "signal_type": signal_type,
                        "error": str(exc),
                    }
                )
            logger.debug("Signal store error for %s on %s: %s", ticker, sim_date, exc)
    if include_diagnostics:
        return summary
    return int(summary["stored"])


def _upsert_intraday_checkpoint_once(
    *,
    session_date: datetime.date,
    checkpoint_at: datetime.datetime,
    ticker: str,
    signal_type: str,
    source: str,
    universe_choice: str,
    price: float,
    score: float,
) -> str:
    existing = BackfillIntradayCheckpoint.get_or_none(
        (BackfillIntradayCheckpoint.session_date == session_date)
        & (BackfillIntradayCheckpoint.checkpoint_at == checkpoint_at)
        & (BackfillIntradayCheckpoint.ticker == ticker)
        & (BackfillIntradayCheckpoint.signal_type == signal_type)
        & (BackfillIntradayCheckpoint.source == source)
    )

    if existing:
        has_change = (
            abs(float(existing.price) - float(price)) > 1e-9
            or abs(float(existing.score) - float(score)) > 1e-9
            or str(existing.universe_choice or "").strip().upper() != universe_choice
        )
        if has_change:
            existing.price = price
            existing.score = score
            existing.universe_choice = universe_choice
            existing.save()
            return "updated"
        return "unchanged"

    BackfillIntradayCheckpoint.create(
        session_date=session_date,
        checkpoint_at=checkpoint_at,
        ticker=ticker,
        signal_type=signal_type,
        source=source,
        universe_choice=universe_choice,
        price=price,
        score=score,
    )
    return "inserted"


def _upsert_intraday_checkpoint_with_retry(
    *,
    session_date: datetime.date,
    checkpoint_at: datetime.datetime,
    ticker: str,
    signal_type: str,
    source: str,
    universe_choice: str,
    price: float,
    score: float,
) -> str:
    for attempt in range(_DB_LOCK_RETRY_ATTEMPTS):
        try:
            with db.atomic():
                return _upsert_intraday_checkpoint_once(
                    session_date=session_date,
                    checkpoint_at=checkpoint_at,
                    ticker=ticker,
                    signal_type=signal_type,
                    source=source,
                    universe_choice=universe_choice,
                    price=price,
                    score=score,
                )
        except IntegrityError:
            with db.atomic():
                return _upsert_intraday_checkpoint_once(
                    session_date=session_date,
                    checkpoint_at=checkpoint_at,
                    ticker=ticker,
                    signal_type=signal_type,
                    source=source,
                    universe_choice=universe_choice,
                    price=price,
                    score=score,
                )
        except OperationalError as exc:
            if not _is_sqlite_lock_error(exc):
                raise
            if attempt >= _DB_LOCK_RETRY_ATTEMPTS - 1:
                raise
            sleep_seconds = min(
                _DB_LOCK_MAX_SLEEP_SECONDS,
                _DB_LOCK_BASE_SLEEP_SECONDS * (2 ** attempt),
            )
            time.sleep(sleep_seconds)


def _store_intraday_checkpoint_snapshot(
    signals: list[dict],
    session_date: datetime.date,
    checkpoint_at: datetime.datetime,
    *,
    source: str = "BackfillIntraday",
    universe_choice: str = DEFAULT_BACKFILL_UNIVERSE_CHOICE,
) -> dict[str, int]:
    summary = {
        "input": 0,
        "stored": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "invalid_ticker": 0,
        "invalid_payload": 0,
        "errors": 0,
    }

    normalized_universe = normalize_backfill_universe_choice(universe_choice)
    checkpoint_dt = _coerce_plain_datetime(checkpoint_at)

    for signal in list(signals or []):
        summary["input"] += 1
        ticker = str(signal.get("Ticker", "")).strip().upper()
        if not ticker:
            summary["invalid_ticker"] += 1
            continue
        signal_type = str(signal.get("Signal_Type", signal.get("Signal", "BUY"))).strip().upper()
        try:
            price = float(signal.get("Entry_Price", signal.get("Price", 0.0)))
            score = float(signal.get("Score", 0.0))
        except (TypeError, ValueError):
            summary["invalid_payload"] += 1
            continue

        try:
            outcome = _upsert_intraday_checkpoint_with_retry(
                session_date=session_date,
                checkpoint_at=checkpoint_dt,
                ticker=ticker,
                signal_type=signal_type,
                source=source,
                universe_choice=normalized_universe,
                price=price,
                score=score,
            )
            if outcome == "inserted":
                summary["stored"] += 1
                summary["inserted"] += 1
            elif outcome == "updated":
                summary["stored"] += 1
                summary["updated"] += 1
            else:
                summary["unchanged"] += 1
        except Exception:
            summary["errors"] += 1

    return summary
