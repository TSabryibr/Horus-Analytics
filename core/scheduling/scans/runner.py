"""
SCHEDULING SCANS RUNNER
=======================
Core scheduled scan orchestration logic.
"""

from __future__ import annotations

import datetime
from peewee import fn
from fastapi import HTTPException

from core import (
    AlertManager,
    DailyScanner,
    ReportGenerator,
    TelegramBot_Alerts,
    TimeUtils,
    subscriptions,
)
from core.settings import settings
from core.signals.executor import SignalExecutor
from core.signals.routing import resolve_target_portfolio_name
from database import Signal
from utils.currency_fetcher import get_historical_usd_egp_rate, get_parallel_usd_egp_rate
from utils.logger import setup_logger

from ..state import (
    _USE_LEGACY_EXECUTOR,
    _resolve_scheduling_dispatch,
)
from .deliveries import (
    _background_ops_paused_for_time_travel,
    _broadcast_no_signal_notice,
    _persist_scheduler_signal_run,
    _publish_scheduler_signal_deliveries,
    _reconcile_scheduler_pre_close_previews,
    _scheduler_scan_type,
    _scheduler_signal_tickers,
)
from .execution import _signal_auto_execution_enabled, execute_run_for_horus

logger = setup_logger("horus.scheduling.scans.runner")


def _get_logger():
    return _resolve_scheduling_dispatch("logger", logger)


def scheduled_scan_logic(
    is_intraday: bool = True,
    scan_label: str | None = None,
    *,
    market_date: datetime.date | None = None,
    _late_data: bool = False,
    preview_only: bool = False,
    scan_type: str | None = None,
    is_pre_close: bool = False,
    is_retry: bool = False,
    run_key: str | None = None,
):
    target_m_date = market_date or TimeUtils.today()
    mode_name = "Intraday" if is_intraday else ("Daily Preview" if preview_only else "Pre-Close/Daily")
    effective_scan_label = scan_label or ("INTRADAY" if is_intraday else "PRE-CLOSE")
    resolved_scan_type = scan_type or _scheduler_scan_type(effective_scan_label, is_intraday)

    if _background_ops_paused_for_time_travel():
        logger.info(f"[Scheduler] {mode_name} scan skipped: time travel/backfill is active.")
        return False

    try:
        try:
            from utils.audit_logger import log_audit_event
            log_audit_event(
                category="scheduler",
                action="scan_start",
                details={
                    "is_intraday": is_intraday,
                    "scan_label": effective_scan_label,
                    "scan_type": resolved_scan_type,
                },
            )
        except Exception:
            pass

        rate = get_parallel_usd_egp_rate()
        logger.info(f"[Scheduler] Active parallel EGP/USD rate: {rate:.4f}")

        currency_warning = None
        try:
            prev_rate = get_historical_usd_egp_rate(datetime.date.today() - datetime.timedelta(days=1))
            rate_change = abs(rate - prev_rate) / prev_rate * 100
            if rate_change > 2.0:
                currency_warning = f"⚠️ [CURRENCY_VOLATILITY] Parallel FX shifted {rate_change:.2f}% in 24h ({prev_rate:.2f} -> {rate:.2f})"
                logger.warning(f"[Scheduler] {currency_warning}")
        except Exception as exc:
            logger.warning(f"[Scheduler] Failed to check currency volatility: {exc}")

        scan_kwargs = {
            "index_choice": "EGX30",
            "is_intraday": is_intraday,
        }
        if not is_intraday:
            scan_kwargs["is_pre_close"] = resolved_scan_type == "PRE_CLOSE" or is_pre_close

        scanner_obj = _resolve_scheduling_dispatch("DailyScanner", DailyScanner)
        signals_list, monitored, breadth, regime = scanner_obj.get_market_signals(**scan_kwargs)
        signals_list = list(signals_list or [])

        if currency_warning:
            regime = f"{regime} - {currency_warning}"
            for s in signals_list:
                s['Confirmation'] = f"{s.get('Confirmation', 'CONFIRMED')} [CURRENCY_VOLATILITY]"

        logger.info(f"[Scheduler] {mode_name}: scanner returned {len(signals_list)} signals (regime={regime}).")

        if _late_data:
            regime = f"{regime} [LATE DATA]" if regime else "[LATE DATA]"
            for s in signals_list:
                conf = str(s.get("Confirmation", "PRE-CLOSE")).upper()
                if "[LATE DATA]" not in conf:
                    s["Confirmation"] = f"{conf} [LATE DATA]"
        final_daily_tickers_for_reconciliation: set[str] = set()

        if (not is_intraday) and signals_list and effective_scan_label == "DAILY SIGNAL":
            today = target_m_date
            fresh_signals = []
            stale_meta = []
            for s in signals_list:
                sig_dt = s.get("Date")
                sig_day = sig_dt.date() if hasattr(sig_dt, "date") else None
                if sig_day is None and sig_dt:
                    try:
                        sig_str = str(sig_dt)
                        sig_day = datetime.date.fromisoformat(sig_str[0:10])
                    except Exception:
                        sig_day = None
                if sig_day == today:
                    fresh_signals.append(s)
                else:
                    stale_meta.append((s.get("Ticker"), sig_day))

            if stale_meta:
                logger.info(f"[Scheduler] Dropping stale daily signals (expected {today}): {stale_meta}")
            signals_list = fresh_signals
            logger.info(f"[Scheduler] {mode_name}: stale filter dropped {len(stale_meta)} signals; remaining={len(signals_list)}.")

            if preview_only:
                for s in signals_list:
                    s["Confirmation"] = "PREVIEW"
            elif TimeUtils.now().strftime("%H:%M") >= settings.MARKET_END_TIME:
                for s in signals_list:
                    if str(s.get("Confirmation", "")).upper() == "PRE-CLOSE":
                        s["Confirmation"] = "CONFIRMED"
        if (not is_intraday) and effective_scan_label == "DAILY SIGNAL":
            final_daily_tickers_for_reconciliation = _scheduler_signal_tickers(signals_list)

        execution_watchlist_only = False
        execution_block_reason = None
        persisted_run_id = None
        try:
            persist_run_fn = _resolve_scheduling_dispatch("_persist_scheduler_signal_run", _persist_scheduler_signal_run)
            run_result = persist_run_fn(
                scan_label=effective_scan_label,
                is_intraday=is_intraday,
                signals_list=signals_list,
                monitored=monitored,
                breadth=breadth,
                regime=regime,
                market_date=target_m_date,
                preview_only=preview_only,
            )
            persisted_run = (run_result.get("run") if isinstance(run_result, dict) else None) or {}
            if isinstance(persisted_run, dict):
                persisted_run_id = persisted_run.get("id")
            elif isinstance(persisted_run, int):
                persisted_run_id = persisted_run
            else:
                persisted_run_id = None

            logger.info(
                f"[Scheduler] {mode_name}: persisted signal run "
                f"status={run_result.get('status') if isinstance(run_result, dict) else run_result} scan_type={_scheduler_scan_type(effective_scan_label, is_intraday)} "
                f"run_id={persisted_run_id}"
            )
            if isinstance(run_result, dict) and run_result.get("status") == "blocked":
                logger.warning(
                    f"[Scheduler] {mode_name}: run blocked "
                    f"block_type={run_result.get('block_type')} "
                    f"block_reason={run_result.get('block_reason')} "
                    f"message={run_result.get('message')}"
                )
                return False
            persisted_scan_type = _scheduler_scan_type(effective_scan_label, is_intraday)
            if (
                isinstance(run_result, dict)
                and run_result.get("status") == "completed"
                and persisted_scan_type == "DAILY"
                and (effective_scan_label or "").strip().upper() == "DAILY SIGNAL"
            ):
                reconcile_fn = _resolve_scheduling_dispatch("_reconcile_scheduler_pre_close_previews", _reconcile_scheduler_pre_close_previews)
                reconcile_fn(
                    final_daily_tickers=final_daily_tickers_for_reconciliation,
                    run_date=target_m_date,
                )
            auto_exec_fn = _resolve_scheduling_dispatch("_signal_auto_execution_enabled", _signal_auto_execution_enabled)
            if (
                not preview_only
                and auto_exec_fn()
                and (isinstance(run_result, dict) and run_result.get("status") == "completed")
                and persisted_run_id
            ):
                exec_run_fn = _resolve_scheduling_dispatch("execute_run", None)
                if exec_run_fn is None or exec_run_fn is execute_run_for_horus or exec_run_fn is SignalExecutor.execute_run:
                    exec_run_fn = _resolve_scheduling_dispatch("execute_run_for_horus", SignalExecutor.execute_run)
                execution_result = exec_run_fn(int(persisted_run_id))
                if str((execution_result or {}).get("status", "")).lower() == "blocked":
                    execution_block_reason = (
                        (execution_result or {}).get("blocked_reason")
                        or (execution_result or {}).get("message")
                        or "execution_blocked"
                    )
                    execution_watchlist_only = True

        except HTTPException as he:
            logger.warning(f"[Scheduler] {mode_name}: signal-run persistence blocked/failed: {he.detail}")
        except Exception as run_exc:
            logger.error(f"[Scheduler] {mode_name}: signal-run persistence error: {run_exc}")

        card_alerts = []
        should_broadcast_toggle = settings.TELEGRAM_AUTO_BROADCAST_INTRADAY if is_intraday else settings.TELEGRAM_AUTO_BROADCAST_DAILY
        should_main_channel_broadcast = should_broadcast_toggle and subscriptions.automated_main_channel_signal_allowed()
        if not should_broadcast_toggle:
            logger.info(f"[Scheduler] {mode_name}: automated signal dispatch disabled by settings toggle.")
        elif not should_main_channel_broadcast:
            logger.info(f"[Scheduler] {mode_name}: main-channel signal broadcast disabled by channel level policy.")

        if should_main_channel_broadcast and not signals_list:
            if not is_intraday or getattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False):
                logger.info(f"[Scheduler] {mode_name}: no eligible signals after scheduler filters. Broadcasting status notice.")
                broadcast_no_sig_fn = _resolve_scheduling_dispatch("_broadcast_no_signal_notice", _broadcast_no_signal_notice)
                broadcast_no_sig_fn(
                    scan_label=effective_scan_label,
                    is_intraday=is_intraday,
                    regime=regime,
                    reason="none_found",
                )
            else:
                logger.info(f"[Scheduler] {mode_name}: no eligible signals found. Intraday no-signal notice suppressed.")

        if signals_list and should_broadcast_toggle:
            alert_mgr = _resolve_scheduling_dispatch("AlertManager", AlertManager)
            pre_dedup_count = len(signals_list)
            signals_list = alert_mgr.filter_new_signals(signals_list, effective_scan_label)
            dedup_dropped = pre_dedup_count - len(signals_list)
            if dedup_dropped > 0:
                _get_logger().info(f"[Scheduler] {mode_name}: dedup dropped {dedup_dropped}/{pre_dedup_count} signals.")
            if pre_dedup_count > 0 and not signals_list:
                _get_logger().info(f"[Scheduler] {mode_name}: dedup filtered all {pre_dedup_count} signals; nothing to broadcast.")
                if not is_intraday or getattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False):
                    broadcast_no_sig_fn = _resolve_scheduling_dispatch("_broadcast_no_signal_notice", _broadcast_no_signal_notice)
                    broadcast_no_sig_fn(
                        scan_label=effective_scan_label,
                        is_intraday=is_intraday,
                        regime=regime,
                        reason="dedup",
                    )
                else:
                    _get_logger().info(f"[Scheduler] {mode_name}: dedup filtered all signals. Intraday no-signal notice suppressed.")

            if signals_list:
                alert_mgr = _resolve_scheduling_dispatch("AlertManager", AlertManager)
                broadcast_mode_note = ""
                execution_block_display = None
                if should_main_channel_broadcast:
                    if execution_watchlist_only:
                        execution_block_display = str(execution_block_reason).replace("_", " ")
                        broadcast_mode_note = " WATCHLIST ONLY"
                        logger.info(
                            f"[Scheduler] {mode_name}: execution blocked ({execution_block_reason}); "
                            "broadcasting signals as watchlist-only."
                        )
                    logger.info(f"[Scheduler] {mode_name}: broadcasting {len(signals_list)} signals after dedup{broadcast_mode_note}.")
                    from core import ReportGenerator
                    if is_pre_close:
                        header = "[DAILY PREVIEW REPORT]"
                    else:
                        header = "[INTRADAY ALERT]" if is_intraday else "[DAILY CLOSE REPORT]"
                    if execution_watchlist_only:
                        header = header[:-1] + " - WATCHLIST ONLY]"

                    def _safe_num(val, default=0.0):
                        try:
                            return float(val) if val is not None else default
                        except (TypeError, ValueError):
                            return default

                    card_alerts = list(signals_list)
                    for i, s in enumerate(card_alerts):
                        try:
                            ticker = s.get('Ticker')
                            entry = _safe_num(s.get('Entry_Price', 0))
                            sl = _safe_num(s.get('Stop_Loss', 0))
                            tp1 = _safe_num(s.get('Target_Price', 0))
                            raw_tp2 = s.get('Target_Price_2')
                            tp2_val = _safe_num(raw_tp2, tp1 * 1.04 if tp1 else 0.0) if raw_tp2 is not None else (tp1 * 1.04 if tp1 else 0.0)

                            tp1_pct = ((tp1 - entry) / entry * 100) if entry > 0 and tp1 > 0 else 0.0
                            sl_pct = ((entry - sl) / entry * 100) if entry > 0 and sl > 0 else 0.0
                            risk = entry - sl
                            reward = tp1 - entry
                            rr_ratio = (reward / risk) if risk > 0 and reward > 0 else 0.0
                            rr_text = f"1:{rr_ratio:.1f}" if rr_ratio > 0 else "N/A"

                            img_buf = ReportGenerator.create_horus_signal_card(
                                ticker=ticker,
                                entry=entry,
                                stop_loss=sl,
                                tp1=tp1,
                                tp2=tp2_val if tp2_val > 0 else None,
                                score=s.get('Score', 0),
                                rsi=s.get('RSI'),
                                volume_x=s.get('Volume_x'),
                                confirmation=s.get('Confirmation'),
                                regime=regime,
                                signal_data_date=s.get('Date'),
                                signal_label=(
                                    f"{effective_scan_label} WATCHLIST ONLY"
                                    if execution_watchlist_only
                                    else effective_scan_label
                                ),
                            )
                            rsi_text = f"{_safe_num(s.get('RSI')):.1f}" if s.get('RSI') is not None else "N/A"
                            vol_text = f"{_safe_num(s.get('Volume_x')):.1f}x" if s.get('Volume_x') is not None else "N/A"
                            caption = (
                                f"[SIGNAL {i+1}] {ticker} | Score: {s.get('Score', 0)}/10\n"
                                f"Entry: {entry:.2f} LE | TP1: {tp1:.2f} LE (+{tp1_pct:.1f}%) | SL: {sl:.2f} LE (-{sl_pct:.1f}%)\n"
                                f"R:R: {rr_text} | RSI: {rsi_text} | Vol Spike: {vol_text} | Regime: {regime}"
                            )
                            if execution_watchlist_only:
                                caption = f"{caption}\nWATCHLIST ONLY - execution blocked by {execution_block_display}"
                            alert_mgr.broadcast_image(img_buf, caption)
                        except Exception as img_e:
                            logger.error(f"[Scheduler] Could not generate card for {s.get('Ticker')}: {img_e}")

                    msg = TelegramBot_Alerts.format_signal_alert(
                        signals_list,
                        regime=regime,
                        scan_label=effective_scan_label,
                    )
                    summary_header = f"{header} [FULL SUMMARY]"
                    if execution_watchlist_only:
                        summary_header = f"{header} [FULL SUMMARY - WATCHLIST ONLY]"
                        msg = f"Execution blocked by {execution_block_display}. Signals are informational only.\n\n{msg}"
                    alert_mgr.broadcast_alert(f"{summary_header}\n{msg}")
                else:
                    logger.info(f"[Scheduler] {mode_name}: main-channel cards suppressed by policy; publishing subscriber deliveries only.")

                _publish_scheduler_signal_deliveries(
                    run_id=persisted_run_id,
                    signals_list=signals_list,
                    include_main_channel_record=should_main_channel_broadcast,
                )

                for s in signals_list:
                    ticker_clean = str((s or {}).get('Ticker', '')).strip().upper()
                    if not ticker_clean:
                        continue
                    try:
                        exists = Signal.select().where(
                            (fn.Upper(Signal.ticker) == ticker_clean) & 
                            (Signal.signal_type == s['Signal_Type']) & 
                            (Signal.date == TimeUtils.today())
                        ).exists()
                        if not exists:
                            Signal.create(
                                ticker=s['Ticker'],
                                signal_type=s['Signal_Type'],
                                price=float(s['Entry_Price']),
                                score=float(s['Score']),
                                source=effective_scan_label,
                                rationale=" | ".join(s.get('Alpha_Rationale', []))
                            )
                    except Exception as e:
                        logger.error(f"Error saving scheduled signal {s.get('Ticker')}: {e}")

                target_port = resolve_target_portfolio_name("INTRADAY" if is_intraday else "DAILY")
                if _signal_auto_execution_enabled():
                    if _USE_LEGACY_EXECUTOR:
                        SignalExecutor.process_scanner_signals(signals_list, target_portfolio_name=target_port)
                else:
                    logger.info("[Scheduler] Signal auto-execution disabled; skipping auto-entry.")

                logger.info(f"[Scheduler] {mode_name}: broadcast completed (cards={len(card_alerts)}, summary_signals={len(signals_list)}).")
        try:
            from utils.audit_logger import log_audit_event
            log_audit_event(
                category="scheduler",
                action="scan_complete",
                details={
                    "is_intraday": is_intraday,
                    "scan_label": effective_scan_label,
                    "scan_type": resolved_scan_type,
                    "signals_count": len(signals_list) if 'signals_list' in locals() else 0,
                    "regime": regime if 'regime' in locals() else "UNKNOWN"
                }
            )
        except Exception:
            pass
        return True
    except Exception as e:
        logger.exception(f"[Scheduler] Error in {mode_name} Scan: {e}")
        try:
            from utils.audit_logger import log_audit_event
            log_audit_event(
                category="scheduler",
                action="scan_failed",
                status="failed",
                details={
                    "is_intraday": is_intraday,
                    "scan_label": effective_scan_label,
                    "scan_type": resolved_scan_type,
                    "error": str(e)
                }
            )
        except Exception:
            pass
        return False
