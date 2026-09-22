"""
DRY RUN ENGINE — End-to-End Pipeline Fire Drill
=================================================
Fires the entire Horus pipeline synchronously for a specific date:
  scan → generate signals → send Telegram cards → generate report → monitor

Usage via API:
    POST /api/v1/dryrun/start  { date, notify, report, ai_report }
    GET  /api/v1/dryrun/status
"""

from core.settings import settings
import datetime
import threading
import time
import traceback

from core import DailyScanner
from core.simulation_profiles import resolve_simulation_scanner_profile, run_selected_simulation_profile_scan
from utils.logger import setup_logger

logger = setup_logger("horus.dryrun_engine")

# ── Module-level state ──────────────────────────────────────────────────────
_DRYRUN_STATE = {
    "status": "IDLE",       # IDLE | RUNNING | COMPLETED | ERROR
    "date": None,
    "notify": False,
    "report": False,
    "ai_report": False,
    "started_at": None,
    "completed_at": None,
    "duration_sec": 0,
    "steps": [],            # Ordered list of step results
    "signals_found": 0,
    "signals": [],
    "regime": None,
    "breadth": 0,
    "report_generated": False,
    "ai_report_generated": False,
    "telegram_messages_sent": 0,
    "profile_id": None,
    "profile_name": None,
    "profile_source_type": None,
    "profile_scope": "HORUS_CORE",
    "market": "EGX30",
    "error": None,
}
_DRYRUN_LOCK = threading.Lock()

# ── Telegram prefix for dry run messages ─────────────────────────────────────
DRYRUN_PREFIX = "[🧪 DRY RUN]"


def _reset_state():
    """Reset dry run state to defaults."""
    _DRYRUN_STATE.update({
        "status": "IDLE",
        "date": None,
        "notify": False,
        "report": False,
        "ai_report": False,
        "started_at": None,
        "completed_at": None,
        "duration_sec": 0,
        "steps": [],
        "signals_found": 0,
        "signals": [],
        "regime": None,
        "breadth": 0,
        "report_generated": False,
        "ai_report_generated": False,
        "telegram_messages_sent": 0,
        "profile_id": None,
        "profile_name": None,
        "profile_source_type": None,
        "profile_scope": "HORUS_CORE",
        "market": "EGX30",
        "error": None,
    })


def _resolve_dryrun_scanner_profile(profile_id: int | None = None, use_active_profile: bool = False):
    return resolve_simulation_scanner_profile(profile_id=profile_id, use_active_profile=use_active_profile)


def _run_selected_dryrun_profile_scan(profile):
    return run_selected_simulation_profile_scan(profile)


def _run_dryrun_scan(replay_profile=None, replay_market: str = "EGX30") -> dict:
    if replay_profile is not None:
        signals, monitored, breadth, regime, strategy_profile = _run_selected_dryrun_profile_scan(replay_profile)
    else:
        signals, monitored, breadth, regime = DailyScanner.get_market_signals(
            index_choice=replay_market,
            is_intraday=False,
        )
        strategy_profile = {
            "source_type": "HORUS",
            "profile_name": "Horus Core",
            "market": replay_market,
            "timeframe": "1D",
        }

    signals = list(signals or [])
    for signal in signals:
        signal["source"] = "DRYRUN"

    return {
        "signals_count": len(signals),
        "monitored_count": len(monitored or []),
        "breadth": breadth,
        "regime": regime,
        "signals": signals,
        "strategy_profile": strategy_profile,
    }


def _step(name: str, fn, *args, **kwargs) -> dict:
    """Execute a step, time it, and return results."""
    step_result = {
        "step": name,
        "status": "running",
        "started_at": datetime.datetime.now().isoformat(),
        "duration_sec": 0,
        "result": None,
        "error": None,
    }
    _DRYRUN_STATE["steps"].append(step_result)

    start = time.time()
    try:
        result = fn(*args, **kwargs)
        step_result["status"] = "completed"
        step_result["result"] = result
    except Exception as e:
        step_result["status"] = "error"
        step_result["error"] = str(e)
        logger.error(f"[DryRun] Step '{name}' failed: {e}")
    finally:
        step_result["duration_sec"] = round(time.time() - start, 2)

    return step_result


def _dryrun_worker(
    target_date: datetime.date,
    notify: bool,
    report: bool,
    ai_report: bool,
    replay_profile=None,
    replay_market: str = "EGX30",
):
    """Execute the full pipeline synchronously for the target date."""
    from core import TimeUtils

    wall_start = time.time()

    try:
        _DRYRUN_STATE["status"] = "RUNNING"

        # ── Step 1: Enter simulation mode ────────────────────────────────
        # Set simulated time to market close for that day (signals are EOD)
        s = settings
        end_hhmm = s._active_market_end().zfill(4)
        close_time = datetime.datetime.combine(
            target_date,
            datetime.time(int(end_hhmm[:2]), int(end_hhmm[2:])),
        )
        TimeUtils.set_simulation(close_time)
        TimeUtils.set_market_override(True)

        logger.info(f"[DryRun] Simulating {target_date} @ {close_time.strftime('%H:%M')}")

        if notify:
            from core import AlertManager, TelegramBot_Alerts
            token, chat_id = TelegramBot_Alerts._test_telegram_config()
            AlertManager.broadcast_alert(
                f"{DRYRUN_PREFIX} 🧪 DRY RUN STARTED\n"
                f"Date: {target_date}\n"
                f"Notify: {notify} | Report: {report} | AI: {ai_report}",
                token=token,
                chat_id=chat_id
            )
            _DRYRUN_STATE["telegram_messages_sent"] += 1

        # ── Step 2: Run market scan ──────────────────────────────────────
        def _scan():
            return _run_dryrun_scan(replay_profile=replay_profile, replay_market=replay_market)

        scan_step = _step("Market Scan", _scan)
        scan_result = scan_step.get("result") or {}
        signals = scan_result.get("signals", [])
        regime = scan_result.get("regime", "UNKNOWN")
        breadth = scan_result.get("breadth", 0)
        strategy_profile = scan_result.get("strategy_profile") or {}

        _DRYRUN_STATE["signals_found"] = len(signals)
        _DRYRUN_STATE["regime"] = regime
        _DRYRUN_STATE["breadth"] = breadth
        if strategy_profile:
            _DRYRUN_STATE["profile_name"] = strategy_profile.get("profile_name")
            _DRYRUN_STATE["profile_source_type"] = strategy_profile.get("source_type")
        _DRYRUN_STATE["signals"] = [
            {
                "ticker": s.get("Ticker"),
                "score": s.get("Score"),
                "type": s.get("Signal_Type"),
                "entry": s.get("Entry_Price"),
                "stop_loss": s.get("Stop_Loss"),
                "target": s.get("Target_Price"),
            }
            for s in signals
        ]

        logger.info(f"[DryRun] Scan complete: {len(signals)} signals, regime={regime}")

        # ── Step 3: Persist signals to DB ────────────────────────────────
        def _persist():
            from database import Signal
            from peewee import fn
            from core.exclusions import normalize_ticker

            saved = 0
            for s in signals:
                ticker_clean = normalize_ticker(s.get("Ticker"))
                if not ticker_clean:
                    continue
                try:
                    exists = Signal.select().where(
                        (fn.Upper(Signal.ticker) == ticker_clean)
                        & (Signal.signal_type == s["Signal_Type"])
                        & (Signal.date == TimeUtils.today())
                        & (Signal.source == "DRYRUN")
                    ).exists()
                    if not exists:
                        Signal.create(
                            ticker=s["Ticker"],
                            signal_type=s["Signal_Type"],
                            price=float(s.get("Entry_Price", 0)),
                            score=float(s.get("Score", 0)),
                            source="DRYRUN",
                            rationale=" | ".join(s.get("Alpha_Rationale", [])),
                        )
                        saved += 1
                except Exception as e:
                    logger.error(f"[DryRun] DB save error for {ticker_clean}: {e}")
            return {"saved": saved}

        _step("Persist Signals", _persist)

        # ── Step 4: Generate signal cards ────────────────────────────────
        def _generate_cards():
            if not signals:
                return {"cards_generated": 0}
            from core import ReportGenerator

            cards = 0
            for i, s in enumerate(signals[:3]):
                try:
                    ReportGenerator.create_horus_signal_card(
                        ticker=s.get("Ticker"),
                        entry=float(s.get("Entry_Price", 0)),
                        stop_loss=float(s.get("Stop_Loss", 0)),
                        tp1=float(s.get("Target_Price", 0)),
                        tp2=float(s.get("Target_Price_2", 0)) if s.get("Target_Price_2") is not None else None,
                        score=s.get("Score", 0),
                        rsi=s.get("RSI"),
                        volume_x=s.get("Volume_x"),
                        signal_label=f"{DRYRUN_PREFIX} DAILY",
                    )
                    cards += 1
                except Exception as e:
                    logger.error(f"[DryRun] Card error for {s.get('Ticker')}: {e}")
            return {"cards_generated": cards}

        _step("Generate Signal Cards", _generate_cards)

        # ── Step 5: Send Telegram alerts ─────────────────────────────────
        def _broadcast():
            if not notify or not signals:
                return {"messages_sent": 0, "skipped": True}

            from core import AlertManager, ReportGenerator, TelegramBot_Alerts

            filtered_signals = AlertManager.filter_new_signals(signals, "DAILY SIGNAL")
            if not filtered_signals:
                return {"messages_sent": 0, "skipped": True}

            msgs = 0

            # Header
            token, chat_id = TelegramBot_Alerts._test_telegram_config()
            AlertManager.broadcast_alert(
                f"{DRYRUN_PREFIX} [DAILY SCAN COMPLETE]\n"
                f"[MARKET REGIME: {regime}]\n"
                f"Signals Found: {len(filtered_signals)}",
                token=token,
                chat_id=chat_id
            )
            msgs += 1

            # Signal cards
            for i, s in enumerate(filtered_signals[:3]):
                try:
                    img_buf = ReportGenerator.create_horus_signal_card(
                        ticker=s.get("Ticker"),
                        entry=float(s.get("Entry_Price", 0)),
                        stop_loss=float(s.get("Stop_Loss", 0)),
                        tp1=float(s.get("Target_Price", 0)),
                        tp2=float(s.get("Target_Price_2", 0)) if s.get("Target_Price_2") is not None else None,
                        score=s.get("Score", 0),
                        rsi=s.get("RSI"),
                        volume_x=s.get("Volume_x"),
                        signal_label=f"{DRYRUN_PREFIX} DAILY",
                    )
                    rsi_text = f"{float(s.get('RSI')):.1f}" if s.get("RSI") is not None else "N/A"
                    vol_text = f"{float(s.get('Volume_x')):.1f}x" if s.get("Volume_x") is not None else "N/A"
                    caption = (
                        f"{DRYRUN_PREFIX} [TOP {i+1}] {s.get('Ticker')} | Score: {s.get('Score', 0)}/10\n"
                        f"RSI: {rsi_text} | Vol Spike: {vol_text}"
                    )
                    AlertManager.broadcast_image(img_buf, caption, token=token, chat_id=chat_id)
                    msgs += 1
                except Exception as e:
                    logger.error(f"[DryRun] Card broadcast error for {s.get('Ticker')}: {e}")

            # Full summary
            full_msg = TelegramBot_Alerts.format_signal_alert(filtered_signals)
            if full_msg:
                AlertManager.broadcast_alert(f"{DRYRUN_PREFIX} [FULL SUMMARY]\n{full_msg}", token=token, chat_id=chat_id)
                msgs += 1

            return {"messages_sent": msgs}

        broadcast_step = _step("Telegram Broadcast", _broadcast)
        _DRYRUN_STATE["telegram_messages_sent"] += (broadcast_step.get("result") or {}).get("messages_sent", 0)

        # ── Step 6: Run signal pipeline (persist run) ────────────────────
        def _signal_pipeline():
            from core.scheduling import _persist_scheduler_signal_run
            try:
                run_result = _persist_scheduler_signal_run(
                    scan_label="DAILY SIGNAL",
                    is_intraday=False,
                    signals_list=signals,
                    monitored=[],
                    breadth=breadth,
                    regime=regime,
                )
                return {
                    "status": run_result.get("status"),
                    "run_id": (run_result.get("run") or {}).get("id"),
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        _step("Signal Pipeline", _signal_pipeline)

        # ── Step 7: Generate AI Report ───────────────────────────────────
        if ai_report:
            def _ai_report():
                from routes import ai_report as ai_report_route
                payload = ai_report_route.get_ai_daily_report(force_refresh=True, use_llm=True)
                success = isinstance(payload, dict) and payload.get("status") == "success"

                if success and notify:
                    from core import AlertManager, TelegramBot_Alerts
                    from core.scheduling import _build_ai_report_telegram_message
                    token, chat_id = TelegramBot_Alerts._test_telegram_config()
                    message = _build_ai_report_telegram_message(payload)
                    AlertManager.broadcast_alert(f"{DRYRUN_PREFIX} [AI DAILY REPORT]\n{message}", token=token, chat_id=chat_id)
                    _DRYRUN_STATE["telegram_messages_sent"] += 1

                return {"generated": success}

            ai_step = _step("AI Report", _ai_report)
            _DRYRUN_STATE["ai_report_generated"] = (ai_step.get("result") or {}).get("generated", False)

        # ── Step 8: Monitor signals (one tick) ───────────────────────────
        def _monitor():
            from core.signals.lifecycle import monitor_published_signal_lifecycles
            try:
                monitor_published_signal_lifecycles()
                return {"status": "completed"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        _step("Signal Monitor", _monitor)

        # ── Finalize ─────────────────────────────────────────────────────
        _DRYRUN_STATE["status"] = "COMPLETED"
        _DRYRUN_STATE["completed_at"] = datetime.datetime.now().isoformat()
        _DRYRUN_STATE["duration_sec"] = round(time.time() - wall_start, 2)

        if notify:
            from core import AlertManager, TelegramBot_Alerts
            token, chat_id = TelegramBot_Alerts._test_telegram_config()
            step_summary = " → ".join(
                f"{'✅' if s['status'] == 'completed' else '❌'} {s['step']}"
                for s in _DRYRUN_STATE["steps"]
            )
            AlertManager.broadcast_alert(
                f"{DRYRUN_PREFIX} ✅ DRY RUN COMPLETE\n"
                f"Date: {target_date}\n"
                f"Signals: {_DRYRUN_STATE['signals_found']} | Regime: {regime}\n"
                f"Duration: {_DRYRUN_STATE['duration_sec']}s\n"
                f"Pipeline: {step_summary}",
                token=token,
                chat_id=chat_id
            )
            _DRYRUN_STATE["telegram_messages_sent"] += 1

        logger.info(
            f"[DryRun] Completed in {_DRYRUN_STATE['duration_sec']}s: "
            f"{_DRYRUN_STATE['signals_found']} signals, "
            f"{_DRYRUN_STATE['telegram_messages_sent']} messages sent"
        )

    except Exception as e:
        _DRYRUN_STATE["status"] = "ERROR"
        _DRYRUN_STATE["error"] = str(e)
        _DRYRUN_STATE["duration_sec"] = round(time.time() - wall_start, 2)
        logger.error(f"[DryRun] Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        # ALWAYS clean up simulation state
        TimeUtils.clear_simulation()
        TimeUtils.clear_market_override()


# ── Public API ───────────────────────────────────────────────────────────────

def start_dryrun(
    target_date: str | None = None,
    notify: bool = False,
    report: bool = True,
    ai_report: bool = False,
    profile_id: int | None = None,
    use_active_profile: bool = False,
) -> dict:
    """Start an end-to-end dry run.

    Args:
        target_date: Date in YYYY-MM-DD format (defaults to last trading day).
        notify: Send Telegram alerts.
        report: Generate signal reports.
        ai_report: Generate AI daily report.

    Returns:
        Status dict.
    """
    if not _DRYRUN_LOCK.acquire(blocking=False):
        return {"status": "error", "message": "A dry run is already in progress."}

    try:
        if _DRYRUN_STATE["status"] == "RUNNING":
            return {"status": "error", "message": "Dry run already in progress."}

        # Resolve target date
        if target_date:
            try:
                parsed_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                return {"status": "error", "message": f"Invalid date format: {target_date}. Use YYYY-MM-DD."}
        else:
            parsed_date = settings.get_last_completed_market_day()
        resolved_profile = _resolve_dryrun_scanner_profile(profile_id=profile_id, use_active_profile=use_active_profile)

        _reset_state()
        _DRYRUN_STATE.update({
            "status": "RUNNING",
            "date": str(parsed_date),
            "notify": notify,
            "report": report,
            "ai_report": ai_report,
            "started_at": datetime.datetime.now().isoformat(),
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
            "profile_source_type": getattr(resolved_profile, "source_type", None),
            "profile_scope": "DAILY_PHASES_ONLY" if resolved_profile is not None else "HORUS_CORE",
            "market": getattr(resolved_profile, "market", "EGX30") or "EGX30",
        })

        # Run in a background thread (same pattern as scanner)
        thread = threading.Thread(
            target=_dryrun_worker,
            args=(parsed_date, notify, report, ai_report, resolved_profile, _DRYRUN_STATE["market"]),
            daemon=True,
            name="DryRunEngine",
        )
        thread.start()

        return {
            "status": "started",
            "date": str(parsed_date),
            "notify": notify,
            "report": report,
            "ai_report": ai_report,
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
        }
    finally:
        _DRYRUN_LOCK.release()


def get_dryrun_status() -> dict:
    """Get the current dry run status."""
    return dict(_DRYRUN_STATE)
