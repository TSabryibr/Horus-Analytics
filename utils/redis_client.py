import logging
import json
from typing import Any, Optional

logger = logging.getLogger("horus.redis")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
    logger.info("redis-py package is not installed. Falling back to in-memory cache.")

class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisClient, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._redis = None
        self._in_memory = {}
        self._initialized = True
        
        if REDIS_AVAILABLE:
            try:
                from core.settings import settings
                redis_enabled = getattr(settings, "REDIS_ENABLED", False)
                if not redis_enabled:
                    logger.debug("Redis is disabled (REDIS_ENABLED=0). Using in-memory cache.")
                    self._redis = None
                    return

                host = getattr(settings, "REDIS_HOST", "localhost")
                port = int(getattr(settings, "REDIS_PORT", 6379))
                db = int(getattr(settings, "REDIS_DB", 0))
                password = getattr(settings, "REDIS_PASSWORD", None)
                
                self._redis = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                    decode_responses=True
                )
                # Test connection
                self._redis.ping()
                logger.info(f"Connected to Redis at {host}:{port}/{db}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory mode.")
                self._redis = None

    @property
    def is_connected(self) -> bool:
        if not self._redis:
            return False
        try:
            return bool(self._redis.ping())
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        if self._redis:
            try:
                return self._redis.get(key)
            except Exception as e:
                logger.error(f"Redis get error for key '{key}': {e}. Falling back to in-memory.")
        return self._in_memory.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self._redis:
            try:
                self._redis.set(key, value, ex=ex)
                return True
            except Exception as e:
                logger.error(f"Redis set error for key '{key}': {e}. Falling back to in-memory.")
        
        self._in_memory[key] = value
        return True

    def delete(self, key: str) -> bool:
        if self._redis:
            try:
                self._redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error for key '{key}': {e}. Falling back to in-memory.")
        
        if key in self._in_memory:
            del self._in_memory[key]
            return True
        return False

    def sadd(self, key: str, member: str) -> bool:
        if self._redis:
            try:
                self._redis.sadd(key, member)
                return True
            except Exception as e:
                logger.error(f"Redis sadd error for key '{key}': {e}. Falling back to in-memory.")
        
        if key not in self._in_memory:
            self._in_memory[key] = set()
        elif not isinstance(self._in_memory[key], set):
            self._in_memory[key] = set()
            
        self._in_memory[key].add(member)
        return True

    def smembers(self, key: str) -> set:
        if self._redis:
            try:
                members = self._redis.smembers(key)
                return set(members) if members else set()
            except Exception as e:
                logger.error(f"Redis smembers error for key '{key}': {e}. Falling back to in-memory.")
        
        val = self._in_memory.get(key)
        if isinstance(val, set):
            return val
        return set()

    def scard(self, key: str) -> int:
        if self._redis:
            try:
                return int(self._redis.scard(key) or 0)
            except Exception as e:
                logger.error(f"Redis scard error for key '{key}': {e}. Falling back to in-memory.")
        
        val = self._in_memory.get(key)
        if isinstance(val, set):
            return len(val)
        return 0

    def sismember(self, key: str, member: str) -> bool:
        if self._redis:
            try:
                return bool(self._redis.sismember(key, member))
            except Exception as e:
                logger.error(f"Redis sismember error for key '{key}': {e}. Falling back to in-memory.")
        
        val = self._in_memory.get(key)
        if isinstance(val, set):
            return member in val
        return False

    def clear(self):
        self._in_memory.clear()
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass

redis_client = RedisClient()
