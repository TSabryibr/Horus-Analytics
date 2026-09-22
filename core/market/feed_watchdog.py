"""
MARKET FEED WATCHDOG & SELF-HEALING ENGINE
==========================================
Monitors intraday market data feeds (Mubasher, MetaStock, etc.) during active
market hours (10:00 - 14:30 EGX). If feed lag exceeds the threshold (> 5m),
it automatically invalidates stale caches, attempts incremental resync, and
escalates to admin alerts with a configurable cooldown if the stall persists.
"""
from __future__ import annotations

import datetime
from typing import Any, Optional
import pandas as pd

from core import TimeUtils
from core.settings import settings
from utils.logger import setup_logger

logger = setup_logger("horus.market.feed_watchdog")


class MarketFeedWatchdog:
    """Watchdog for intraday market data freshness and feed self-healing."""

    _last_alert_time: Optional[datetime.datetime] = None
    _consecutive_stalls: int = 0
    _last_heal_attempt: Optional[datetime.datetime] = None

    @classmethod
    def reset_state(cls) -> None:
        """Reset in-memory watchdog state (primarily for tests)."""
        cls._last_alert_time = None
        cls._consecutive_stalls = 0
        cls._last_heal_attempt = None

    @classmethod
    def check_feed_heartbeat(
        cls,
        max_stall_minutes: float = 5.0,
        realm: str = "EGX",
    ) -> dict[str, Any]:
        """
        Evaluates whether the market feed is currently lagging behind real-time.
        
        If the market is closed, heartbeat reports healthy (closed).
        If the market is open, it inspects the latest bar timestamps across the store.
        """
        now = TimeUtils.now()
        market_open = bool(settings.is_market_open())

        if not market_open:
            return {
                "is_market_open": False,
                "stalled": False,
                "status": "MARKET_CLOSED",
                "reason": "Market is closed",
                "lag_minutes": None,
                "latest_timestamp": None,
                "tickers_monitored": 0,
                "checked_at": now.isoformat(),
            }

        try:
            from data_engine.intraday_store import get_latest_timestamps
            timestamps = get_latest_timestamps(realm=realm)
        except Exception as exc:
            logger.error(f"[FeedWatchdog] Failed to query latest timestamps: {exc}")
            timestamps = {}

        if not timestamps:
            return {
                "is_market_open": True,
                "stalled": True,
                "status": "NO_DATA",
                "reason": "No intraday bars found for realm",
                "lag_minutes": None,
                "latest_timestamp": None,
                "tickers_monitored": 0,
                "checked_at": now.isoformat(),
            }

        valid_ts = [ts for ts in timestamps.values() if ts is not None and not pd.isna(ts)]
        if not valid_ts:
            return {
                "is_market_open": True,
                "stalled": True,
                "status": "NO_VALID_DATA",
                "reason": "No valid timestamps found in intraday bars",
                "lag_minutes": None,
                "latest_timestamp": None,
                "tickers_monitored": len(timestamps),
                "checked_at": now.isoformat(),
            }

        latest_ts = max(valid_ts)
        now_ts = pd.Timestamp(now)

        # Handle timezone alignment if one is aware and other is naive
        if latest_ts.tzinfo is not None and now_ts.tzinfo is None:
            now_ts = now_ts.tz_localize(latest_ts.tzinfo)
        elif latest_ts.tzinfo is None and now_ts.tzinfo is not None:
            latest_ts = latest_ts.tz_localize(now_ts.tzinfo)

        lag_seconds = max(0.0, (now_ts - latest_ts).total_seconds())
        lag_minutes = round(lag_seconds / 60.0, 2)
        stalled = lag_minutes > max_stall_minutes

        status_str = "STALLED" if stalled else "HEALTHY"
        reason = (
            f"Feed stalled: newest bar is {lag_minutes}m old (threshold: {max_stall_minutes}m)"
            if stalled
            else f"Feed healthy: lag is {lag_minutes}m"
        )

        return {
            "is_market_open": True,
            "stalled": stalled,
            "status": status_str,
            "reason": reason,
            "lag_minutes": lag_minutes,
            "latest_timestamp": latest_ts.isoformat() if hasattr(latest_ts, "isoformat") else str(latest_ts),
            "tickers_monitored": len(timestamps),
            "checked_at": now.isoformat(),
        }

    @classmethod
    def check_and_heal(
        cls,
        max_stall_minutes: float = 5.0,
        alert_cooldown_minutes: float = 15.0,
        realm: str = "EGX",
    ) -> dict[str, Any]:
        """
        Executes heartbeat check. If stalled, performs self-healing:
          1. Invalidates freshness cache.
          2. Triggers incremental intraday sync.
          3. Re-checks heartbeat.
          4. If still stalled, alerts administrator via Telegram (with cooldown).
        """
        status = cls.check_feed_heartbeat(max_stall_minutes=max_stall_minutes, realm=realm)

        if not status.get("stalled", False):
            if cls._consecutive_stalls > 0:
                logger.info(
                    "[FeedWatchdog] Market feed recovered after %d stalled ticks.",
                    cls._consecutive_stalls,
                )
                cls._consecutive_stalls = 0
            return {
                "action": "none",
                "healed": False,
                "status": status,
            }

        cls._consecutive_stalls += 1
        logger.warning(
            "[FeedWatchdog] Market feed stall detected (lag: %s min, stall tick: #%d). Initiating self-healing...",
            status.get("lag_minutes"),
            cls._consecutive_stalls,
        )

        # 1. Invalidate cache
        try:
            from data_engine.freshness import invalidate_freshness_cache
            invalidate_freshness_cache(realm=realm)
        except Exception as cache_err:
            logger.error(f"[FeedWatchdog] Cache invalidation failed: {cache_err}")

        # 2. Trigger incremental sync
        try:
            from data_engine.sync import _sync_intraday
            intraday_provider = str(getattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB"))
            _sync_intraday(realm, intraday_provider)
            invalidate_freshness_cache(realm=realm)
            cls._last_heal_attempt = TimeUtils.now()
        except Exception as sync_err:
            logger.error(f"[FeedWatchdog] Self-healing sync failed: {sync_err}")

        # 3. Recheck status
        recheck = cls.check_feed_heartbeat(max_stall_minutes=max_stall_minutes, realm=realm)
        if not recheck.get("stalled", False):
            logger.info("[FeedWatchdog] Self-healing succeeded: feed resumed.")
            cls._consecutive_stalls = 0
            return {
                "action": "sync_healed",
                "healed": True,
                "status": recheck,
            }

        # 4. Feed is still stalled — evaluate alert cooldown
        now = TimeUtils.now()
        in_cooldown = False
        if cls._last_alert_time is not None:
            elapsed_min = (now - cls._last_alert_time).total_seconds() / 60.0
            if elapsed_min < alert_cooldown_minutes:
                in_cooldown = True

        if not in_cooldown:
            cls._last_alert_time = now
            msg = (
                f"🚨 *CRITICAL: MARKET FEED STALLED*\n"
                f"Market is OPEN but intraday feed has stalled for *{recheck.get('lag_minutes', 'N/A')} minutes*.\n"
                f"Monitored Tickers: {recheck.get('tickers_monitored', 0)}\n"
                f"Latest Bar: {recheck.get('latest_timestamp', 'Unknown')}\n"
                f"Self-healing sync attempt did not resolve the lag.\n"
                f"Action Required: Verify Mubasher/MetaStock data feed source."
            )
            try:
                from core import AlertManager
                AlertManager.broadcast_alert(msg)
                logger.info("[FeedWatchdog] Broadcasted feed stall alert to admin.")
            except Exception as alert_err:
                logger.error(f"[FeedWatchdog] Failed to broadcast alert: {alert_err}")

            return {
                "action": "alert_sent",
                "healed": False,
                "status": recheck,
            }

        logger.warning(
            "[FeedWatchdog] Feed remains stalled, but alert is in cooldown (%s min threshold).",
            alert_cooldown_minutes,
        )
        return {
            "action": "alert_cooldown",
            "healed": False,
            "status": recheck,
        }
