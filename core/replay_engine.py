"""
REPLAY ENGINE — Facade Module
=============================
Provides full backward compatibility for `core.replay_engine`.
All functionality has been decomposed into `core.replay`.
"""

import threading
import datetime
import time
from core.settings import settings
from core import TimeUtils, DailyScanner, AlertManager, ReportGenerator, TelegramBot_Alerts
from utils.logger import setup_logger

logger = setup_logger("horus.replay")

from core.replay import (
    REPLAY_PREFIX,
    _REPLAY_STATE,
    _REPLAY_LOCK,
    _REPLAY_THREAD,
    _REPLAY_STOP_EVENT,
    _reset_state,
    _parse_market_times,
    _resolve_replay_scanner_profile,
    _run_selected_replay_profile_scan,
    _realm_for_replay_market,
    _get_replay_intraday_availability,
    _format_intraday_availability_error,
    _safe_float,
    _format_duration,
    _get_simulation_portfolio,
    _clear_simulation_portfolio,
    _load_open_replay_positions,
    _summarize_replay_trades,
    _build_risk_sized_replay_trade,
    _create_mock_replay_position,
    _update_mock_position_state,
    _latest_replay_exit_price,
    _close_open_replay_positions_at_end,
    _replay_telegram_config,
    _build_replay_followup_message,
    _broadcast_replay_followup,
    _mock_trade_monitor,
    _empty_pending_replay_result,
    _is_daily_replay_scan,
    _is_pre_close_replay_scan,
    _replay_signal_tickers,
    _record_replay_pre_close_previews,
    _reconcile_replay_pre_close_previews,
    _has_open_replay_trade,
    _has_pending_replay_entry,
    _queue_daily_replay_entry,
    _resolve_pending_replay_gap_pct,
    _latest_replay_open_price,
    _execute_pending_replay_entries,
    _persist_replay_signals,
    _notify_replay_entry,
    _safe_broadcast,
    _safe_broadcast_image,
    _broadcast_replay_signals,
    _generate_replay_report,
    _run_one_tick,
    _replay_worker,
    _iter_campaign_dates,
    _get_replay_campaign_intraday_availability,
    _format_campaign_availability_error,
    _record_campaign_tick_result,
    _update_campaign_progress,
    _run_replay_campaign_day,
    _replay_campaign_worker,
    start_replay,
    start_replay_campaign,
    stop_replay,
    get_replay_status,
)
