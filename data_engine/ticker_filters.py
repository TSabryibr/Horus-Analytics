from __future__ import annotations
from core.settings import settings

import datetime as dt
import re
from typing import Any


from core.exclusions import normalize_ticker

_RIGHTS_STYLE_RE = re.compile(r".+_R\d+$")


def is_supported_ticker(raw: str) -> bool:
    """
    Filter non-tradable/legacy symbols from feed scans.
    """
    ticker = (raw or "").strip().upper()
    if not ticker:
        return False
    if ticker.isdigit():
        return False
    if ticker.startswith("REOPEN"):
        return False
    # Allow all EGX indices (starting with EGX)
    if ticker.startswith("EGX"):
        return True

    # Treat other EGX synthetic/index-like labels as non-tradable symbols.
    if ticker.startswith("EG") and any(c.isdigit() for c in ticker):
        return False
    return True


def is_rights_style_ticker(raw: str) -> bool:
    ticker = normalize_ticker(raw)
    if not ticker:
        return False
    return bool(_RIGHTS_STYLE_RE.fullmatch(ticker))


def _coerce_date(value: Any) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if hasattr(value, "date"):
        try:
            coerced = value.date()
            if isinstance(coerced, dt.date):
                return coerced
        except Exception:
            pass
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _is_market_day(day: dt.date) -> bool:
    weekend_days = getattr(settings, "MARKET_WEEKEND", [4, 5])
    if day.weekday() in weekend_days:
        return False
    try:
        return not bool(settings._is_db_holiday(day))
    except Exception:
        return True


def trading_day_age(last_date: Any, ref_date: Any) -> int | None:
    start = _coerce_date(last_date)
    end = _coerce_date(ref_date)
    if start is None or end is None:
        return None
    if start >= end:
        return 0

    age = 0
    candidate = start + dt.timedelta(days=1)
    while candidate <= end:
        if _is_market_day(candidate):
            age += 1
        candidate += dt.timedelta(days=1)
    return age


INDEX_TICKERS = {
    "EGX30", "EGX70 EWI", "EGX100 EWI", "EGX30 CAPPED", "EGX30 TR", "EGX35-LV",
    "TAMAYUZ", "SHARIAH"
}


def is_index_ticker(raw: str) -> bool:
    ticker = (raw or "").strip().upper()
    if not ticker:
        return False
    if ticker in INDEX_TICKERS:
        return True
    if ticker.startswith("EGX") or (ticker.startswith("EG") and "EWI" in ticker):
        return True
    return False


def classify_runtime_ticker_state(
    raw: str,
    *,
    last_history_date: Any = None,
    last_intraday_timestamp: Any = None,
    ref_date: Any = None,
    dormant_trading_days: int = 90,
) -> dict[str, Any]:
    ticker = normalize_ticker(raw)
    effective_ref_date = _coerce_date(ref_date) or dt.date.today()
    history_date = _coerce_date(last_history_date)
    intraday_date = _coerce_date(last_intraday_timestamp)
    dormant_limit = max(1, int(dormant_trading_days))

    if is_index_ticker(ticker):
        reason = "INDEX"
        quarantined = True
    elif is_rights_style_ticker(ticker):
        reason = "RIGHTS"
        quarantined = True
    else:
        history_age = trading_day_age(history_date, effective_ref_date)
        intraday_age = trading_day_age(intraday_date, effective_ref_date)
        recent_intraday = intraday_age is not None and intraday_age <= dormant_limit

        if (history_age is None or history_age > dormant_limit) and not recent_intraday:
            reason = "DORMANT"
            quarantined = True
        elif history_age is not None and history_age > 0:
            reason = "SOURCE_STALE"
            quarantined = False
        else:
            reason = "ACTIVE"
            quarantined = False

    return {
        "ticker": ticker,
        "reason": reason,
        "quarantined": quarantined,
        "last_history_date": history_date.isoformat() if history_date is not None else None,
        "last_intraday_timestamp": (
            last_intraday_timestamp.isoformat()
            if hasattr(last_intraday_timestamp, "isoformat")
            else (str(last_intraday_timestamp) if last_intraday_timestamp is not None else None)
        ),
        "history_trading_day_age": trading_day_age(history_date, effective_ref_date),
        "intraday_trading_day_age": trading_day_age(intraday_date, effective_ref_date),
    }


def is_runtime_quarantined_ticker(
    raw: str,
    *,
    last_history_date: Any = None,
    last_intraday_timestamp: Any = None,
    ref_date: Any = None,
    dormant_trading_days: int = 90,
) -> bool:
    state = classify_runtime_ticker_state(
        raw,
        last_history_date=last_history_date,
        last_intraday_timestamp=last_intraday_timestamp,
        ref_date=ref_date,
        dormant_trading_days=dormant_trading_days,
    )
    return bool(state["quarantined"])
