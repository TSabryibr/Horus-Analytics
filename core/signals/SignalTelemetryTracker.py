import logging
import json
from database import db, Signal, LegacySignalOutcome
from core import TimeUtils

logger = logging.getLogger("SignalTelemetryTracker")

class SignalTelemetryTracker:
    def __init__(self):
        pass

    def record_signal_entry(self, ticker: str, price: float, target_1: float = 0.0, target_2: float = 0.0, stop_loss: float = 0.0, signal_obj=None):
        """
        Registers a new breakout signal outcome tracking record.
        """
        try:
            with db.atomic():
                outcome = LegacySignalOutcome.create(
                    signal=signal_obj,
                    ticker=ticker,
                    signal_date=TimeUtils.today(),
                    entry_price=price,
                    max_price=price,
                    min_price=price,
                    current_price=price,
                    max_gain_pct=0.0,
                    max_drawdown_pct=0.0,
                    realized_pnl_pct=0.0,
                    target_1_hit=False,
                    target_2_hit=False,
                    stop_loss_hit=False,
                    outcome_status="ACTIVE",
                    updated_at=TimeUtils.now()
                )
                logger.info(f"[SignalTelemetryTracker] Recorded new telemetry tracking for ticker={ticker} entry={price:.2f}")
                return outcome
        except Exception as e:
            logger.error(f"[SignalTelemetryTracker] Failed to record signal entry for ticker={ticker}: {e}")
            return None

    def update_price_tick(self, ticker: str, current_price: float):
        """
        Evaluates incoming price tick against active outcomes for the given ticker.
        Updates peak gain, max drawdown, and checks Target 1, Target 2, and Stop Loss hits.
        """
        if current_price <= 0:
            return

        try:
            active_outcomes = LegacySignalOutcome.select().where(
                (LegacySignalOutcome.ticker == ticker) & (LegacySignalOutcome.outcome_status == "ACTIVE")
            )
            for outcome in active_outcomes:
                entry = outcome.entry_price
                if entry <= 0:
                    continue

                # Update max and min observed prices
                new_max = max(outcome.max_price or entry, current_price)
                new_min = min(outcome.min_price or entry, current_price)

                max_gain = round(((new_max - entry) / entry) * 100.0, 2)
                max_dd = round(((new_min - entry) / entry) * 100.0, 2)
                current_pnl = round(((current_price - entry) / entry) * 100.0, 2)

                # Fetch targets from linked signal rationale if not stored explicitly
                target_1 = 0.0
                target_2 = 0.0
                stop_loss = 0.0

                if outcome.signal and outcome.signal.rationale:
                    try:
                        rationale = json.loads(outcome.signal.rationale)
                        target_1 = float(rationale.get("Target_1", 0.0))
                        target_2 = float(rationale.get("Target_2", 0.0))
                        stop_loss = float(rationale.get("Stop_Loss", 0.0))
                    except Exception:
                        pass

                # Check Target/Stop status
                t1_hit = outcome.target_1_hit or (target_1 > 0 and current_price >= target_1)
                t2_hit = outcome.target_2_hit or (target_2 > 0 and current_price >= target_2)
                sl_hit = outcome.stop_loss_hit or (stop_loss > 0 and current_price <= stop_loss)

                status = outcome.outcome_status
                if t2_hit:
                    status = "WIN_TP2"
                elif t1_hit:
                    status = "WIN_TP1"
                elif sl_hit:
                    status = "LOSS_SL"

                outcome.max_price = new_max
                outcome.min_price = new_min
                outcome.current_price = current_price
                outcome.max_gain_pct = max_gain
                outcome.max_drawdown_pct = max_dd
                outcome.realized_pnl_pct = current_pnl
                outcome.target_1_hit = t1_hit
                outcome.target_2_hit = t2_hit
                outcome.stop_loss_hit = sl_hit
                outcome.outcome_status = status
                outcome.updated_at = TimeUtils.now()
                outcome.save()

        except Exception as e:
            logger.error(f"[SignalTelemetryTracker] Error updating price tick for ticker={ticker}: {e}")

    def get_telemetry_summary(self) -> dict:
        """
        Computes global telemetry statistics across all recorded signal outcomes.
        """
        try:
            total_signals = LegacySignalOutcome.select().count()
            if total_signals == 0:
                return {
                    "total_signals": 0,
                    "win_rate_pct": 0.0,
                    "avg_realized_pnl_pct": 0.0,
                    "tp1_hits": 0,
                    "tp2_hits": 0,
                    "sl_hits": 0,
                    "active_signals": 0
                }

            tp1_hits = LegacySignalOutcome.select().where(LegacySignalOutcome.target_1_hit == True).count()
            tp2_hits = LegacySignalOutcome.select().where(LegacySignalOutcome.target_2_hit == True).count()
            sl_hits = LegacySignalOutcome.select().where(LegacySignalOutcome.stop_loss_hit == True).count()
            active_signals = LegacySignalOutcome.select().where(LegacySignalOutcome.outcome_status == "ACTIVE").count()

            winners = LegacySignalOutcome.select().where(
                (LegacySignalOutcome.outcome_status == "WIN_TP1") | (LegacySignalOutcome.outcome_status == "WIN_TP2")
            ).count()

            win_rate = round((winners / (total_signals - active_signals) * 100.0), 2) if (total_signals - active_signals) > 0 else 0.0

            outcomes = list(LegacySignalOutcome.select())
            pnls = [o.realized_pnl_pct for o in outcomes if o.realized_pnl_pct is not None]
            avg_pnl = round(sum(pnls) / len(pnls), 2) if pnls else 0.0

            return {
                "total_signals": total_signals,
                "win_rate_pct": win_rate,
                "avg_realized_pnl_pct": avg_pnl,
                "tp1_hits": tp1_hits,
                "tp2_hits": tp2_hits,
                "sl_hits": sl_hits,
                "active_signals": active_signals
            }

        except Exception as e:
            logger.error(f"[SignalTelemetryTracker] Error generating telemetry summary: {e}")
            return {
                "total_signals": 0,
                "win_rate_pct": 0.0,
                "avg_realized_pnl_pct": 0.0,
                "tp1_hits": 0,
                "tp2_hits": 0,
                "sl_hits": 0,
                "active_signals": 0,
                "error": str(e)
            }

# Global instance for thread-safe telemetry tracking
telemetry_tracker = SignalTelemetryTracker()
