from __future__ import annotations

import os
import re
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


from core.settings import settings

_FS = b"\x1c"
_MESSAGE_MARKER = b"\x0a\x00\x04CASE\x1c"
_REALTIME_AUTH_MARKER = b"Sending Auth Request to Realtime:"
_SESSION_RANGE_TOLERANCE = 0.02


def _empty_intraday_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])


def _inside_reported_session_range(
    price: float,
    session_low: float | None,
    session_high: float | None,
) -> bool:
    if session_low is not None and session_low > 0:
        if price < session_low * (1.0 - _SESSION_RANGE_TOLERANCE):
            return False
    if session_high is not None and session_high > 0:
        if price > session_high * (1.0 + _SESSION_RANGE_TOLERANCE):
            return False
    return True


@dataclass(frozen=True)
class MubasherQuoteSnapshot:
    symbol: str
    timestamp: pd.Timestamp
    last: float
    last_quantity: float = 0.0
    session_volume: float | None = None
    session_open: float | None = None
    session_high: float | None = None
    session_low: float | None = None
    previous_close: float | None = None
    trades: int | None = None

    def to_intraday_frame(self) -> pd.DataFrame:
        ts = pd.to_datetime(self.timestamp, errors="coerce")
        if pd.isna(ts):
            return _empty_intraday_frame()

        price = self.last
        if not _inside_reported_session_range(price, self.session_low, self.session_high):
            return _empty_intraday_frame()

        volume = max(self.last_quantity or 0.0, 0.0)

        return pd.DataFrame(
            [
                {
                    "timestamp": ts.floor("min"),
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": volume,
                }
            ]
        )



@dataclass(frozen=True)
class _RealtimeAuth:
    host: str
    port: int
    payload: bytes


def _cairo_tz() -> timezone | ZoneInfo:
    if ZoneInfo is None:
        return timezone(timedelta(hours=2), name="UTC+02")
    try:
        return ZoneInfo("Africa/Cairo")
    except Exception:
        return timezone(timedelta(hours=2), name="UTC+02")


def _clean_value(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore").replace("\x00", "")
    text = "".join(ch for ch in text if ch >= " ")
    return text.strip()


def _decode_binary_fields(raw: bytes) -> dict[int, str]:
    fields: dict[int, str] = {}
    for part in raw.split(_FS):
        if len(part) < 3:
            continue
        tag = int.from_bytes(part[:2], "big", signed=False)
        value = _clean_value(part[2:])
        if value:
            fields[tag] = value
    return fields


def _message_segments(raw: bytes) -> Iterable[bytes]:
    starts = [m.start() - 2 for m in re.finditer(re.escape(_MESSAGE_MARKER), raw) if m.start() >= 2]
    if not starts:
        yield raw
        return
    starts.append(len(raw))
    for start, end in zip(starts, starts[1:]):
        segment = raw[start:end]
        if segment:
            yield segment


def _float_field(fields: dict[int, str], tag: int) -> float | None:
    value = fields.get(tag)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_field(fields: dict[int, str], tag: int) -> int | None:
    value = _float_field(fields, tag)
    if value is None:
        return None
    return int(value)


def _parse_utc_timestamp(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        return None
    try:
        dt_utc = datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return pd.Timestamp(dt_utc.astimezone(_cairo_tz()).replace(tzinfo=None))


def parse_quote_messages(raw: bytes) -> list[MubasherQuoteSnapshot]:
    snapshots: list[MubasherQuoteSnapshot] = []
    for segment in _message_segments(raw):
        fields = _decode_binary_fields(segment)
        symbol = (fields.get(3) or "").strip().upper()
        # In Mubasher's binary quote stream tag 55 is the traded last price.
        # Tag 10 may carry a daily limit/reference price for some symbols.
        last = _float_field(fields, 55)
        if last is None or last <= 0:
            last = _float_field(fields, 10)
        last_quantity = _float_field(fields, 56)
        if last_quantity is None:
            last_quantity = _float_field(fields, 11)
        timestamp = _parse_utc_timestamp(fields.get(635))
        if not symbol or last is None or last <= 0 or timestamp is None:
            continue
        snapshots.append(
            MubasherQuoteSnapshot(
                symbol=symbol,
                timestamp=timestamp,
                last=last,
                last_quantity=last_quantity or 0.0,
                session_volume=_float_field(fields, 16),
                session_open=_float_field(fields, 32),
                session_high=_float_field(fields, 30),
                session_low=_float_field(fields, 31),
                previous_close=_float_field(fields, 33),
                trades=_int_field(fields, 75),
            )
        )
    return snapshots


def _read_latest_realtime_auth(root: Path) -> _RealtimeAuth:
    log_path = root / "logs" / "Log_ClientServicePlatform.txt"
    if not log_path.exists():
        raise FileNotFoundError(log_path)

    data = log_path.read_bytes()
    marker_index = data.rfind(_REALTIME_AUTH_MARKER)
    if marker_index < 0:
        raise ValueError("Mubasher realtime auth request not found in client log")

    header_end = data.find(b" - ", marker_index)
    if header_end < 0:
        raise ValueError("Mubasher realtime auth request header is incomplete")

    descriptor = data[marker_index + len(_REALTIME_AUTH_MARKER) : header_end].decode(
        "ascii", errors="ignore"
    )
    endpoint = re.match(r"([^:\s]+):(\d+)", descriptor)
    if endpoint is None:
        raise ValueError("Mubasher realtime endpoint not found in client log")

    payload_start = header_end + 3
    payload_end = data.find(b"\x1c\n", payload_start)
    if payload_end < 0:
        raise ValueError("Mubasher realtime auth request payload is incomplete")

    return _RealtimeAuth(
        host=endpoint.group(1),
        port=int(endpoint.group(2)),
        payload=data[payload_start : payload_end + 1],
    )


def _socket_drain(sock: socket.socket, duration_sec: float) -> bytes:
    deadline = time.monotonic() + max(0.0, duration_sec)
    chunks: list[bytes] = []
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_realtime_snapshots(
    symbols: Iterable[str],
    root: Path | str,
    user_id: str | None = None,
) -> dict[str, MubasherQuoteSnapshot]:
    if not getattr(settings, "MUBASHER_REALTIME_OVERLAY_ENABLED", False):
        return {}

    del user_id  # The active session is already embedded in Mubasher's local feed log.

    requested = []
    seen: set[str] = set()
    for raw_symbol in symbols:
        symbol = (raw_symbol or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        requested.append(symbol)
        seen.add(symbol)
    if not requested:
        return {}


    auth = _read_latest_realtime_auth(Path(root))
    connect_timeout = float(os.getenv("MUBASHER_REALTIME_CONNECT_TIMEOUT_SEC", "5"))
    read_timeout = float(os.getenv("MUBASHER_REALTIME_READ_TIMEOUT_SEC", "8"))
    request_gap = float(os.getenv("MUBASHER_REALTIME_REQUEST_GAP_SEC", "0.01"))
    auth_drain = float(os.getenv("MUBASHER_REALTIME_AUTH_DRAIN_SEC", "0.8"))

    with socket.create_connection((auth.host, auth.port), timeout=connect_timeout) as sock:
        sock.settimeout(0.1)
        sock.sendall(auth.payload + b"\n")
        _socket_drain(sock, auth_drain)

        for symbol in requested:
            sock.sendall(b"1\x1c10\x1cCASE~" + symbol.encode("ascii", errors="ignore") + b"\x1c\n")
            if request_gap > 0:
                time.sleep(request_gap)

        raw = _socket_drain(sock, read_timeout)

    snapshots: dict[str, MubasherQuoteSnapshot] = {}
    for snapshot in parse_quote_messages(raw):
        if snapshot.symbol in seen:
            snapshots[snapshot.symbol] = snapshot
    return snapshots
