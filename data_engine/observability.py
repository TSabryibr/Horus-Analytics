from __future__ import annotations
from core.settings import settings

import json
import logging
import os
import threading
import time
import datetime as dt
from datetime import datetime, timezone


_LOGGER = logging.getLogger("horus.data_pipeline")
if not _LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(handler)
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False

_METRICS_LOCK = threading.Lock()
_COUNTERS: dict[str, float] = {}
_GAUGES: dict[str, float] = {}
_LAST_ALERT_TS: dict[str, float] = {}
_PROCESS_START_TS = time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit_event(event: str, level: str = "info", **fields) -> None:
    payload = {
        "ts": _now_iso(),
        "event": event,
        **fields,
    }
    text = json.dumps(payload, default=str, separators=(",", ":"))
    lvl = (level or "info").lower()
    if lvl == "warning":
        _LOGGER.warning(text)
    elif lvl == "error":
        _LOGGER.error(text)
    else:
        _LOGGER.info(text)


def incr_counter(name: str, value: float = 1.0) -> None:
    with _METRICS_LOCK:
        _COUNTERS[name] = float(_COUNTERS.get(name, 0.0) + value)


def set_gauge(name: str, value: float) -> None:
    with _METRICS_LOCK:
        _GAUGES[name] = float(value)


def counter_value(name: str) -> float:
    with _METRICS_LOCK:
        return float(_COUNTERS.get(name, 0.0))


def snapshot_metrics() -> dict:
    with _METRICS_LOCK:
        return {
            "counters": dict(_COUNTERS),
            "gauges": dict(_GAUGES),
        }


def maybe_emit_freshness_alerts(freshness: dict) -> list[str]:
    from core import TimeUtils

    # SILENCE FRESHNESS ALERTS DURING REPLAY
    if TimeUtils.is_replay():
        return []

    history_ratio = float((((freshness or {}).get("history") or {}).get("kpis") or {}).get("fresh_ratio", 0.0))
    intraday_ratio = float((((freshness or {}).get("intraday") or {}).get("kpis") or {}).get("live_ratio", 0.0))
    history_stale_sample = list((((freshness or {}).get("history") or {}).get("stale_sample") or []))
    history_stale_sample_count = int((((freshness or {}).get("history") or {}).get("stale_sample_count") or 0))

    min_history_ratio = getattr(settings, "FRESHNESS_MIN_HISTORY_RATIO", 0.95)
    min_intraday_ratio = getattr(settings, "FRESHNESS_MIN_INTRADAY_RATIO", 0.85)
    cooldown_sec = int(os.getenv("ALERT_COOLDOWN_SEC", "900"))
    startup_grace_sec = max(0.0, float(os.getenv("FRESHNESS_ALERT_STARTUP_GRACE_SEC", "120")))
    intraday_grace_minutes = max(0, int(os.getenv("FRESHNESS_INTRADAY_ALERT_GRACE_MINUTES", "20")))
    history_threshold_epsilon = max(0.0, float(os.getenv("FRESHNESS_HISTORY_ALERT_THRESHOLD_EPSILON", "0.0")))
    intraday_threshold_epsilon = max(0.0, float(os.getenv("FRESHNESS_INTRADAY_ALERT_THRESHOLD_EPSILON", "0.01")))

    alerts = []
    now_ts = time.time()
    now_local = TimeUtils.now()

    if startup_grace_sec > 0 and (now_ts - _PROCESS_START_TS) < startup_grace_sec:
        return []

    market_open_grace_active = False
    if settings.is_market_open() and intraday_grace_minutes > 0:
        try:
            start_hhmm = str(getattr(settings, "MARKET_START_TIME", "10:00") or "10:00")
            start_hour, start_minute = [int(part) for part in start_hhmm.split(":", 1)]
            market_open_at = now_local.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            market_open_grace_active = now_local < (market_open_at + dt.timedelta(minutes=intraday_grace_minutes))
        except Exception:
            market_open_grace_active = False

    checks = [
        ("history_fresh_ratio_low", history_ratio, min_history_ratio),
    ]
    if settings.is_market_open():
        checks.append(("intraday_live_ratio_low", intraday_ratio, min_intraday_ratio))

    for key, observed, threshold in checks:
        if key == "intraday_live_ratio_low" and market_open_grace_active:
            continue

        epsilon = intraday_threshold_epsilon if key == "intraday_live_ratio_low" else history_threshold_epsilon
        if observed + epsilon >= threshold:
            continue
        last = float(_LAST_ALERT_TS.get(key, 0.0))
        if now_ts - last < cooldown_sec:
            continue
        _LAST_ALERT_TS[key] = now_ts
        suffix = ""
        event_fields = {}
        if key == "history_fresh_ratio_low" and history_stale_sample:
            sample_text = ",".join(history_stale_sample)
            suffix = f" stale_sample={sample_text}"
            event_fields = {
                "stale_sample": history_stale_sample,
                "stale_sample_count": history_stale_sample_count,
            }
        msg = f"{key}: observed={observed:.4f} threshold={threshold:.4f}{suffix}"
        alerts.append(msg)
        emit_event(
            "pipeline.alert",
            level="warning",
            alert_key=key,
            observed=round(float(observed), 4),
            threshold=round(float(threshold), 4),
            **event_fields,
        )
    return alerts
