from core.settings import settings
import zmq
import json
import time
import pytest
from unittest.mock import MagicMock
from core.market.LiveFeedManager import  LiveFeedManager

def test_zmq_subscriber_receives_data(monkeypatch):
    # 1. Setup a dummy ZMQ publisher on a random free port
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.LINGER, 0)
    port = pub_socket.bind_to_random_port("tcp://127.0.0.1")
    
    # 2. Redirect LiveFeedManager to connect to localhost via settings
    monkeypatch.setattr(settings, "ZMQ_HOST", "127.0.0.1", raising=False)
    monkeypatch.setattr(settings, "ZMQ_PORT", str(port), raising=False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    
    # 3. Start LiveFeedManager
    lfm = LiveFeedManager()
    
    import data_engine.parquet_writer
    mock_save = MagicMock()
    monkeypatch.setattr(data_engine.parquet_writer, "save_stream", mock_save)
    
    lfm.start_monitoring()
    
    try:
        base_time = 1750000000.0
        test_data = {
            "ticker": "COMI",
            "price": 90.5,
            "volume": 1000,
            "timestamp": base_time
        }
        time.sleep(1)
        pub_socket.send_string(f"TICK {json.dumps(test_data)}")
        time.sleep(0.2)
        # Next 5-minute bucket tick closes previous candle and triggers parquet_writer.save_stream
        closing_data = {
            "ticker": "COMI",
            "price": 91.0,
            "volume": 100,
            "timestamp": base_time + 305
        }
        pub_socket.send_string(f"TICK {json.dumps(closing_data)}")
        
        timeout = 5
        start = time.time()
        received = False
        while time.time() - start < timeout:
            if mock_save.called:
                received = True
                break
            time.sleep(0.1)
            
        assert received, "LiveFeedManager did not receive the ZMQ message"
        args, kwargs = mock_save.call_args
        assert args[0] == "COMI"
        assert args[1]['close'].iloc[0] == 90.5
        
    finally:
        lfm.stop_monitoring()
        pub_socket.close(linger=0)
        context.term()

def test_zmq_subscriber_handles_malformed_json(monkeypatch):
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.LINGER, 0)
    port = pub_socket.bind_to_random_port("tcp://127.0.0.1")
    
    monkeypatch.setattr(settings, "ZMQ_HOST", "127.0.0.1", raising=False)
    monkeypatch.setattr(settings, "ZMQ_PORT", str(port), raising=False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    
    lfm = LiveFeedManager()
    lfm.start_monitoring()
    
    try:
        time.sleep(1)
        pub_socket.send_string("TICK INVALID JSON")
        time.sleep(0.5)
        
        # Should not crash, should still be running
        assert lfm.is_running()
        
    finally:
        lfm.stop_monitoring()
        pub_socket.close(linger=0)
        context.term()
