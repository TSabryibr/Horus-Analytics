"""
DAILY SCANNER - CORE LOGIC
==========================
Scans the latest market data for Buy Signals using the Optimized Strategy.
Returns structured data signals. Pure Logic - No UI.
"""

from core.settings import settings
import pandas as pd
# import pandas_ta as ta  # REMOVED: Heavy import, logic is now native
import numpy as np
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from typing import Any, Optional, overload
from core import audit
from core import TimeUtils
from core.DataManager import DataManager
from core.market import SignalArchive
from core import PositionTracker
from core import SignalEngine
from core.regime_router import calculate_sector_relative_strength, route_candidate
from core.execution_model import build_candidate_microstructure_defaults
from core.market_profiles import EGX30_TREND_PROFILE, EGX70_TACTICAL_PROFILE
from core.market import MarketLists
from core.analyzers import Vanaheim
from core.analyzers import Svartalfheim
from concurrent.futures import ThreadPoolExecutor, as_completed
# Moved to lazy loading for speed: alpha_intelligence, SectorAnalysis, data_engine.ingest_intraday
from data_engine.freshness import evaluate_freshness
from core.WalkForwardValidation import get_trade_permission
from core.exclusions import get_excluded_tickers_upper, normalize_ticker
from core.whale_flow import evaluate_whale_flow
from core.trap_risk import assess_trap_risk
from core.whale_flow import summarize_whale_trap_diagnostics
from core.enforcement_gates import (
    assess_enforcement_gate,
    summarize_enforcement_diagnostics,
)
from core.enforcement_calibration import summarize_calibration_diagnostics

# === LOGGING SERVER ===
from utils.logger import setup_logger
logger = setup_logger("horus.scanner")


_last_intraday_sync_ts = None


def _empty_market_signal_payload(regime: str = "UNKNOWN"):
    return [], [], 0.0, regime


def _list_tickers_with_cold_retry():
    tickers = list(DataManager.list_tickers() or [])
    if tickers:
        return tickers

    try:
        from data_engine import api as data_engine_api

        data_engine_api.clear_data_cache()
    except Exception as exc:
        logger.warning("Ticker list empty; data-engine cache clear failed before retry: %s", exc)

    retry_tickers = list(DataManager.list_tickers() or [])
    if retry_tickers:
        logger.info("Ticker list recovered after clearing data-engine cache. count=%s", len(retry_tickers))
    return retry_tickers

def _maybe_sync_intraday(force: bool = False):
    """
    Ensure intraday sqlite is refreshed before an intraday or pre-close scan.
    Throttled to avoid repeated heavy syncs, but forced for pre-close scans.
    """
    global _last_intraday_sync_ts
    try:
        if not settings.is_market_open():
            return
        now = TimeUtils.now()
        min_interval = int(os.getenv("INTRADAY_SYNC_MINUTES", "5"))
        if not force and _last_intraday_sync_ts and (now - _last_intraday_sync_ts).total_seconds() < min_interval * 60:
            return
        if not force:
            try:
                import core.Heimdall as Heimdall
                realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
                freshness = evaluate_freshness(realm=realm, run_date=TimeUtils.today(), scan_type="INTRADAY")
                intraday = (freshness or {}).get("intraday") or {}
                if bool(intraday.get("ok", False)):
                    age_mins_raw = intraday.get("age_mins")
                    try:
                        age_mins = float(age_mins_raw) if age_mins_raw is not None else None
                    except (TypeError, ValueError):
                        age_mins = None
                    if age_mins is None or age_mins < float(min_interval):
                        logger.info("Intraday sync skipped: freshness already OK.")
                        _last_intraday_sync_ts = now
                        return
                    logger.info(
                        f"Intraday sync proceeding: latest live bar age={age_mins:.1f}m "
                        f"exceeds interval={min_interval}m."
                    )
            except Exception as freshness_exc:
                logger.warning(f"Intraday freshness probe failed; proceeding with sync: {freshness_exc}")
        logger.info(f"Intraday sync start (throttle={min_interval}m, force={force})")
        import data_engine.ingest_intraday as ingest_intraday
        ingest_intraday.ingest_intraday()
        _last_intraday_sync_ts = now
        # Ensure freshness cache reflects the new data immediately
        try:
            from data_engine.freshness import invalidate_freshness_cache
            invalidate_freshness_cache()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Intraday sync failed/skipped: {e}")

def _candidate_diagnostics_enabled(is_pre_close: bool = False, is_intraday: bool = False) -> bool:
    if is_pre_close or is_intraday:
        return True
    return os.getenv("SCANNER_CANDIDATE_DIAGNOSTICS", "0").strip().lower() in {"1", "true", "yes", "on"}


def _daily_preview_mode(is_intraday: bool, is_pre_close: bool) -> bool:
    return is_pre_close and not is_intraday


@overload
def _safe_float(value: Any, default: float) -> float: ...
@overload
def _safe_float(value: Any, default: None = None) -> Optional[float]: ...
def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _buy_signal_rejection_reason(row, settings, resistance_col, profile):
    if row is None:
        return "empty_row"
    if pd.isna(row.get(resistance_col)):
        return "missing_resistance"
    if pd.isna(row.get("RSI")):
        return "missing_rsi"

    close = _safe_float(row.get("Close"), 0.0)
    res = _safe_float(row.get(resistance_col), 0.0)
    rsi = _safe_float(row.get("RSI"), 0.0)
    turnover = _safe_float(row.get("Avg_Turnover"), 0.0)
    rel_vol = _safe_float(row.get("Rel_Vol"), 0.0)
    move = _safe_float(row.get("Move"), 0.0)

    if turnover <= float(getattr(settings, "MIN_TURNOVER", 0.0)):
        return "liquidity_floor"
    if rel_vol <= float(getattr(settings, "VOL_SPIKE", 0.0)):
        return "volume_spike"
    if move < float(getattr(settings, "MOMENTUM", 0.0)):
        return "momentum"
    if not (float(getattr(settings, "RSI_MIN", 0.0)) < rsi < float(getattr(settings, "RSI_MAX", 100.0))):
        return "rsi_range"
    if close <= res:
        return "breakout"

    try:
        from core.signal_validation import validate_long_signal

        validation = validate_long_signal(row, settings, profile=profile)
        if not validation.get("is_valid", False):
            return str(validation.get("veto_reason") or "long_validation")
    except Exception as exc:
        return f"validation_error:{exc}"
    return "unknown_buy_signal_gate"


def _trickster_rejection_reason(row):
    if row is None:
        return "empty_row"
    required = ("RSI", "EMA9", "Close", "ATR", "Open")
    for col in required:
        if pd.isna(row.get(col)):
            return f"missing_{col.lower()}"

    close = _safe_float(row.get("Close"), 0.0)
    open_price = _safe_float(row.get("Open"), 0.0)
    ema9 = _safe_float(row.get("EMA9"), 0.0)
    rsi = _safe_float(row.get("RSI"), 0.0)
    atr = _safe_float(row.get("ATR"), 0.0)
    rel_vol = _safe_float(row.get("Rel_Vol"), 0.0)

    rsi_min_base = float(getattr(settings, "RSI_MIN", 50.0))
    trickster_rsi_max = float(getattr(settings, "TRICKSTER_RSI_MAX", min(30.0, rsi_min_base - 20.0)))
    vol_spike_base = float(getattr(settings, "VOL_SPIKE", 1.5))
    trickster_rel_vol_min = float(getattr(settings, "TRICKSTER_REL_VOL_MIN", min(1.5, vol_spike_base * 0.7)))
    mom_base = float(getattr(settings, "MOMENTUM", 2.0))
    trickster_stretch_atr = float(getattr(settings, "TRICKSTER_STRETCH_ATR", min(3.0, mom_base)))

    ema_dist = (ema9 - close) / atr if atr > 0 else 0.0
    if rsi >= trickster_rsi_max:
        return "trickster_rsi"
    if ema_dist <= trickster_stretch_atr:
        return "trickster_stretch"
    if close <= open_price:
        return "trickster_turning"
    if rel_vol < trickster_rel_vol_min:
        return "trickster_participation"
    return "unknown_trickster_gate"


def _log_candidate_rejection(ticker, row, reason, is_pre_close=False, is_intraday=False, route=None):
    if not _candidate_diagnostics_enabled(is_pre_close=is_pre_close, is_intraday=is_intraday):
        return
    route = route or {}
    logger.info(
        "[CandidateDiagnostics] rejected ticker=%s reason=%s close=%s move=%s rsi=%s rel_vol=%s "
        "turnover=%s route_reason=%s sector_rs=%s",
        ticker,
        reason,
        _safe_float(row.get("Close")),
        _safe_float(row.get("Move")),
        _safe_float(row.get("RSI")),
        _safe_float(row.get("Rel_Vol")),
        _safe_float(row.get("Turnover"), _safe_float(row.get("Avg_Turnover"))),
        route.get("routing_reason"),
        route.get("sector_rs_14"),
    )

def get_market_signals(index_choice="ALL", is_intraday=False, is_pre_close=False, progress_callback=None, universe_df=None):
    # ... (Setup) ...
    from core.market import MarketLists
    source_folder = settings.METASTOCK_INTRADAY_FOLDER if is_intraday else settings.METASTOCK_HISTORY_FOLDER
    daily_preview = _daily_preview_mode(is_intraday, is_pre_close)
    
    # 1. Ticker Acquisition (Pre-load aware)
    if universe_df is not None and not universe_df.empty:
        # Use provided data (H1 Optimization)
        tickers = list(universe_df.index.get_level_values(0).unique())
        logger.info(f"Using pre-loaded universe with {len(tickers)} tickers.")
    else:
        market_filter = MarketLists.get_market_list(index_choice)
        tickers = _list_tickers_with_cold_retry()
        if not tickers:
            logger.warning("No tickers found in Data Engine after cache refresh.")
            return _empty_market_signal_payload()
        # Apply Global Exclusions
        excluded_set = get_excluded_tickers_upper()
        tickers = [
            t for t in tickers
            if normalize_ticker(t) not in excluded_set and normalize_ticker(t) not in ['REPORT', 'EGX30_70_100']
        ]

    use_live_prices = bool(is_intraday or daily_preview)
    if not use_live_prices and not is_pre_close and not is_intraday:
        try:
            from data_engine.freshness import evaluate_freshness
            from core import Heimdall
            freshness = evaluate_freshness(
                realm=getattr(Heimdall, "CURRENT_REALM", "EGX"),
                run_date=TimeUtils.today(),
                scan_type="DAILY",
            )
            history = freshness.get("history", {}) if isinstance(freshness, dict) else {}
            history_kpis = history.get("kpis", {}) if isinstance(history, dict) else {}
            fresh_ratio = float(history_kpis.get("fresh_ratio", 0.0) or 0.0)
            pending_eod = bool(history.get("pending_eod_history", False))
            if fresh_ratio < 0.90 or pending_eod:
                use_live_prices = True
                logger.info(
                    f"[DailyScanner] Daily scan using live prices — "
                    f"history fresh_ratio={fresh_ratio:.2%}, pending_eod={pending_eod}"
                )
        except Exception as exc:
            logger.warning(f"[DailyScanner] Failed to check daily freshness for live price fallback: {exc}")

    if use_live_prices and (universe_df is None or universe_df.empty):
        _maybe_sync_intraday(force=is_pre_close)

    signals = []
    monitored = []
    
    # --- PHASE 3: UNIVERSE-WIDE BULK PROCESSING ---

    # 1. Fetch Data (if not provided)
    if universe_df is None or universe_df.empty:
        logger.info(
            f"Scanning {len(tickers)} tickers. "
            f"Intraday={is_intraday} PreClose={is_pre_close} DailyPreview={daily_preview}"
        )
        universe_df = DataManager.get_universe_data(tickers, include_live=use_live_prices)
    
    if universe_df is None or universe_df.empty:
        logger.error("Failed to load universe data.")
        return _empty_market_signal_payload()
        
    # 2. Bulk Calculate Indicators
    if 'RSI' not in universe_df.columns:
        universe_df = SignalEngine.add_indicators_universe(universe_df, settings.LOOKBACK)

    # 3. Extract Latest Bar per Ticker and Score
    latest_rows = universe_df.groupby(level=0).tail(1).reset_index(level=1)
    
    # --- VECTORIZED STALENESS & MONITORING (Phase 8) ---
    # Calculate staleness for all at once
    now_ts = TimeUtils.now()
    # Normalize timezones for comparison
    now_naive = now_ts.replace(tzinfo=None)
    latest_dates = pd.Series(pd.to_datetime(latest_rows['Date'], utc=True)).dt.tz_convert(None)
    latest_rows['Staleness_Days'] = (now_naive - latest_dates).dt.days
    
    # Identify non-stale tickers
    if daily_preview:
        is_today = latest_dates.dt.date == TimeUtils.today()
        is_fresh = is_today
    elif use_live_prices:
        is_today = latest_dates.dt.date == TimeUtils.today()
        is_recent = latest_dates.dt.date.apply(lambda d: settings.is_recent_trading_day(d, max_trading_days=1))
        is_fresh = is_today | (is_recent & settings.is_market_open())
    else:
        is_fresh = latest_rows['Staleness_Days'] <= 10
    
    # Build Monitoring Overview (Vectorized)
    latest_rows['Trend'] = np.where(latest_rows['Close'] > latest_rows['EMA9'], 'UP', 'DOWN')
    monitored_df = latest_rows[is_fresh][['Close', 'Trend', 'RSI']].copy()
    monitored_df['Ticker'] = monitored_df.index
    monitored = monitored_df.to_dict('records')
    
    # --- PRE-FILTER Gating (Fast path) ---
    # Apply raw breakouts gating across the whole batch
    passed_mask = SignalEngine.vectorize_signals(latest_rows, settings, f'Res_{settings.LOOKBACK}')
    
    # Handle Trickster separately (blood-in-the-streets)
    latest_rsi = latest_rows['RSI']
    is_trickster_candidate = latest_rsi < 30
    
    # Final Candidates = (Fresh) AND (Passed Vectorized OR Is Trickster Candidate)
    if passed_mask is None:
        logger.warning("Vectorized signals returned None, using empty mask.")
        passed_mask = pd.Series([False] * len(latest_rows), index=latest_rows.index)
        
    candidates_mask = is_fresh & (passed_mask | is_trickster_candidate)
    candidate_tickers = latest_rows[candidates_mask].index.tolist()

    # Batch Sector Lookup for candidates only
    candidate_sectors = {}
    whale_candidates = []
    bull_traps = []
    bear_traps = []
    sector_rs_map = {}
    
    if candidate_tickers:
        from core.market import SectorAnalysis
        candidate_sectors = {t: SectorAnalysis.get_sector(t) for t in candidate_tickers}

        # M8 Fix: Only fetch whale/trap/sector metadata when there are candidates
        try:
            whales = Vanaheim.hunt_whales(candidate_tickers)
            if isinstance(whales, list):
                whale_candidates = whales
            elif isinstance(whales, dict):
                candidates_raw = whales.get("candidates")
                whale_candidates = list(candidates_raw) if isinstance(candidates_raw, (list, tuple, set)) else []
        except Exception as exc:
            logger.warning(f"Whale metadata scan failed: {exc}")
        try:
            traps = Svartalfheim.hunt_traps(candidate_tickers)
            if isinstance(traps, dict):
                b_traps = traps.get("bull_traps")
                bull_traps = list(b_traps) if isinstance(b_traps, (list, tuple, set)) else []
                be_traps = traps.get("bear_traps")
                bear_traps = list(be_traps) if isinstance(be_traps, (list, tuple, set)) else []
            elif isinstance(traps, list):
                bull_traps = traps
        except Exception as exc:
            logger.warning(f"Trap metadata scan failed: {exc}")

        sector_rs_map = calculate_sector_relative_strength(
            universe_df,
            lookback=14,
            sector_map=MarketLists.SECTOR_MAP,
            benchmark_tickers=MarketLists.EGX_30,
        )

    # 4. FINAL SCORING LOOP (Parallelized for Speed)
    signals = []
    if candidate_tickers:
        # --- WFA GATE CHECK (Correctness) ---
        # Filter candidates based on Walk-Forward Analysis permissions
        candidate_tickers = [t for t in candidate_tickers if get_trade_permission(t).get("allowed", True)]
        
        if candidate_tickers:
            if _candidate_diagnostics_enabled(is_pre_close=is_pre_close, is_intraday=is_intraday):
                logger.info(
                    "[CandidateDiagnostics] candidates_after_wfa count=%s tickers=%s",
                    len(candidate_tickers),
                    ",".join(candidate_tickers),
                )
            logger.info(f"Parallel scoring {len(candidate_tickers)} candidates...")
            with ThreadPoolExecutor(max_workers=min(len(candidate_tickers), 16)) as executor:
                future_to_ticker = {
                    executor.submit(
                        _score_single_candidate,
                        ticker,
                        latest_rows.loc[ticker],
                        universe_df.loc[ticker] if ticker in universe_df.index.levels[0] else None,
                        is_trickster_candidate.get(ticker, False),
                        candidate_sectors.get(ticker, "Unknown"),
                        sector_rs_map,
                        whale_candidates,
                        bull_traps,
                        bear_traps,
                        is_intraday,
                        is_pre_close
                    ): ticker for ticker in candidate_tickers
                }
                
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        sig = future.result()
                        if sig:
                            signals.append(sig)
                    except Exception as exc:
                        logger.error(f"Error scoring {ticker}: {exc}")
            
    # Breadth
    above_trend = sum(1 for m in monitored if m['Trend'] == 'UP')
    total = len(monitored)
    breadth = (above_trend / total * 100) if total > 0 else 0
    
    if breadth > 50: regime = "BULLISH"
    elif breadth > 30: regime = "CAUTIOUS"
    else: regime = "BEARISH"
    
    # --- LOKI'S LEASH: Regime-Adaptive Signal Gating ---
    original_count = len(signals)
    if signals:
        # Sort by score (highest conviction first)
        signals = sorted(signals, key=lambda x: x.get('Score', 0), reverse=True)
        
        # Relaxed limits during historical backfill to avoid artificial signal drought
        is_backfill = TimeUtils.is_simulating()

        if regime == "BEARISH":
            if is_backfill:
                signals = [s for s in signals if s.get('Score', 0) >= 6][:5]
                logger.info(f"[BEAR-BACKFILL] BEARISH REGIME (relaxed): Filtered from {original_count} to {len(signals)}.")
            else:
                signals = [s for s in signals if s.get('Score', 0) >= 8][:1]
                logger.warning(f"[BEAR] BEARISH REGIME: Choked signal count from {original_count} down to {len(signals)}.")
        elif regime == "CAUTIOUS":
            if is_backfill:
                signals = signals[:10]
                logger.info(f"[WARN-BACKFILL] CAUTIOUS REGIME (relaxed): Limited to {len(signals)}.")
            else:
                signals = signals[:3]
                logger.info(f"[WARN] CAUTIOUS REGIME: Limited signal count to {len(signals)}.")

    signal_tickers = [s.get('Ticker', '?') for s in signals]
    logger.info(
        f"[DailyScanner] Scan complete. Found {len(signals)} signals across {len(tickers)} tickers."
        + (f" Tickers: {signal_tickers}" if signals else "")
    )
    
    whale_trap_diagnostics = summarize_whale_trap_diagnostics(signals)
    enforcement_diagnostics = summarize_enforcement_diagnostics(signals)
    calibration_diagnostics = summarize_calibration_diagnostics(signals)

    audit.log_event(
        category="SIGNAL",
        event="SCAN_COMPLETE",
        message=f"Found {len(signals)} signals. Regime: {regime} ({breadth:.1f}%)",
        level="INFO",
        meta={
            "signals": len(signals),
            "tickers": len(tickers),
            "regime": regime,
            "breadth": breadth,
            "whale_trap_diagnostics": whale_trap_diagnostics,
            "enforcement_diagnostics": enforcement_diagnostics,
            "calibration_diagnostics": calibration_diagnostics,
        }
    )
    
    return signals, monitored, breadth, regime

# === BACKWARD COMPATIBILITY WRAPPER ===
def scan_market(index_choice="ALL", data_folder=None, is_intraday=False):
    """
    Wrapper for existing Dashboard calls.
    Ignores 'data_folder' argument as we rely on GlobalSettings/DataManager now.
    """
    return get_market_signals(index_choice, is_intraday)

def _score_single_candidate(
    ticker, 
    last, 
    ticker_df, 
    is_trickster, 
    sector, 
    sector_rs_map, 
    whale_candidates,
    bull_traps,
    bear_traps,
    is_intraday,
    is_pre_close
):
    """Worker function for parallel scoring."""
    signal_profile = EGX70_TACTICAL_PROFILE if MarketLists.is_egx70_ticker(ticker) else EGX30_TREND_PROFILE
    
    # Detailed scoring (Trickster / Scored Signal)
    sig: dict[str, Any] | None = SignalEngine.check_buy_signal(
        last,
        settings,
        f'Res_{settings.LOOKBACK}',
        profile=signal_profile,
    )
    
    if sig is None and is_trickster and ticker_df is not None:
        sig = SignalEngine.check_trickster_signal(ticker_df, row_idx=-1, settings=settings)
        if sig is None:
            try:
                _log_candidate_rejection(
                    ticker,
                    ticker_df.iloc[-1],
                    _trickster_rejection_reason(ticker_df.iloc[-1]),
                    is_pre_close=is_pre_close,
                    is_intraday=is_intraday,
                )
            except Exception:
                _log_candidate_rejection(
                    ticker,
                    last,
                    "trickster_validation",
                    is_pre_close=is_pre_close,
                    is_intraday=is_intraday,
                )
    
    if not sig:
        if not is_trickster:
            _log_candidate_rejection(
                ticker,
                last,
                _buy_signal_rejection_reason(
                    last,
                    settings,
                    f'Res_{settings.LOOKBACK}',
                    signal_profile,
                ),
                is_pre_close=is_pre_close,
                is_intraday=is_intraday,
            )
        return None

    sig = dict(sig)
    sig.setdefault('VSA_Valid', None)
    sig.setdefault('Volume_Mult_20', sig.get('Volume_Spike'))
    sig.setdefault('Validation_Profile', None)
    sig.setdefault('Trap_Risk', None)
    sig.setdefault('Expected_Slippage_Pct', None)
    sig.setdefault('Execution_Cap_Shares', None)
    sig.setdefault('Microstructure', build_candidate_microstructure_defaults())

    from core.regime_router import route_candidate
    route = route_candidate(
        ticker=ticker,
        row=last,
        sector=sector,
        sector_rs_map=sector_rs_map,
        egx30_tickers=MarketLists.EGX_30,
        egx70_tickers=MarketLists.EGX_70,
    )
    if not route['allowed']:
        _log_candidate_rejection(ticker, last, f"route_{route.get('routing_reason', 'blocked')}", is_pre_close, route=route)
        return None

    sig['Ticker'] = ticker
    sig['Confirmation'] = 'PRE-CLOSE' if is_pre_close else ('PROVISIONAL' if is_intraday else 'CONFIRMED')
    if is_pre_close:
        sig['Preview_Mode'] = 'DAILY_RULES_LIVE_CLOSE'
        sig['Preview_Source'] = 'PRE_CLOSE_DAILY_PREVIEW'
        sig['Preview_Close'] = _safe_float(last.get('Close'))
        sig['Preview_Volume'] = _safe_float(last.get('Volume'))
        sig['Preview_Date'] = last.get('Date')
    
    prec = settings.PRICE_PRECISION
    sig['Entry_Price'] = round(float(sig['Entry_Price']), prec)
    sig['Stop_Loss'] = round(float(sig['Stop_Loss']), prec)
    sig['Target_Price'] = round(float(sig['Target_Price']), prec)
    target2 = sig.get('Target_Price_2')
    if target2 is None:
        target2 = sig['Target_Price'] * 1.04
    sig['Target_Price_2'] = round(float(target2), prec)
    
    sig['Sector'] = sector
    sig['Route_Profile'] = route['route_profile']
    sig['Liquidity_Tier'] = route['liquidity_tier']
    sig['Sector_RS_14'] = route['sector_rs_14']
    sig['Routing_Reason'] = route['routing_reason']
    
    whale_meta = evaluate_whale_flow(
        ticker=ticker,
        whale_candidates=whale_candidates,
        candidate_side=str(sig.get('Signal_Type', 'BUY')),
    )
    trap_meta = assess_trap_risk(
        ticker=ticker,
        liquidity_tier=route['liquidity_tier'],
        sector_rs_14=route['sector_rs_14'],
        vsa_valid=bool(sig['VSA_Valid']) if sig.get('VSA_Valid') is not None else None,
        whale_alignment=whale_meta['whale_alignment'],
        bull_traps=bull_traps,
        bear_traps=bear_traps,
    )
    sig['Whale_Signal'] = whale_meta['whale_signal']
    sig['Whale_Strength'] = whale_meta['whale_strength']
    sig['Whale_Alignment'] = whale_meta['whale_alignment']
    sig['Whale_Reason'] = whale_meta['whale_reason']
    sig['Trap_Risk'] = trap_meta['trap_risk_band']
    sig['Trap_Risk_Score'] = trap_meta['trap_risk_score']
    sig['Trap_Risk_Band'] = trap_meta['trap_risk_band']
    sig['Trap_Risk_Reason'] = trap_meta['trap_risk_reason']
    sig['Trap_Risk_Components'] = trap_meta['trap_risk_components']
    
    enforcement_meta = assess_enforcement_gate(
        trap_risk_band=trap_meta['trap_risk_band'],
        whale_alignment=whale_meta['whale_alignment'],
        route_profile=route['route_profile'],
    )
    sig['Enforcement_State'] = enforcement_meta['enforcement_state']
    sig['Enforcement_Visibility'] = enforcement_meta['enforcement_visibility']
    sig['Enforcement_Reason'] = enforcement_meta['enforcement_reason']
    sig['Enforcement_Notes'] = enforcement_meta['enforcement_notes']
    sig['Enforcement_Profile'] = enforcement_meta['enforcement_profile']
    sig['Date'] = last['Date']
    
    vol_spike = sig.get('Volume_Spike', 0)
    sig['Volume_x'] = round(float(vol_spike), 1) if pd.notna(vol_spike) else 0.0
    
    return sig

if __name__ == "__main__":
    # Test Run
    print("Running DailyScanner Logic Test...")
    sigs, _, br, reg = get_market_signals()
    print(f"BREADTH: {br:.1f}% ({reg})")
    print(f"SIGNALS: {len(sigs)}")
    if sigs:
        print(sigs[0])
