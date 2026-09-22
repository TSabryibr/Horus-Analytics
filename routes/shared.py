import copy
import threading
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler

from core.app_state import (
    AppStateManager,
    FreshnessState,
    GLOBAL_APP_STATE,
    SyncWorkerState,
)
from core.domain_enums import PipelineState, ProvisioningStatus, SessionMode

# === SHARED SYSTEM STATE ===
# Bound to GLOBAL_APP_STATE singleton for typed, thread-safe access
SYSTEM_STATE: Dict[str, Any] = GLOBAL_APP_STATE.raw_state_dict
SYSTEM_STATE_LOCK = GLOBAL_APP_STATE.lock
OPTIMIZATION_STATE_LOCK = GLOBAL_APP_STATE.optimization_lock
HARD_RESET_TOKENS = GLOBAL_APP_STATE.raw_hard_reset_tokens

def update_system_state(updates: dict) -> None:
    GLOBAL_APP_STATE.update_system_state(updates)

def get_system_state_snapshot() -> dict:
    return GLOBAL_APP_STATE.get_system_state_snapshot()

def set_stale_override(on: bool) -> None:
    """Toggle user-approved stale data bypass."""
    GLOBAL_APP_STATE.set_stale_override(on)

def is_stale_overridden() -> bool:
    return GLOBAL_APP_STATE.is_stale_overridden()

def set_pipeline_state(pipeline_state: str, message: str | None = None, **extra) -> None:
    """Sets pipeline state while keeping legacy `status` compatible for UI readiness checks."""
    GLOBAL_APP_STATE.set_pipeline_state(pipeline_state, message=message, **extra)

def set_provisioning_state(
    provisioning_status: str,
    *,
    target_trading_days: int | None = None,
    completed_trading_days: int | None = None,
    message: str | None = None,
    error: str | None = None,
) -> None:
    GLOBAL_APP_STATE.set_provisioning_state(
        provisioning_status,
        target_trading_days=target_trading_days,
        completed_trading_days=completed_trading_days,
        message=message,
        error=error,
    )

def get_durable_provisioning_state() -> dict:
    try:
        from database import ProvisioningState

        row = ProvisioningState.get_or_none(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
        if row is None:
            return {}

        return {
            "last_backfill_status": str(row.status or "IDLE").upper(),
            "last_backfill_target_trading_days": int(row.target_trading_days or 0),
            "last_backfill_completed_trading_days": int(row.completed_trading_days or 0),
            "last_backfill_error": row.last_error,
            "last_backfill_mode": str(row.mode or "AUTOMATIC").upper(),
            "last_backfill_universe_choice": str(getattr(row, "backfill_universe_choice", "EGX30") or "EGX30").upper(),
            "last_backfill_started_at": row.started_at.isoformat() if row.started_at else None,
            "last_backfill_completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }
    except Exception:
        return {}

def set_freshness_state(
    *,
    history_fresh_ratio: float,
    intraday_live_ratio: float,
    history_ok: bool,
    intraday_ok: bool,
    market_open: bool,
    overall_ok: bool,
    checked_at: str | None,
    session_mode: str | None = None,
) -> None:
    GLOBAL_APP_STATE.set_freshness_state(
        history_fresh_ratio=history_fresh_ratio,
        intraday_live_ratio=intraday_live_ratio,
        history_ok=history_ok,
        intraday_ok=intraday_ok,
        market_open=market_open,
        overall_ok=overall_ok,
        checked_at=checked_at,
        session_mode=session_mode,
    )

# === BACKGROUND TASKS ===
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

# === BACKGROUND TASKS ===
scheduler = BackgroundScheduler()

def _rate_limits_default() -> list:
    raw = os.getenv("HORUS_RATE_LIMIT_PER_MIN", "600").strip().lower()
    if raw in ("0", "off", "false", "disable", "disabled", "none"):
        return ["1000000/minute"]
    try:
        per_min = int(raw)
        if per_min <= 0:
            return ["1000000/minute"]
        return [f"{per_min}/minute"]
    except ValueError:
        return ["600/minute"]

limiter = Limiter(key_func=get_remote_address, default_limits=_rate_limits_default())

# === EAGER CACHES ===
# Many analytics modules use caches to avoid heavy re-computation on every UI refresh
NEWS_CACHE = {"data": [], "timestamp": None, "version": -1}
SECTOR_CACHE = {"data": [], "timestamp": None, "version": -1}
WHALE_CACHE = {"data": [], "timestamp": None, "version": -1}
ARBITRAGE_CACHE = {"data": [], "timestamp": None, "version": -1, "variants": {}}
TRAP_CACHE = {"data": [], "timestamp": None, "version": -1}
STRATEGY_CACHE = {"data": [], "timestamp": None, "version": -1}
ORACLE_CACHE = {"data": [], "timestamp": None, "version": -1}
CONFLUENCE_CACHE = {"data": {}, "timestamp": None, "version": -1}

def purge_all_caches():
    """Wipes all eager caches when market parameters or time travel state change."""
    with SYSTEM_STATE_LOCK:
        SYSTEM_STATE["data_version"] = 0
    
    NEWS_CACHE.update({"data": [], "timestamp": None, "version": -1})
    SECTOR_CACHE.update({"data": [], "timestamp": None, "version": -1})
    WHALE_CACHE.update({"data": [], "timestamp": None, "version": -1})
    ARBITRAGE_CACHE.update({"data": [], "timestamp": None, "version": -1, "variants": {}})
    TRAP_CACHE.update({"data": [], "timestamp": None, "version": -1})
    STRATEGY_CACHE.update({"data": [], "timestamp": None, "version": -1})
    ORACLE_CACHE.update({"data": [], "timestamp": None, "version": -1})
    CONFLUENCE_CACHE.update({"data": {}, "timestamp": None, "version": -1})
    
    # 2. Clear Performance Layer Cache (Calculation Cache)
    try:
        from core import StockLoader
        StockLoader.clear_cache()
    except Exception as e:
        print(f"[Cache] Failed to clear StockLoader: {e}")
    
    print("[Cache] All analytics caches purged.")

# Shared Scanner State
SCAN_STATE: Dict[str, Any] = {
    "status": "IDLE", # IDLE, RUNNING, COMPLETED, ERROR
    "progress": 0,
    "current_ticker": "",
    "result": None
}

# Shared Optimization State
OPTIMIZATION_STATE: Dict[str, Any] = {
    "status": "IDLE", # IDLE, PREPARING, RUNNING, COMPLETED, ERROR
    "index": None,
    "progress": 0,
    "completed": 0,
    "total": 0,
    "eta": 0,
    "found": 0,
    "best_win_rate": 0,
    "result": None,
    "error": None
}

# === SHARED MODELS ===
class SignalCardRequest(BaseModel):
    ticker: str
    entry: float
    sl: float
    tp1: float
    tp2: Optional[float] = None
    score: Optional[float] = None
    rsi: Optional[float] = None
    volume_x: Optional[float] = None
    confirmation: Optional[str] = None
    regime: Optional[str] = None
    signal_date: Optional[str] = None
    caption: Optional[str] = None
