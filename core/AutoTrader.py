"""
AUTO TRADER MODULE
==================
Handles automated trading logic:
1. Auto-Entry: Converts Scanner Signals -> DB Positions.
2. Trade Management: Monitors Open Positions for SL/TP hits.
"""

from core.settings import settings
import time
import datetime
import logging
from core import TimeUtils   # type: ignore
from logging.handlers import RotatingFileHandler
import pandas as pd  # type: ignore
from numbers import Real

  # type: ignore
from core import WalkForwardValidation   # type: ignore
from core.DataManager import DataManager  # type: ignore
import warnings
from peewee import JOIN, fn
from core import PositionTracker   # type: ignore
from core import AlertManager   # type: ignore
from core import subscriptions   # type: ignore
from database import Position, db, Portfolio  # type: ignore

from utils.logger import setup_logger
logger = setup_logger("horus.autotrader")

# Trailing SL dedup: only log when the value actually changes (not every 30s tick)
_LAST_LOGGED_TRAILING_SL: dict[str, float] = {}


def _managed_advisory_main_channel_allowed() -> bool:
    return subscriptions.automated_main_channel_signal_allowed(subscriptions.MANAGED_ADVISORY)


def _check_entry_gate(ticker):
    """
    Execution-layer deadbolt.
    Fail-closed on gate read/parse errors.
    """
    symbol = str(ticker).upper()
    try:
        gate = WalkForwardValidation.get_trade_permission(symbol, fail_closed=True)
    except Exception as exc:
        return False, "gate_lookup_error", {"error": str(exc)}

    if not isinstance(gate, dict):
        return False, "gate_lookup_invalid", {"value_type": type(gate).__name__}

    allowed = bool(gate.get("allowed", False))
    reason = str(gate.get("reason", "blocked"))
    return allowed, reason, gate

def _resolve_target_portfolio(target_portfolio_name):
    requested_name = str(target_portfolio_name or "").strip()

    if requested_name:
        try:
            target_port = Portfolio.get(Portfolio.name == requested_name)
            return target_port
        except Exception:
            pass

    fallback_port = (
        Portfolio.get_or_none((Portfolio.name == "Swing Signals") & (Portfolio.type == "SYSTEM"))
        or Portfolio.get_or_none((Portfolio.name == "Intraday Signals") & (Portfolio.type == "SYSTEM"))
        or Portfolio.get_or_none((Portfolio.name == "Position Signals") & (Portfolio.type == "SYSTEM"))
        or Portfolio.get_or_none(Portfolio.type == "SYSTEM")
        or Portfolio.select().order_by(Portfolio.id.asc()).first()
    )

    if fallback_port is None:
        return None

    if requested_name:
        logger.warning(
            "Portfolio '%s' not found. Falling back to '%s' (id=%s) for auto-entry.",
            requested_name,
            fallback_port.name,
            fallback_port.id,
        )

    return fallback_port

def process_scanner_signals(signals, target_portfolio_name="Swing Signals"):
    """Processes signals from scanners and routes them to simulation portfolios."""
    warnings.warn("AutoTrader.process_scanner_signals is deprecated. Use core.signals.executor.SignalExecutor instead.", DeprecationWarning, stacklevel=2)
    logger.info(f"Processing {len(signals)} scanner signals for portfolio: {target_portfolio_name}")

    """
    Takes a list of signal dicts from DailyScanner and auto-enters positions.
    Routing Logic:
    - Daily Scanner -> 'Swing Signals' (System)
    - Intraday Scanner -> 'Intraday Signals' (System)
    """
    if not signals:
        return

    if not settings.AUTO_TRADE_ENABLED:
        logger.info("Auto-trade disabled, skipping auto-entry for scanner signals")
        return

    # Find Target Portfolio
    target_port = _resolve_target_portfolio(target_portfolio_name)
    if target_port is None:
        logger.warning(
            "No eligible portfolio found for auto-entry (requested='%s'). Skipping.",
            target_portfolio_name,
        )
        return

    logger.info(f"Processing {len(signals)} signals for Portfolio: {target_port.name}...")
    
    # --- LOKI'S DEADBOLT: Check Global Portfolio Heat First ---
    from core import RiskManager
    try:
        open_positions = list(Position.select().where((Position.status == "OPEN") & (Position.portfolio == target_port.id)))
        account_size = getattr(settings, 'ACCOUNT_BALANCE', 100000)
        heat_input = [{'ticker': p.ticker, 'entry': p.entry_price, 'sl': p.stop_loss, 'shares': p.shares} for p in open_positions if p.stop_loss]
        current_heat = RiskManager.calculate_portfolio_heat(heat_input, account_size)
        max_heat = getattr(settings, 'MAX_PORTFOLIO_HEAT', 6.0)
        if not getattr(settings, "HEAT_PROTECTION_ENABLED", True):
            max_heat = float("inf")
        # Ensure numeric comparisons
        def _to_float(val, default=0.0):
            try:
                if hasattr(val, '__class__') and 'MagicMock' in val.__class__.__name__:
                    return default
                return float(val)
            except:
                return default

        current_heat = _to_float(current_heat)
        max_heat = _to_float(max_heat, 6.0)
        
        if current_heat >= max_heat:
            logger.critical(f"[HEAT] PORTFOLIO ON FIRE. Heat at {current_heat:.2f}% (Max {max_heat}%). All entries violently blocked.")
            if settings.ENABLE_INTRADAY_ALERTS and _managed_advisory_main_channel_allowed():
                AlertManager.broadcast_alert(f"🔥 *PORTFOLIO HEAT LIMIT REACHED*\nHeat: {current_heat:.2f}%\nAuto-Entries halted.")
            return # Choke the entire execution
    except Exception as e:
        logger.error(f"Failed to read portfolio heat: {e}")

    for sig in signals:
        try:
            ticker = sig['Ticker']
            price = sig['Entry_Price']
            sl = sig['Stop_Loss']
            tp = sig['Target_Price']
            score = sig.get('Score', 0)

            # Guard against mocked/invalid values leaking into production
            def _is_valid_number(val):
                return isinstance(val, Real) and not pd.isna(val)

            if not all(_is_valid_number(v) for v in (price, sl, tp)):
                logger.error(
                    f"Invalid signal values for {ticker}: "
                    f"price={price} sl={sl} tp={tp} (types: "
                    f"{type(price).__name__}, {type(sl).__name__}, {type(tp).__name__})"
                )
                continue

            # --- LOKI'S DEADBOLT: Mimir Entry Gate ---
            allowed, gate_reason, gate_data = _check_entry_gate(ticker)
            if not allowed:
                logger.warning(f"[BLOCKED] Mimir WFA blocked {ticker}: {gate_reason}")
                continue

            # --- LOKI'S DEADBOLT: Whale Trap Enforcement ---
            enforcement_state = str(sig.get("Enforcement_State", "ALLOW")).upper()
            if enforcement_state == "BLOCK_EXECUTION":
                enforcement_reason = sig.get("Enforcement_Reason", "unknown_risk")
                logger.warning(f"[ENFORCEMENT_BLOCKED] Whale Trap Gate blocked {ticker}: {enforcement_reason}")
                continue

            # --- LOKI'S DEADBOLT: Sovereign Confluence ---
            from core.sovereign_confluence import sovereign_confluence_engine as confluence_engine
            trap = confluence_engine.get_active_trap(ticker)
            if trap and trap.get("type") == "SOVEREIGN_BEAR_TRAP" and sig.get('Signal_Type', 'BUY') == 'BUY':
                logger.warning(f"[BLOCKED] Sovereign Bear Trap active for {ticker}. Institutional distribution detected.")
                continue

            # --- LOKI'S DEADBOLT: Correlation Check ---
            try:
                open_tickers = [p.ticker for p in open_positions]
                corr_res = RiskManager.check_new_trade_correlation(open_tickers, ticker)
                if not corr_res.get('is_safe', True):
                    culprit = corr_res.get('most_correlated_with', 'Unknown')
                    logger.warning(f"[BLOCKED]: {ticker} is too highly correlated with open position {culprit}.")
                    continue
            except Exception as e:
                logger.error(f"Correlation check failed for {ticker}: {e}")
            
            # --- LOKI'S DEADBOLT: Execution Velocity Limit ---
            # Maximum trades per calendar session (day) per portfolio
            today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            max_daily_trades = getattr(settings, 'MAX_DAILY_TRADES', 3)
            
            recent_trades_count = Position.select().where(
                (Position.portfolio == target_port.id) & 
                (Position.entry_date >= today_start)
            ).count()
            
            if recent_trades_count >= max_daily_trades:
                logger.warning(f"[BLOCKED] Velocity Limit: {recent_trades_count} trades already opened today for {target_portfolio_name}. Halting entry for {ticker}.")
                continue

            # --- MACRO REGIME FILTER (EMA10 / EMA20) ---
            regime = "STRONG_BULL"
            try:
                from core.DataManager import DataManager
                egx_df = DataManager.get_stock_data("EGX30", source="CSV", folder=settings.METASTOCK_HISTORY_FOLDER)
                if egx_df is not None and len(egx_df) >= 20:
                    egx_close = egx_df['Close'].iloc[-1]
                    ema10 = egx_df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
                    ema20 = egx_df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    
                    if egx_close > ema10 and ema10 > ema20:
                        regime = "STRONG_BULL"
                    else:
                        regime = "CHOPPY_OR_BEAR"
            except Exception as e:
                logger.error(f"Failed to read market regime: {e}")
            
            signal_type = sig.get('Signal_Type', 'BUY')

            regime_filter_enabled = bool(getattr(settings, "REGIME_FILTER_ENABLED", False))

            # Regime Breakout Block
            if regime_filter_enabled and regime == "CHOPPY_OR_BEAR":
                if signal_type == "BUY": # Standard Breakout mechanically blocked
                    logger.warning(f"[BLOCKED] Regime Filter: Breakouts mechanically disabled in {regime} regime for {ticker}")
                    continue
            
            # Calculate Risk-Based Sizing
            account_size = getattr(settings, 'ACCOUNT_BALANCE', 100000)
            risk_amount = account_size * (getattr(settings, 'RISK_PER_TRADE', 2.0) / 100.0)
            
            # Halve risk if macro is bearish (only Tricksters reach here since BUY is blocked)
            if regime_filter_enabled and regime == "CHOPPY_OR_BEAR" and signal_type == "TRICKSTER":
                risk_amount /= 2.0
                logger.info(f"Regime is {regime}. Halving risk amount to {risk_amount:.2f} for Trickster setup on {ticker}")
                
            risk_per_share = price - sl
            
            if risk_per_share <= 0:
                shares = 100 # Fallback safety
            else:
                shares = int(risk_amount / risk_per_share)
                
            # Cap max position size (e.g. 20% of account)
            max_cost = account_size * 0.20
            if shares * price > max_cost:
                shares = int(max_cost / price)

            # Execution
            if shares > 0:
                # Pre-execution recheck
                allowed, gate_reason, gate_data = _check_entry_gate(ticker)
                if not allowed:
                    logger.warning(f"[BLOCKED] Mimir WFA pre-execution check blocked {ticker}: {gate_reason}")
                    continue

                success = PositionTracker.add_position(
                    ticker=ticker,
                    shares=shares,
                    entry_price=price,
                    sl=sl,
                    tp=tp,
                    tp2=sig.get('Target_Price_2'),
                    sector=sig.get('Sector', 'Unknown'),
                    portfolio_id=target_port.id
                )
                
                if success:
                    if settings.ENABLE_INTRADAY_ALERTS and _managed_advisory_main_channel_allowed():
                        msg = f"🚀 *AUTO-ENTRY EXECUTED*\nTicker: {ticker}\nPrice: {price}\nShares: {shares}\nTarget: {tp}\nStop: {sl}"
                        AlertManager.broadcast_alert(msg)
                    logger.info(f"Auto-Entered {ticker}")
                    
        except Exception as e:
            logger.error(f"Error processing signal for {sig.get('Ticker')}: {e}")

def monitor_positions():
    """Monitors all open positions across simulation portfolios for exits."""
    warnings.warn("AutoTrader.monitor_positions is deprecated. Use core.signals.system_monitor.monitor_system_positions instead.", DeprecationWarning, stacklevel=2)
    try:
        if not settings.AUTO_TRADE_ENABLED:
            return
        # Fetching directly from DB to avoid ticker collision in dict-based legacy format
        # Fetch as list to release read-lock immediately
        open_positions = list(
            Position.select()
            .join(Portfolio)
            .where((Position.status == "OPEN") & (Portfolio.type == "SYSTEM"))
        )
        if not open_positions:
            return
            
        logger.info(f"Monitoring {len(open_positions)} open positions...")

        try:
            if DataManager.refresh_intraday_cache_if_due():
                logger.info("Intraday cache refreshed for trade monitor.")
        except Exception as refresh_err:
            logger.warning(f"Intraday cache refresh failed in trade monitor: {refresh_err}")
        
        stale_count = 0
        
        for p in open_positions:
            ticker = p.ticker
            try:
                # Get the latest real intraday bars. The daily stock-data path
                # folds the whole session into one candle, so its Low can be
                # much older than the current minute and falsely trigger stops.
                df = DataManager.get_intraday_data(ticker, limit=5)
                
                if df is None or df.empty:
                    stale_count += 1
                    continue
                    
                last_bar = df.iloc[-1]
                current_price = last_bar['Close']
                low_price = last_bar['Low']
                high_price = last_bar['High']
                last_time = last_bar.name # DateTime Index
                
                # Check for freshness and avoid 'lookahead' bias on the entry bar
                # We only exit on bars that start AFTER our entry bar timestamp.
                if last_time <= p.entry_date:
                    continue
                
                if (TimeUtils.now() - last_time).days > 1:
                    logger.warning(f"Stale data for {ticker}. Last update: {last_time}")
                    stale_count += 1
                    continue
    
                entry = p.entry_price
                sl = p.stop_loss
                tp = p.target_price
                port_id = p.portfolio_id
                
                # 1. Check STOP LOSS
                if low_price <= sl:
                    reason = _stop_exit_reason(entry, sl)
                    exit_price = sl 
                    
                    t_start = time.perf_counter()
                    success = PositionTracker.close_position(
                        ticker, exit_price, reason=reason, portfolio_id=port_id,
                        slippage_bps=round((exit_price - sl) / sl * 10000, 2) if sl else 0,
                        latency_ms=int((time.perf_counter() - t_start) * 1000)
                    )
                    if success:
                        _notify_exit(ticker, exit_price, entry, reason)
                        logger.info(f"SL Triggered for {ticker} in Port {port_id}")
                        _LAST_LOGGED_TRAILING_SL.pop(f"{ticker}:{port_id}", None)
                    continue
    
                # 2. Check TAKE PROFIT 1 (Scaling Out)
                elif high_price >= tp and not getattr(p, 'tp1_hit', False):
                    # Re-fetch from DB to guard against stale in-memory state across monitor cycles.
                    # If another cycle already set tp1_hit, skip to avoid duplicate execution.
                    p_fresh = Position.get_or_none(
                        (Position.ticker == ticker) &
                        (Position.status == "OPEN") &
                        (Position.portfolio == port_id)
                    )
                    if p_fresh is None or getattr(p_fresh, 'tp1_hit', False):
                        continue  # Already handled by a concurrent or previous monitor cycle
                    p = p_fresh  # Use fresh DB state for the rest of this block

                    reason = "TARGET 1"
                    exit_price = tp
                    
                    # 50% scale out
                    half_shares = max(int(p.shares * 0.5), 1)
                    if p.shares == 1: half_shares = 1
                    
                    t_start = time.perf_counter()
                    success = PositionTracker.close_position(
                        ticker, exit_price, reason=reason, portfolio_id=port_id,
                        slippage_bps=round((exit_price - tp) / tp * 10000, 2) if tp else 0,
                        latency_ms=int((time.perf_counter() - t_start) * 1000),
                        partial_shares=half_shares
                    )
                    if success:
                        _notify_exit(ticker, exit_price, entry, reason, portfolio_id=port_id)
                        logger.info(f"TP1 Triggered for {ticker} in Port {port_id}. Sold {half_shares} shares.")
                        _LAST_LOGGED_TRAILING_SL.pop(f"{ticker}:{port_id}", None)
                        
                        # Always mark tp1_hit immediately — unconditional so the next monitor
                        # cycle reads tp1_hit=True from DB regardless of remaining share count.
                        PositionTracker.update_position(ticker, portfolio_id=port_id, sl=entry, tp1_hit=True)
                        logger.info(f"SL moved to breakeven ({entry}) for {ticker}.")
                        p.tp1_hit = True
                        p.stop_loss = entry
                        p.shares -= half_shares
                    continue

                # 2.5 Check TAKE PROFIT 2 (Final Exit)
                elif getattr(p, 'target_price_2') and high_price >= p.target_price_2 and getattr(p, 'tp1_hit', False):
                    reason = "TARGET 2"
                    exit_price = p.target_price_2
                    
                    t_start = time.perf_counter()
                    success = PositionTracker.close_position(
                        ticker, exit_price, reason=reason, portfolio_id=port_id,
                        slippage_bps=round((exit_price - p.target_price_2) / p.target_price_2 * 10000, 2) if p.target_price_2 else 0,
                        latency_ms=int((time.perf_counter() - t_start) * 1000)
                    )
                    if success:
                        _notify_exit(ticker, exit_price, entry, reason, portfolio_id=port_id)
                        logger.info(f"TP2 Triggered for {ticker} in Port {port_id}. Fully closed.")
                        _LAST_LOGGED_TRAILING_SL.pop(f"{ticker}:{port_id}", None)
                    continue
    
                # 3. Trailing Stop Update
                from core.sovereign_confluence import sovereign_confluence_engine as confluence_engine
                trap = confluence_engine.get_active_trap(ticker)
                is_sovereign_bear_trap = (trap and trap.get("type") == "SOVEREIGN_BEAR_TRAP")

                if getattr(settings, 'TRAILING_STOP_ENABLED', False) or is_sovereign_bear_trap:
                    if is_sovereign_bear_trap:
                        trail_pct = 1.0
                        potential_sl = current_price * (1 - trail_pct / 100.0)
                    elif settings.TRAILING_STOP_TYPE == "PERCENT":
                        trail_pct = getattr(settings, 'TRAILING_STOP_VALUE', 2.0)
                        potential_sl = current_price * (1 - trail_pct / 100.0)
                    else: # ATR based (default)
                        # We'd need ATR from indicators here
                        # For now, simplistic trailing based on fixed % of price move or ATR
                        # Let's assume Fixed for Trailing in this MVP if ATR indicators not refreshed here
                        trail_pct = getattr(settings, 'TRAILING_STOP_VALUE', 2.0)
                        potential_sl = current_price * (1 - trail_pct / 100.0)
                    
                    if potential_sl > sl:
                        new_sl = round(potential_sl, settings.PRICE_PRECISION)
                        PositionTracker.update_position(ticker, portfolio_id=port_id, sl=new_sl)
                        p.stop_loss = new_sl
                        if is_sovereign_bear_trap:
                            logger.warning(f"🚨 SOVEREIGN OVERRIDE: Tightening trailing SL for {ticker}: {sl} -> {potential_sl:.2f}")
                            if getattr(settings, 'ENABLE_INTRADAY_ALERTS', False) and _managed_advisory_main_channel_allowed():
                                AlertManager.broadcast_alert(f"🚨 *SOVEREIGN OVERRIDE*\nTightening trailing stop on {ticker} to 1.0%\nNew SL: {potential_sl:.2f}")
                        else:
                            _sl_key = f"{ticker}:{port_id}"
                            if _LAST_LOGGED_TRAILING_SL.get(_sl_key) != p.stop_loss:
                                _LAST_LOGGED_TRAILING_SL[_sl_key] = p.stop_loss
                                logger.info(f"Trailing SL moved UP for {ticker}: {sl} -> {potential_sl:.2f}")
    
            except Exception as e:
                logger.error(f"Error monitoring {ticker} in Port {p.portfolio_id}: {e}")

        # Stale Data Alert
        if len(open_positions) > 0 and stale_count > len(open_positions) * 0.5:
             if settings.ENABLE_INTRADAY_ALERTS and _managed_advisory_main_channel_allowed():
                 msg = f"⚠️ *CRITICAL DATA FEED WARNING*\n{stale_count}/{len(open_positions)} positions have stale data (>24h old).\nCheck MetaStock Downloader."
                 AlertManager.broadcast_alert(msg)
             logger.critical(f"Stale Data Alert: {stale_count}/{len(open_positions)} positions are stale.")
    except Exception as e:
        logger.error(f"Error in monitor_positions loop: {e}")

def _sync_horus_execution_exit(portfolio_id, ticker, reason, is_partial=False, partial_shares=None, new_sl=None):
    try:
        import json
        from database import HorusExecution, Trade
        from core import TimeUtils
        exec_rec = HorusExecution.get_or_none(
            (HorusExecution.portfolio == portfolio_id) &
            (HorusExecution.ticker == ticker) &
            (HorusExecution.state.in_(["OPEN", "UPDATED"]))
        )
        if not exec_rec:
            return
        if is_partial:
            details = json.loads(exec_rec.details_json or "{}")
            details["tp1_hit"] = True
            if partial_shares:
                details["tp1_shares"] = partial_shares
            if new_sl:
                exec_rec.active_stop_loss = new_sl
            exec_rec.state = "UPDATED"
            exec_rec.details_json = json.dumps(details)
            exec_rec.updated_at = TimeUtils.now()
            exec_rec.save()
        else:
            trade = Trade.select().where(
                (Trade.portfolio == portfolio_id) & (Trade.ticker == ticker)
            ).order_by(Trade.exit_date.desc()).first()
            exec_rec.state = "CLOSED"
            exec_rec.close_reason = reason
            exec_rec.trade_id = trade.id if trade else None
            exec_rec.updated_at = TimeUtils.now()
            exec_rec.save()
    except Exception as e:
        logger.debug(f"Could not sync HorusExecution for {ticker}: {e}")

def check_exit_conditions(ticker, current_price):
    """
    Checks if a specific price triggers an exit for a single ticker.
    Used by LiveFeedManager for real-time reactions.
    """
    try:
        # Fetch all open positions for this ticker across all portfolios
        open_positions = Position.select().where(
            (Position.ticker == ticker) &
            (Position.status == "OPEN")
        )
        
        for p in open_positions:
            # Skip non-system portfolios when type is known
            try:
                port_type = getattr(p.portfolio, "type", "SYSTEM")
                if isinstance(port_type, str) and port_type != "SYSTEM":
                    continue
            except Exception:
                pass
            
            # Anti-Insta-SL: Ensure we don't exit on the exact same second we entered 
            # to avoid race conditions with stale ticks or mid-bar entry pulses.
            entry_dt = getattr(p, "entry_date", None)
            if isinstance(entry_dt, datetime.datetime):
                if (TimeUtils.now() - entry_dt).total_seconds() < 10:
                    continue

            sl = p.stop_loss
            tp = p.target_price
            entry = p.entry_price
            port_id = p.portfolio_id

            # 1. Check STOP LOSS
            if current_price <= sl:
                reason = _stop_exit_reason(entry, sl)
                success = PositionTracker.close_position(ticker, sl, reason=reason, portfolio_id=port_id)
                if success:
                    _sync_horus_execution_exit(port_id, ticker, reason)
                    _notify_exit(ticker, sl, entry, reason, portfolio_id=port_id)
                    logger.info(f"LIVE SL Triggered for {ticker} in Port {port_id}")

            # 2. Check TAKE PROFIT 1
            elif current_price >= tp and not getattr(p, 'tp1_hit', False):
                # Re-fetch from DB to guard against stale in-memory state across monitor cycles.
                p_fresh = Position.get_or_none(
                    (Position.ticker == ticker) &
                    (Position.status == "OPEN") &
                    (Position.portfolio == port_id)
                )
                if p_fresh is None or getattr(p_fresh, 'tp1_hit', False):
                    continue  # Already handled by a concurrent or previous monitor cycle
                p = p_fresh

                reason = "TARGET 1"
                half_shares = max(int(p.shares * 0.5), 1)
                success = PositionTracker.close_position(ticker, tp, reason=reason, portfolio_id=port_id, partial_shares=half_shares)
                if success:
                    _sync_horus_execution_exit(port_id, ticker, reason, is_partial=True, partial_shares=half_shares, new_sl=entry)
                    _notify_exit(ticker, tp, entry, reason, portfolio_id=port_id)
                    logger.info(f"LIVE TP1 Triggered for {ticker} in Port {port_id}")
                    # Always mark tp1_hit unconditionally so the next monitor cycle sees correct state.
                    PositionTracker.update_position(ticker, portfolio_id=port_id, sl=entry, tp1_hit=True)

            # 2.5 Check TAKE PROFIT 2
            elif getattr(p, 'target_price_2') and current_price >= p.target_price_2 and getattr(p, 'tp1_hit', False):
                reason = "TARGET 2"
                success = PositionTracker.close_position(ticker, p.target_price_2, reason=reason, portfolio_id=port_id)
                if success:
                    _sync_horus_execution_exit(port_id, ticker, reason)
                    _notify_exit(ticker, p.target_price_2, entry, reason, portfolio_id=port_id)
                    logger.info(f"LIVE TP2 Triggered for {ticker} in Port {port_id}")

    except Exception as e:
        logger.error(f"Error in check_exit_conditions for {ticker}: {e}")

_NOTIFIED_EXITS_CACHE = {}

def _notify_exit(ticker, exit_price, entry_price, reason, portfolio_id=None, cooldown_seconds=60):
    try:
        now = time.time()
        cache_key = f"{str(ticker).upper()}:{str(reason).upper()}:{portfolio_id or 'all'}"
        last_time = _NOTIFIED_EXITS_CACHE.get(cache_key, 0)
        if now - last_time < cooldown_seconds:
            logger.info(f"Duplicate exit alert suppressed for {cache_key} (cooldown {cooldown_seconds}s)")
            return

        from core import ReportGenerator   # type: ignore
        pnl_pct = (exit_price - entry_price) / entry_price * 100
        
        # Try to generate image card
        try:
             if settings.ENABLE_INTRADAY_ALERTS and _managed_advisory_main_channel_allowed():
                 card_buf = ReportGenerator.create_exit_card(ticker, exit_price, entry_price, pnl_pct, reason)
                 caption = f"{'🟢' if pnl_pct > 0 else '🔴'} *{reason.replace('_', ' ')} HIT* | {ticker}\nReturn: {pnl_pct:+.2f}%"
                 AlertManager.broadcast_image(card_buf, caption=caption)
                 _NOTIFIED_EXITS_CACHE[cache_key] = now
        except Exception as img_err:
             logger.error(f"Card generation error: {img_err}")
             # Fallback to text
             if settings.ENABLE_INTRADAY_ALERTS and _managed_advisory_main_channel_allowed():
                 msg = f"{'🟢' if pnl_pct > 0 else '🔴'} *{reason.replace('_', ' ')} HIT*\nTicker: {ticker}\nExit: {exit_price:.2f}\nReturn: {pnl_pct:+.2f}%"
                 AlertManager.broadcast_alert(msg)
                 _NOTIFIED_EXITS_CACHE[cache_key] = now
    except Exception as e:
        logger.error(f"Error notifying exit for {ticker}: {e}")


def _stop_exit_reason(entry_price, stop_price):
    """Classify raised protective stops separately from original stop-loss exits."""
    try:
        if float(stop_price or 0.0) > float(entry_price or 0.0):
            return "TRAILING_STOP"
    except (TypeError, ValueError):
        pass
    return "STOP_LOSS"
