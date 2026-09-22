"""
ALERT MANAGER
=============
Unified interface for multi-channel notifications.
"""

from core.settings import settings
from utils.redis_client import redis_client
from core import TelegramBot_Alerts
import DiscordBot_Alerts
import logging
import os
import threading
import tempfile
import json
import asyncio
import inspect
from pathlib import Path
from core.websocket import ws_manager

logger = logging.getLogger("horus.alerts")

DEDUP_FILE = Path(settings.DATA_ROOT) / "sent_signals.json"
_DEDUP_LOCK = threading.Lock()


def _call_with_supported_kwargs(func, *args, **kwargs):
    """Call patched or legacy notification functions without assuming kwargs support."""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return func(*args, **kwargs)

    parameters = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values()):
        return func(*args, **kwargs)

    accepted_kwargs = {key: value for key, value in kwargs.items() if key in parameters}
    return func(*args, **accepted_kwargs)


def _normalize_scan_label(scan_label: str) -> str:
    """
    Normalizes scan labels and groups related phases (e.g., PRE-CLOSE and DAILY SIGNAL)
    to prevent duplicate alerts for the same ticker on the same day.
    """
    label = str(scan_label or "").strip().upper()
    # Grouping related daily phases to share the same deduplication namespace
    if label in ("PRE-CLOSE", "DAILY SIGNAL", "EOD", "DAILY"):
        return "DAILY_CONFIRMED"
    return label or "UNLABELED"


def _normalize_ticker(ticker) -> str:
    text = str(ticker or "").strip().upper()
    return text


def _atomic_write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    target_dir = directory or os.getcwd()
    fd, tmp_path = tempfile.mkstemp(prefix="dedup_", suffix=".json", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(payload, tmp)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def filter_new_signals(signals: list, scan_label: str) -> list:
    """
    Filters out signals that have already been broadcast today for the given scan_label.
    Supports score-based upgrades: if a signal's score significantly improves (e.g., +2),
    it allows a re-broadcast even if previously sent.
    """
    from core import TimeUtils
    if not signals:
        return []

    today_str = TimeUtils.today().strftime("%Y-%m-%d")
    scan_key = _normalize_scan_label(scan_label)
    now_ts = TimeUtils.now().timestamp()

    # Configuration for re-broadcasting
    SCORE_IMPROVEMENT_THRESHOLD = 2.0
    SCORE_BUMP_COOLDOWN_SEC = 30 * 60  # 30 minutes
    repeat_cooldown_hours = float(getattr(settings, "SIGNAL_REPEAT_COOLDOWN_HOURS", 4.0) or 4.0)
    REPEAT_COOLDOWN_SEC = max(0.0, repeat_cooldown_hours * 60 * 60)

    with _DEDUP_LOCK:
        state = {}
        # Try Redis first
        state_str = redis_client.get("sent_signals_state")
        if state_str:
            try:
                state = json.loads(state_str)
            except Exception:
                pass
        
        # If Redis was empty/failed, try local file
        if not state and os.path.exists(DEDUP_FILE):
            try:
                with open(DEDUP_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        state = loaded
                # Seed Redis
                try:
                    redis_client.set("sent_signals_state", json.dumps(state))
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"[Deduplicator] Error loading state: {e}")
                state = {}

        # 1. Normalize and migrate state format
        # Old format: {"YYYY-MM-DD": {"LABEL": ["TICKER", ...]}}
        # New format: {"YYYY-MM-DD": {"LABEL": {"TICKER": {"score": X, "time": Y}}}}
        raw_today = state.get(today_str, {})
        today_state = {}
        if isinstance(raw_today, dict):
            for raw_label, data in raw_today.items():
                key = _normalize_scan_label(raw_label)
                today_state.setdefault(key, {})
                
                if isinstance(data, list):
                    # Migrate legacy list format
                    for t in data:
                        t_norm = _normalize_ticker(t)
                        if t_norm:
                            today_state[key][t_norm] = {"score": 0, "time": 0.0}
                elif isinstance(data, dict):
                    # New format
                    for t, info in data.items():
                        t_norm = _normalize_ticker(t)
                        if t_norm and isinstance(info, dict):
                            today_state[key][t_norm] = info

        # BUG FIX: Preserve historical dates by updating instead of overwriting
        state[today_str] = today_state

        sent_info = state[today_str].get(scan_key, {})

        fresh_signals = []
        updates_to_save = {}
        dropped_signals = []

        for s in signals:
            ticker = _normalize_ticker((s or {}).get("Ticker"))
            if not ticker:
                continue

            new_score = float((s or {}).get("Score", 0))
            prev_info = sent_info.get(ticker)

            should_send = False
            drop_reason = None
            if prev_info is None:
                # Never sent today
                should_send = True
            else:
                prev_score = float(prev_info.get("score", 0))
                prev_time = float(prev_info.get("time", 0))
                
                # Rule A: Significant score improvement
                score_bump = new_score - prev_score
                if score_bump >= SCORE_IMPROVEMENT_THRESHOLD:
                    if (now_ts - prev_time) >= SCORE_BUMP_COOLDOWN_SEC:
                        should_send = True
                    else:
                        drop_reason = "score_bump_cooldown"
                
                # Rule B: Periodic re-broadcast for high-conviction (Score >= 8) after long cooldown
                if not should_send and new_score >= 8:
                    if (now_ts - prev_time) >= REPEAT_COOLDOWN_SEC:
                        should_send = True
                    else:
                        drop_reason = drop_reason or "repeat_cooldown"

                if not should_send and drop_reason is None:
                    drop_reason = "already_sent_no_material_change"

            if should_send:
                fresh_signals.append(s)
                updates_to_save[ticker] = {"score": new_score, "time": now_ts}
                sent_info[ticker] = updates_to_save[ticker]
            else:
                dropped_signals.append(
                    {
                        "ticker": ticker,
                        "reason": drop_reason or "suppressed",
                        "previous_score": float(prev_info.get("score", 0)) if prev_info else None,
                        "new_score": new_score,
                    }
                )

        if updates_to_save:
            state[today_str][scan_key] = sent_info
            try:
                redis_client.set("sent_signals_state", json.dumps(state))
            except Exception:
                pass
            try:
                _atomic_write_json(DEDUP_FILE, state)
            except Exception as e:
                logger.error(f"[Deduplicator] Error saving state: {e}")

        if dropped_signals:
            counts_by_reason = {}
            for item in dropped_signals:
                reason = item["reason"]
                counts_by_reason[reason] = int(counts_by_reason.get(reason, 0) + 1)
            logger.info(
                "[Deduplicator] label=%s kept=%s dropped=%s counts_by_reason=%s dropped_tickers=%s",
                scan_key,
                len(fresh_signals),
                len(dropped_signals),
                counts_by_reason,
                [item["ticker"] for item in dropped_signals],
            )

        return fresh_signals

def clear_deduplication_state(day_str: str = None) -> bool:
    """
    Clears the deduplication state (sent_signals.json) for a specific day or all days.
    Useful for resetting simulations or handling context switches.
    If day_str is None, it clears the entry for TimeUtils.today().
    """
    from core import TimeUtils
    target_day = day_str or TimeUtils.today().strftime("%Y-%m-%d")

    with _DEDUP_LOCK:
        state = {}
        # Try Redis first
        state_str = redis_client.get("sent_signals_state")
        if state_str:
            try:
                state = json.loads(state_str)
            except Exception:
                pass

        # If Redis empty, try file
        if not state and os.path.exists(DEDUP_FILE):
            try:
                with open(DEDUP_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        state = loaded
            except Exception:
                pass

        if target_day in state:
            del state[target_day]
            try:
                redis_client.set("sent_signals_state", json.dumps(state))
            except Exception:
                pass
            try:
                _atomic_write_json(DEDUP_FILE, state)
            except Exception:
                pass
            logger.info(f"[Deduplicator] Cleared state for day: {target_day}")
            return True

    return False

def broadcast_alert(message: str, priority: str = "INFO", ticker: str | None = None, signal_data: dict | None = None, token: str | None = None, chat_id: str | None = None):
    """
    Sends an alert to all active channels (Telegram, Discord).
    """
    results = {}
    
    # 1. Telegram
    if settings.TELEGRAM_ENABLED:
        try:
            res_tg = _call_with_supported_kwargs(
                TelegramBot_Alerts.send_message,
                message,
                token=token,
                chat_id=chat_id,
            )
            results["telegram"] = res_tg
        except Exception as e:
            logger.error(f"Telegram broadcast error: {e}")
            results["telegram"] = {"status": "error", "message": str(e)}
            
    # 2. Discord
    if settings.DISCORD_ENABLED:
        try:
            if signal_data and ticker:
                res_ds = DiscordBot_Alerts.send_signal_alert(
                    ticker=ticker,
                    signal_type=signal_data.get("type", "BUY"),
                    price=signal_data.get("price", 0.0),
                    score=signal_data.get("score", 0),
                    rationale=signal_data.get("rationale", [])
                )
            else:
                res_ds = DiscordBot_Alerts.send_discord_webhook(message)
            results["discord"] = res_ds
        except Exception as e:
            logger.error(f"Discord broadcast error: {e}")
            results["discord"] = {"status": "error", "message": str(e)}
            
    # 3. Generic Webhook
    if settings.WEBHOOK_ENABLED:
        try:
            from core import WebhookManager
            event_data = {
                "message": message,
                "ticker": ticker,
                "priority": priority
            }
            if signal_data:
                event_data["signal"] = signal_data
            
            res_wh = WebhookManager.send_webhook("BROADCAST", event_data)
            results["webhook"] = res_wh
        except Exception as e:
            logger.error(f"Webhook broadcast error: {e}")
            results["webhook"] = {"status": "error", "message": str(e)}
            
    # 4. WebSockets (Live Dashboard)
    try:
        # Check if we have a running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast(message, event_type="alert"))
        except RuntimeError:
            # No event loop in this thread
            pass
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")
            
    return results

def broadcast_image(image_buf, caption: str = "", token: str | None = None, chat_id: str | None = None):
    """
    Sends an image to all active channels.
    """
    results = {}
    
    # 1. Telegram
    if settings.TELEGRAM_ENABLED:
        try:
            res_tg = _call_with_supported_kwargs(
                TelegramBot_Alerts.send_image,
                image_buf,
                caption=caption,
                token=token,
                chat_id=chat_id,
            )
            results["telegram"] = res_tg
        except Exception as e:
            logger.error(f"Telegram image broadcast error: {e}")
            results["telegram"] = {"status": "error", "message": str(e)}
            
    # 2. Discord (Webhooks support file uploads but let's start with basic content/embed for now)
    # If we want to send the actual image to Discord via webhook, we'd need to post it as a file.
    if settings.DISCORD_ENABLED:
        try:
            # Simple fallback for Discord if image sending isn't fully implemented in DiscordBot_Alerts:
            # just send the caption.
            res_ds = DiscordBot_Alerts.send_discord_webhook(f"🖼️ **[Image Alert]**\n{caption}")
            results["discord"] = res_ds
        except Exception as e:
            logger.error(f"Discord image broadcast error: {e}")
            results["discord"] = {"status": "error", "message": str(e)}
            
    return results
