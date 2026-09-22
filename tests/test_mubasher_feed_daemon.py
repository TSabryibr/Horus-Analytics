import pytest
from unittest.mock import MagicMock
from data_engine.mubasher_feed_daemon import MubasherFeedDaemon

def test_extract_auth_token_extracts_tag_20():
    payload = b"150\x02100\x1c20\x02MY_SECRET_TOKEN_XYZ\x1c25\x02Memory: 123456\x1c"
    token = MubasherFeedDaemon._extract_auth_token(payload)
    assert token == b"20\x02MY_SECRET_TOKEN_XYZ"

def test_extract_auth_token_fallback():
    payload = b"150\x02100\x1c25\x02Memory: 123456\x1c"
    token = MubasherFeedDaemon._extract_auth_token(payload)
    assert token == payload

def test_auth_changed_ignores_memory_fluctuations():
    daemon = MubasherFeedDaemon(mubasher_root=".")
    
    auth1 = MagicMock()
    auth1.payload = b"150\x02100\x1c20\x02SAME_TOKEN\x1c25\x02Available Memory: 1000000\x1c"
    
    # First check should detect auth (sets _last_auth_hash and returns True)
    assert daemon._auth_changed(auth1) is True
    
    # Second check with DIFFERENT available memory but SAME token should NOT trigger change
    auth2 = MagicMock()
    auth2.payload = b"150\x02100\x1c20\x02SAME_TOKEN\x1c25\x02Available Memory: 9999999\x1c"
    assert daemon._auth_changed(auth2) is False

def test_auth_changed_detects_real_token_rotation():
    daemon = MubasherFeedDaemon(mubasher_root=".")
    
    auth1 = MagicMock()
    auth1.payload = b"150\x02100\x1c20\x02TOKEN_A\x1c25\x02Available Memory: 1000000\x1c"
    assert daemon._auth_changed(auth1) is True
    
    # Real token change to TOKEN_B
    auth2 = MagicMock()
    auth2.payload = b"150\x02100\x1c20\x02TOKEN_B\x1c25\x02Available Memory: 1000000\x1c"
    assert daemon._auth_changed(auth2) is True
