from __future__ import annotations

import os
import time
from typing import Any, Iterable

from core.settings import settings
from managers.ExclusionManager import ExclusionManager

EXCLUDED_TICKERS = {
    "SIMO", "SLAP", "CCAPP", "SFWA", "HDST", "POCO", "KORA", "EGWA", "EGB0509230926G0",
    "DCCC", "BQDC", "ALMF", "UBEE-", "PTCC", "HAVC", "GEOS", "GOCO", "TRST", "SMCSA",
    "SEIGA", "EGB0810231026G0", "EGB0403250328G0", "ARPI", "GETO", "EIUD", "EKHO",
    "AIVC", "AUTO", "MNHD", "REAC", "EDBM", "QNBA", "AIH", "EKHOA.CA", "EKHOA",
    "MBEN", "GBIM", "AIFI_R1", "COPR_R2"
}

GlobalExclusions = ExclusionManager(EXCLUDED_TICKERS, settings.EXCLUSIONS_FILE)

def get_all_exclusions() -> set[str]:
    globs = GlobalExclusions.get_all()
    EXCLUDED_TICKERS.clear()
    EXCLUDED_TICKERS.update(globs)
    return globs

def save_exclusions(tickers) -> bool:
    res = GlobalExclusions.save_dynamic(tickers)
    get_all_exclusions()
    return res

def add_exclusion(ticker: str) -> bool:
    res = GlobalExclusions.add(ticker)
    get_all_exclusions()
    return res

def remove_exclusion(ticker: str) -> bool:
    res = GlobalExclusions.remove(ticker)
    get_all_exclusions()
    return res

_DROP = object()

# Common field names used across API payloads for single ticker symbols.
_TICKER_KEYS = {
    "ticker",
    "symbol",
    "lead_ticker",
    "follower_ticker",
    "leader",
    "follower",
    "instrument",
    "asset",
}

# Common field names that carry multiple ticker symbols.
_TICKER_LIST_KEYS = {"tickers", "symbols"}
_EXCLUDED_TICKERS_CACHE: tuple[float, int, set[str]] | None = None
_EXCLUDED_TICKERS_CACHE_TTL_SEC = float(os.getenv("EXCLUSIONS_CACHE_TTL_SEC", "5"))


def normalize_ticker(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def get_excluded_tickers_upper() -> set[str]:
    global _EXCLUDED_TICKERS_CACHE
    now = time.monotonic()
    provider_id = id(get_all_exclusions)
    raw = get_all_exclusions()
    normalized: set[str] = set()
    for ticker in raw:
        symbol = normalize_ticker(ticker)
        if symbol:
            normalized.add(symbol)

    if _EXCLUDED_TICKERS_CACHE is not None:
        cached_at, cached_provider_id, cached_values = _EXCLUDED_TICKERS_CACHE
        if (
            cached_provider_id == provider_id
            and now - cached_at < _EXCLUDED_TICKERS_CACHE_TTL_SEC
            and cached_values == normalized
        ):
            return set(cached_values)

    _EXCLUDED_TICKERS_CACHE = (now, provider_id, normalized)
    return normalized


def invalidate_exclusion_cache() -> None:
    global _EXCLUDED_TICKERS_CACHE
    _EXCLUDED_TICKERS_CACHE = None


def is_excluded_ticker(value: Any, excluded: set[str] | None = None) -> bool:
    symbol = normalize_ticker(value)
    if not symbol:
        return False
    excluded_set = excluded if excluded is not None else get_excluded_tickers_upper()
    return symbol in excluded_set


def assert_ticker_allowed(value: Any, detail_prefix: str = "Ticker") -> str:
    symbol = normalize_ticker(value)
    if not symbol:
        return symbol
    if is_excluded_ticker(symbol):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"{detail_prefix} {symbol} is blacklisted and cannot be used.",
        )
    return symbol


def filter_excluded_symbols(values: Iterable[Any], excluded: set[str] | None = None) -> list[Any]:
    excluded_set = excluded if excluded is not None else get_excluded_tickers_upper()
    if not excluded_set:
        return list(values)
    out: list[Any] = []
    for value in values:
        if not is_excluded_ticker(value, excluded_set):
            out.append(value)
    return out


def _dict_has_excluded_ticker(payload: dict[str, Any], excluded: set[str]) -> bool:
    for key, value in payload.items():
        key_l = str(key).strip().lower()
        if key_l in _TICKER_KEYS and is_excluded_ticker(value, excluded):
            return True
    return False


def _walk_and_filter(node: Any, excluded: set[str]) -> Any:
    if isinstance(node, list):
        output = []
        for item in node:
            filtered = _walk_and_filter(item, excluded)
            if filtered is _DROP:
                continue
            output.append(filtered)
        return output

    if isinstance(node, dict):
        if _dict_has_excluded_ticker(node, excluded):
            return _DROP
        output: dict[str, Any] = {}
        for key, value in node.items():
            key_l = str(key).strip().lower()
            if key_l in _TICKER_LIST_KEYS and isinstance(value, list):
                output[key] = filter_excluded_symbols(value, excluded)
                continue
            filtered = _walk_and_filter(value, excluded)
            if filtered is _DROP:
                continue
            output[key] = filtered
        return output

    return node


def filter_excluded_from_payload(payload: Any, excluded: set[str] | None = None) -> Any:
    excluded_set = excluded if excluded is not None else get_excluded_tickers_upper()
    if not excluded_set:
        return payload

    filtered = _walk_and_filter(payload, excluded_set)
    if filtered is _DROP:
        if isinstance(payload, list):
            return []
        if isinstance(payload, dict):
            return {}
    return filtered


def purge_blacklisted_data(excluded: set[str]) -> dict:
    from database import Position, Trade, Signal, SignalOutcome, SignalRecommendation, TickerStrategyMetrics
    from peewee import fn
    
    excluded_upper = {normalize_ticker(t) for t in (excluded or set()) if normalize_ticker(t)}
    counts = {
        "positions": 0,
        "trades": 0,
        "signals": 0,
        "signal_recommendations": 0,
        "signal_outcomes": 0,
        "ticker_strategy_metrics": 0,
    }
    if not excluded_upper:
        return counts

    counts["positions"] = Position.delete().where(fn.Upper(Position.ticker).in_(excluded_upper)).execute()
    counts["trades"] = Trade.delete().where(fn.Upper(Trade.ticker).in_(excluded_upper)).execute()
    counts["signals"] = Signal.delete().where(fn.Upper(Signal.ticker).in_(excluded_upper)).execute()
    counts["signal_outcomes"] = SignalOutcome.delete().where(fn.Upper(SignalOutcome.ticker).in_(excluded_upper)).execute()
    counts["signal_recommendations"] = SignalRecommendation.delete().where(
        fn.Upper(SignalRecommendation.ticker).in_(excluded_upper)
    ).execute()
    counts["ticker_strategy_metrics"] = TickerStrategyMetrics.delete().where(
        fn.Upper(TickerStrategyMetrics.ticker).in_(excluded_upper)
    ).execute()
    return counts
