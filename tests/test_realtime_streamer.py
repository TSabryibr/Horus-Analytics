import pytest
import socket
import json
import datetime
import time
import zmq
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.settings import settings
from data_engine.harvester_service import run_harvest_loop, PID_FILE

class MockSocket:
    def __init__(self):
        self.sent_data = []
        self.recv_count = 0

    def sendall(self, data):
        self.sent_data.append(data)

    def settimeout(self, t):
        pass

    def recv(self, size):
        self.recv_count += 1
        if self.recv_count == 1:
            # First recv: return some auth response
            return b"AUTH_OK\n"
        elif self.recv_count == 2:
            # Second recv: return a valid binary quote message
            # Format matches data_engine/mubasher_realtime_source.py:
            # tag 3: COMI, tag 55: 12.50, tag 56: 500.0, tag 635: 20260711100000 (UTC)
            msg = (
                b"\x0a\x00\x04CASE\x1c"
                b"\x00\x03COMI\x1c"
                b"\x00\x3712.50\x1c"
                b"\x00\x38500.0\x1c"
                b"\x02\x7b20260711100000\x1c\n"
            )
            return msg
        elif self.recv_count == 3:
            # Third recv: simulate socket timeout
            raise socket.timeout()
        else:
            # Fourth recv: raise a custom exception to exit the infinite stream loop
            raise KeyboardInterrupt("StopStream")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@patch("socket.create_connection")
@patch("zmq.Context")
def test_realtime_streamer_loop(mock_zmq_context, mock_create_connection, tmp_path, monkeypatch):
    # 1. Setup temporary Mubasher log directory & config file
    mubasher_root = tmp_path / "Mubasher"
    logs_dir = mubasher_root / "logs"
    logs_dir.mkdir(parents=True)
    
    # Write a mock Log_ClientServicePlatform.txt file containing auth payload
    log_file = logs_dir / "Log_ClientServicePlatform.txt"
    log_file.write_bytes(
        b"Sending Auth Request to Realtime:127.0.0.1:9099 - MOCK_AUTH_PAYLOAD\x1c\n"
    )
    
    # Patch settings to point to our mock paths
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root))
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "TEST_USER")
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    
    # Mock ZeroMQ socket and context
    mock_pub_socket = MagicMock()
    mock_zmq_context.return_value.socket.return_value = mock_pub_socket
    
    # Mock Socket Connection
    mock_sock = MockSocket()
    mock_create_connection.return_value = mock_sock
    
    # Mock database symbol lookup to return list
    monkeypatch.setattr(
        "data_engine.mubasher_sqlite_source.list_intraday_symbols",
        lambda paths: ["COMI"]
    )
    monkeypatch.setattr(
        "data_engine.mubasher_sqlite_source.list_history_symbols",
        lambda paths: []
    )
    # Mock is_supported_ticker to return True
    monkeypatch.setattr("data_engine.ticker_filters.is_supported_ticker", lambda ticker: True)
    # Mock get_all_exclusions to return empty set
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: set())
    
    # Mock database upsert so it doesn't try to write to sqlite
    mock_upsert = MagicMock(return_value=1)
    monkeypatch.setattr("data_engine.intraday_store.upsert_intraday", mock_upsert)
    
    # Run the harvester streamer loop. It should exit on StopStream KeyboardInterrupt.
    with pytest.raises(KeyboardInterrupt, match="StopStream"):
        run_harvest_loop()
        
    # Verify TCP connections and subscriptions
    mock_create_connection.assert_called_once_with(("127.0.0.1", 9099), timeout=10)
    assert b"MOCK_AUTH_PAYLOAD" in mock_sock.sent_data[0]
    
    # Subscription message should match tag CASE~COMI
    assert b"1\x1c10\x1cCASE~COMI" in mock_sock.sent_data[1]
    
    # Verify ZMQ publication broadcasted the tick
    mock_pub_socket.send_string.assert_called()
    call_args = mock_pub_socket.send_string.call_args[0][0]
    assert call_args.startswith("TICK ")
    
    payload = json.loads(call_args[5:])
    assert payload["ticker"] == "COMI"
    assert payload["price"] == 12.50
    assert payload["volume"] == 500.0
    
    # Verify SQLite intraday database cache was updated in real-time
    mock_upsert.assert_called_once()
    upserted_df = mock_upsert.call_args[0][1]
    assert not upserted_df.empty
    assert upserted_df.iloc[0]["close"] == 12.50
    assert upserted_df.iloc[0]["volume"] == 500.0
