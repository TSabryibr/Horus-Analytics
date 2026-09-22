from __future__ import annotations
from core.settings import settings

import time
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
from core import TimeUtils

VALID_PROVIDERS = {"AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}

INTRADAY_PRECISION_RANK = {
    "MUBASHER_DB": 3,
    "DIRECTFN": 2,
    "METASTOCK_DAT": 2,
    "CSV": 1,
}

_COMPARE_CACHE = {"timestamp": 0.0, "data": None}
_COMPARE_LOCK = threading.Lock()

from data_engine.directfn_feed_source import (
    detect_layout as detect_directfn_layout,
    latest_history_snapshot as directfn_history_snapshot,
    latest_intraday_snapshot as directfn_intraday_snapshot,
    load_symbol_map as load_directfn_symbol_map,
)
from data_engine.metastock_dat_source import (
    detect_layout as detect_metastock_dat_layout,
    latest_history_snapshot as metastock_dat_history_snapshot,
    latest_intraday_snapshot as metastock_dat_intraday_snapshot,
    load_symbol_map as load_metastock_dat_symbol_map,
)
from data_engine.mubasher_sqlite_source import (
    build_paths,
    epoch_minute_to_local_naive,
    get_history_last_dates,
    get_intraday_last_minutes,
)
from data_engine.provider_selection import (
    normalize_provider as _provider_normalize_provider,
    format_quality_report as _provider_format_quality_report,
    resolved_provider_context as _provider_resolved_provider_context,
    resolve_timeframe_provider as _provider_resolve_timeframe_provider,
)


VALID_PROVIDERS = {"AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}


def normalize_provider(provider: str | None) -> str:
    return _provider_normalize_provider(provider)


def _timeframe_policy_provider(timeframe: str) -> str:
    tf = timeframe.strip().lower()
    if tf == "history":
        return normalize_provider(getattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO"))
    if tf == "intraday":
        return normalize_provider(getattr(settings, "LOCAL_INTRADAY_PROVIDER", "AUTO"))
    if tf == "ticks":
        raw = (getattr(settings, "LOCAL_TICKS_PROVIDER", "MUBASHER_DB") or "").strip().upper()
        if raw in {"MUBASHER_DB"}:
            return raw
    return "AUTO"


def _parse_compact_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    fmt = "%Y%m%d%H%M%S" if len(text) == 14 else "%Y%m%d"
    try:
        return datetime.strptime(text, fmt)
    except ValueError:
        return None


def _is_db_intraday_stale(csv_latest: str | None, db_latest: str | None, stale_minutes: int) -> bool:
    csv_ts = _parse_compact_timestamp(csv_latest)
    db_ts = _parse_compact_timestamp(db_latest)
    if csv_ts is None or db_ts is None:
        return False
    age_minutes = (csv_ts - db_ts).total_seconds() / 60.0
    return age_minutes >= max(1, int(stale_minutes))


def _expected_live_intraday_date() -> str | None:
    try:
        if not settings.is_market_open():
            return None
        return TimeUtils.today().strftime("%Y%m%d")
    except Exception:
        return None


def _intraday_latest_before_expected_day(latest: str | None, expected_day: str | None) -> bool:
    if not latest or not expected_day:
        return False
    ts = _parse_compact_timestamp(latest)
    if ts is None:
        return False
    return ts.strftime("%Y%m%d") < expected_day


def _latest_history_from_csv(folder: Path) -> tuple[int, str | None]:
    if not folder.exists():
        return 0, None

    symbol_count = 0
    latest_date: str | None = None

    for path in folder.glob("*.csv"):
        try:
            line = _last_data_line(path)
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if not parts:
                continue
            date_text = parts[0].replace('"', "")
            if len(date_text) != 8 or not date_text.isdigit():
                continue
            symbol_count += 1
            if latest_date is None or date_text > latest_date:
                latest_date = date_text
        except Exception:
            continue

    return symbol_count, latest_date


def _latest_intraday_from_csv(folder: Path) -> tuple[int, str | None]:
    if not folder.exists():
        return 0, None

    symbol_count = 0
    latest_ts: str | None = None

    for path in folder.glob("*.csv"):
        try:
            line = _last_data_line(path)
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            date_text = parts[0].replace('"', "")
            time_text = parts[1].replace('"', "").zfill(6)
            if len(date_text) != 8 or not date_text.isdigit() or len(time_text) != 6 or not time_text.isdigit():
                continue
            symbol_count += 1
            stamp = f"{date_text}{time_text}"
            if latest_ts is None or stamp > latest_ts:
                latest_ts = stamp
        except Exception:
            continue

    return symbol_count, latest_ts


def _last_data_line(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size == 0:
        return None

    with path.open("rb") as fh:
        fh.seek(0, 2)
        file_size = fh.tell()
        block = b""
        pos = file_size
        while pos > 0 and block.count(b"\n") < 20:
            step = min(4096, pos)
            pos -= step
            fh.seek(pos)
            block = fh.read(step) + block

    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    for raw in reversed(lines):
        line = raw.decode("utf-8", errors="ignore")
        if not line:
            continue
        if line.lstrip().startswith("<"):
            continue
        return line
    return None


def compare_local_sources(force_refresh: bool = False) -> dict:
    ttl_sec = int(getattr(settings, "COMPARE_CACHE_TTL_SEC", 300))
    now = time.monotonic()
    
    if not force_refresh:
        with _COMPARE_LOCK:
            if _COMPARE_CACHE["data"] is not None and (now - _COMPARE_CACHE["timestamp"]) <= ttl_sec:
                return _COMPARE_CACHE["data"]

    history_csv_dir = Path(getattr(settings, "METASTOCK_HISTORY_FOLDER", ""))
    intraday_csv_dir = Path(getattr(settings, "METASTOCK_INTRADAY_FOLDER", ""))
    history_dat_dir = Path(getattr(settings, "METASTOCK_DAT_HISTORY_FOLDER", ""))
    intraday_dat_dir = Path(getattr(settings, "METASTOCK_DAT_INTRADAY_FOLDER", ""))

    csv_hist_symbols, csv_hist_latest = _latest_history_from_csv(history_csv_dir)
    csv_intra_symbols, csv_intra_latest = _latest_intraday_from_csv(intraday_csv_dir)

    mubasher_hist_symbols = 0
    mubasher_hist_latest: str | None = None
    mubasher_intra_symbols = 0
    mubasher_intra_latest: str | None = None
    db_available = False
    directfn_hist_symbols = 0
    directfn_hist_latest: str | None = None
    directfn_intra_symbols = 0
    directfn_intra_latest: str | None = None
    directfn_available = False
    metastock_dat_hist_symbols = 0
    metastock_dat_hist_latest: str | None = None
    metastock_dat_intra_symbols = 0
    metastock_dat_intra_latest: str | None = None
    metastock_dat_available = False

    root = Path(getattr(settings, "MUBASHER_ROOT_DIR", "")).expanduser()
    user_id = getattr(settings, "MUBASHER_USER_ID", None) or None

    hist_map = {}
    intra_map = {}
    try:
        paths = build_paths(root, user_id=user_id)
        hist_map = get_history_last_dates(paths)
        intra_map = get_intraday_last_minutes(paths)
        db_available = paths.history_db.exists() and paths.intraday_db.exists()

        mubasher_hist_symbols = len(hist_map)
        mubasher_hist_latest = max(hist_map.values()) if hist_map else None

        mubasher_intra_symbols = len(intra_map)
        if intra_map:
            max_minute = max(intra_map.values())
            local_ts = epoch_minute_to_local_naive(pd.Series([max_minute])).iloc[0]
            mubasher_intra_latest = local_ts.strftime("%Y%m%d%H%M%S")
    except Exception:
        db_available = False

    try:
        layout = detect_directfn_layout(history_csv_dir, intraday_csv_dir)
        if layout:
            symbol_map = load_directfn_symbol_map(layout.symbol_map)
            directfn_hist_symbols, directfn_hist_latest = directfn_history_snapshot(layout, symbol_map)
            directfn_intra_symbols, directfn_intra_latest = directfn_intraday_snapshot(layout, symbol_map)
            if db_available:
                mapped_symbols = {str(s).upper() for s in symbol_map.values()}
                if hist_map:
                    directfn_hist_symbols = len(mapped_symbols & set(hist_map.keys()))
                if intra_map:
                    directfn_intra_symbols = len(mapped_symbols & set(intra_map.keys()))
            directfn_available = directfn_hist_symbols > 0 or directfn_intra_symbols > 0
    except Exception:
        directfn_available = False

    try:
        layout = detect_metastock_dat_layout(history_dat_dir, intraday_dat_dir)
        if layout:
            symbol_map = load_metastock_dat_symbol_map(layout)
            metastock_dat_hist_symbols, metastock_dat_hist_latest = metastock_dat_history_snapshot(layout, symbol_map)
            metastock_dat_intra_symbols, metastock_dat_intra_latest = metastock_dat_intraday_snapshot(layout, symbol_map)
            if db_available:
                mapped_symbols = {str(s).upper() for s in symbol_map.values()}
                if hist_map:
                    metastock_dat_hist_symbols = len(mapped_symbols & set(hist_map.keys()))
                if intra_map:
                    metastock_dat_intra_symbols = len(mapped_symbols & set(intra_map.keys()))
            metastock_dat_available = metastock_dat_hist_symbols > 0 or metastock_dat_intra_symbols > 0
    except Exception:
        metastock_dat_available = False

    providers = {
        "csv": {
            "history_symbols": csv_hist_symbols,
            "history_latest": csv_hist_latest,
            "intraday_symbols": csv_intra_symbols,
            "intraday_latest": csv_intra_latest,
            "score": 0,
            "available": csv_hist_symbols > 0 or csv_intra_symbols > 0,
        },
        "mubasher_db": {
            "history_symbols": mubasher_hist_symbols,
            "history_latest": mubasher_hist_latest,
            "intraday_symbols": mubasher_intra_symbols,
            "intraday_latest": mubasher_intra_latest,
            "score": 0,
            "available": db_available,
        },
        "directfn": {
            "history_symbols": directfn_hist_symbols,
            "history_latest": directfn_hist_latest,
            "intraday_symbols": directfn_intra_symbols,
            "intraday_latest": directfn_intra_latest,
            "score": 0,
            "available": directfn_available,
        },
        "metastock_dat": {
            "history_symbols": metastock_dat_hist_symbols,
            "history_latest": metastock_dat_hist_latest,
            "intraday_symbols": metastock_dat_intra_symbols,
            "intraday_latest": metastock_dat_intra_latest,
            "score": 0,
            "available": metastock_dat_available,
        },
    }

    # Score based on max coverage/recency across providers.
    metrics = ["history_symbols", "intraday_symbols", "history_latest", "intraday_latest"]
    for metric in metrics:
        values = [providers[p][metric] for p in providers if providers[p][metric]]
        if not values:
            continue
        max_val = max(values)
        for name, rec in providers.items():
            if rec[metric] and rec[metric] == max_val:
                rec["score"] += 1

    recommended = max(
        providers.items(),
        key=lambda kv: (
            kv[1]["score"],
            kv[1].get("history_latest") or "",
            kv[1].get("intraday_latest") or "",
            kv[1].get("history_symbols") or 0,
            kv[1].get("intraday_symbols") or 0,
        ),
    )[0].upper()

    base_report = {
        "db_available": db_available,
        "csv": providers["csv"],
        "mubasher_db": providers["mubasher_db"],
        "directfn": providers["directfn"],
        "metastock_dat": providers["metastock_dat"],
        "recommended_provider": recommended,
    }
    history_details = provider_decision_for_timeframe(base_report, timeframe="history")
    intraday_details = provider_decision_for_timeframe(base_report, timeframe="intraday")
    report_out = {
        **base_report,
        "recommended_history_provider": history_details["provider"],
        "recommended_intraday_provider": intraday_details["provider"],
        "recommended_history_details": history_details,
        "recommended_intraday_details": intraday_details,
    }

    with _COMPARE_LOCK:
        _COMPARE_CACHE["timestamp"] = time.monotonic()
        _COMPARE_CACHE["data"] = report_out

    return report_out


def resolve_local_feed_provider(provider: str | None = None) -> tuple[str, dict | None]:
    requested = normalize_provider(provider or getattr(settings, "LOCAL_FEED_PROVIDER", "AUTO"))
    if requested in {"CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}:
        return requested, None

    report = compare_local_sources()
    return report["recommended_history_provider"], report


def apply_startup_recommended_provider(unified: bool = True, force_unified: bool = False) -> dict:
    """
    Run live source comparison and apply recommended provider policy in-memory.
    If a user has explicitly set LOCAL_HISTORY_PROVIDER or LOCAL_INTRADAY_PROVIDER to something
    other than 'AUTO', we must respect their choice and bypass the autoselection for that timeframe.
    """
    report = compare_local_sources()

    # Read explicit configurations
    explicit_history = normalize_provider(getattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO"))
    explicit_intraday = normalize_provider(getattr(settings, "LOCAL_INTRADAY_PROVIDER", "AUTO"))
    explicit_unified = normalize_provider(getattr(settings, "LOCAL_FEED_PROVIDER", "AUTO"))

    # Resolve actual providers: explicit wins, otherwise fallback to recommended
    history_provider = explicit_history if explicit_history != "AUTO" else normalize_provider(report.get("recommended_history_provider"))
    intraday_provider = explicit_intraday if explicit_intraday != "AUTO" else normalize_provider(report.get("recommended_intraday_provider"))

    if history_provider == "AUTO":
        history_provider = normalize_provider(report.get("recommended_provider"))
    if intraday_provider == "AUTO":
        intraday_provider = normalize_provider(report.get("recommended_provider"))
    if history_provider == "AUTO":
        history_provider = "CSV"
    if intraday_provider == "AUTO":
        intraday_provider = "CSV"

    # Only apply unified logic if the user hasn't explicitly split them and wants unified.
    # If the user explicitly set them differently (e.g. history=CSV, intraday=MUBASHER_DB),
    # we should ideally respect that split unless force_unified is strictly True.
    if unified:
        # If user explicitly set them to different non-auto values, they want split mode.
        if not force_unified and history_provider != intraday_provider:
            # Leave GlobalSettings alone if they were explicitly set, otherwise update.
            if explicit_unified == "AUTO":
                settings.LOCAL_FEED_PROVIDER = "AUTO"
            settings.LOCAL_HISTORY_PROVIDER = history_provider
            settings.LOCAL_INTRADAY_PROVIDER = intraday_provider
            return {
                "mode": "TIMEFRAME",
                "selected_provider": explicit_unified,
                "history_provider": history_provider,
                "intraday_provider": intraday_provider,
                "fallback_from": "UNIFIED",
                "report": report,
            }

        selected = explicit_unified
        if selected == "AUTO":
            selected = normalize_provider(report.get("recommended_provider"))
        if selected == "AUTO":
            selected = history_provider
        if selected == "AUTO":
            selected = intraday_provider
        if selected == "AUTO":
            selected = "CSV"

        # Even in unified mode, if the user explicitly pinned a history or intraday provider,
        # we shouldn't mercilessly crush it with the unified 'selected' unless they specifically
        # requested a unified provider.
        # Even in unified mode, if the user explicitly pinned a history or intraday provider,
        # we shouldn't mercilessly crush it with the unified 'selected' unless they specifically
        # requested a unified provider OR we are forcing unified mode.
        if explicit_unified != "AUTO" or force_unified:
            settings.LOCAL_FEED_PROVIDER = selected
            settings.LOCAL_HISTORY_PROVIDER = selected
            settings.LOCAL_INTRADAY_PROVIDER = selected
        else:
            settings.LOCAL_FEED_PROVIDER = "AUTO"
            settings.LOCAL_HISTORY_PROVIDER = history_provider
            settings.LOCAL_INTRADAY_PROVIDER = intraday_provider

        return {
            "mode": "UNIFIED" if (explicit_unified != "AUTO" or force_unified) else "TIMEFRAME",
            "selected_provider": selected,
            "history_provider": settings.LOCAL_HISTORY_PROVIDER,
            "intraday_provider": settings.LOCAL_INTRADAY_PROVIDER,
            "report": report,
        }

    # Not unified mode
    if explicit_unified == "AUTO":
        settings.LOCAL_FEED_PROVIDER = "AUTO"
    settings.LOCAL_HISTORY_PROVIDER = history_provider
    settings.LOCAL_INTRADAY_PROVIDER = intraday_provider
    return {
        "mode": "TIMEFRAME",
        "selected_provider": explicit_unified,
        "history_provider": history_provider,
        "intraday_provider": intraday_provider,
        "report": report,
    }


def resolved_provider_context(
    *,
    timeframe: str,
    selected_provider: str,
    selection_report: dict | None = None,
    unified_policy_provider: str | None = None,
) -> dict:
    return _provider_resolved_provider_context(
        timeframe=timeframe,
        selected_provider=selected_provider,
        selection_report=selection_report,
        unified_policy_provider=unified_policy_provider,
    )


def recommend_provider_for_timeframe(report: dict, timeframe: str) -> str:
    return provider_decision_for_timeframe(report, timeframe)["provider"]


def provider_decision_for_timeframe(report: dict, timeframe: str) -> dict:
    providers = {
        "CSV": report.get("csv", {}),
        "MUBASHER_DB": report.get("mubasher_db", {}),
        "DIRECTFN": report.get("directfn", {}),
        "METASTOCK_DAT": report.get("metastock_dat", {}),
    }
    available = {name: rec for name, rec in providers.items() if rec.get("available")}
    if not available:
        return {
            "timeframe": timeframe.strip().lower(),
            "provider": "CSV",
            "reason": "no_available_provider",
            "fallback_from": None,
            "evidence": {},
        }

    tf = timeframe.strip().lower()

    if tf == "intraday":
        # prefer freshest intraday timestamp
        latest_intraday = max(rec.get("intraday_latest") or "" for rec in available.values())
        latest_candidates = {
            name: rec
            for name, rec in available.items()
            if (rec.get("intraday_latest") or "") == latest_intraday
        }
        best = max(
            latest_candidates.items(),
            key=lambda kv: (
                INTRADAY_PRECISION_RANK.get(kv[0], 0),
                kv[1].get("intraday_symbols") or 0,
            ),
        )[0]
        best_record = available.get(best, {})
        reason = (
            "freshest_intraday_precision_tiebreak"
            if len(latest_candidates) > 1
            else "freshest_intraday"
        )
        decision = {
            "timeframe": tf,
            "provider": best,
            "reason": reason,
            "fallback_from": None,
            "evidence": {
                "intraday_latest": best_record.get("intraday_latest"),
                "intraday_symbols": best_record.get("intraday_symbols"),
            },
        }
        # allow stale override for Mubasher DB vs CSV
        csv_latest = providers["CSV"].get("intraday_latest") or ""
        db_latest = providers["MUBASHER_DB"].get("intraday_latest") or ""
        stale_minutes = int(getattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20))
        db_is_stale = _is_db_intraday_stale(csv_latest, db_latest, stale_minutes=stale_minutes)
        if providers["CSV"].get("available") and db_is_stale and decision["provider"] == "CSV":
            return {
                "timeframe": tf,
                "provider": "CSV",
                "reason": "stale_db_fallback",
                "fallback_from": "MUBASHER_DB",
                "evidence": {
                    "csv_intraday_latest": csv_latest or None,
                    "db_intraday_latest": db_latest or None,
                    "stale_minutes": stale_minutes,
                    "csv_intraday_symbols": providers["CSV"].get("intraday_symbols"),
                    "db_intraday_symbols": providers["MUBASHER_DB"].get("intraday_symbols"),
                },
            }
        if best == "MUBASHER_DB" and db_is_stale:
            fallback = "CSV" if providers["CSV"].get("available") else best
            if fallback != best:
                return {
                    "timeframe": tf,
                    "provider": fallback,
                    "reason": "stale_db_fallback",
                    "fallback_from": best,
                    "evidence": {
                        "csv_intraday_latest": csv_latest or None,
                        "db_intraday_latest": db_latest or None,
                        "stale_minutes": stale_minutes,
                        "csv_intraday_symbols": providers["CSV"].get("intraday_symbols"),
                        "db_intraday_symbols": providers["MUBASHER_DB"].get("intraday_symbols"),
                    },
                }
        expected_live_day = _expected_live_intraday_date()
        if (
            expected_live_day
            and latest_intraday
            and _intraday_latest_before_expected_day(latest_intraday, expected_live_day)
        ):
            available_intraday_latest = {
                name: rec.get("intraday_latest")
                for name, rec in available.items()
                if rec.get("intraday_latest")
            }
            if not any(
                not _intraday_latest_before_expected_day(latest, expected_live_day)
                for latest in available_intraday_latest.values()
            ):
                return {
                    "timeframe": tf,
                    "provider": best,
                    "reason": "upstream_intraday_stale",
                    "fallback_from": None,
                    "evidence": {
                        "intraday_latest": best_record.get("intraday_latest"),
                        "intraday_symbols": best_record.get("intraday_symbols"),
                        "expected_intraday_date": expected_live_day,
                        "market_open": True,
                        "available_intraday_latest": available_intraday_latest,
                    },
                }
        return decision

    # History: prefer most recent, then coverage
    best = max(
        available.items(),
        key=lambda kv: (kv[1].get("history_latest") or "", kv[1].get("history_symbols") or 0),
    )[0]
    best_record = available.get(best, {})
    return {
        "timeframe": tf,
        "provider": best,
        "reason": "most_recent_history",
        "fallback_from": None,
        "evidence": {
            "history_latest": best_record.get("history_latest"),
            "history_symbols": best_record.get("history_symbols"),
        },
    }


def resolve_timeframe_provider(timeframe: str, provider: str | None = None) -> tuple[str, dict | None]:
    return _provider_resolve_timeframe_provider(timeframe=timeframe, provider=provider)


def format_quality_report(report: dict) -> str:
    return _provider_format_quality_report(report)
