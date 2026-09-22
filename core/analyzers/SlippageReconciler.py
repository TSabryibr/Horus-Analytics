import json
import datetime
import logging
import numpy as np
from core import TimeUtils
from database import Trade, SignalStateArchive

logger = logging.getLogger("SlippageReconciler")

class SlippageReconciler:
    @staticmethod
    def get_dynamic_calibration_metrics(ticker: str, lookback_days: int = 30) -> float:
        """
        Calculates the average execution entry slippage % for the given ticker
        over the last `lookback_days` of trades.
        
        Slippage % = ((actual_entry - theoretical_entry) / theoretical_entry) * 100
        """
        try:
            ticker_upper = str(ticker).upper().strip()
            cutoff_date = TimeUtils.now() - datetime.timedelta(days=lookback_days)
            
            # Find trades matching ticker within the lookback window that have a valid signal_id
            trades = list(
                Trade.select(Trade.entry_price, Trade.signal_id)
                .where(
                    (Trade.ticker == ticker_upper) &
                    (Trade.entry_date >= cutoff_date) &
                    (Trade.signal_id.is_null(False))
                )
            )
            
            slippage_values = []
            for t in trades:
                if not t.signal_id or t.signal_id.startswith(("ERR-", "INVALID")):
                    continue
                
                # Fetch corresponding signal generation snapshot
                archive = SignalStateArchive.get_or_none(SignalStateArchive.signal_id == t.signal_id)
                if not archive:
                    continue
                
                try:
                    snapshot = json.loads(archive.filter_snapshot_json or "{}")
                    theoretical_entry = snapshot.get("raw_close_egp")
                    if theoretical_entry and theoretical_entry > 0:
                        slippage_pct = ((t.entry_price - theoretical_entry) / theoretical_entry) * 100.0
                        slippage_values.append(slippage_pct)
                except Exception as parse_err:
                    logger.debug(f"Failed to parse snapshot JSON for signal {t.signal_id}: {parse_err}")
            
            if len(slippage_values) >= 3:
                # Require at least 3 trades for statistical relevance
                avg_slippage = float(np.mean(slippage_values))
                logger.info(f"Dynamic calibration: Ticker {ticker_upper} average execution slippage = {avg_slippage:.2f}% (over {len(slippage_values)} trades)")
                return avg_slippage
                
        except Exception as err:
            logger.error(f"Error computing calibration metrics for {ticker}: {err}")
            
        return 0.0

    @staticmethod
    def generate_reconciliation_report(limit: int = 50) -> dict:
        """
        Generates a comprehensive report comparing theoretical signal entries
        against actual execution entries and exit outcomes.
        """
        try:
            trades = list(
                Trade.select()
                .where(Trade.signal_id.is_null(False))
                .order_by(Trade.exit_date.desc(), Trade.id.desc())
                .limit(limit)
            )
            
            reconciled_trades = []
            total_slippage_pct = 0.0
            slippage_count = 0
            
            for t in trades:
                if not t.signal_id or t.signal_id.startswith(("ERR-", "INVALID")):
                    continue
                
                archive = SignalStateArchive.get_or_none(SignalStateArchive.signal_id == t.signal_id)
                if not archive:
                    continue
                
                try:
                    snapshot = json.loads(archive.filter_snapshot_json or "{}")
                    theoretical_entry = snapshot.get("raw_close_egp")
                    
                    if theoretical_entry and theoretical_entry > 0:
                        slippage = t.entry_price - theoretical_entry
                        slippage_pct = (slippage / theoretical_entry) * 100.0
                        
                        # Decay is calculated relative to theoretical entry
                        decay_pnl = t.exit_price - theoretical_entry
                        decay_pnl_pct = (decay_pnl / theoretical_entry) * 100.0
                        
                        total_slippage_pct += slippage_pct
                        slippage_count += 1
                        
                        reconciled_trades.append({
                            "trade_id": t.id,
                            "ticker": t.ticker,
                            "signal_id": t.signal_id,
                            "currency": t.currency,
                            "date_executed": t.exit_date.isoformat() if t.exit_date else None,
                            "shares": t.shares,
                            "actual_entry": round(t.entry_price, 4),
                            "theoretical_entry": round(theoretical_entry, 4),
                            "slippage_nominal": round(slippage, 4),
                            "slippage_pct": round(slippage_pct, 2),
                            "actual_exit": round(t.exit_price, 4),
                            "decay_pct": round(decay_pnl_pct, 2),
                            "actual_pnl_pct": round(t.pnl_pct, 2)
                        })
                except Exception as trade_err:
                    logger.debug(f"Failed to reconcile trade {t.id}: {trade_err}")
            
            avg_slippage = (total_slippage_pct / slippage_count) if slippage_count > 0 else 0.0
            
            return {
                "average_slippage_pct": round(avg_slippage, 2),
                "reconciled_trades_count": len(reconciled_trades),
                "trades": reconciled_trades
            }
        except Exception as err:
            logger.error(f"Error generating reconciliation report: {err}")
            return {
                "average_slippage_pct": 0.0,
                "reconciled_trades_count": 0,
                "trades": [],
                "error": str(err)
            }
