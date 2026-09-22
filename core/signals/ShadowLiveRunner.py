import logging
import time
import json
from database import db, Signal, SignalOutcome
from core.signals.SignalTelemetryTracker import telemetry_tracker
from core.analyzers.MomentumBreakoutScanner import analyze_stock
from core import TimeUtils

logger = logging.getLogger("ShadowLiveRunner")

class ShadowLiveRunner:
    def __init__(self, shadow_mode: bool = True):
        self.shadow_mode = shadow_mode
        self.running = False

    def process_shadow_tick(self, ticker: str, price: float, volume: float = 0, bid_depth: float = 0):
        """
        Processes market tick in Private Shadow-Live mode, evaluating RVU breakout logic
        and logging telemetry outcomes without dispatching external subscriber alerts.
        """
        if not ticker or price <= 0:
            return None

        try:
            signal = analyze_stock(ticker, include_live=True)
            if not signal:
                return None

            score = signal.get("Score", 0)
            status = signal.get("Status", "")
            is_manipulation = signal.get("Manipulation_Flag", "CLEAR") != "CLEAR"
            is_liquidity_trap = "LIQUIDITY TRAP" in status or "⚠️" in status
            is_ppp_failure = signal.get("Projected_Return_%", 0.0) < signal.get("PPP_Hurdle_%", 0.0)

            if is_manipulation or is_liquidity_trap or is_ppp_failure or score < 4:
                return None

            logger.info(f"[ShadowLiveRunner] Private Shadow Signal Logged: ticker={ticker} score={score} price={price:.2f}")

            # Persist to Signal and SignalOutcome telemetry tracker privately
            with db.atomic():
                sig_obj, _ = Signal.get_or_create(
                    ticker=ticker,
                    date=TimeUtils.today(),
                    signal_type=f"[SHADOW] {status}",
                    defaults={
                        "price": price,
                        "score": score,
                        "source": "ShadowLiveRunner",
                        "rationale": json.dumps(signal)
                    }
                )

            outcome = telemetry_tracker.record_signal_entry(
                ticker=ticker,
                price=price,
                target_1=float(signal.get("Target_1", 0.0)),
                target_2=float(signal.get("Target_2", 0.0)),
                stop_loss=float(signal.get("Stop_Loss", 0.0)),
                signal_obj=sig_obj
            )

            return outcome

        except Exception as e:
            logger.error(f"[ShadowLiveRunner] Error processing shadow tick for ticker={ticker}: {e}")
            return None

    def get_forward_test_metrics(self) -> dict:
        """
        Computes empirical forward-test performance metrics: win rate %, profit factor, total signals.
        """
        summary = telemetry_tracker.get_telemetry_summary()
        total = summary.get("total_signals", 0)
        win_rate = summary.get("win_rate_pct", 0.0)
        avg_pnl = summary.get("avg_realized_pnl_pct", 0.0)

        return {
            "mode": "SHADOW_LIVE_FORWARD_TEST",
            "total_forward_signals": total,
            "realized_win_rate_pct": win_rate,
            "avg_realized_pnl_pct": avg_pnl,
            "tp1_hits": summary.get("tp1_hits", 0),
            "tp2_hits": summary.get("tp2_hits", 0),
            "sl_hits": summary.get("sl_hits", 0),
            "active_tracking": summary.get("active_signals", 0),
            "status": "PASS" if win_rate >= 50.0 or total == 0 else "DEGRADED"
        }

shadow_runner = ShadowLiveRunner(shadow_mode=True)
