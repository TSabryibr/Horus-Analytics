from __future__ import annotations
from core.settings import settings

import os
import time

from utils.logger import setup_logger


logger = setup_logger("horus.pipeline_alerts")

_ALERT_STATES = {"STALE", "DEGRADED"}
_LAST_ALERT_STATE: str | None = None
_LAST_ALERT_TS: float | None = None


def _coerce_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _coerce_float(value, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _setting_bool(name: str, default: bool) -> bool:
    env_value = os.getenv(name)
    try:

        value = getattr(settings, name, env_value)
    except Exception:
        value = env_value
    return _coerce_bool(value, default)


def _setting_float(name: str, default: float) -> float:
    env_value = os.getenv(name)
    try:

        value = getattr(settings, name, env_value)
    except Exception:
        value = env_value
    return _coerce_float(value, default)


def _play_windows_stale_beep() -> bool:
    try:
        import winsound
    except Exception:
        logger.debug("[Pipeline] Local stale sound alert is unavailable on this platform.")
        return False

    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        return True
    except Exception as exc:
        try:
            winsound.Beep(880, 350)
            return True
        except Exception:
            logger.debug(f"[Pipeline] Local stale sound alert failed: {exc}")
            return False


def reset_pipeline_stale_sound_alert_state() -> None:
    global _LAST_ALERT_STATE, _LAST_ALERT_TS
    _LAST_ALERT_STATE = None
    _LAST_ALERT_TS = None


def maybe_play_pipeline_stale_sound(
    pipeline_state: str,
    *,
    now_fn=None,
    sound_fn=None,
    enabled: bool | None = None,
    cooldown_sec: float | None = None,
) -> bool:
    """Play one local admin sound when the pipeline is stale, with cooldown."""
    global _LAST_ALERT_STATE, _LAST_ALERT_TS

    normalized = str(pipeline_state or "").strip().upper()
    if normalized not in _ALERT_STATES:
        if normalized == "FRESH":
            reset_pipeline_stale_sound_alert_state()
        return False

    if enabled is None:
        enabled = _setting_bool("PIPELINE_STALE_SOUND_ALERT_ENABLED", True)
    if not enabled:
        return False

    if cooldown_sec is None:
        cooldown_sec = _setting_float("PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC", 600.0)
    cooldown = max(0.0, float(cooldown_sec or 0.0))

    now = float((now_fn or time.monotonic)())
    if _LAST_ALERT_TS is not None and (now - _LAST_ALERT_TS) < cooldown:
        return False

    player = sound_fn or _play_windows_stale_beep
    played = False
    try:
        result = player()
        played = result is not False
    except Exception as exc:
        logger.debug(f"[Pipeline] Local stale sound alert failed: {exc}")

    _LAST_ALERT_STATE = normalized
    _LAST_ALERT_TS = now
    if played:
        logger.warning(f"[Pipeline] Local stale pipeline sound alert emitted for state={normalized}.")
    return played
