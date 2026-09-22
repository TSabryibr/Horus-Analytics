from __future__ import annotations

import datetime
import math
import os
from calendar import monthrange
from typing import Any, Optional

from fastapi import HTTPException

from core import TimeUtils
from core.settings import settings

_ANALYSIS_REPORT_CACHE: dict[str, dict[str, Any]] = {}
_ALLOWED_PERIODS = {"WEEKLY", "MONTHLY"}


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        coerced = float(value)
        if not math.isfinite(coerced):
            return default
        return coerced
    except (TypeError, ValueError):
        return default


def _market_weekend_set() -> set[int]:
    weekend = getattr(settings, "MARKET_WEEKEND", [4, 5])
    normalized: set[int] = set()
    for day in weekend:
        try:
            normalized.add(int(day) % 7)
        except (TypeError, ValueError):
            continue
    if not normalized:
        normalized = {4, 5}
    return normalized


def _is_trading_day(day: datetime.date) -> bool:
    return day.weekday() not in _market_weekend_set()


def _last_trading_day_on_or_before(day: datetime.date) -> datetime.date:
    candidate = day
    while not _is_trading_day(candidate):
        candidate -= datetime.timedelta(days=1)
    return candidate


def _last_trading_day_of_month(year: int, month: int) -> datetime.date:
    last_dom = monthrange(year, month)[1]
    candidate = datetime.date(year, month, last_dom)
    return _last_trading_day_on_or_before(candidate)


def _final_weekday_for_market_week() -> int:
    weekend = sorted(_market_weekend_set())
    first_weekend_day = weekend[0]
    return (first_weekend_day - 1) % 7


def is_final_trading_day_of_week(day: datetime.date) -> bool:
    if not _is_trading_day(day):
        return False
    return day.weekday() == _final_weekday_for_market_week()


def is_final_trading_day_of_month(day: datetime.date) -> bool:
    if not _is_trading_day(day):
        return False
    return day == _last_trading_day_of_month(day.year, day.month)


def _parse_period(period: str) -> str:
    normalized = str(period or "").strip().upper()
    if normalized not in _ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail="period must be weekly or monthly")
    return normalized


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="period_end must be YYYY-MM-DD")


def _weekly_start_from_end(period_end: datetime.date) -> datetime.date:
    start = period_end
    while True:
        prev = start - datetime.timedelta(days=1)
        if not _is_trading_day(prev) or is_final_trading_day_of_week(prev):
            break
        start = prev
    return start


def _monthly_start_from_end(period_end: datetime.date) -> datetime.date:
    start = datetime.date(period_end.year, period_end.month, 1)
    while not _is_trading_day(start):
        start += datetime.timedelta(days=1)
    return start


def _count_trading_days(period_start: datetime.date, period_end: datetime.date) -> int:
    count = 0
    cursor = period_start
    while cursor <= period_end:
        if _is_trading_day(cursor):
            count += 1
        cursor += datetime.timedelta(days=1)
    return count


def _default_period_end(period: str) -> datetime.date:
    ref_day = settings.get_last_completed_market_day()
    if period == "WEEKLY":
        end = ref_day
        while not is_final_trading_day_of_week(end):
            end -= datetime.timedelta(days=1)
        return end

    month_end = _last_trading_day_of_month(ref_day.year, ref_day.month)
    if ref_day >= month_end:
        return month_end
    prev_month_anchor = datetime.date(ref_day.year, ref_day.month, 1) - datetime.timedelta(days=1)
    return _last_trading_day_of_month(prev_month_anchor.year, prev_month_anchor.month)


def _resolve_period_window(period: str, period_end_raw: Optional[str]) -> tuple[datetime.date, datetime.date, bool, list[str]]:
    notes: list[str] = []
    if period_end_raw:
        requested_end = _parse_date(period_end_raw)
        adjusted_end = _last_trading_day_on_or_before(requested_end)
        if adjusted_end != requested_end:
            notes.append(
                f"period_end adjusted from {requested_end.isoformat()} to trading day {adjusted_end.isoformat()}"
            )
        period_end = adjusted_end
    else:
        period_end = _default_period_end(period)

    if period == "WEEKLY":
        period_start = _weekly_start_from_end(period_end)
        complete = is_final_trading_day_of_week(period_end)
    else:
        period_start = _monthly_start_from_end(period_end)
        complete = is_final_trading_day_of_month(period_end)

    if not complete:
        notes.append("period is not fully complete; report reflects an in-progress window")

    return period_start, period_end, complete, notes


def _analysis_cache_ttl_sec(period: str) -> int:
    key = "ANALYSIS_WEEKLY_CACHE_TTL_SEC" if period == "WEEKLY" else "ANALYSIS_MONTHLY_CACHE_TTL_SEC"
    default = 6 * 3600 if period == "WEEKLY" else 12 * 3600
    try:
        return max(60, int(os.getenv(key, str(default))))
    except ValueError:
        return default


def _cache_is_fresh(entry: Optional[dict[str, Any]], ttl_sec: int) -> bool:
    if not entry:
        return False
    generated_at = entry.get("generated_at")
    if not isinstance(generated_at, datetime.datetime):
        return False
    age = (TimeUtils.now() - generated_at).total_seconds()
    return age <= ttl_sec


def _build_cache_key(period: str, period_end: datetime.date, portfolio_id: Optional[int]) -> str:
    return f"{period}:{period_end.isoformat()}:{portfolio_id or 'auto'}"
