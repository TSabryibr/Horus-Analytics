"""
Horus Core - Typed Application State Manager.
Encapsulates thread-safe runtime state, pipeline health, provisioning tracking,
and telemetry for FastAPI services and background workers.
"""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from core.domain_enums import PipelineState, ProvisioningStatus, SessionMode


@dataclass
class FreshnessState:
    history_fresh_ratio: float = 0.0
    intraday_live_ratio: float = 0.0
    history_ok: bool = False
    intraday_ok: bool = False
    market_open: bool = False
    overall_ok: bool = False
    checked_at: Optional[str] = None
    session_mode: str = "LIVE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_fresh_ratio": float(self.history_fresh_ratio),
            "intraday_live_ratio": float(self.intraday_live_ratio),
            "history_ok": bool(self.history_ok),
            "intraday_ok": bool(self.intraday_ok),
            "market_open": bool(self.market_open),
            "overall_ok": bool(self.overall_ok),
            "checked_at": self.checked_at,
            "session_mode": self.session_mode,
        }


@dataclass
class SyncWorkerState:
    enabled: bool = False
    running: bool = False
    last_attempt_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_error: Optional[str] = None
    fail_count: int = 0
    next_retry_seconds: int = 0
    backoff_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "running": bool(self.running),
            "last_attempt_at": self.last_attempt_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_error": self.last_error,
            "fail_count": int(self.fail_count),
            "next_retry_seconds": int(self.next_retry_seconds),
            "backoff_seconds": int(self.backoff_seconds),
        }


class AppStateManager:
    """Thread-safe manager for application runtime state and background coordination."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._optimization_lock = threading.Lock()

        self._state: Dict[str, Any] = {
            "status": "STARTING",
            "message": "Initializing Horus Core...",
            "progress": 0,
            "step": "Init",
            "bootstrap_complete": False,
            "provisioning_status": ProvisioningStatus.IDLE.value,
            "provisioning_target_trading_days": 0,
            "provisioning_completed_trading_days": 0,
            "provisioning_error": None,
            "pipeline_state": PipelineState.STARTING.value,
            "stale_mode": False,
            "stale_override": False,
            "freshness": FreshnessState().to_dict(),
            "data_version": 0,
            "sync_worker": SyncWorkerState().to_dict(),
        }

        self._scan_state: Dict[str, Any] = {
            "status": "IDLE",
            "progress": 0,
            "current_ticker": "",
            "result": None,
        }

        self._optimization_state: Dict[str, Any] = {
            "status": "IDLE",
            "index": None,
            "progress": 0,
            "completed": 0,
            "total": 0,
            "eta": 0,
            "found": 0,
            "best_win_rate": 0,
            "result": None,
            "error": None,
        }

        self._hard_reset_tokens: Dict[str, Any] = {}

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    @property
    def optimization_lock(self) -> threading.Lock:
        return self._optimization_lock

    @property
    def raw_state_dict(self) -> Dict[str, Any]:
        """Provides direct access for backward compatibility."""
        return self._state

    @property
    def raw_scan_state(self) -> Dict[str, Any]:
        return self._scan_state

    @property
    def raw_optimization_state(self) -> Dict[str, Any]:
        return self._optimization_state

    @property
    def raw_hard_reset_tokens(self) -> Dict[str, Any]:
        return self._hard_reset_tokens

    def update_system_state(self, updates: Dict[str, Any]) -> None:
        with self._lock:
            self._state.update(updates)

    def get_system_state_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def set_stale_override(self, on: bool) -> None:
        self.update_system_state({"stale_override": bool(on)})

    def is_stale_overridden(self) -> bool:
        with self._lock:
            return bool(self._state.get("stale_override", False))

    def set_pipeline_state(self, pipeline_state: str, message: Optional[str] = None, **extra: Any) -> None:
        normalized = str(pipeline_state or PipelineState.STARTING.value).upper()
        if normalized == "ERROR":
            status = "ERROR"
        elif normalized == "STARTING":
            status = "STARTING"
        else:
            status = "READY"

        stale_mode = normalized in {"SYNCING", "STALE", "DEGRADED"}
        payload: Dict[str, Any] = {
            "pipeline_state": normalized,
            "status": status,
            "stale_mode": stale_mode,
        }
        if normalized == PipelineState.FRESH.value:
            payload["stale_override"] = False
        if message:
            payload["message"] = message
        payload.update(extra)
        self.update_system_state(payload)

    def set_provisioning_state(
        self,
        provisioning_status: str,
        *,
        target_trading_days: Optional[int] = None,
        completed_trading_days: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        normalized = str(provisioning_status or ProvisioningStatus.IDLE.value).strip().upper() or "IDLE"

        if normalized == ProvisioningStatus.RUNNING.value:
            status = "PROVISIONING"
            bootstrap_complete = False
        elif normalized in {ProvisioningStatus.COMPLETED.value, ProvisioningStatus.COMPLETED_WITH_WARNINGS.value}:
            status = "READY"
            bootstrap_complete = True
        elif normalized == ProvisioningStatus.ERROR.value:
            status = "ERROR"
            bootstrap_complete = False
        else:
            status = "STARTING"
            bootstrap_complete = False

        payload: Dict[str, Any] = {
            "status": status,
            "bootstrap_complete": bootstrap_complete,
            "provisioning_status": normalized,
            "provisioning_error": error,
        }
        if target_trading_days is not None:
            payload["provisioning_target_trading_days"] = int(target_trading_days)
        if completed_trading_days is not None:
            payload["provisioning_completed_trading_days"] = int(completed_trading_days)
        if message is not None:
            payload["message"] = message
        self.update_system_state(payload)

    def set_freshness_state(
        self,
        *,
        history_fresh_ratio: float,
        intraday_live_ratio: float,
        history_ok: bool,
        intraday_ok: bool,
        market_open: bool,
        overall_ok: bool,
        checked_at: Optional[str],
        session_mode: Optional[str] = None,
    ) -> None:
        freshness = FreshnessState(
            history_fresh_ratio=history_fresh_ratio,
            intraday_live_ratio=intraday_live_ratio,
            history_ok=history_ok,
            intraday_ok=intraday_ok,
            market_open=market_open,
            overall_ok=overall_ok,
            checked_at=checked_at,
            session_mode=session_mode or SessionMode.LIVE.value,
        )
        self.update_system_state({"freshness": freshness.to_dict()})


# Singleton AppState instance
GLOBAL_APP_STATE = AppStateManager()
