from core.settings import settings
import json
import logging
import time
from typing import Any, Optional, List

from core import PositionTracker, TelegramBot_Alerts, TimeUtils, AlertManager, ReportGenerator
from core import subscriptions
from core.DataManager import DataManager
from database import HorusExecution, Position, Portfolio, Trade
from core.horus.telegram import build_close_message

logger = logging.getLogger('SystemMonitor')

class SystemMonitor:
    @staticmethod
    def _managed_advisory_main_channel_allowed() -> bool:
        return subscriptions.automated_main_channel_signal_allowed(subscriptions.MANAGED_ADVISORY)

    @staticmethod
    def _broadcast_managed_alert(message: str) -> dict:
        if not SystemMonitor._managed_advisory_main_channel_allowed():
            logger.info("[SystemMonitor] Managed alert suppressed by channel policy.")
            return {"ok": False, "suppressed": True, "description": "managed_advisory_channel_policy"}
        return AlertManager.broadcast_alert(message)

    @staticmethod
    def monitor_system_positions() -> dict:
        """Unified monitor for all SYSTEM portfolios."""
        try:
            if not settings.AUTO_TRADE_ENABLED:
                return {"status": "skipped", "message": "Auto-trade disabled"}

            try:
                if DataManager.refresh_intraday_cache_if_due():
                    logger.info("Intraday cache refreshed for trade monitor.")
            except Exception as refresh_err:
                logger.warning(f"Intraday cache refresh failed in trade monitor: {refresh_err}")

            # 1. Fetch all OPEN positions in SYSTEM portfolios and Horus portfolio
            open_positions = list(
                Position.select()
                .join(Portfolio)
                .where((Position.status == "OPEN") & ((Portfolio.type == "SYSTEM") | (Portfolio.name == "Horus")))
            )
            
            if not open_positions:
                return {"status": "completed", "summary": {"closed": 0, "updated": 0, "failed": 0, "stale": 0}}

            summary = {"closed": 0, "updated": 0, "failed": 0, "stale": 0}
            
            for pos in open_positions:
                try:
                    # 2. Link or create execution record for tracking
                    execution = SystemMonitor._get_or_create_execution(pos)
                    if not execution: continue

                    # 3. Get latest data
                    bar_data = SystemMonitor._get_latest_bar(pos.ticker)
                    if not bar_data:
                        summary["stale"] += 1
                        continue
                    
                    last_bar, bar_time = bar_data
                    
                    # 4. Freshness & Lookahead checks
                    if bar_time <= pos.entry_date: continue
                    if (TimeUtils.now() - bar_time).days > 1:
                        summary["stale"] += 1
                        continue

                    # 5. Core Monitoring Logic
                    low = float(last_bar['Low'])
                    high = float(last_bar['High'])
                    close = float(last_bar['Close'])
                    
                    # Update local state for checks
                    active_sl = float(execution.active_stop_loss or pos.stop_loss or 0.0)
                    active_tp1 = float(execution.active_target_price or pos.target_price or 0.0)
                    tp2 = float(pos.target_price_2 or 0.0)
                    tp1_hit = getattr(pos, 'tp1_hit', False)

                    # A. Stop Loss
                    if low <= active_sl:
                        reason = SystemMonitor._resolve_stop_reason(pos, execution)
                        if SystemMonitor._close_execution(pos, execution, active_sl, reason):
                            summary["closed"] += 1
                        else:
                            summary["failed"] += 1
                        continue

                    # B. Take Profit 1 (Scale out 50%)
                    if high >= active_tp1 and not tp1_hit and active_tp1 > 0:
                        if SystemMonitor._handle_tp1(pos, execution, active_tp1):
                            summary["updated"] += 1
                        else:
                            summary["failed"] += 1
                        continue

                    # C. Take Profit 2 (Full close)
                    if tp1_hit and tp2 > 0 and high >= tp2:
                        if SystemMonitor._close_execution(pos, execution, tp2, "TARGET_2"):
                            summary["closed"] += 1
                        else:
                            summary["failed"] += 1
                        continue

                    # D. Trailing Stop Ratchet
                    if SystemMonitor._check_trailing_ratchet(pos, execution, close):
                        summary["updated"] += 1

                except Exception as e:
                    logger.error(f"Error monitoring {pos.ticker} (Port {pos.portfolio_id}): {e}")
                    summary["failed"] += 1

            # 6. Global Stale Data Alert
            if len(open_positions) > 0 and summary["stale"] > len(open_positions) * 0.5:
                SystemMonitor._broadcast_managed_alert(f"⚠️ *CRITICAL DATA FEED WARNING*\n{summary['stale']}/{len(open_positions)} positions have stale data.\nCheck MetaStock Downloader.")

            return {"status": "completed", "summary": summary}
        except Exception as e:
            logger.error(f"Global monitor error: {e}")
            return {"status": "error", "message": str(e)}

    # --- Internal Helpers ---

    @staticmethod
    def _get_or_create_execution(pos: Position) -> Optional[HorusExecution]:
        """Ensures every monitored position has a linked HorusExecution record."""
        exec_rec = HorusExecution.select().where(
            (HorusExecution.portfolio == pos.portfolio) & 
            (HorusExecution.ticker == pos.ticker) & 
            (HorusExecution.state.in_(["OPEN", "UPDATED"]))
        ).first()
        
        if not exec_rec:
            # Create on-the-fly for legacy/migrated positions
            exec_rec = HorusExecution.create(
                portfolio=pos.portfolio,
                ticker=pos.ticker,
                state="OPEN",
                trigger_source="LEGACY_MONITOR",
                planned_entry_price=pos.entry_price,
                actual_entry_price=pos.entry_price,
                active_stop_loss=pos.stop_loss,
                active_target_price=pos.target_price,
                details_json=json.dumps({"migrated": True, "shares": pos.shares}),
                created_at=pos.entry_date or TimeUtils.now(),
                updated_at=TimeUtils.now()
            )
        return exec_rec

    @staticmethod
    def _get_latest_bar(ticker: str):
        try:
            df = DataManager.get_intraday_data(ticker, limit=5)
            if df is not None and not df.empty:
                return df.iloc[-1], df.index[-1]
        except Exception as e:
            logger.debug(f"Failed to get latest bar for {ticker}: {e}", exc_info=True)
        return None

    @staticmethod
    def _resolve_stop_reason(pos: Position, execution: HorusExecution) -> str:
        # If active_sl is higher than planned entry/stop, it's a trailing stop or breakeven
        planned_sl = float(execution.planned_entry_price or 0.0) # Conservative
        if execution.recommendation:
            planned_sl = float(execution.recommendation.stop_loss or planned_sl)
        
        current_sl = float(execution.active_stop_loss or pos.stop_loss or 0.0)
        if current_sl > planned_sl:
            return "TRAILING_STOP"
        return "STOP_LOSS"

    @staticmethod
    def _handle_tp1(pos: Position, execution: HorusExecution, price: float) -> bool:
        shares_to_sell = max(int(pos.shares * 0.5), 1)
        if pos.shares == 1: shares_to_sell = 1
        
        success = PositionTracker.close_position(
            pos.ticker, price, reason="TARGET_1", 
            portfolio_id=pos.portfolio_id, partial_shares=shares_to_sell
        )
        
        if success:
            # Move SL to breakeven
            PositionTracker.update_position(pos.ticker, portfolio_id=pos.portfolio_id, sl=pos.entry_price, tp1_hit=True)
            
            # Update execution record
            details = json.loads(execution.details_json or "{}")
            details["tp1_hit"] = True
            details["tp1_shares"] = shares_to_sell
            execution.active_stop_loss = pos.entry_price
            execution.state = "UPDATED"
            execution.details_json = json.dumps(details)
            execution.updated_at = TimeUtils.now()
            execution.save()
            
            # Notify
            SystemMonitor._notify_exit(pos.ticker, price, pos.entry_price, 0.0, "TARGET_1")
            return True
        return False

    @staticmethod
    def _close_execution(pos: Position, execution: HorusExecution, price: float, reason: str) -> bool:
        success = PositionTracker.close_position(pos.ticker, price, reason=reason, portfolio_id=pos.portfolio_id)
        if not success: return False

        trade = Trade.select().where((Trade.portfolio == pos.portfolio) & (Trade.ticker == pos.ticker)).order_by(Trade.exit_date.desc()).first()
        
        execution.state = "CLOSED"
        execution.close_reason = reason
        execution.trade_id = trade.id if trade else None
        execution.updated_at = TimeUtils.now()
        execution.save()

        # Final Notification
        pnl = trade.pnl_pct if trade else 0.0
        SystemMonitor._notify_exit(pos.ticker, price, pos.entry_price, pnl, reason, execution, trade)
        return True

    @staticmethod
    def _check_trailing_ratchet(pos: Position, execution: HorusExecution, close_price: float) -> bool:
        from core.sovereign_confluence import sovereign_confluence_engine as confluence_engine
        trap = confluence_engine.get_active_trap(pos.ticker)
        is_sovereign_bear = (trap and trap.get("type") == "SOVEREIGN_BEAR_TRAP")
        
        enabled = getattr(settings, 'TRAILING_STOP_ENABLED', False) or is_sovereign_bear
        if not enabled: return False

        trail_pct = 1.0 if is_sovereign_bear else float(getattr(settings, 'TRAILING_STOP_VALUE', 2.0))
        potential_sl = close_price * (1 - trail_pct / 100.0)
        current_sl = float(execution.active_stop_loss or pos.stop_loss or 0.0)

        if potential_sl > current_sl:
            PositionTracker.update_position(pos.ticker, portfolio_id=pos.portfolio_id, sl=potential_sl)
            
            execution.active_stop_loss = potential_sl
            trailing_state = {
                "previous_sl": current_sl,
                "current_sl": potential_sl,
                "updated_at": TimeUtils.now().isoformat(),
                "reason": "SOVEREIGN_BEAR" if is_sovereign_bear else "NORMAL_TRAIL"
            }
            execution.trailing_state = json.dumps(trailing_state)
            execution.updated_at = TimeUtils.now()
            execution.save()
            
            if is_sovereign_bear:
                SystemMonitor._broadcast_managed_alert(f"🚨 *SOVEREIGN OVERRIDE*\nTightening trailing stop on {pos.ticker} to 1.0%\nNew SL: {potential_sl:.2f}")
            return True
        return False

    @staticmethod
    def _notify_exit(ticker, price, entry, pnl, reason, execution=None, trade=None):
        if not SystemMonitor._managed_advisory_main_channel_allowed():
            logger.info("[SystemMonitor] Exit alert suppressed by managed-advisory channel policy for %s.", ticker)
            return

        try:
            # 1. Try to send image card via ReportGenerator
            card = ReportGenerator.create_exit_card(ticker, price, entry, pnl, reason)
            caption = f"{'🟢' if pnl > 0 else '🔴'} *{reason.replace('_', ' ')} HIT* | {ticker}\nReturn: {pnl:+.2f}%"
            AlertManager.broadcast_image(card, caption=caption)
        except Exception:
            # 2. Fallback to text message
            if execution and trade:
                TelegramBot_Alerts.send_message(build_close_message(execution.portfolio, execution, trade))
            else:
                AlertManager.broadcast_alert(f"{'🟢' if pnl > 0 else '🔴'} *{reason.replace('_', ' ')} HIT*\nTicker: {ticker}\nExit: {price:.2f}\nReturn: {pnl:+.2f}%")

    @staticmethod
    def check_exit_conditions(ticker: str, current_price: float):
        """
        Checks if a specific price triggers an exit for a single ticker.
        Used for real-time reactions and tick-level checks.
        """
        import datetime
        try:
            ticker = str(ticker).upper()
            open_positions = list(
                Position.select().where(
                    (Position.ticker == ticker) &
                    (Position.status == "OPEN")
                )
            )
            for p in open_positions:
                try:
                    port_type = getattr(p.portfolio, "type", "SYSTEM")
                    if isinstance(port_type, str) and port_type != "SYSTEM":
                        continue
                except Exception:
                    pass

                entry_dt = getattr(p, "entry_date", None)
                if isinstance(entry_dt, datetime.datetime):
                    if (TimeUtils.now() - entry_dt).total_seconds() < 10:
                        continue

                sl = float(p.stop_loss or 0.0)
                tp = float(p.target_price or 0.0)
                entry = float(p.entry_price or 0.0)
                port_id = p.portfolio_id

                execution = SystemMonitor._get_or_create_execution(p)

                # 1. Stop Loss
                active_sl = float(execution.active_stop_loss if execution else sl) or sl
                if current_price <= active_sl:
                    reason = SystemMonitor._resolve_stop_reason(p, execution) if execution else ("TRAILING_STOP" if active_sl > entry else "STOP_LOSS")
                    if execution:
                        SystemMonitor._close_execution(p, execution, active_sl, reason)
                    else:
                        PositionTracker.close_position(ticker, active_sl, reason=reason, portfolio_id=port_id)
                        SystemMonitor._notify_exit(ticker, active_sl, entry, (active_sl - entry) / entry * 100 if entry else 0.0, reason)
                    logger.info("LIVE SL Triggered for %s in Port %s", ticker, port_id)

                # 2. Take Profit 1
                elif current_price >= tp and not getattr(p, "tp1_hit", False) and tp > 0:
                    p_fresh = Position.get_or_none(
                        (Position.ticker == ticker) &
                        (Position.status == "OPEN") &
                        (Position.portfolio == port_id)
                    )
                    if p_fresh is None or getattr(p_fresh, "tp1_hit", False):
                        continue
                    if execution:
                        SystemMonitor._handle_tp1(p_fresh, execution, tp)
                    else:
                        half_shares = max(int(p_fresh.shares * 0.5), 1)
                        PositionTracker.close_position(ticker, tp, reason="TARGET 1", portfolio_id=port_id, partial_shares=half_shares)
                        PositionTracker.update_position(ticker, portfolio_id=port_id, sl=entry, tp1_hit=True)
                        SystemMonitor._notify_exit(ticker, tp, entry, (tp - entry) / entry * 100 if entry else 0.0, "TARGET 1")
                    logger.info("LIVE TP1 Triggered for %s in Port %s", ticker, port_id)

                # 3. Take Profit 2
                elif getattr(p, "target_price_2", None) and current_price >= float(p.target_price_2) and getattr(p, "tp1_hit", False):
                    tp2 = float(p.target_price_2)
                    if execution:
                        SystemMonitor._handle_tp2(p, execution, tp2)
                    else:
                        PositionTracker.close_position(ticker, tp2, reason="TARGET 2", portfolio_id=port_id)
                        SystemMonitor._notify_exit(ticker, tp2, entry, (tp2 - entry) / entry * 100 if entry else 0.0, "TARGET 2")
                    logger.info("LIVE TP2 Triggered for %s in Port %s", ticker, port_id)
        except Exception as e:
            logger.error("Error in check_exit_conditions for %s: %s", ticker, e)

def monitor_system_positions():
    """Wrapper function for easier imports."""
    return SystemMonitor.monitor_system_positions()

def check_exit_conditions(ticker: str, current_price: float):
    """Wrapper function for tick-level exit checks."""
    return SystemMonitor.check_exit_conditions(ticker, current_price)
