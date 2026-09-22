"""
SCHEDULING SCANS DELIVERIES & DATA SYNC
=======================================
Telegram channel delivery recording, subscriber publishing, and data readiness checks.
"""

from __future__ import annotations

import datetime
import os
from peewee import fn
from fastapi import HTTPException

from core import TimeUtils, subscriptions, Heimdall, AlertManager, TelegramBot_Alerts
from core.pipeline import _env_bool, _env_int
from core.settings import settings
from core.signals.followups import process_signal_followups
from core.signals.lifecycle import reconcile_pre_close_previews
from data_engine.freshness import evaluate_freshness
from database import SignalDelivery, SignalRecommendation, SignalRun
from routes import signals
from utils.logger import setup_logger

from ..state import (
    _NO_SIGNAL_NOTICE_KEYS,
    _NO_SIGNAL_NOTICE_LOCK,
    _increment_daily_signal_retry_count,
    _mark_ai_daily_report_pending,
    _mark_daily_signal_pending,
    _maybe_broadcast_data_waiting_subscriber_notice,
    _resolve_scheduling_dispatch,
)

logger = setup_logger("horus.scheduling.scans.deliveries")


def _get_logger():
    return _resolve_scheduling_dispatch("logger", logger)


def _scheduler_signal_tickers(signals_list) -> set[str]:
    return {
        str((item or {}).get("Ticker") or "").strip().upper()
        for item in (signals_list or [])
        if str((item or {}).get("Ticker") or "").strip()
    }


def _record_direct_main_channel_signal_delivery(run_id: int, signals_list) -> SignalDelivery | None:
    tickers = _scheduler_signal_tickers(signals_list)
    if not run_id or not tickers:
        return None
    run = SignalRun.get_or_none(SignalRun.id == run_id)
    if run is None:
        return None
    chat_id = str(getattr(settings, "CHAT_ID", "") or "").strip()
    if not chat_id:
        return None

    sent_at = TimeUtils.now()
    delivery, _created = SignalDelivery.get_or_create(
        run=run,
        channel="TELEGRAM",
        destination_type="MAIN_CHANNEL",
        destination_id="main",
        defaults={
            "service_tier": subscriptions.SIGNALS_ONLY,
            "destination_name": "Main Telegram Channel",
            "destination_chat_id": chat_id,
            "status": "SENT",
            "sent_at": sent_at,
        },
    )
    delivery.portfolio = None
    delivery.service_tier = subscriptions.SIGNALS_ONLY
    delivery.destination_name = "Main Telegram Channel"
    delivery.destination_chat_id = chat_id
    delivery.status = "SENT"
    delivery.last_error = None
    delivery.sent_at = delivery.sent_at or sent_at
    delivery.save()

    recommendations = list(
        SignalRecommendation.select()
        .where(
            (SignalRecommendation.run == run)
            & (SignalRecommendation.state == "ACTIVE")
            & (fn.Upper(SignalRecommendation.ticker).in_(tickers))
        )
        .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc())
    )
    if recommendations:
        try:
            signals._create_published_signal_lifecycle_records(
                run=run,
                delivery=delivery,
                portfolio=None,
                recommendations=recommendations,
                operating_mode="AUTOPILOT",
                published_at=delivery.sent_at or sent_at,
            )
        except Exception as exc:
            logger.error(f"[Scheduler] Main-channel lifecycle recording failed for run {run_id}: {exc}")
    return delivery


def _publish_scheduler_signal_deliveries(
    *,
    run_id: int | None,
    signals_list,
    include_main_channel_record: bool,
) -> None:
    if not run_id:
        return
    tickers = _scheduler_signal_tickers(signals_list)
    if not tickers:
        return

    if include_main_channel_record:
        _record_direct_main_channel_signal_delivery(run_id, signals_list)

    if not _env_bool("SIGNAL_AUTO_PUBLISH_ENABLED", True):
        logger.info(f"[Scheduler] Subscriber signal publish skipped for run {run_id}: SIGNAL_AUTO_PUBLISH_ENABLED is off.")
        return

    publish_req = signals.PublishSignalsRequest(
        run_id=run_id,
        portfolio_ids=[],
        channel="TELEGRAM",
        service_tier=subscriptions.SIGNALS_ONLY,
        operating_mode="AUTOPILOT",
        include_portfolios=False,
        include_subscribers=True,
        include_main_channel=False,
        dry_run=_env_bool("SIGNAL_AUTO_PUBLISH_DRY_RUN", False),
        max_retries=_env_int("SIGNAL_PUBLISH_RETRIES", 2),
        backoff_ms=_env_int("SIGNAL_PUBLISH_BACKOFF_MS", 500),
        enforce_window=False,
        ignore_guard=False,
    )
    try:
        publish_result = signals.publish_signal_run_logic(
            publish_req,
            recommendation_filter_fn=lambda rec: str(rec.ticker or "").strip().upper() in tickers,
        )
        publish_summary = publish_result.get("summary") or {}
        failed_count = publish_summary.get("failed", 0)
        failure_reasons = publish_summary.get("failure_reasons", {})
        if failed_count > 0:
            logger.warning(
                f"[Scheduler] Subscriber signal publish partial/full failure for run {run_id}: "
                f"sent={publish_summary.get('sent', 0)} failed={failed_count} reasons={failure_reasons}"
            )
        else:
            logger.info(f"[Scheduler] Subscriber signal publish summary: {publish_summary}")
    except HTTPException as he:
        detail = he.detail if isinstance(he.detail, dict) else {}
        reason = detail.get("error_reason") or detail.get("reason") or f"{he.detail}"
        if reason == "no_eligible_signal_destinations":
            logger.info(f"[Scheduler] Subscriber signal publish skipped for run {run_id}: no eligible destinations.")
            return
        logger.warning(f"[Scheduler] Subscriber signal publish blocked/failed for run {run_id}: {he.detail}")
    except Exception as exc:
        logger.error(f"[Scheduler] Subscriber signal publish failed for run {run_id}: {exc}")


def _background_ops_paused_for_time_travel() -> bool:
    if TimeUtils.is_replay():
        return True
    if TimeUtils.is_simulating():
        return True
    try:
        from core.market.HistoricalBackfill import is_backfill_running
        return is_backfill_running()
    except Exception:
        return False


def _reconcile_scheduler_pre_close_previews(*, final_daily_tickers: set[str], run_date=None) -> dict:
    try:
        reconcile_fn = _resolve_scheduling_dispatch("reconcile_pre_close_previews", reconcile_pre_close_previews)
        time_utils = _resolve_scheduling_dispatch("TimeUtils", TimeUtils)
        result = reconcile_fn(
            run_date=run_date or time_utils.today(),
            confirmed_tickers=final_daily_tickers,
            now_fn=time_utils.now,
        )
        summary = result.get("summary", {})
        if any(int(summary.get(key, 0) or 0) for key in ("confirmed_lifecycles", "cancelled_lifecycles", "cancelled_pending_entries")):
            logger.info(f"[Scheduler] Daily confirmation reconciled pre-close previews: {summary}")
        if int(summary.get("cancelled_lifecycles", 0) or 0) > 0 and _env_bool("SIGNAL_AUTO_FOLLOWUPS_ENABLED", True):
            followups_fn = _resolve_scheduling_dispatch("process_signal_followups", process_signal_followups)
            tg_alerts = _resolve_scheduling_dispatch("TelegramBot_Alerts", TelegramBot_Alerts)
            followup_result = followups_fn(
                limit=_env_int("SIGNAL_AUTO_FOLLOWUP_BATCH_LIMIT", 20),
                send_message_fn=tg_alerts.send_message,
                now_fn=time_utils.now,
            )
            logger.info(f"[Scheduler] Daily confirmation processed pre-close follow-ups: {followup_result.get('summary')}")
        return result
    except Exception as exc:
        logger.error(f"[Scheduler] Daily confirmation failed to reconcile pre-close previews: {exc}")
        return {"status": "error", "message": str(exc)}


def _scheduler_scan_type(scan_label: str, is_intraday: bool) -> str:
    normalized = (scan_label or "").strip().upper()
    if normalized == "PRE-CLOSE":
        return "PRE_CLOSE"
    if normalized == "DAILY SIGNAL":
        return "DAILY"
    return "INTRADAY" if is_intraday else "DAILY"


def _scheduler_run_key(
    scan_label: str,
    is_intraday: bool,
    *,
    market_date: datetime.date | None = None,
    preview_only: bool = False,
) -> str:
    m_date = market_date or TimeUtils.today()
    date_str = m_date.isoformat() if hasattr(m_date, "isoformat") else str(m_date)
    scan_type = _scheduler_scan_type(scan_label, is_intraday)
    if scan_type == "INTRADAY":
        now_dt = TimeUtils.now()
        return f"{date_str}:{scan_type}:{now_dt.strftime('%H:%M')}"
    if scan_type == "PRE_CLOSE":
        return f"{date_str}:PRE_CLOSE"
    if scan_type == "DAILY":
        if preview_only:
            return f"{date_str}:DAILY:PREVIEW"
        return f"{date_str}:DAILY:CONFIRMED"
    return f"{date_str}:{scan_type}"


def _run_is_durable_completed(run_key: str) -> bool:
    run = SignalRun.get_or_none(SignalRun.run_key == run_key)
    if run and str(run.status or "").upper() == "COMPLETED":
        return True
    return False


def _completed_daily_signal_run_has_results(run_key: str) -> bool:
    run = SignalRun.get_or_none(SignalRun.run_key == run_key)
    if run is None:
        return False
    if str(run.status or "").upper() != "COMPLETED":
        return False
    if int(run.signals_count or 0) > 0 or int(run.published_count or 0) > 0:
        return True
    if SignalRecommendation.select().where(SignalRecommendation.run == run).exists():
        return True
    return SignalDelivery.select().where(SignalDelivery.run == run).exists()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _parse_scheduler_datetime(value) -> datetime.datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            try:
                parsed = datetime.datetime.strptime(text[:16], "%Y-%m-%d %H:%M")
            except Exception:
                return None
    if getattr(parsed, "tzinfo", None) is not None:
        parsed = parsed.replace(tzinfo=None)
    return parsed


def _scheduler_freshness(scan_type: str) -> dict:
    return evaluate_freshness(
        realm=getattr(Heimdall, "CURRENT_REALM", "EGX"),
        run_date=TimeUtils.today(),
        scan_type=scan_type,
    )


def _daily_signal_history_ready(freshness: dict) -> bool:
    history = freshness.get("history") if isinstance(freshness, dict) else {}
    if not isinstance(history, dict):
        history = {}
    if bool(history.get("pending_eod_history", False)):
        return False
    kpis = history.get("kpis") if isinstance(history.get("kpis"), dict) else {}
    expected = (
        str(history.get("calendar_expected_last_working_day") or "").strip()
        or str(history.get("expected_last_working_day") or "").strip()
    )
    last_updated = str(history.get("last_updated") or freshness.get("last_updated") or "").strip()
    fresh_ratio = float(kpis.get("fresh_ratio", 0.0) or 0.0)
    min_ratio = _env_float("DAILY_SIGNAL_HISTORY_FRESH_RATIO_MIN", 0.90)
    return bool(expected) and last_updated == expected and fresh_ratio >= min_ratio


def _pre_close_intraday_ready(freshness: dict) -> bool:
    history = freshness.get("history") if isinstance(freshness, dict) else {}
    intraday = freshness.get("intraday") if isinstance(freshness, dict) else {}
    if not isinstance(history, dict):
        history = {}
    if not isinstance(intraday, dict):
        intraday = {}
    kpis = intraday.get("kpis") if isinstance(intraday.get("kpis"), dict) else {}
    latest_bar = _parse_scheduler_datetime(intraday.get("last_bar"))
    if latest_bar is None or latest_bar.date() != TimeUtils.today():
        return False
    age_mins = (TimeUtils.now().replace(tzinfo=None) - latest_bar).total_seconds() / 60.0
    max_age_mins = max(1.0, _env_float("PRE_CLOSE_INTRADAY_MAX_AGE_MINS", 10.0))
    live_ratio = float(kpis.get("live_ratio", 0.0) or 0.0)
    min_ratio = _env_float("PRE_CLOSE_INTRADAY_LIVE_RATIO_MIN", 0.75)
    return bool(history.get("ok")) and age_mins <= max_age_mins and live_ratio >= min_ratio


def _log_scheduler_data_waiting(scan_label: str, freshness: dict, *, source: str) -> None:
    history = freshness.get("history") if isinstance(freshness, dict) else {}
    intraday = freshness.get("intraday") if isinstance(freshness, dict) else {}
    if not isinstance(history, dict):
        history = {}
    if not isinstance(intraday, dict):
        intraday = {}
    history_kpis = history.get("kpis") if isinstance(history.get("kpis"), dict) else {}
    intraday_kpis = intraday.get("kpis") if isinstance(intraday.get("kpis"), dict) else {}
    logger.info(
        f"[Scheduler] {scan_label} data not ready ({source}): "
        f"history_expected={history.get('calendar_expected_last_working_day') or history.get('expected_last_working_day')} "
        f"history_last={history.get('last_updated') or freshness.get('last_updated')} "
        f"history_ratio={history_kpis.get('fresh_ratio')} "
        f"intraday_last={intraday.get('last_bar')} "
        f"intraday_age={intraday.get('age_mins')} "
        f"intraday_ratio={intraday_kpis.get('live_ratio')}"
    )


def _sync_scheduler_data(scan_label: str) -> bool:
    if not _env_bool("SCHEDULER_DATA_SYNC_ENABLED", True):
        logger.info(f"[Scheduler] {scan_label} data refresh skipped: SCHEDULER_DATA_SYNC_ENABLED is off.")
        return False
    try:
        from data_engine.sync import sync_all

        force_history_recent_days = 0
        if scan_label == "DAILY SIGNAL":
            force_history_recent_days = _env_int("DAILY_SIGNAL_FORCE_HISTORY_RECENT_DAYS", 3)
        logger.info(
            f"[Scheduler] {scan_label} refreshing data before scan "
            f"(force_history_recent_days={force_history_recent_days})."
        )
        sync_all(force_history_recent_days=force_history_recent_days)
        try:
            from data_engine.freshness import invalidate_freshness_cache

            invalidate_freshness_cache(realm=getattr(Heimdall, "CURRENT_REALM", "EGX"))
        except Exception as cache_exc:
            logger.warning(f"[Scheduler] {scan_label} freshness cache invalidation failed: {cache_exc}")
        return True
    except Exception as exc:
        logger.error(f"[Scheduler] {scan_label} data refresh failed: {exc}")
        return False


def _daily_signal_run_date() -> str:
    return TimeUtils.today().isoformat()


def _history_and_intraday_ready(freshness: dict) -> bool:
    if not isinstance(freshness, dict):
        return False
    history = freshness.get("history") if isinstance(freshness, dict) else {}
    if isinstance(history, dict) and bool(history.get("pending_eod_history", False)):
        return False
    hist_fn = _resolve_scheduling_dispatch("_daily_signal_history_ready", _daily_signal_history_ready)
    intra_fn = _resolve_scheduling_dispatch("_pre_close_intraday_ready", _pre_close_intraday_ready)
    hist_ready = hist_fn(freshness)
    intra_ready = intra_fn(freshness)
    overall_ok = bool(freshness.get("overall_ok", False))
    return (hist_ready and intra_ready) or (overall_ok and hist_ready)


def _ensure_scheduler_data_ready(scan_label: str) -> bool:
    label = (scan_label or "").strip().upper()
    run_date_fn = _resolve_scheduling_dispatch("_daily_signal_run_date", _daily_signal_run_date)
    run_date = run_date_fn()

    if label in {"DAILY SIGNAL", "PRE-CLOSE"}:
        scan_type_arg = "PRE_CLOSE" if label == "PRE-CLOSE" else "DAILY"
        freshness_fn = _resolve_scheduling_dispatch("_scheduler_freshness", _scheduler_freshness)
        hist_fn = _resolve_scheduling_dispatch("_daily_signal_history_ready", _daily_signal_history_ready)
        ready_fn = _resolve_scheduling_dispatch("_history_and_intraday_ready", _history_and_intraday_ready)
        sync_fn = _resolve_scheduling_dispatch("_sync_scheduler_data", _sync_scheduler_data)
        log_waiting_fn = _resolve_scheduling_dispatch("_log_scheduler_data_waiting", _log_scheduler_data_waiting)

        freshness = freshness_fn(scan_type_arg)
        check_ready = hist_fn(freshness) if label == "DAILY SIGNAL" else ready_fn(freshness)
        if check_ready:
            return True

        log_waiting_fn(label, freshness, source="precheck")
        sync_fn(label)
        freshness = freshness_fn(scan_type_arg)
        if ready_fn(freshness):
            return True

        log_waiting_fn(label, freshness, source="post-refresh")
        _maybe_broadcast_data_waiting_subscriber_notice(run_date)

        if label == "DAILY SIGNAL":
            max_retries = max(1, _env_int("DAILY_SIGNAL_MAX_RETRIES", 5))
            current_retries = _increment_daily_signal_retry_count(run_date)

            if current_retries >= max_retries:
                _get_logger().warning(
                    f"[Scheduler] DAILY SIGNAL data readiness timeout: reached {current_retries}/{max_retries} retries."
                )
                try:
                    msg = f"⚠️ Daily signal scan failed after {current_retries} retries — history/intraday data still not ready."
                    alert_mgr = _resolve_scheduling_dispatch("AlertManager", AlertManager)
                    alert_mgr.broadcast_alert(msg)
                except Exception as e:
                    logger.error(f"[Scheduler] Failed to send admin alert: {e}")

                if _env_bool("DAILY_SIGNAL_FORCE_ON_TIMEOUT", False):
                    _get_logger().warning("[Scheduler] DAILY SIGNAL scan proceeding anyway due to DAILY_SIGNAL_FORCE_ON_TIMEOUT=True.")
                    return True

            _mark_daily_signal_pending(run_date)
            _mark_ai_daily_report_pending(run_date)

        return False

    return True


def _persist_scheduler_signal_run(
    *,
    scan_label: str,
    is_intraday: bool,
    signals_list,
    monitored,
    breadth,
    regime,
    market_date: datetime.date | None = None,
    preview_only: bool = False,
):
    m_date = market_date or TimeUtils.today()
    scan_type = _scheduler_scan_type(scan_label, is_intraday)
    force_refresh = scan_type == "DAILY" and (scan_label or "").strip().upper() == "DAILY SIGNAL"
    run_key = _scheduler_run_key(scan_label, is_intraday, market_date=m_date, preview_only=preview_only)
    if force_refresh and _completed_daily_signal_run_has_results(run_key):
        force_refresh = False
    req = signals.DailyRunRequest(
        run_date=m_date.strftime("%Y-%m-%d"),
        scan_type=scan_type,
        run_key=run_key,
        force=force_refresh,
        notify=False,
        index="EGX30",
        model_version=os.getenv("SIGNAL_MODEL_VERSION", "v1"),
    )
    signals_mod = _resolve_scheduling_dispatch("signals", signals)
    return signals_mod.run_daily_signals_logic(
        req,
        get_market_signals_fn=lambda **kwargs: (list(signals_list or []), list(monitored or []), breadth, regime),
    )


def _scan_display_label(scan_label: str | None, is_intraday: bool) -> str:
    normalized = (scan_label or "").strip().upper()
    if normalized:
        return normalized
    return "INTRADAY" if is_intraday else "DAILY"


def _should_send_no_signal_notice(scan_label: str | None, is_intraday: bool) -> bool:
    if is_intraday:
        return bool(getattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False))
    notice_key = _scheduler_run_key(scan_label or "DAILY", is_intraday)
    with _NO_SIGNAL_NOTICE_LOCK:
        if notice_key in _NO_SIGNAL_NOTICE_KEYS:
            return False
        _NO_SIGNAL_NOTICE_KEYS.add(notice_key)
        return True


def _broadcast_no_signal_notice(
    *,
    scan_label: str | None,
    is_intraday: bool,
    regime,
    reason: str = "none_found",
) -> bool:
    if not _should_send_no_signal_notice(scan_label, is_intraday):
        logger.info(f"[Scheduler] {_scan_display_label(scan_label, is_intraday)}: no-signal notice suppressed.")
        return False

    display_label = _scan_display_label(scan_label, is_intraday)
    if reason == "dedup":
        detail = "All eligible signals were already sent earlier today."
    else:
        detail = "Scanner found no eligible setups."
    message = (
        f"[{display_label} NO ELIGIBLE SIGNALS]\n"
        f"Date: {TimeUtils.today().strftime('%Y-%m-%d')}\n"
        f"Regime: {regime or 'UNKNOWN'}\n"
        f"{detail}"
    )
    alert_mgr = _resolve_scheduling_dispatch("AlertManager", AlertManager)
    alert_mgr.broadcast_alert(message)
    logger.info(f"[Scheduler] {display_label}: no-signal notice broadcast.")
    return True
