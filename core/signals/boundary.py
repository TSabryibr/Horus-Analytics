import datetime
import os
from typing import Callable, Optional

from fastapi import HTTPException

from core import TimeUtils


def error_context(error_type: str, error_reason: str, message: str, **extra) -> dict:
    return {
        "message": message,
        "error_type": error_type,
        "error_reason": error_reason,
        **extra,
    }


def validation_error(error_reason: str, message: str, parameter: Optional[str] = None, **extra) -> dict:
    detail = error_context("validation", error_reason, message, **extra)
    if parameter is not None:
        detail["parameter"] = parameter
    return detail


def noop_context(noop_type: str, noop_reason: str, message: str, **extra) -> dict:
    return {
        "message": message,
        "noop_type": noop_type,
        "noop_reason": noop_reason,
        **extra,
    }


def parse_run_date(
    value: Optional[str],
    *,
    today_fn: Callable[[], datetime.date] = TimeUtils.today,
    validation_error_fn: Callable[..., dict] = validation_error,
) -> datetime.date:
    if not value:
        return today_fn()
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "invalid_run_date",
                "run_date must be YYYY-MM-DD",
                parameter="run_date",
                run_date=value,
            ),
        ) from exc


def int_env(name: str, default: int, *, env_get_fn: Callable[[str], Optional[str]]) -> int:
    raw = env_get_fn(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def float_env(name: str, default: float, *, env_get_fn: Callable[[str], Optional[str]]) -> float:
    raw = env_get_fn(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def bool_env(name: str, default: bool, *, env_get_fn: Callable[[str], Optional[str]]) -> bool:
    raw = env_get_fn(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def get_publish_window_status(
    run_date: datetime.date,
    now_dt: Optional[datetime.datetime] = None,
    *,
    int_env_fn: Optional[Callable[[str, int], int]] = None,
) -> dict:
    int_env_fn = int_env_fn or (lambda name, default: int_env(name, default, env_get_fn=os.getenv))
    now_dt = now_dt or TimeUtils.now()
    start_h = int_env_fn("SIGNAL_PUBLISH_START_HOUR", 14)
    start_m = int_env_fn("SIGNAL_PUBLISH_START_MINUTE", 35)
    cutoff_h = int_env_fn("SIGNAL_PUBLISH_CUTOFF_HOUR", 16)
    cutoff_m = int_env_fn("SIGNAL_PUBLISH_CUTOFF_MINUTE", 0)

    start_dt = datetime.datetime.combine(now_dt.date(), datetime.time(start_h, start_m))
    cutoff_dt = datetime.datetime.combine(now_dt.date(), datetime.time(cutoff_h, cutoff_m))
    if run_date != now_dt.date():
        return {
            "ok": False,
            "reason": "run_date_mismatch",
            "window_start": start_dt.isoformat(),
            "window_cutoff": cutoff_dt.isoformat(),
            "now": now_dt.isoformat(),
        }
    if now_dt < start_dt:
        return {
            "ok": False,
            "reason": "window_not_open",
            "window_start": start_dt.isoformat(),
            "window_cutoff": cutoff_dt.isoformat(),
            "now": now_dt.isoformat(),
        }
    if now_dt > cutoff_dt:
        return {
            "ok": False,
            "reason": "window_closed",
            "window_start": start_dt.isoformat(),
            "window_cutoff": cutoff_dt.isoformat(),
            "now": now_dt.isoformat(),
        }
    return {
        "ok": True,
        "reason": "within_window",
        "window_start": start_dt.isoformat(),
        "window_cutoff": cutoff_dt.isoformat(),
        "now": now_dt.isoformat(),
    }


def freshness_context(freshness: dict) -> dict:
    issues = freshness.get("issues") or []
    return {
        "block_type": "freshness",
        "block_reason": freshness.get("reason") or (issues[0] if issues else "freshness_gate_failed"),
        "freshness": freshness,
    }


def window_context(window: dict) -> dict:
    return {
        "block_type": "window",
        "block_reason": window.get("reason") or "window_blocked",
        "window": window,
    }


def validated_publish_channel(
    channel: str,
    *,
    error_context_fn: Callable[..., dict] = error_context,
) -> str:
    normalized = (channel or "TELEGRAM").upper()
    if normalized != "TELEGRAM":
        raise HTTPException(
            status_code=400,
            detail=error_context_fn(
                "validation",
                "unsupported_channel",
                "Only TELEGRAM channel is supported.",
                channel=normalized,
            ),
        )
    return normalized
