from core.settings import settings
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import threading
import multiprocessing
import numpy as np
import datetime
from peewee import fn

from core import DailyScanner
from core import TelegramBot_Alerts
from core import subscriptions
from database import Signal, Trade, db
from routes.shared import SCAN_STATE, OPTIMIZATION_STATE, SignalCardRequest
from core import TimeUtils
from core.exclusions import filter_excluded_from_payload, get_excluded_tickers_upper, is_excluded_ticker, normalize_ticker
from core.whale_flow import summarize_whale_trap_diagnostics
from core.enforcement_gates import summarize_enforcement_diagnostics
from core.enforcement_calibration import summarize_calibration_diagnostics
from core.pine_lab import get_active_pine_scanner_profile, get_pine_scanner_profile, run_pine_scanner_profile_scan
from core.price_action.scanner import run_price_action_scanner_profile_scan
from core.signals.routing import resolve_target_portfolio_name
from core.signals.executor import SignalExecutor

import logging
from core import AlertManager
logger = logging.getLogger("horus.scanner")

router = APIRouter(tags=["scanner"])


def _run_selected_scanner_profile(profile, *, intraday: bool):
    source_type = str(getattr(profile, "source_type", "") or "").strip().upper()
    if source_type == "PINE":
        if intraday:
            raise ValueError("Pine scanner profiles currently support daily scans only.")
        return run_pine_scanner_profile_scan(profile=profile)
    if source_type == "PRICE_ACTION":
        if intraday:
            raise ValueError("Price-action scanner profiles currently support daily scans only.")
        return run_price_action_scanner_profile_scan(profile=profile)
    if source_type == "PINE_LOGIC_IMPORT":
        raise ValueError("Imported Pine logic profiles are not scanner-executable.")
    raise ValueError(f"Unsupported scanner profile source_type '{source_type or 'UNKNOWN'}'.")


def _validate_selected_profile_for_scan(resolved_profile, *, intraday: bool, profile_id: Optional[int]):
    if profile_id is not None and resolved_profile is None:
        raise HTTPException(status_code=404, detail="Requested scanner profile was not found")
    if resolved_profile is None:
        return
    source_type = str(getattr(resolved_profile, "source_type", "") or "").strip().upper()
    if intraday and source_type in {"PINE", "PRICE_ACTION"}:
        label = "Pine" if source_type == "PINE" else "Price-action"
        raise HTTPException(status_code=400, detail=f"{label} scanner profiles currently support daily scans only")
    if source_type == "PINE_LOGIC_IMPORT":
        raise HTTPException(status_code=400, detail="Imported Pine logic profiles are not scanner-executable")

def sanitize_floats(obj):
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj): return 0.0
        return float(obj)
    elif isinstance(obj, np.generic): return sanitize_floats(obj.item())
    elif isinstance(obj, dict): return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [sanitize_floats(x) for x in obj]
    return obj


def _manual_scan_run_key(scan_type: str) -> str:
    now_dt = TimeUtils.now()
    return f"{TimeUtils.today().isoformat()}:{scan_type}:MANUAL:{now_dt.strftime('%H:%M:%S')}"


def _persist_manual_scan_run(
    *,
    index: str,
    intraday: bool,
    signals,
    monitored,
    breadth,
    regime,
):
    from routes import signals as signal_routes

    scan_type = "INTRADAY" if intraday else "DAILY"
    req = signal_routes.DailyRunRequest(
        run_date=TimeUtils.today().strftime("%Y-%m-%d"),
        scan_type=scan_type,
        run_key=_manual_scan_run_key(scan_type),
        force=True,
        notify=False,
        index=index,
        model_version="v1",
    )
    return signal_routes.run_daily_signals_logic(
        req,
        get_market_signals_fn=lambda **kwargs: (list(signals or []), list(monitored or []), breadth, regime),
    )

def background_scan_task(index: str, intraday: bool, notify: bool, profile_id: Optional[int] = None, use_active_profile: bool = True):
    SCAN_STATE["status"] = "RUNNING"
    SCAN_STATE["progress"] = 0
    SCAN_STATE["result"] = None
    SCAN_STATE["error"] = None
    
    def on_progress(current, total, ticker):
        SCAN_STATE["progress"] = current
        SCAN_STATE["total"] = total
        SCAN_STATE["current_ticker"] = ticker

    try:
        resolved_profile = (
            get_pine_scanner_profile(profile_id)
            if profile_id is not None
            else (get_active_pine_scanner_profile() if use_active_profile else None)
        )
        if resolved_profile is not None:
            profile = resolved_profile
            if profile is None:
                raise ValueError(f"Scanner profile {profile_id} was not found.")
            signals, monitored, breadth, regime, strategy_profile = _run_selected_scanner_profile(profile, intraday=intraday)
        else:
            signals, monitored, breadth, regime = DailyScanner.get_market_signals(
                index_choice=index,
                is_intraday=intraday,
                progress_callback=on_progress
            )
            strategy_profile = {
                "source_type": "HORUS",
                "profile_name": "Horus Core",
                "target_portfolio_name": resolve_target_portfolio_name("INTRADAY" if intraday else "DAILY"),
                "market": index,
                "timeframe": "INTRADAY" if intraday else "1D",
            }
        excluded = get_excluded_tickers_upper()
        signals = [s for s in (signals or []) if not is_excluded_ticker((s or {}).get("Ticker"), excluded)]
        monitored = [m for m in (monitored or []) if not is_excluded_ticker((m or {}).get("Ticker"), excluded)]
        execution_signals = list(signals)
        trade_signals = list(execution_signals)
        
        # Unified broadcast logic (deduplicated)
        should_auto_broadcast = (
            settings.TELEGRAM_AUTO_BROADCAST_INTRADAY if intraday
            else settings.TELEGRAM_AUTO_BROADCAST_DAILY
        )
        main_channel_signal_allowed = subscriptions.automated_main_channel_signal_allowed()
        wants_signal_broadcast = should_auto_broadcast or notify
        if wants_signal_broadcast and not main_channel_signal_allowed:
            logger.info("[Scanner] Auto-broadcast blocked by main channel signal level policy.")
        if wants_signal_broadcast and main_channel_signal_allowed and execution_signals:
            from core import AlertManager
            # Match the labels in api.py for cross-deduplication
            scan_label = "INTRADAY" if intraday else "DAILY SIGNAL"
            mode_label = "INTRADAY" if intraday else "DAILY"
            broadcast_signals = list(execution_signals)
            
            # DEDUPLICATION: Remove any tickers we already broadcasted today (broadcast-only gate)
            broadcast_signals = AlertManager.filter_new_signals(broadcast_signals, scan_label)
            trade_signals = list(broadcast_signals)
            
            if broadcast_signals:
                try:
                    # 1. Send regime/summary header
                    AlertManager.broadcast_alert(
                        f"🔍 *{mode_label} SCAN COMPLETE*\n"
                        f"Signals Found: {len(broadcast_signals)}"
                    )

                    # 2. Send signal cards with images for every signal in this run.
                    from core import ReportGenerator
                    for i, s in enumerate(broadcast_signals):
                        try:
                            ticker = s.get('Ticker', '')
                            entry = float(s.get('Entry_Price', 0))
                            sl = float(s.get('Stop_Loss', 0))
                            tp1 = float(s.get('Target_Price', 0))
                            tp2 = float(s.get('Target_Price_2', 0)) if s.get('Target_Price_2') is not None else None
                            score = int(s.get('Score', 0))
                            rsi = s.get('RSI')
                            volume_x = s.get('Volume_x')

                            img_buf = ReportGenerator.create_horus_signal_card(
                                ticker=ticker,
                                entry=entry,
                                stop_loss=sl,
                                tp1=tp1,
                                tp2=tp2,
                                score=score,
                                rsi=rsi,
                                volume_x=volume_x,
                                signal_label=f"{mode_label} SIGNAL"
                            )
                            rsi_text = f"{float(rsi):.1f}" if rsi is not None else "N/A"
                            vol_text = f"{float(volume_x):.1f}x" if volume_x is not None else "N/A"
                            caption = (
                                f"[SIGNAL {i+1}] {ticker} | Score: {score}/10\n"
                                f"RSI: {rsi_text} | Vol Spike: {vol_text}"
                            )
                            AlertManager.broadcast_image(img_buf, caption)
                        except Exception as card_err:
                            logger.error(f"[Scanner] Card generation failed for {s.get('Ticker')}: {card_err}")

                    # 3. Send full text summary
                    full_msg = TelegramBot_Alerts.format_signal_alert(broadcast_signals)
                    if full_msg:
                        AlertManager.broadcast_alert(f"📋 *FULL SUMMARY*\n\n{full_msg}")
                except Exception as broadcast_err:
                    logger.error(f"[Scanner] Auto-broadcast error: {broadcast_err}")

        for s in execution_signals:
            ticker_clean = normalize_ticker(s.get("Ticker"))
            if not ticker_clean or ticker_clean in excluded:
                continue
            try:
                # Get the absolute LATEST signal for this ticker regardless of date
                last_sig = (Signal.select()
                            .where((fn.Upper(Signal.ticker) == ticker_clean) & 
                                   (Signal.signal_type == s['Signal_Type']))
                            .order_by(Signal.date.desc(), Signal.id.desc())
                            .first())
                
                current_score = int(s['Score'])
                
                # Horus Eye Trigger: Previous state was score 7, now it's 8+
                if settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE and main_channel_signal_allowed:
                    if last_sig and int(last_sig.score) == 7 and current_score >= 8:
                        from core import AlertManager
                        from core import ReportGenerator
                        # DEDUPLICATION for Horus Eye
                        horus_signals = AlertManager.filter_new_signals([s], "HORUS MomentumBreakoutScanner")
                        
                        if horus_signals:
                            AlertManager.broadcast_alert(f"👁️ HORUS MomentumBreakoutScanner RECOMMENDATION 👁️\n{s['Ticker']} upgraded from score 7 to {current_score}!")
                            try:
                                img_buf = ReportGenerator.create_horus_signal_card(
                                    ticker=s['Ticker'],
                                    entry=float(s['Entry_Price']),
                                    stop_loss=float(s.get('Stop_Loss', 0)),
                                    tp1=float(s.get('Target_Price', 0)),
                                    score=current_score,
                                    rsi=s.get('RSI'),
                                    volume_x=s.get('Volume_x'),
                                    signal_label="HORUS MomentumBreakoutScanner"
                                )
                                AlertManager.broadcast_image(img_buf, f"👁️ Horus Eye Upgraded {s['Ticker']} to {current_score}/10")
                            except Exception as img_e:
                                logger.error(f"Failed to generate Horus Eye card for {s['Ticker']}: {img_e}")

                # Database Persistence Logic
                today_sig = Signal.get_or_none(
                    (fn.Upper(Signal.ticker) == ticker_clean) & 
                    (Signal.signal_type == s['Signal_Type']) & 
                    (Signal.date == TimeUtils.today())
                )

                if today_sig:
                    # If we found a HIGHER score today, update the record
                    if current_score > today_sig.score:
                        today_sig.score = current_score
                        today_sig.price = float(s['Entry_Price'])
                        today_sig.save()
                else:
                    # New signal for today
                    Signal.create(
                        ticker=ticker_clean,
                        signal_type=s['Signal_Type'],
                        price=float(s['Entry_Price']),
                        score=current_score,
                        source="Scanner"
                    )
            except Exception as e:
                print(f"Error processing signal {ticker_clean}: {e}")

        if settings.AUTO_TRADE_ENABLED:
            if not trade_signals:
                logger.info("[Scanner] Manual auto-trade skipped: no new execution-eligible signals after dedup.")
            elif intraday:
                run_result = _persist_manual_scan_run(
                    index=index,
                    intraday=intraday,
                    signals=trade_signals,
                    monitored=monitored,
                    breadth=breadth,
                    regime=regime,
                )
                persisted_run = run_result.get("run") or {}
                persisted_run_id = persisted_run.get("id")
                if run_result.get("status") == "completed" and persisted_run_id:
                    SignalExecutor.execute_run(int(persisted_run_id))
                else:
                    logger.warning(
                        "[Scanner] Manual intraday auto-trade skipped: persistence status=%s run=%s",
                        run_result.get("status"),
                        persisted_run,
                    )
            else:
                run_result = _persist_manual_scan_run(
                    index=index,
                    intraday=intraday,
                    signals=trade_signals,
                    monitored=monitored,
                    breadth=breadth,
                    regime=regime,
                )
                persisted_run = run_result.get("run") or {}
                persisted_run_id = persisted_run.get("id")
                if run_result.get("status") == "completed" and persisted_run_id:
                    SignalExecutor.execute_run(int(persisted_run_id))
                else:
                    logger.warning(
                        "[Scanner] Manual daily auto-trade skipped: persistence status=%s run=%s",
                        run_result.get("status"),
                        persisted_run,
                    )
        else:
            print("[Scanner] Auto-trade disabled; signals not auto-entered.")

        SCAN_STATE["result"] = sanitize_floats(filter_excluded_from_payload({
            "regime": regime,
            "breadth": breadth,
            "signals_count": len(execution_signals),
            "signals": execution_signals,
            "strategy_profile": strategy_profile,
            "whale_trap_diagnostics": summarize_whale_trap_diagnostics(execution_signals),
            "enforcement_diagnostics": summarize_enforcement_diagnostics(execution_signals),
            "calibration_diagnostics": summarize_calibration_diagnostics(execution_signals),
        }, excluded))
        SCAN_STATE["status"] = "COMPLETED"
        
    except Exception as e:
        SCAN_STATE["status"] = "ERROR"
        SCAN_STATE["error"] = str(e)

@router.get("/api/v1/scanner/run")
def run_scanner_deprecated():
    raise HTTPException(status_code=400, detail="Use POST /api/scanner/start instead")

@router.post("/api/v1/scanner/start")
async def start_scanner(background_tasks: BackgroundTasks, index: str = "EGX30", intraday: bool = False, notify: bool = False, profile_id: Optional[int] = None, use_active_profile: bool = True):
    if SCAN_STATE["status"] == "RUNNING":
        return {"message": "Scan already running", "started": False}
    resolved_profile = (
        get_pine_scanner_profile(profile_id)
        if profile_id is not None
        else (get_active_pine_scanner_profile() if use_active_profile else None)
    )
    _validate_selected_profile_for_scan(resolved_profile, intraday=intraday, profile_id=profile_id)
    background_tasks.add_task(background_scan_task, index, intraday, notify, resolved_profile.id if resolved_profile else None, use_active_profile)
    return {"message": "Scan started", "started": True}

# Manual Control endpoint used by Dashboard/Telegram
@router.post("/api/v1/control/scan")
async def control_scan(background_tasks: BackgroundTasks, payload: dict):
    scan_type = str(payload.get("type", "DAILY")).upper()
    notify = bool(payload.get("notify", False))
    intraday = scan_type == "INTRADAY"
    index = payload.get("index", "EGX30")
    profile_id = payload.get("profile_id")
    use_active_profile = bool(payload.get("use_active_profile", True))
    if SCAN_STATE["status"] == "RUNNING":
        return {"message": "Scan already running", "started": False}
    resolved_profile = (
        get_pine_scanner_profile(profile_id)
        if profile_id is not None
        else (get_active_pine_scanner_profile() if use_active_profile else None)
    )
    _validate_selected_profile_for_scan(resolved_profile, intraday=intraday, profile_id=profile_id)
    background_tasks.add_task(background_scan_task, index, intraday, notify, resolved_profile.id if resolved_profile else None, use_active_profile)
    return {"message": "Scan started", "started": True}


@router.get("/api/v1/scanner/status")
def get_scanner_status():
    return SCAN_STATE

@router.get("/api/v1/scanner/history")
def get_signal_history():
    # Time Travel Filter: Only see signals ON OR BEFORE "today"
    excluded = get_excluded_tickers_upper()
    query = Signal.select().where(Signal.date <= TimeUtils.today())
    if excluded:
        query = query.where(~fn.Upper(Signal.ticker).in_(excluded))
    rows = list(query.order_by(Signal.date.desc()).limit(100).dicts().iterator())
    return filter_excluded_from_payload(rows, excluded)

@router.get("/api/v1/reports/weekly")
def get_weekly_report():
    try:
        excluded = get_excluded_tickers_upper()
        trades = Trade.select().order_by(Trade.exit_date.desc()).limit(50).iterator()
        trades_data = [
            {"ticker": t.ticker, "pnl_pct": t.pnl_pct, "exit_date": str(t.exit_date)}
            for t in trades
            if t.exit_date and not is_excluded_ticker(t.ticker, excluded)
        ]
        return {"status": "success", "trades": trades_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
