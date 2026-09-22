"""
MubasherFeedDaemon
==================
Persistent, self-healing background thread that maintains a continuous TCP
connection to the Mubasher live price feed (port 9006) and writes incoming
bars directly into Horus's intraday_store.

Key behaviours
--------------
* On startup it reads the latest auth token from Log_ClientServicePlatform.txt
  (same mechanism as mubasher_realtime_source.py) and opens a streaming socket.
* Every POLL_INTERVAL_SEC seconds it re-reads the log to see whether Mubasher
  has reconnected and issued a new auth token.  If the token has changed the
  daemon closes the current socket and reconnects immediately — following
  Mubasher's reconnect within ~2 seconds instead of waiting for the next
  5-minute sync cycle.
* Incoming binary frames are parsed with the existing parse_quote_messages()
  function and upserted into intraday_store using the standard
  upsert_intraday() call.
* The daemon only runs while the market is open (settings.is_market_open()).
  Outside market hours it idles and polls every IDLE_POLL_SEC seconds.
* All errors are swallowed and logged; the daemon never crashes Horus.
"""

from __future__ import annotations

import logging
import os
import select
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass

logger = logging.getLogger("horus.feed_daemon")

# ---------------------------------------------------------------------------
# Public state (readable by FeedWatchdog / API)
# ---------------------------------------------------------------------------
_DAEMON_INSTANCE: "MubasherFeedDaemon | None" = None


def get_daemon() -> "MubasherFeedDaemon | None":
    """Return the running daemon instance (or None if not started)."""
    return _DAEMON_INSTANCE


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------


class MubasherFeedDaemon(threading.Thread):
    """
    Background thread: persistent Mubasher TCP stream → intraday_store.
    """

    # ------------------------------------------------------------------
    # Configuration (overridable via env at init time)
    # ------------------------------------------------------------------
    CONNECT_TIMEOUT_SEC: float = 8.0
    RECV_BUFFER: int = 65536
    POLL_INTERVAL_SEC: float = 2.0      # How often to check for a new auth token
    IDLE_POLL_SEC: float = 30.0         # Polling interval when market is closed
    RECONNECT_DELAY_SEC: float = 2.0    # Pause between reconnect attempts
    FRAME_FLUSH_SEC: float = 2.0        # How long to accumulate frames before writing
    REQUEST_GAP_SEC: float = 0.01       # Gap between per-ticker subscription requests
    AUTH_DRAIN_SEC: float = 1.0         # Time to drain server greeting after auth
    MAX_SUBSCRIBE_PER_CONNECT: int = 500  # Safety cap on ticker subscriptions

    def __init__(self, mubasher_root: Path | str, realm: str = "EGX") -> None:
        super().__init__(name="MubasherFeedDaemon", daemon=True)
        self._root = Path(mubasher_root)
        self._realm = realm
        self._stop_event = threading.Event()

        # Timestamps / health metrics (read by watchdog / API)
        self.last_bar_at: datetime | None = None
        self.last_connect_at: datetime | None = None
        self.last_error: str | None = None
        self.bars_written: int = 0
        self.reconnect_count: int = 0
        self.running: bool = False

        # Last known auth payload — used to detect token rotation
        self._last_auth_hash: str = ""
        self._current_sock: socket.socket | None = None
        self._sock_lock = threading.Lock()

        # Apply env overrides
        self.CONNECT_TIMEOUT_SEC = float(
            os.getenv("MUBASHER_FEED_DAEMON_CONNECT_TIMEOUT_SEC", str(self.CONNECT_TIMEOUT_SEC))
        )
        self.POLL_INTERVAL_SEC = float(
            os.getenv("MUBASHER_FEED_DAEMON_POLL_INTERVAL_SEC", str(self.POLL_INTERVAL_SEC))
        )
        self.IDLE_POLL_SEC = float(
            os.getenv("MUBASHER_FEED_DAEMON_IDLE_POLL_SEC", str(self.IDLE_POLL_SEC))
        )
        self.RECONNECT_DELAY_SEC = float(
            os.getenv("MUBASHER_FEED_DAEMON_RECONNECT_SEC", str(self.RECONNECT_DELAY_SEC))
        )
        self.FRAME_FLUSH_SEC = float(
            os.getenv("MUBASHER_FEED_DAEMON_FRAME_FLUSH_SEC", str(self.FRAME_FLUSH_SEC))
        )

    # ------------------------------------------------------------------
    # Public control
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the daemon to stop gracefully."""
        self._stop_event.set()
        self._close_socket()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_stop(self) -> bool:
        return self._stop_event.is_set()

    def _close_socket(self) -> None:
        with self._sock_lock:
            if self._current_sock is not None:
                try:
                    self._current_sock.close()
                except Exception:
                    pass
                self._current_sock = None

    def _read_auth(self):
        """Return the latest _RealtimeAuth from the Mubasher log, or None."""
        try:
            from data_engine.mubasher_realtime_source import _read_latest_realtime_auth
            return _read_latest_realtime_auth(self._root)
        except Exception as exc:
            self.last_error = f"auth_read: {exc}"
            return None

    @staticmethod
    def _extract_auth_token(payload: bytes) -> bytes:
        """
        Extract Tag 20 (session authentication token) from binary payload.
        Ignores fluctuating environment fields like Tag 25 (available RAM bytes).
        """
        if not payload:
            return b""
        for part in payload.split(b"\x1c"):
            if part.startswith(b"20\x02"):
                return part
        return payload

    def _auth_changed(self, auth) -> bool:
        """Return True if the auth token has rotated since last check."""
        if auth is None:
            return False
        token = self._extract_auth_token(auth.payload)
        new_hash = str(hash(token))
        if new_hash != self._last_auth_hash:
            self._last_auth_hash = new_hash
            return True
        return False

    def _get_subscription_symbols(self) -> list[str]:
        """
        Return the list of EGX tickers to subscribe to.
        Tries Mubasher DB first, then falls back to intraday_store's known tickers.
        """
        try:
            from data_engine.mubasher_sqlite_source import build_paths, list_intraday_symbols
            from core.settings import settings
            paths = build_paths(self._root, user_id=getattr(settings, "MUBASHER_USER_ID", None))
            symbols = list_intraday_symbols(paths)
            result = [s for s in symbols if s][:self.MAX_SUBSCRIBE_PER_CONNECT]
            if result:
                return result
        except Exception:
            pass
        # Fallback: ask intraday_store for its known tickers
        try:
            from data_engine.intraday_store import list_tickers
            return list_tickers(realm=self._realm)[:self.MAX_SUBSCRIBE_PER_CONNECT]
        except Exception:
            return []


    def _subscribe_symbols(self, sock: socket.socket, symbols: list[str]) -> None:
        """Send subscription request for each ticker."""
        for symbol in symbols:
            clean = (symbol or "").strip().upper()
            if not clean:
                continue
            try:
                sock.sendall(
                    b"1\x1c10\x1cCASE~" + clean.encode("ascii", errors="ignore") + b"\x1c\n"
                )
            except Exception:
                break
            if self.REQUEST_GAP_SEC > 0:
                time.sleep(self.REQUEST_GAP_SEC)

    def _drain(self, sock: socket.socket, duration: float) -> bytes:
        """Read bytes from sock for up to `duration` seconds."""
        deadline = time.monotonic() + max(0.0, duration)
        chunks: list[bytes] = []
        while time.monotonic() < deadline:
            try:
                ready, _, _ = select.select([sock], [], [], min(0.1, deadline - time.monotonic()))
                if ready:
                    chunk = sock.recv(self.RECV_BUFFER)
                    if not chunk:
                        break
                    chunks.append(chunk)
            except Exception:
                break
        return b"".join(chunks)

    def _flush_bars(self, raw: bytes) -> int:
        """Parse binary frames and write bars to intraday_store. Returns rows written."""
        if not raw:
            return 0
        try:
            from data_engine.mubasher_realtime_source import parse_quote_messages
            from data_engine import intraday_store
            snapshots = parse_quote_messages(raw)
            if not snapshots:
                return 0

            rows_written = 0
            for snap in snapshots:
                try:
                    frame = snap.to_intraday_frame()
                    if frame.empty:
                        continue
                    written = intraday_store.upsert_intraday(
                        snap.symbol, frame, realm=self._realm, accumulate_volume=True
                    )
                    rows_written += written
                except Exception as exc:
                    logger.debug("[FeedDaemon] upsert error for %s: %s", snap.symbol, exc)

            if rows_written > 0:
                self.bars_written += rows_written
                self.last_bar_at = datetime.now()

            return rows_written
        except Exception as exc:
            logger.warning("[FeedDaemon] flush_bars error: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Core streaming loop
    # ------------------------------------------------------------------

    def _stream_session(self, auth) -> None:
        """
        Open one TCP session: connect → subscribe → stream until disconnected
        or stop requested or auth token rotates.
        """
        symbols = self._get_subscription_symbols()
        logger.info(
            "[FeedDaemon] Connecting to %s:%d — subscribing %d tickers",
            auth.host, auth.port, len(symbols),
        )

        try:
            sock = socket.create_connection((auth.host, auth.port), timeout=self.CONNECT_TIMEOUT_SEC)
        except Exception as exc:
            self.last_error = f"connect: {exc}"
            logger.warning("[FeedDaemon] Connection failed: %s", exc)
            return

        with self._sock_lock:
            self._current_sock = sock

        self.last_connect_at = datetime.now()
        self.reconnect_count += 1

        try:
            sock.settimeout(0.1)
            # Authenticate
            sock.sendall(auth.payload + b"\n")
            self._drain(sock, self.AUTH_DRAIN_SEC)

            # Subscribe
            self._subscribe_symbols(sock, symbols)
            logger.info("[FeedDaemon] Connected and subscribed. Streaming...")

            frame_buffer: list[bytes] = []
            flush_deadline = time.monotonic() + self.FRAME_FLUSH_SEC
            last_token_check = time.monotonic()

            while not self._should_stop():
                now = time.monotonic()

                # Periodically check if Mubasher reconnected with a new token
                if now - last_token_check >= self.POLL_INTERVAL_SEC:
                    last_token_check = now
                    fresh_auth = self._read_auth()
                    if fresh_auth is not None and self._auth_changed(fresh_auth):
                        logger.info("[FeedDaemon] Auth token rotated — reconnecting with fresh token")
                        break  # Exit stream loop; outer loop will reconnect

                # Read data
                try:
                    ready, _, _ = select.select([sock], [], [], 0.05)
                    if ready:
                        chunk = sock.recv(self.RECV_BUFFER)
                        if not chunk:
                            logger.info("[FeedDaemon] Server closed connection")
                            break
                        frame_buffer.append(chunk)
                except socket.timeout:
                    pass
                except OSError:
                    break

                # Flush buffer periodically
                if now >= flush_deadline and frame_buffer:
                    raw = b"".join(frame_buffer)
                    frame_buffer.clear()
                    flush_deadline = time.monotonic() + self.FRAME_FLUSH_SEC
                    written = self._flush_bars(raw)
                    if written:
                        logger.debug("[FeedDaemon] Flushed %d bar rows", written)

            # Final flush
            if frame_buffer:
                self._flush_bars(b"".join(frame_buffer))

        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("[FeedDaemon] Stream error: %s", exc)
        finally:
            self._close_socket()

    # ------------------------------------------------------------------
    # Thread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        global _DAEMON_INSTANCE
        _DAEMON_INSTANCE = self
        self.running = True
        logger.info("[FeedDaemon] Started")

        try:
            from core.settings import settings
        except Exception:
            settings = None

        while not self._should_stop():
            # Wait for market hours
            try:
                is_open = settings.is_market_open() if settings else False
            except Exception:
                is_open = False

            if not is_open:
                logger.debug("[FeedDaemon] Market closed — idling")
                self._stop_event.wait(self.IDLE_POLL_SEC)
                continue

            # Read auth
            auth = self._read_auth()
            if auth is None:
                logger.warning("[FeedDaemon] Cannot read auth token — retrying in %ds", int(self.RECONNECT_DELAY_SEC))
                self._stop_event.wait(self.RECONNECT_DELAY_SEC)
                continue

            # Mark token as known (so we only reconnect on *changes*)
            # If this is our first connect, treat any token as "new"
            if not self._last_auth_hash:
                token = self._extract_auth_token(auth.payload)
                self._last_auth_hash = str(hash(token))

            # Stream until disconnected / token rotated / stop requested
            self._stream_session(auth)

            if not self._should_stop():
                logger.info("[FeedDaemon] Reconnecting in %ds...", int(self.RECONNECT_DELAY_SEC))
                self._stop_event.wait(self.RECONNECT_DELAY_SEC)

        self.running = False
        logger.info("[FeedDaemon] Stopped")


# ---------------------------------------------------------------------------
# Module-level helpers for lifespan.py
# ---------------------------------------------------------------------------


def start_feed_daemon(mubasher_root: Path | str, realm: str = "EGX") -> "MubasherFeedDaemon":
    """
    Create and start a MubasherFeedDaemon.  Idempotent — if one is already
    running it is returned as-is.
    """
    global _DAEMON_INSTANCE
    if _DAEMON_INSTANCE is not None and _DAEMON_INSTANCE.is_alive():
        return _DAEMON_INSTANCE
    daemon = MubasherFeedDaemon(mubasher_root=mubasher_root, realm=realm)
    daemon.start()
    return daemon


def stop_feed_daemon() -> None:
    """Stop the running daemon (if any)."""
    global _DAEMON_INSTANCE
    if _DAEMON_INSTANCE is not None:
        _DAEMON_INSTANCE.stop()
        _DAEMON_INSTANCE = None
