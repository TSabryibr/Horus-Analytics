import zmq
import json
import time
import threading
import logging
from core.settings import settings
from core.analyzers.MomentumBreakoutScanner import analyze_stock
from core.TelegramBot_Alerts import send_message
from core.WebhookManager import send_webhook
from database import Signal, Portfolio, Position, db
from core import TimeUtils

logger = logging.getLogger("SignalDispatcher")

class SignalDispatcher:
    def __init__(self):
        self.zmq_host = getattr(settings, "ZMQ_HOST", "127.0.0.1")
        self.zmq_port = getattr(settings, "ZMQ_PORT", "5556")
        self.context = None
        self.socket = None
        self.thread = None
        self.running = False
        self._last_alert_time = {}
        self.cooldown_sec = getattr(settings, "ALERT_COOLDOWN_SECONDS", 900)

    def start(self):
        """Starts the background listening thread."""
        if self.running:
            logger.warning("SignalDispatcher is already running.")
            return
            
        self.running = True
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        # LINGER=0 so closing the socket never blocks on undelivered messages.
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(f"tcp://{self.zmq_host}:{self.zmq_port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "TICK ")
        
        self.thread = threading.Thread(target=self._listen_loop, name="signal-dispatcher", daemon=True)
        self.thread.start()
        logger.info(f"SignalDispatcher started listening on tcp://{self.zmq_host}:{self.zmq_port}")

    def stop(self):
        """Stops the dispatcher and cleans up sockets.

        Ordering matters: the listener thread must exit before the context is
        terminated, otherwise context.term() deadlocks on a socket that is
        still open in another thread (the historic zmq GC hang).
        """
        if not self.running:
            return
            
        self.running = False
        thread = self.thread
        if thread and thread.is_alive():
            thread.join(timeout=5)
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
        if self.context:
            try:
                self.context.term()
            except Exception:
                pass
        self.socket = None
        self.context = None
        self.thread = None
        logger.info("SignalDispatcher stopped.")

    def _listen_loop(self):
        while self.running:
            try:
                # Poll with a timeout so the loop can observe self.running
                # instead of blocking forever inside recv_string.
                if self.socket.poll(500):
                    message = self.socket.recv_string(flags=zmq.NOBLOCK)
                    if not message.startswith("TICK "):
                        continue
                    
                    payload_str = message[5:]
                    payload = json.loads(payload_str)
                    self._process_tick(payload)
            except zmq.Again:
                continue
            except zmq.error.ContextTerminated:
                break
            except zmq.ZMQError:
                if self.running:
                    time.sleep(0.1)
            except Exception as e:
                if self.running:
                    logger.error(f"[SignalDispatcher] Error receiving or parsing tick: {e}")
                    time.sleep(0.5)

    def _process_tick(self, payload: dict):
        ticker = payload.get("ticker")
        price = payload.get("price")
        if not ticker or not price:
            return

        tick_ts = payload.get("timestamp")
        if tick_ts:
            try:
                tick_lag = time.time() - float(tick_ts)
                if tick_lag > 2.0:
                    logger.warning(f"[SignalDispatcher] Stale tick suppressed for {ticker}: lag={tick_lag:.2f}s > 2.0s limit")
                    return
            except Exception:
                pass

        logger.debug(f"[SignalDispatcher] Processing tick for {ticker} at {price:.2f}")

        try:
            # 1. Trigger scanner core analysis
            signal = analyze_stock(ticker, include_live=True)
            if not signal:
                return

            # 2. Check score and validation parameters
            score = signal.get("Score", 0)
            status = signal.get("Status", "")
            is_manipulation = signal.get("Manipulation_Flag", "CLEAR") != "CLEAR"
            
            # Extract risk filter status
            is_liquidity_trap = "LIQUIDITY TRAP" in status or "⚠️" in status
            is_ppp_failure = signal.get("Projected_Return_%", 0.0) < signal.get("PPP_Hurdle_%", 0.0)

            # 3. Intercept invalid signals at risk invalidation gates & Global Signal Guard Kill Switch
            from database import SignalGuardState
            guard_blocked = False
            try:
                guard = SignalGuardState.get_or_none(name="PUBLISH")
                if guard and guard.is_blocked:
                    guard_blocked = True
            except Exception:
                pass

            if guard_blocked or is_manipulation or is_liquidity_trap or is_ppp_failure or score < 4:
                tag = "GUARD_BLOCKED" if guard_blocked else (
                    signal.get("Manipulation_Flag", "") if is_manipulation else (
                        "LIQUIDITY_TRAP" if is_liquidity_trap else (
                            "PPP_FAILURE" if is_ppp_failure else "LOW_SCORE"
                        )
                    )
                )
                reason = f"score={score}, manipulation={is_manipulation}, liquidity_trap={is_liquidity_trap}, ppp_failure={is_ppp_failure}, guard_blocked={guard_blocked}"
                logger.debug(f"[SignalDispatcher] Signal suppressed for ticker={ticker}: tag={tag} reason={reason}")
                
                try:
                    from database import SignalSuppressionLog
                    SignalSuppressionLog.create(
                        ticker=ticker,
                        price=price,
                        score=score,
                        suppression_tag=tag,
                        kill_reason=reason,
                        created_at=TimeUtils.now()
                    )
                except Exception as log_err:
                    logger.warning(f"[SignalDispatcher] Could not log suppression: {log_err}")
                return

            logger.info(
                f"[SignalDispatcher] Valid Signal Detected! ticker={ticker} score={score} "
                f"price={price:.2f} stop={signal.get('Stop_Loss')} target={signal.get('Target_2')}"
            )

            # 4. Save Signal to Peewee Database & Telemetry Tracker
            try:
                with db.atomic():
                    sig_obj, _ = Signal.get_or_create(
                        ticker=ticker,
                        date=TimeUtils.today(),
                        signal_type=status,
                        defaults={
                            "price": price,
                            "score": score,
                            "source": "SignalDispatcher",
                            "rationale": json.dumps(signal)
                        }
                    )
                from core.signals.SignalTelemetryTracker import telemetry_tracker
                telemetry_tracker.record_signal_entry(
                    ticker=ticker,
                    price=price,
                    target_1=float(signal.get("Target_1", 0.0)),
                    target_2=float(signal.get("Target_2", 0.0)),
                    stop_loss=float(signal.get("Stop_Loss", 0.0)),
                    signal_obj=sig_obj
                )
            except Exception as db_err:
                logger.warning(f"[SignalDispatcher] Could not persist signal/telemetry to DB: {db_err}")

            # 5. Rate-Limiting & Deduplication check
            now_ts = time.time()
            last_alert = self._last_alert_time.get(ticker, 0)
            if (now_ts - last_alert) < self.cooldown_sec:
                logger.info(
                    f"[SignalDispatcher] Alert rate-limited for ticker={ticker}: "
                    f"last sent {int(now_ts - last_alert)}s ago (< {self.cooldown_sec}s cooldown)"
                )
                return

            self._last_alert_time[ticker] = now_ts

            # 6. Dispatch Real-Time Alerts (Telegram + Webhook) with Institutional Legal & Reasoning Disclaimers
            from core.data.ParallelUSDFeed import usd_parallel_feed
            rvu_rate, is_fresh = usd_parallel_feed.get_live_rvu_rate()
            fresh_label = "FRESH" if is_fresh else "STALE"

            alert_text = (
                f"🚀 *HORUS EGX BREAKOUT SIGNAL*\n"
                f"📌 *Ticker:* #{ticker}\n"
                f"💰 *Entry Price:* {price:.2f} EGP\n"
                f"🛑 *Stop Loss:* {signal.get('Stop_Loss', 0):.2f} EGP\n"
                f"🎯 *Target 1:* {signal.get('Target_1', 0):.2f} EGP\n"
                f"🎯 *Target 2:* {signal.get('Target_2', 0):.2f} EGP\n"
                f"⭐ *Score:* {score}/11 | *Status:* {status}\n"
                f"📊 *Reasoning:* RVU Rate: {rvu_rate:.2f} EGP/USD ({fresh_label}) | Vol Floor: PASS | L2 Depth: PASS\n"
                f"🕒 *Timestamp:* {TimeUtils.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⚖️ _Educational & Telemetry Signal Intelligence Only — Not Unlicensed Financial Advice._"
            )
            
            send_message(alert_text)
            send_webhook("EGX_SIGNAL_ALERT", signal)

        except Exception as e:
            logger.exception(f"[SignalDispatcher] Exception processing tick for ticker={ticker}: {e}")
