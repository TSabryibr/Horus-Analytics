from __future__ import annotations

import glob
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("horus.breakout.scanner")

import numpy as np
import pandas as pd

from core import TimeUtils
from core.pre_scanner_middleware import DataValidationError, PreScannerMiddleware
from core.settings import settings
from database import SignalStateArchive
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_usd_trend_slope

from .excel import export_scan_results_to_excel
from .metrics import detect_manipulation, estimate_bid_ask_spread
from .pivots import (
    DATA_FOLDER,
    EMA_FAST,
    FORCE_PERIOD,
    LOOKBACK,
    MAX_SPREAD_PCT,
    MIN_AVG_VOLUME_20D,
    MIN_DATA_POINTS,
    MIN_TURNOVER_EGP,
    MOMENTUM_THRESHOLD,
    RSI_MAX,
    RSI_MIN,
    RSI_PERIOD,
    SL_BUFFER_PCT,
    TP1_PCT,
    TP2_RR_RATIO,
    TP3_RR_RATIO,
    TP4_RR_RATIO,
    USD_STOCKS,
    VOL_AVG_PERIOD,
    VOL_SPIKE_FACTOR,
    _prepare_analysis_frame,
    calculate_critical_points,
)


def _get_active_module_attr(attr_name: str, fallback: object) -> object:
    mod = sys.modules.get("core.analyzers.MomentumBreakoutScanner")
    if mod is not None and hasattr(mod, attr_name):
        return getattr(mod, attr_name)
    mod_pkg = sys.modules.get("core.analyzers.breakout")
    if mod_pkg is not None and hasattr(mod_pkg, attr_name):
        return getattr(mod_pkg, attr_name)
    return fallback


def _include_live_for_analysis(include_live: bool | None = None) -> bool:
    if include_live is not None:
        return bool(include_live)
    try:
        return settings.is_market_open() and not TimeUtils.is_simulating()
    except Exception:
        return False


def analyze_stock_frame(ticker: str, df: pd.DataFrame | None) -> dict | None:
    """Analyze a single ticker from an already-loaded history DataFrame."""
    try:
        import uuid

        if df is None or df.empty:
            err_msg = "Input DataFrame is empty or None"
            logger.warning(f"[PreScanner] Validation failed for {ticker}: {err_msg}")
            try:
                SignalStateArchive.create(
                    ticker=ticker,
                    timestamp=TimeUtils.now(),
                    final_status="DATA_CORRUPTED",
                    signal_score=0,
                    filter_snapshot_json=json.dumps({"error": err_msg}),
                    kill_reason=err_msg,
                    signal_id=f"ERR-{ticker.upper()}-{uuid.uuid4().hex[:8].upper()}",
                )
            except Exception as archive_err:
                logger.error(f"Failed to create database audit event for corrupted data: {archive_err}")
            return None

        prepare_fn = _get_active_module_attr("_prepare_analysis_frame", _prepare_analysis_frame)
        df = prepare_fn(df)
        if df is None:
            err_msg = "Input DataFrame preparation failed"
            logger.warning(f"[PreScanner] Validation failed for {ticker}: {err_msg}")
            try:
                SignalStateArchive.create(
                    ticker=ticker,
                    timestamp=TimeUtils.now(),
                    final_status="DATA_CORRUPTED",
                    signal_score=0,
                    filter_snapshot_json=json.dumps({"error": err_msg}),
                    kill_reason=err_msg,
                    signal_id=f"ERR-{ticker.upper()}-{uuid.uuid4().hex[:8].upper()}",
                )
            except Exception as archive_err:
                logger.error(f"Failed to create database audit event for corrupted data: {archive_err}")
            return None

        try:
            df, signal_id, raw_snapshot = PreScannerMiddleware.process(ticker, df)
        except DataValidationError as err:
            logger.warning(f"[PreScanner] Validation failed for {ticker}: {err}")
            try:
                SignalStateArchive.create(
                    ticker=ticker,
                    timestamp=TimeUtils.now(),
                    final_status="DATA_CORRUPTED",
                    signal_score=0,
                    filter_snapshot_json=json.dumps({"error": str(err)}),
                    kill_reason=str(err),
                    signal_id=f"ERR-{ticker.upper()}-{uuid.uuid4().hex[:8].upper()}",
                )
            except Exception as archive_err:
                logger.error(f"Failed to create database audit event for corrupted data: {archive_err}")
            return None

        active_usd_stocks = _get_active_module_attr("USD_STOCKS", USD_STOCKS)
        currency = "USD" if ticker.upper() in active_usd_stocks else "EGP"
        rate_fetcher = _get_active_module_attr("get_parallel_usd_egp_rate", get_parallel_usd_egp_rate)
        current_rate = rate_fetcher()

        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift()).abs()
        tr3 = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

        efi = df['Close'].diff(1) * df['Volume']
        df['EFI'] = efi.ewm(span=FORCE_PERIOD, adjust=False).mean()

        df['Resistance_20D'] = df['High'].rolling(LOOKBACK).max().shift(1)

        df['EMA9'] = df['Close'].ewm(span=EMA_FAST, adjust=False).mean()

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['Avg_Volume'] = df['Volume'].rolling(VOL_AVG_PERIOD).mean()
        df['Rel_Volume'] = df['Volume'] / df['Avg_Volume']
        df['Price_Move_%'] = ((df['Close'] - df['Open']) / df['Open']) * 100
        df['Daily_Turnover'] = df['Close'] * df['Volume']
        df['Avg_Turnover'] = df['Daily_Turnover'].rolling(VOL_AVG_PERIOD).mean()

        current_price = df['Close'].iloc[-1]
        current_open = df['Open'].iloc[-1]
        current_high = df['High'].iloc[-1]
        current_low = df['Low'].iloc[-1]
        current_atr = df['ATR'].iloc[-1]
        resistance_20d = df['Resistance_20D'].iloc[-1]
        current_power = df['EFI'].iloc[-1]
        current_ema9 = df['EMA9'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        current_rel_vol = df['Rel_Volume'].iloc[-1]
        current_price_move = df['Price_Move_%'].iloc[-1]
        avg_turnover = df['Avg_Turnover'].iloc[-1]

        if pd.isna(resistance_20d) or pd.isna(current_atr) or pd.isna(current_rsi):
            return None

        avg_turnover_egp = avg_turnover * current_rate
        is_liquid = avg_turnover_egp > MIN_TURNOVER_EGP
        is_momentum_spike = (
            current_rel_vol > VOL_SPIKE_FACTOR and
            current_price_move >= MOMENTUM_THRESHOLD and
            current_rsi > RSI_MIN and
            current_rsi < RSI_MAX
        )
        institutional_signal = is_liquid and is_momentum_spike

        cp_calc_fn = _get_active_module_attr("calculate_critical_points", calculate_critical_points)
        key_res_1, key_res_2, trend_direction = cp_calc_fn(df, current_price, current_atr)

        key_res_1_dist_pct = ((key_res_1 - current_price) / current_price) * 100
        key_res_2_dist_pct = ((key_res_2 - current_price) / current_price) * 100

        breakout = current_price > resistance_20d
        dist_percent = ((resistance_20d - current_price) / current_price) * 100

        slippage_pct = float(getattr(settings, "SLIPPAGE_PCT", 0.1))
        raw_stop_loss = current_low * (1 - (SL_BUFFER_PCT / 100))
        stop_loss = raw_stop_loss * (1 - (slippage_pct / 100))
        risk_amount = current_price - stop_loss

        slippage_adjusted_entry = current_price * (1 + (slippage_pct / 100))
        adjusted_risk_amount = slippage_adjusted_entry - stop_loss
        if adjusted_risk_amount <= 0:
            adjusted_risk_amount = risk_amount if risk_amount > 0 else 0.01

        target_1 = current_price * (1 + (TP1_PCT / 100)) * (1 - (slippage_pct / 100))
        target_2 = current_price + (adjusted_risk_amount * TP2_RR_RATIO)
        target_3 = current_price + (adjusted_risk_amount * TP3_RR_RATIO)
        target_4 = current_price + (adjusted_risk_amount * TP4_RR_RATIO)

        avg_slippage_pct = 0.0
        try:
            from core.analyzers.SlippageReconciler import SlippageReconciler
            avg_slippage_pct = SlippageReconciler.get_dynamic_calibration_metrics(ticker)
        except Exception as e:
            print(f"Error fetching slippage metrics for {ticker}: {e}")

        if avg_slippage_pct > 0.0:
            dynamic_max_spread = max(0.005, MAX_SPREAD_PCT - (avg_slippage_pct / 100.0))
        else:
            dynamic_max_spread = MAX_SPREAD_PCT

        spread_estimator = _get_active_module_attr("estimate_bid_ask_spread", estimate_bid_ask_spread)
        estimated_spread = spread_estimator(df, avg_turnover_egp)
        current_avg_vol = df['Avg_Volume'].iloc[-1]

        is_liquidity_trap = False
        liquidity_trap_reasons = []

        if estimated_spread > dynamic_max_spread:
            is_liquidity_trap = True
            liquidity_trap_reasons.append("WIDE_SPREAD")
        if current_avg_vol < MIN_AVG_VOLUME_20D:
            is_liquidity_trap = True
            liquidity_trap_reasons.append("LOW_VOLUME")
        if avg_turnover_egp < MIN_TURNOVER_EGP:
            is_liquidity_trap = True
            liquidity_trap_reasons.append("LOW_TURNOVER")

        manip_detector = _get_active_module_attr("detect_manipulation", detect_manipulation)
        is_manipulation, manipulation_tag, manipulation_reason = manip_detector(
            rel_volume=current_rel_vol,
            price_move_pct=current_price_move,
            breakout=breakout,
            avg_turnover=avg_turnover_egp,
        )

        signal_score = 0
        signal_reasons = []

        if breakout and current_power > 0:
            signal_score += 3
            signal_reasons.append("Breakout_Confirmed")

        if institutional_signal:
            signal_score += 5
            signal_reasons.append("Institutional_Activity")

        if current_rel_vol > 1.5:
            signal_score += 1
            signal_reasons.append("High_Volume")

        if 50 < current_rsi < 70:
            signal_score += 1
            signal_reasons.append("RSI_Optimal")

        if current_price > current_ema9:
            signal_score += 1
            signal_reasons.append("Trend_Confirmed")

        is_ppp_failure = False
        ppp_reason = ""
        projected_return = 0.0
        hurdle_rate = 0.0

        if currency == "EGP" and (signal_score >= 4 or breakout or institutional_signal):
            expected_hold_days = 10
            slope_fetcher = _get_active_module_attr("get_usd_trend_slope", get_usd_trend_slope)
            daily_slope = slope_fetcher()
            safety_premium = float(getattr(settings, "PPP_MIN_ALPHA_PREMIUM", 1.0))
            hurdle_rate = (daily_slope * expected_hold_days) + safety_premium

            if current_price > 0:
                projected_return = ((target_2 - current_price) / current_price) * 100

            if projected_return < hurdle_rate:
                is_ppp_failure = True
                ppp_reason = f"Expected: {projected_return:.2f}% < Hurdle: {hurdle_rate:.2f}%"

        if is_manipulation:
            status = manipulation_tag
            signal_score = 0
            signal_reasons.append(f"Manipulation_Sentry ({manipulation_reason})")
        elif is_liquidity_trap and (signal_score >= 4 or breakout or institutional_signal):
            status = f"⚠️ LIQUIDITY TRAP ({', '.join(liquidity_trap_reasons)})"
            signal_score = 0
            signal_reasons.append(f"Blocked_By_Liquidity_Guard ({'/'.join(liquidity_trap_reasons)})")
        elif is_ppp_failure:
            status = "⚠️ NOMINAL TRAP (PPP_FAILURE)"
            signal_score = 0
            signal_reasons.append(f"PPP_Failure ({ppp_reason})")
        elif signal_score >= 8:
            status = "🐋 HIGH CONVICTION BUY"
        elif signal_score >= 6:
            status = "🔥 STRONG BUY"
        elif signal_score >= 4:
            status = "⚡ MODERATE BUY"
        elif institutional_signal:
            status = "🐺 INSTITUTIONAL ACTIVITY"
        elif breakout:
            if current_power > 0:
                status = "🔥 BREAKOUT - CONFIRMED"
            else:
                status = "⚡ BREAKOUT - WEAK"
        elif dist_percent < 2.0:
            status = "👀 WATCHLIST - NEAR RESISTANCE"
        else:
            status = "⏳ ACCUMULATION PHASE"

        try:
            snapshot = {
                **raw_snapshot,
                "rel_volume": float(current_rel_vol),
                "price_move_pct": float(current_price_move),
                "rsi": float(current_rsi),
                "estimated_spread": float(estimated_spread),
                "avg_turnover_usd": float(avg_turnover),
                "avg_turnover_egp": float(avg_turnover_egp),
                "is_manipulation": bool(is_manipulation),
                "manipulation_tag": str(manipulation_tag),
                "is_liquidity_trap": is_liquidity_trap,
                "is_ppp_failure": is_ppp_failure,
                "ppp_hurdle": hurdle_rate,
                "projected_return": float(projected_return),
                "avg_slippage_pct": float(avg_slippage_pct),
                "dynamic_max_spread": float(dynamic_max_spread),
            }
            kill_reason = None
            if is_manipulation:
                kill_reason = f"ManipulationSentry ({manipulation_reason})"
            elif is_liquidity_trap:
                kill_reason = f"LiquidityGuard ({', '.join(liquidity_trap_reasons)})"
            elif is_ppp_failure:
                kill_reason = f"PPP_Failure ({ppp_reason})"

            SignalStateArchive.create(
                ticker=ticker,
                timestamp=TimeUtils.now(),
                final_status=status,
                signal_score=signal_score,
                filter_snapshot_json=json.dumps(snapshot),
                kill_reason=kill_reason,
                signal_id=signal_id,
            )
        except Exception as audit_err:
            print(f"❌ Error creating SignalStateArchive for {ticker}: {audit_err}")

        mult = current_rate if currency == "EGP" else 1.0

        return {
            "Ticker": ticker,
            "Currency": currency,
            "Status": status,
            "Signal_Score": signal_score,
            "Signal_Reasons": ", ".join(signal_reasons) if signal_reasons else "None",
            "Trend": trend_direction,
            "Price": round(current_price * mult, 2),
            "EMA9": round(current_ema9 * mult, 2),
            "RSI": round(current_rsi, 1),
            "Rel_Volume": round(current_rel_vol, 2),
            "Price_Move_%": round(current_price_move, 2),
            "Avg_Turnover_M": round(avg_turnover_egp / 1_000_000, 2),
            "Estimated_Spread_%": round(estimated_spread * 100, 2),
            "Institutional_Signal": "✅" if institutional_signal else "❌",
            "Resistance_20D": round(resistance_20d * mult, 2),
            "Key_Resistance_1": round(key_res_1 * mult, 2),
            "Key_Resistance_2": round(key_res_2 * mult, 2),
            "Distance_%": round(dist_percent, 2),
            "Key_Res_1_Dist_%": round(key_res_1_dist_pct, 2),
            "Key_Res_2_Dist_%": round(key_res_2_dist_pct, 2),
            "ATR": round(current_atr * mult, 2),
            "Force_Power": round(current_power, 0) if not pd.isna(current_power) else 0,
            "Stop_Loss": round(stop_loss * mult, 2),
            "Target_1": round(target_1 * mult, 2),
            "Target_2": round(target_2 * mult, 2),
            "Target_3": round(target_3 * mult, 2),
            "Target_4": round(target_4 * mult, 2),
            "Risk_Reward_Ratio": round((target_2 - current_price) / risk_amount, 2) if risk_amount > 0 else 0,
            "PPP_Hurdle_%": round(hurdle_rate, 2),
            "Projected_Return_%": round(projected_return, 2),
            "Manipulation_Flag": manipulation_tag if is_manipulation else "CLEAR",
            "Price_USD": round(current_price, 4),
            "Stop_Loss_USD": round(stop_loss, 4),
            "Target_1_USD": round(target_1, 4),
            "Target_2_USD": round(target_2, 4),
            "Target_3_USD": round(target_3, 4),
            "Target_4_USD": round(target_4, 4),
            "Signal_Id": signal_id,
        }

    except Exception as e:
        print(f"❌ Error in MomentumBreakoutScanner.analyze_stock({ticker}): {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_stock(file_path: str, include_live: bool | None = None) -> dict | None:
    """Analyze a single stock with integrated Pine Script (Loki) indicators"""
    if os.path.isfile(file_path):
        ticker = os.path.basename(file_path).replace(".csv", "")
    else:
        ticker = file_path

    from core.DataManager import DataManager
    df = DataManager.get_stock_data(ticker, include_live=_include_live_for_analysis(include_live))
    analyze_frame_fn = _get_active_module_attr("analyze_stock_frame", analyze_stock_frame)
    return analyze_frame_fn(ticker, df)


def scan_full_market(include_live: bool | None = None) -> list[dict]:
    """Scan all stocks in the data folder"""
    print(f"\n⚡ INITIATING FULL MARKET SCAN ⚡")
    print(f"📂 Data Folder: {DATA_FOLDER}")
    print(f"{'='*80}\n")

    files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    valid_files = [f for f in files if "Report" not in f and "xlsx" not in f]

    if not valid_files:
        from core.DataManager import DataManager
        tickers = DataManager.list_tickers()
        print(f"📊 No CSV files in data folder. Listing {len(tickers)} tickers via DataManager. Scanning in parallel...\n")
        ticker_paths = {ticker: ticker for ticker in tickers}
    else:
        print(f"📊 Found {len(valid_files)} files. Scanning in parallel...\n")
        tickers = [os.path.basename(f).replace(".csv", "") for f in valid_files]
        ticker_paths = {os.path.basename(f).replace(".csv", ""): f for f in valid_files}

    frames_by_ticker: dict[str, pd.DataFrame] = {}

    try:
        from core.DataManager import DataManager
        history_limit = max(140, MIN_DATA_POINTS, LOOKBACK + 20, VOL_AVG_PERIOD + 20)
        universe_df = DataManager.get_universe_data(
            tickers,
            include_live=_include_live_for_analysis(include_live),
            history_limit=history_limit,
        )
        if universe_df is not None and not universe_df.empty:
            frames_by_ticker = {
                str(ticker): frame
                for ticker, frame in universe_df.groupby(level=0, sort=False)
            }
            print(f"[Info] Preloaded {len(frames_by_ticker)} tickers via bulk data engine.")
    except Exception as exc:
        print(f"[Warning] Bulk preload failed; falling back to per-ticker reads: {exc}")

    results = []
    processed = 0

    max_workers = min(32, (os.cpu_count() or 1) * 2)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {}
        for ticker in tickers:
            frame = frames_by_ticker.get(ticker)
            if frame is not None:
                future = executor.submit(analyze_stock_frame, ticker, frame)
            else:
                path = ticker_paths.get(ticker)
                future = executor.submit(analyze_stock, path)
            future_to_ticker[future] = ticker

        for future in as_completed(future_to_ticker):
            try:
                result = future.result()
                if result:
                    results.append(result)

                processed += 1
                if processed % 50 == 0:
                    print(f"   ✅ Processed {processed} stocks...")
            except Exception as exc:
                t = future_to_ticker[future]
                print(f"❌ Error processing {t}: {exc}")

    print(f"\n✅ Analysis Complete! Processed {processed} stocks.\n")

    if results:
        df_results = pd.DataFrame(results)
        df_results.sort_values(
            by=['Signal_Score', 'Institutional_Signal', 'Risk_Reward_Ratio'],
            ascending=[False, False, False],
            inplace=True,
        )
        export_fn = _get_active_module_attr("export_scan_results_to_excel", export_scan_results_to_excel)
        export_fn(df_results)
    else:
        print("❌ No valid stocks found to analyze.")

    return results
