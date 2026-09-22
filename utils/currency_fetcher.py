import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import time
import json
import datetime
import requests
from core.settings import settings
from utils.redis_client import redis_client


CACHE_FILE = Path(".parallel_rate_cache.json")

def get_parallel_usd_egp_rate() -> float:
    """
    Returns the parallel-market USD/EGP rate using a cached external feed with fallbacks.
    """
    # 1. Configuration checks from settings
    fetch_enabled = getattr(settings, "PARALLEL_RATE_FETCH_ENABLED", True)
    cache_ttl = getattr(settings, "PARALLEL_RATE_CACHE_TTL", 21600)  # Default: 6 hours
    premium = getattr(settings, "PARALLEL_RATE_PREMIUM", 0.05)       # Default: 5% premium
    static_fallback = getattr(settings, "USD_EGP_RATE", 48.5)

    # 2. Check Redis cache first
    cached_rate_str = redis_client.get("parallel_usd_egp_rate")
    if cached_rate_str:
        try:
            cache_data = json.loads(cached_rate_str)
            cached_time = cache_data.get("timestamp", 0)
            cached_rate = cache_data.get("rate", 0.0)
            
            # Check if cache is still within TTL
            if time.time() - cached_time < cache_ttl and cached_rate > 0.0:
                return float(cached_rate)
        except Exception:
            pass

    # 2b. Secondary local file cache check (fallback for cold start or Redis offline)
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
            
            cached_time = cache_data.get("timestamp", 0)
            cached_rate = cache_data.get("rate", 0.0)
            
            if time.time() - cached_time < cache_ttl and cached_rate > 0.0:
                # Populate Redis with local file cache data
                try:
                    redis_client.set("parallel_usd_egp_rate", json.dumps(cache_data), ex=cache_ttl)
                except Exception:
                    pass
                return float(cached_rate)
        except Exception:
            pass

    # 3. If fetch is disabled, just return the static configuration
    if not fetch_enabled:
        return float(static_fallback)

    # 4. Fetch official rate from public feed and apply parallel premium
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            official_rate = float(data["rates"]["EGP"])
            parallel_rate = round(official_rate * (1.0 + premium), 4)
            
            cache_data = {"rate": parallel_rate, "timestamp": time.time()}
            
            # Save to Redis
            try:
                redis_client.set("parallel_usd_egp_rate", json.dumps(cache_data), ex=cache_ttl)
            except Exception:
                pass

            # Save to local file as secondary fallback
            try:
                with open(CACHE_FILE, "w") as f:
                    json.dump(cache_data, f)
            except Exception:
                pass
                
            return parallel_rate
    except Exception:
        pass

    # 5. Stale Redis cache fallback
    cached_rate_str = redis_client.get("parallel_usd_egp_rate")
    if cached_rate_str:
        try:
            cache_data = json.loads(cached_rate_str)
            cached_rate = cache_data.get("rate", 0.0)
            if cached_rate > 0.0:
                return float(cached_rate)
        except Exception:
            pass

    # 5b. Stale file cache fallback
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
            cached_rate = cache_data.get("rate", 0.0)
            if cached_rate > 0.0:
                return float(cached_rate)
        except Exception:
            pass

    # 6. Absolute fallback: user settings
    return float(static_fallback)

def get_historical_usd_egp_rate(dt) -> float:
    """
    Estimates the parallel-market USD/EGP rate at a historical datetime.
    """
    if dt is None:
        return get_parallel_usd_egp_rate()
    
    # Ensure dt is a datetime or date object
    if isinstance(dt, str):
        try:
            from dateutil import parser
            dt = parser.parse(dt)
        except Exception:
            return get_parallel_usd_egp_rate()
            
    import datetime
    # Convert date to datetime if necessary
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.combine(dt, datetime.time.min)
        
    # Calculate difference in days from now
    now_dt = datetime.datetime.now(dt.tzinfo) if hasattr(dt, "tzinfo") and dt.tzinfo else datetime.datetime.now()
    try:
        days_ago = (now_dt - dt).days
    except Exception:
        days_ago = 999
    
    if days_ago <= 7:
        return get_parallel_usd_egp_rate()
        
    # Historical parallel market rate lookup for Egypt
    year = dt.year
    month = dt.month
    
    if year < 2024:
        return 35.0  # approximate parallel rate before massive slide
    elif year == 2024:
        if month <= 2:
            return 65.0  # Peak parallel market rate before float
        elif month == 3:
            return 50.0  # Transition period
        else:
            return 48.0  # Stabilized rate after float
    elif year == 2025:
        return 50.0  # 2025 stabilized average parallel rate
    else: # 2026 and later
        return 52.0  # current regime average parallel rate

def get_usd_trend_slope() -> float:
    """
    Returns the expected daily EGP depreciation rate against USD (as a percentage, e.g. 0.08% per day).
    Can be configured in settings under USD_DEVALUATION_DAILY_SLOPE, default is 0.08%.
    """
    return float(getattr(settings, "USD_DEVALUATION_DAILY_SLOPE", 0.08))

if __name__ == "__main__":
    print(f"Current parallel USD/EGP rate: {get_parallel_usd_egp_rate()}")
    test_date = datetime.datetime(2024, 2, 15)
    print(f"Parallel USD/EGP rate on {test_date}: {get_historical_usd_egp_rate(test_date)}")

