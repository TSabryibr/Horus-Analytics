import zmq
import time
import threading
import logging
from core.settings import settings
from core.TelegramBot_Alerts import send_message
from core.WebhookManager import send_webhook
from core import TimeUtils

logger = logging.getLogger("StreamHealthWatchdog")

class StreamHealthWatchdog:
    def __init__(self, max_stale_seconds: float = 15.0):
        self.zmq_host = getattr(settings, "ZMQ_HOST", "127.0.0.1")
        self.zmq_port = getattr(settings, "ZMQ_PORT", "5556")
        self.max_stale_seconds = max_stale_seconds
        
        self.context = None
        self.socket = None
        self.thread = None
        self.running = False
        
        self.last_tick_time = time.time()
        self.warning_active = False
        self.last_warning_dispatch = 0.0

    def start(self):
        """Starts the background watchdog monitoring thread."""
        if self.running:
            logger.warning("StreamHealthWatchdog is already running.")
            return

        self.running = True
        self.last_tick_time = time.time()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        # LINGER=0 so closing the socket never blocks on undelivered messages.
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(f"tcp://{self.zmq_host}:{self.zmq_port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "TICK ")

        self.thread = threading.Thread(target=self._monitor_loop, name="stream-watchdog", daemon=True)
        self.thread.start()
        logger.info(f"StreamHealthWatchdog started monitoring tcp://{self.zmq_host}:{self.zmq_port} (stale hurdle: {self.max_stale_seconds}s)")

    def stop(self):
        """Stops the watchdog thread and cleans up ZMQ context.

        The listener thread must exit before context.term() is called, else
        term() deadlocks on sockets still open in the other thread.
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
        logger.info("StreamHealthWatchdog stopped.")

    def record_tick(self):
        """Allows direct programmatic notification of a received tick."""
        self.last_tick_time = time.time()
        if self.warning_active:
            self.warning_active = False
            logger.info("StreamHealthWatchdog: Tick stream recovered.")
            send_message("✅ *HORUS STREAM RECOVERED*: Live ZMQ market feed is active.")

    def _monitor_loop(self):
        while self.running:
            try:
                socket = self.socket
                if socket is None:
                    break
                # Polling ZMQ socket with non-blocking check
                try:
                    msg = socket.recv_string(flags=zmq.NOBLOCK)
                    if msg.startswith("TICK "):
                        self.record_tick()
                except zmq.Again:
                    pass

                now = time.time()
                stale_duration = now - self.last_tick_time

                # If feed is stale and warning is not active (or 5 minutes passed since last alert)
                if stale_duration > self.max_stale_seconds:
                    if not self.warning_active or (now - self.last_warning_dispatch > 300):
                        self.warning_active = True
                        self.last_warning_dispatch = now
                        msg_text = (
                            f"⚠️ *HORUS STREAM WARNING*: Live EGX market feed stalled!\n"
                            f"⏱️ No ticks received for {stale_duration:.1f}s (Threshold: {self.max_stale_seconds}s).\n"
                            f"🕒 Timestamp: {TimeUtils.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        logger.warning(f"[StreamHealthWatchdog] Stream stalled for {stale_duration:.1f}s!")
                        send_message(msg_text)
                        send_webhook("STREAM_HEALTH_WARNING", {
                            "stale_duration_sec": round(stale_duration, 2),
                            "threshold_sec": self.max_stale_seconds
                        })

                time.sleep(1.0)
            except Exception as e:
                if self.running:
                    logger.error(f"[StreamHealthWatchdog] Error in monitoring loop: {e}")
                    time.sleep(1.0)

    def get_status(self) -> dict:
        now = time.time()
        stale_duration = round(now - self.last_tick_time, 2)
        return {
            "healthy": stale_duration <= self.max_stale_seconds,
            "stale_duration_sec": stale_duration,
            "max_stale_seconds": self.max_stale_seconds,
            "warning_active": self.warning_active
        }
