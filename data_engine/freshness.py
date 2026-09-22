from __future__ import annotations

from datetime import date, datetime, time as dt_time, timedelta
import os
import time
import threading
from pathlib import Path
from typing import Any

import pandas as pd

from core import TimeUtils
from data_engine import intraday_store
from data_engine.ticker_filters import (
    classify_runtime_ticker_state,
    is_index_ticker,
    is_supported_ticker,
    trading_day_age,
)
from core.exclusions import get_excluded_tickers_upper, normalize_ticker


from core.settings import settings
DATA_ROOT = Path(settings.DATA_ROOT)
_HISTORY_CACHE: dict[str, tuple[datetime, dict[str, date]]] = {}
_HISTORY_CACHE_TTL_SEC = int(os.getenv("FRESHNESS_HISTORY_CACHE_TTL_SEC", "300"))
_EVALUATE_FRESHNESS_LOCK = threading.Lock()
_EVALUATE_FRESHNESS_CACHE: dict[str, tuple[dict, float]] = {}


def invalidate_freshness_cache(realm: str | None = None) -> None:
    """Clear freshness caches after a history/intraday ingest writes new data."""
    with _EVALUATE_FRESHNESS_LOCK:
        _EVALUATE_FRESHNESS_CACHE.clear()
    if realm:
        _HISTORY_CACHE.pop(str(realm), None)
    else:
        _HISTORY_CACHE.clear()


def _ticker_is_candidate(raw: str) -> bool:
    from data_engine.ticker_filters import is_index_ticker
    ticker = normalize_ticker(raw)
    if not ticker:
        return False
    if is_index_ticker(ticker):
        return False
    if not is_supported_ticker(ticker):
        return False
    return ticker not in get_excluded_tickers_upper()


def _runtime_report_ref_day(ref_date: date | None = None) -> date:
    if ref_date is None:
        anchor = TimeUtils.now()
    else:
        anchor = datetime.combine(ref_date, dt_time.max)
    return settings.get_last_completed_market_day(anchor)


def _last_history_date_from_file(path: Path):
    try:
        import pyarrow.parquet as pq
        meta = pq.read_metadata(path)
        last_ts = None
        
        # Try to find 'timestamp' or index-based timestamp in metadata stats
        for i in range(meta.num_row_groups):
            row_group = meta.row_group(i)
            for j in range(row_group.num_columns):
                col = row_group.column(j)
                if col.path_in_schema in ['timestamp', '__index_level_0__']:
                    stats = col.statistics
                    if stats is None:
                        continue
                    cur_max = getattr(stats, "max", None)
                    if cur_max is None:
                        continue
                    if last_ts is None or cur_max > last_ts:
                        last_ts = cur_max
        
        if last_ts is not None:
            if isinstance(last_ts, (int, float)): # Handle epoch
                 ts = pd.to_datetime(last_ts, unit='ns' if last_ts > 1e12 else 's')
            else:
                 ts = pd.to_datetime(last_ts)
            return ts.date()

        # Fallback to partial pandas read if metadata stats are missing
        df = pd.read_parquet(path)
        if df is None or df.empty: return None
        ts = df.index.max() if isinstance(df.index, pd.DatetimeIndex) else (pd.to_datetime(df["timestamp"]).max() if "timestamp" in df.columns else None)
        return ts.date() if ts and not pd.isna(ts) else None
    except Exception:
        return None



def _history_symbol_dates_raw(realm: str) -> dict[str, date]:
    cached = _HISTORY_CACHE.get(realm)
    if cached is not None:
        cached_at, cached_data = cached
        age_sec = (TimeUtils.now() - cached_at).total_seconds()
        if age_sec <= max(1, _HISTORY_CACHE_TTL_SEC):
            return dict(cached_data)

    out: dict[str, date] = {}
    path = DATA_ROOT / realm / "history"
    if not path.exists():
        return out

    partition_root = path / "by_date"
    if partition_root.exists():
        partition_days: list[tuple[date, Path]] = []
        for day_dir in partition_root.iterdir():
            if not day_dir.is_dir():
                continue
            try:
                partition_day = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
            except ValueError:
                continue
            partition_days.append((partition_day, day_dir))

        if partition_days:
            partition_days.sort(key=lambda x: x[0], reverse=True)
            latest_day, latest_dir = partition_days[0]
            for file_path in latest_dir.glob("*.parquet"):
                ticker = file_path.stem.upper()
                if _ticker_is_candidate(ticker):
                    out[ticker] = latest_day

            # Include one prior partition to expose near-stale symbols quickly
            # without scanning every historical partition file.
            if len(partition_days) > 1:
                prev_day, prev_dir = partition_days[1]
                for file_path in prev_dir.glob("*.parquet"):
                    ticker = file_path.stem.upper()
                    if _ticker_is_candidate(ticker):
                        out.setdefault(ticker, prev_day)
    if not partition_root.exists() or not out:
        for file_path in path.glob("*.parquet"):
            ticker = file_path.stem.upper()
            if not _ticker_is_candidate(ticker):
                continue
            last_date = _last_history_date_from_file(file_path)
            if last_date is not None:
                out[ticker] = last_date
    else:
        # Partition updates only touch changed symbols; keep flat-only symbols visible.
        for file_path in path.glob("*.parquet"):
            ticker = file_path.stem.upper()
            if not _ticker_is_candidate(ticker):
                continue
            last_date = _last_history_date_from_file(file_path)
            if last_date is None:
                continue
            current = out.get(ticker)
            if current is None or last_date > current:
                out[ticker] = last_date

    _HISTORY_CACHE[realm] = (TimeUtils.now(), dict(out))
    return out


def _intraday_symbol_timestamps_raw(realm: str) -> dict[str, pd.Timestamp]:
    out = {}
    for ticker, ts in intraday_store.get_latest_timestamps(realm=realm).items():
        if not _ticker_is_candidate(ticker):
            continue
        if ts is None or pd.isna(ts):
            continue
        out[str(ticker).upper()] = pd.to_datetime(ts, errors="coerce")
    return out


def _canonical_runtime_symbols(realm: str) -> set[str]:
    symbols: set[str] = set()
    try:
        from core.market import MarketLists

        symbols.update(MarketLists.get_market_list("ALL") or set())
    except Exception:
        pass

    if not symbols:
        try:
            from core.DataManager import DataManager

            symbols.update(DataManager.list_tickers() or [])
        except Exception:
            pass

    return {normalize_ticker(symbol) for symbol in symbols if _ticker_is_candidate(str(symbol))}


def _missing_source_state(ticker: str) -> dict:
    return {
        "ticker": normalize_ticker(ticker),
        "reason": "MISSING_SOURCE",
        "quarantined": False,
        "last_history_date": None,
        "last_intraday_timestamp": None,
        "history_trading_day_age": None,
        "intraday_trading_day_age": None,
    }


def _build_runtime_ticker_report(
    realm: str,
    ref_date: date | None = None,
    dormant_trading_days: int = 90,
) -> tuple[dict, dict[str, date], dict[str, pd.Timestamp]]:
    report_date = _runtime_report_ref_day(ref_date)
    history_dates = _history_symbol_dates_raw(realm)
    intra_ts = _intraday_symbol_timestamps_raw(realm)
    canonical_symbols = _canonical_runtime_symbols(realm)
    tickers = sorted(set(history_dates) | set(intra_ts) | canonical_symbols)

    states: list[dict] = []
    runtime_quarantined: list[dict] = []
    review_candidates: list[dict] = []
    tracked_symbols: list[str] = []
    counts_by_reason: dict[str, int] = {}

    for ticker in tickers:
        if ticker in canonical_symbols and ticker not in history_dates and ticker not in intra_ts:
            state = _missing_source_state(ticker)
        else:
            state = classify_runtime_ticker_state(
                ticker,
                last_history_date=history_dates.get(ticker),
                last_intraday_timestamp=intra_ts.get(ticker),
                ref_date=report_date,
                dormant_trading_days=dormant_trading_days,
            )
        states.append(state)
        reason = str(state.get("reason") or "UNKNOWN")
        counts_by_reason[reason] = int(counts_by_reason.get(reason, 0) + 1)
        if state.get("quarantined"):
            runtime_quarantined.append(state)
        else:
            tracked_symbols.append(ticker)
            if reason in {"SOURCE_STALE", "MISSING_SOURCE"}:
                review_candidates.append(state)

    report = {
        "realm": realm,
        "report_date": report_date.isoformat(),
        "dormant_trading_days": int(max(1, dormant_trading_days)),
        "runtime_quarantined": runtime_quarantined,
        "review_candidates": review_candidates,
        "tracked_symbols": tracked_symbols,
        "summary": {
            "tracked_count": len(tracked_symbols),
            "runtime_quarantined_count": len(runtime_quarantined),
            "review_candidate_count": len(review_candidates),
            "counts_by_reason": counts_by_reason,
        },
    }
    return report, history_dates, intra_ts


def get_runtime_ticker_report(
    realm: str,
    ref_date: date | None = None,
    dormant_trading_days: int = 90,
) -> dict:
    report, _, _ = _build_runtime_ticker_report(
        realm=realm,
        ref_date=ref_date,
        dormant_trading_days=dormant_trading_days,
    )
    return report


def _coerce_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, (pd.Timestamp,)):
        try:
            return val.date()
        except Exception:
            return None
    if isinstance(val, str):
        try:
            raw = val.strip()
            if not raw:
                return None
            if len(raw) == 8 and raw.isdigit():
                return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
            if len(raw) >= 10 and raw[4] in "-/" and raw[7] in "-/":
                return date(int(raw[:4]), int(raw[5:7]), int(raw[8:10]))
            parsed = pd.to_datetime(raw, errors="coerce")
            if parsed is not None and not pd.isna(parsed):
                return parsed.date()
        except Exception:
            return None
    try:
        parsed = pd.to_datetime(val, errors="coerce")
        if parsed is not None and not pd.isna(parsed):
            return parsed.date()
    except Exception:
        pass
    return None


def _history_kpis_for_day(
    history_dates: dict[str, date],
    expected_day: date,
    expected_symbols: set[str] | None = None,
    source_history_dates: dict[str, date] | None = None,
) -> dict:
    symbols = sorted(set(expected_symbols or history_dates.keys()))
    symbol_count = len(symbols)
    if symbol_count == 0:
        return {
            "symbol_count": 0,
            "fresh_symbols": 0,
            "stale_symbols": 0,
            "missing_symbols": 0,
            "fresh_ratio": 1.0,
            "latest_date": None,
            "oldest_date": None,
        }

    dates = [history_dates[s] for s in symbols if s in history_dates]
    _coerce_src_date = _coerce_date

    def _is_fresh(s: str) -> bool:
        d = history_dates.get(s)
        if d is None:
            return False
        if d >= expected_day:
            return True
        if source_history_dates and s in source_history_dates:
            src_d = _coerce_date(source_history_dates.get(s))
            if src_d and d >= src_d:
                return True
        return False

    fresh_symbols = sum(1 for s in symbols if _is_fresh(s))
    stale_symbols = symbol_count - fresh_symbols
    missing_symbols = sum(1 for s in symbols if s not in history_dates)

    return {
        "symbol_count": symbol_count,
        "fresh_symbols": fresh_symbols,
        "stale_symbols": stale_symbols,
        "missing_symbols": missing_symbols,
        "fresh_ratio": round(fresh_symbols / symbol_count, 4) if symbol_count > 0 else 1.0,
        "latest_date": max(dates).isoformat() if dates else None,
        "oldest_date": min(dates).isoformat() if dates else None,
    }


def _intraday_kpis_for_day(
    intra_ts: dict[str, pd.Timestamp],
    target_day: date,
    stale_minutes: int,
    market_open: bool,
    expected_symbols: set[str] | None = None,
    history_kpis: dict | None = None,
    source_history_dates: dict[str, date] | None = None,
) -> dict:
    symbols = sorted(set(expected_symbols or intra_ts.keys()))
    symbol_count = len(symbols)
    if symbol_count == 0:
        return {
            "symbol_count": 0,
            "live_symbols": 0,
            "stale_symbols": 0,
            "missing_symbols": 0,
            "live_ratio": 1.0,
            "latest_bar": None,
            "max_age_mins": None,
        }

    now = TimeUtils.now()
    live_symbols = 0
    ages = []
    latest_bar = None

    history_fresh_ratio = float((history_kpis or {}).get("fresh_ratio", 0.0) or 0.0)
    active_days = max(1, int(getattr(settings, "FRESHNESS_REVIEW_ACTIVE_DAYS", 2)))

    for ticker in symbols:
        ts = intra_ts.get(ticker)
        if ts is None or pd.isna(ts):
            if not market_open and history_fresh_ratio >= 0.9:
                live_symbols += 1
            continue
        age_mins = (now - ts).total_seconds() / 60.0
        ages.append(age_mins)
        if latest_bar is None or ts > latest_bar:
            latest_bar = ts

        is_live = False
        if ts.date() == target_day and (not market_open or age_mins <= stale_minutes):
            is_live = True
        elif not market_open and history_fresh_ratio >= 0.9:
            is_live = True
        elif not market_open and source_history_dates and ticker in source_history_dates:
            src_d = _coerce_date(source_history_dates.get(ticker))
            if src_d and ts.date() >= src_d:
                is_live = True
        elif not market_open:
            age = trading_day_age(ts.date(), target_day)
            if age is not None and age <= active_days:
                is_live = True

        if is_live:
            live_symbols += 1

    stale_symbols = symbol_count - live_symbols
    missing_symbols = sum(1 for s in symbols if s not in intra_ts)
    latest_age_mins = None
    if latest_bar is not None:
        latest_age_mins = round((now - latest_bar).total_seconds() / 60.0, 1)
    return {
        "symbol_count": symbol_count,
        "live_symbols": live_symbols,
        "stale_symbols": stale_symbols,
        "missing_symbols": missing_symbols,
        "live_ratio": round(live_symbols / symbol_count, 4) if symbol_count > 0 else 1.0,
        "latest_bar": latest_bar.strftime("%Y-%m-%d %H:%M") if latest_bar is not None else None,
        "latest_age_mins": latest_age_mins,
        "max_age_mins": round(max(ages), 1) if ages else None,
    }


def _freshness_expected_symbols(
    runtime_report: dict,
    history_dates: dict[str, date],
    intra_ts: dict[str, pd.Timestamp],
) -> set[str]:
    """Return the actionable symbol set used for freshness ratios."""
    from data_engine.ticker_filters import is_index_ticker
    tracked_symbols = {
        normalize_ticker(symbol)
        for symbol in (runtime_report.get("tracked_symbols") or [])
        if normalize_ticker(symbol) and not is_index_ticker(symbol)
    }
    if not tracked_symbols:
        return set()

    review_by_ticker = {
        normalize_ticker(item.get("ticker")): item
        for item in (runtime_report.get("review_candidates") or [])
        if normalize_ticker(item.get("ticker"))
    }
    if not review_by_ticker:
        return tracked_symbols

    active_review_days = max(0, int(getattr(settings, "FRESHNESS_REVIEW_ACTIVE_DAYS", 2)))
    expected = set(tracked_symbols)

    for ticker, state in review_by_ticker.items():
        if ticker not in expected:
            continue
        history_age = state.get("history_trading_day_age")
        intraday_age = state.get("intraday_trading_day_age")
        has_history = ticker in history_dates
        has_intraday = ticker in intra_ts

        if state.get("reason") == "MISSING_SOURCE" and not has_history and not has_intraday:
            expected.discard(ticker)
            continue

        history_inactive = history_age is None or int(history_age) > active_review_days
        intraday_inactive = intraday_age is None or int(intraday_age) > active_review_days
        if history_inactive and intraday_inactive:
            expected.discard(ticker)

    return expected


def _resolve_expected_history_day(
    run_date: date,
    calendar_expected_day: date,
    history_dates: dict[str, date],
    intra_ts: dict[str, pd.Timestamp],
) -> tuple[date, bool]:
    """Avoid marking history stale while same-day EOD bars are not published yet."""
    now = TimeUtils.now()
    if run_date != now.date() or calendar_expected_day != run_date:
        return calendar_expected_day, False

    if not history_dates or not intra_ts:
        return calendar_expected_day, False

    latest_history_day = max(history_dates.values())
    previous_expected_day = settings.get_last_completed_market_day(
        datetime.combine(calendar_expected_day - timedelta(days=1), dt_time.max)
    )
    has_today_intraday = any(
        ts is not None and not pd.isna(ts) and pd.to_datetime(ts).date() == run_date
        for ts in intra_ts.values()
    )

    if latest_history_day < calendar_expected_day:
        if not has_today_intraday or latest_history_day == previous_expected_day:
            return previous_expected_day, True
    return calendar_expected_day, False


def evaluate_freshness(realm: str, run_date: date, scan_type: str = "DAILY") -> dict:
    scan_type = (scan_type or "DAILY").upper()
    cache_key = f"{realm}_{run_date.isoformat()}_{scan_type}"
    now_ts = time.time()
    with _EVALUATE_FRESHNESS_LOCK:
        if cache_key in _EVALUATE_FRESHNESS_CACHE:
            cached_data, cached_time = _EVALUATE_FRESHNESS_CACHE[cache_key]
            if now_ts - cached_time < 30.0:
                return cached_data
    now = TimeUtils.now()
    # For current-day checks, use actual clock time; using time.max incorrectly
    # forces "today" before market close and marks morning data as stale.
    if run_date == now.date():
        calendar_expected_history_day = settings.get_last_completed_market_day(now)
    else:
        calendar_expected_history_day = settings.get_last_completed_market_day(datetime.combine(run_date, dt_time.max))
    market_open = settings.is_market_open()
    intraday_stale_threshold = 60

    source_history_dates = {}
    try:
        from data_engine.mubasher_sqlite_source import build_paths, get_history_last_dates
        from pathlib import Path
        mubasher_root_raw = getattr(settings, "MUBASHER_ROOT_DIR", None) or getattr(settings, "MUBASHER_PATH", None) or r"C:\Mubasher\Mubasher Pro EGX"
        mubasher_root = Path(mubasher_root_raw)
        if mubasher_root.exists():
            user_id = getattr(settings, "MUBASHER_USER_ID", None) or None
            paths = build_paths(mubasher_root, user_id=user_id)
            if paths.history_db.exists():
                raw_source_dates = get_history_last_dates(paths)
                source_history_dates = {
                    ticker: coerced
                    for ticker, raw_val in raw_source_dates.items()
                    if (coerced := _coerce_date(raw_val)) is not None
                }
    except Exception:
        pass

    runtime_report, history_dates_raw, intra_ts_raw = _build_runtime_ticker_report(
        realm=realm,
        ref_date=run_date,
    )
    tracked_symbols = _freshness_expected_symbols(runtime_report, history_dates_raw, intra_ts_raw)
    history_dates = {
        ticker: last_date for ticker, last_date in history_dates_raw.items() if ticker in tracked_symbols
    }
    intra_ts = {
        ticker: ts for ticker, ts in intra_ts_raw.items() if ticker in tracked_symbols
    }
    expected_history_day, pending_eod_history = _resolve_expected_history_day(
        run_date,
        calendar_expected_history_day,
        history_dates,
        intra_ts,
    )

    history_kpis = _history_kpis_for_day(
        history_dates,
        expected_history_day,
        expected_symbols=tracked_symbols,
        source_history_dates=source_history_dates,
    )
    stale_sample = sorted(
        ticker
        for ticker in tracked_symbols
        if not (
            history_dates.get(ticker) == expected_history_day
            or (
                source_history_dates
                and _coerce_date(history_dates.get(ticker)) == _coerce_date(source_history_dates.get(ticker))
            )
        )
    )[:10]
    intraday_target_day = run_date if market_open else expected_history_day
    intraday_kpis = _intraday_kpis_for_day(
        intra_ts,
        intraday_target_day,
        intraday_stale_threshold,
        market_open=market_open,
        expected_symbols=tracked_symbols,
        history_kpis=history_kpis,
        source_history_dates=source_history_dates,
    )

    history_last = history_kpis.get("latest_date")
    history_ok = bool(history_last) and (history_kpis.get("fresh_ratio", 0.0) >= 0.9 or history_last == expected_history_day.isoformat())
    intraday_ok = bool(intraday_kpis.get("latest_bar")) and intraday_kpis.get("live_ratio", 0.0) > 0

    if not market_open and history_ok and bool(intraday_kpis.get("latest_bar")):
        intraday_ok = True

    requires_intraday_freshness = scan_type in {"INTRADAY", "PRE_CLOSE"}
    overall_ok = (history_ok and intraday_ok) if requires_intraday_freshness else history_ok
    status = "FRESH" if history_ok else "STALE"

    return {
        "run_date": run_date.strftime("%Y-%m-%d"),
        "scan_type": scan_type,
        "overall_ok": overall_ok,
        "status": status,
        "last_updated": history_last,
        "history": {
            "ok": history_ok,
            "status": status,
            "last_updated": history_last,
            "expected_last_working_day": expected_history_day.strftime("%Y-%m-%d"),
            "calendar_expected_last_working_day": calendar_expected_history_day.strftime("%Y-%m-%d"),
            "pending_eod_history": pending_eod_history,
            "kpis": history_kpis,
            "stale_sample": stale_sample,
            "stale_sample_count": int(history_kpis.get("stale_symbols", 0)),
        },
        "intraday": {
            "ok": intraday_ok,
            "status": "LIVE" if intraday_ok else "STALE",
            "last_bar": intraday_kpis.get("latest_bar"),
            "age_mins": intraday_kpis.get("latest_age_mins")
            if intraday_kpis.get("latest_age_mins") is not None
            else intraday_kpis.get("max_age_mins"),
            "kpis": intraday_kpis,
        },
    }
