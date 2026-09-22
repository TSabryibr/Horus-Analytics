"""
SCHEDULING SCANS EXECUTION
==========================
Signal run execution and pending daily entry dispatch.
"""

from __future__ import annotations

import os

from core.pipeline import _env_bool
from core.settings import settings
from core.signals.executor import SignalExecutor

from ..state import _resolve_scheduling_dispatch


def execute_run_for_horus(run_id: int):
    executor_cls = _resolve_scheduling_dispatch("SignalExecutor", SignalExecutor)
    return executor_cls.execute_run(run_id)


execute_run = execute_run_for_horus


def execute_pending_daily_entries_for_horus():
    executor_cls = _resolve_scheduling_dispatch("SignalExecutor", SignalExecutor)
    return executor_cls.execute_pending_entries()


execute_pending_entries = execute_pending_daily_entries_for_horus


def _signal_auto_execution_enabled() -> bool:
    if not bool(getattr(settings, "AUTO_TRADE_ENABLED", False)):
        return False
    if os.getenv("SIGNAL_AUTO_EXECUTION_ENABLED") is not None:
        return _env_bool("SIGNAL_AUTO_EXECUTION_ENABLED", False)
    return bool(getattr(settings, "SIGNAL_AUTO_EXECUTION_ENABLED", False))
