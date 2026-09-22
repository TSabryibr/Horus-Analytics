import sys
from unittest.mock import MagicMock

# Mock redis module in sys.modules so patch("redis.Redis") resolves successfully even without redis-py installed.
if "redis" not in sys.modules:
    mock_redis = MagicMock()
    mock_redis.Redis = MagicMock
    sys.modules["redis"] = mock_redis

import pytest
from unittest.mock import patch
from utils.redis_client import RedisClient

def test_redis_client_in_memory_fallback():
    """Verify that when Redis is unavailable, RedisClient falls back to in-memory mode."""
    # Force Redis connection failure
    with patch("redis.Redis") as mock_redis_class:
        mock_redis_class.side_effect = Exception("Connection refused")
        
        # Instantiate client
        client = RedisClient()
        # Reset internal state to simulate offline status
        client._redis = None
        client._in_memory = {}
        
        # Test basic GET/SET operations
        assert client.get("test_key") is None
        assert client.set("test_key", "test_value") is True
        assert client.get("test_key") == "test_value"
        
        # Test DELETE operation
        assert client.delete("test_key") is True
        assert client.get("test_key") is None
        
        # Test Set operations (SADD, SMEMBERS, SCARD, SISMEMBER)
        assert client.scard("test_set") == 0
        assert client.sadd("test_set", "item1") is True
        assert client.sadd("test_set", "item2") is True
        assert client.scard("test_set") == 2
        assert client.smembers("test_set") == {"item1", "item2"}
        assert client.sismember("test_set", "item1") is True
        assert client.sismember("test_set", "item3") is False

def test_redis_client_disabled_by_default(monkeypatch):
    """Verify that when REDIS_ENABLED is False (default), no Redis connection attempt is made."""
    with patch("redis.Redis") as mock_redis_class:
        from core.settings import settings
        monkeypatch.setattr(settings, "REDIS_ENABLED", False, raising=False)
        client = RedisClient.__new__(RedisClient)
        client._initialized = False
        client.__init__()
        assert client._redis is None
        mock_redis_class.assert_not_called()


def test_redis_client_enabled_connects(monkeypatch):
    """Verify that when REDIS_ENABLED is True, connection attempt is made."""
    mock_instance = MagicMock()
    mock_instance.ping.return_value = True
    with patch("redis.Redis", return_value=mock_instance) as mock_redis_class:
        from core.settings import settings
        monkeypatch.setattr(settings, "REDIS_ENABLED", True, raising=False)
        client = RedisClient.__new__(RedisClient)
        client._initialized = False
        client.__init__()
        assert client._redis is mock_instance
        mock_redis_class.assert_called_once()
