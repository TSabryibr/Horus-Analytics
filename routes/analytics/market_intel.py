import logging
import sys
from fastapi import APIRouter, HTTPException, Request

from core import MarketPredictor, TimeUtils
from core.analyzers import Helheim, SentimentCrawler, Svartalfheim, Vanaheim
from core.market import SectorRotation, SmartMoneyTracker
from routes.analytics.cache import (
    _cache_age_seconds,
    _cache_is_fresh,
    _cache_ttl_seconds,
    _disk_grace_ttl_seconds,
    _load_news_cache_from_disk,
    _mark_cache_timestamp,
    _persist_news_cache_to_disk,
)
from routes.analytics.models import PredictionRequest
from routes.shared import (
    NEWS_CACHE,
    ORACLE_CACHE,
    SECTOR_CACHE,
    TRAP_CACHE,
    WHALE_CACHE,
    limiter,
)

logger = logging.getLogger(__name__)

public_router = APIRouter(tags=["analytics"])
router = APIRouter(tags=["analytics"])


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback


@public_router.get("/api/v1/news", summary="Get Market News", description="Retrieves aggregated market news and sentiment analysis from various sources via SentimentCrawler.")
async def get_market_news():
    try:
        ttl = _cache_ttl_seconds("NEWS_CACHE_TTL_SEC", 300)
        disk_grace_ttl = _disk_grace_ttl_seconds("NEWS_DISK_GRACE_TTL_SEC", 300)
        crawler = _resolve_symbol("SentimentCrawler", SentimentCrawler)

        if NEWS_CACHE.get("cache_source") != "memory":
            _load_news_cache_from_disk()

        # Robust Cache Handling
        if NEWS_CACHE["data"] and _cache_is_fresh(NEWS_CACHE, ttl):
            cached = crawler.sanitize_market_news_payload(NEWS_CACHE["data"])
            NEWS_CACHE["data"] = cached
            # Standardize stories and sentiment extraction
            stories = cached.get("stories", []) if isinstance(cached, dict) else cached
            bifrost = crawler.get_bifrost_sentiment(cached)
            return {
                "status": "success",
                "data": stories,
                "count": len(stories),
                "source": "cache",
                "bifrost": bifrost,
                "macro_correlation": cached.get("macro_correlation", 0) if isinstance(cached, dict) else 0,
            }
        if (
            NEWS_CACHE.get("data")
            and NEWS_CACHE.get("cache_source") == "disk"
            and ((_cache_age_seconds(NEWS_CACHE) or float("inf")) <= disk_grace_ttl)
        ):
            cached = crawler.sanitize_market_news_payload(NEWS_CACHE["data"])
            NEWS_CACHE["data"] = cached
            stories = cached.get("stories", []) if isinstance(cached, dict) else cached
            bifrost = crawler.get_bifrost_sentiment(cached)
            return {
                "status": "success",
                "data": stories,
                "count": len(stories),
                "source": "cache",
                "cache_state": "stale",
                "bifrost": bifrost,
                "macro_correlation": cached.get("macro_correlation", 0) if isinstance(cached, dict) else 0,
            }

        # Fetch Live
        time_utils = _resolve_symbol("TimeUtils", TimeUtils)
        raw_news = await crawler.async_gather_gossip()
        news_payload = crawler.sanitize_market_news_payload(raw_news)
        NEWS_CACHE["data"] = news_payload
        _mark_cache_timestamp(NEWS_CACHE)
        _persist_news_cache_to_disk(
            news_payload,
            NEWS_CACHE.get("timestamp") or time_utils.now(),
            NEWS_CACHE.get("version", -1),
        )

        stories = news_payload.get("stories", [])
        bifrost = crawler.get_bifrost_sentiment(news_payload)

        return {
            "status": "success",
            "data": stories,
            "count": len(stories),
            "bifrost": bifrost,
            "macro_correlation": news_payload.get("macro_correlation", 0),
        }
    except Exception as e:
        logger.error(f"News API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/sectors", summary="Sector Rotation Analysis", description="Analyzes sector performance, momentum, and rotation trends.")
async def get_sector_map():
    try:
        ttl = _cache_ttl_seconds("SECTOR_CACHE_TTL_SEC", 300)
        sector_rotation = _resolve_symbol("SectorRotation", SectorRotation)
        if SECTOR_CACHE["data"] and _cache_is_fresh(SECTOR_CACHE, ttl):
            return {"status": "success", "data": SECTOR_CACHE["data"], "count": len(SECTOR_CACHE["data"]), "source": "cache"}
        data = await sector_rotation.async_analyze_rotation()
        SECTOR_CACHE["data"] = data
        _mark_cache_timestamp(SECTOR_CACHE)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/traps", summary="Market Trap Detection", description="Identifies potential Bull and Bear traps using Svartalfheim logic.")
async def get_market_traps():
    try:
        ttl = _cache_ttl_seconds("TRAP_CACHE_TTL_SEC", 300)
        svartalfheim = _resolve_symbol("Svartalfheim", Svartalfheim)
        if TRAP_CACHE["data"] and _cache_is_fresh(TRAP_CACHE, ttl):
            return {"status": "success", "data": TRAP_CACHE["data"], "source": "cache"}
        data = await svartalfheim.async_hunt_traps()
        TRAP_CACHE["data"] = data
        _mark_cache_timestamp(TRAP_CACHE)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/prediction", summary="Market Predictions", description="Generates macro market health checks or short-term squeeze predictions.")
def get_prediction(req: PredictionRequest):
    try:
        predictor = _resolve_symbol("MarketPredictor", MarketPredictor)
        if req.mode == "SQUEEZE":
            return {"status": "success", "mode": "SQUEEZE", "data": predictor.hunt_the_coil()}
        ttl = _cache_ttl_seconds("ORACLE_CACHE_TTL_SEC", 300)
        index_upper = str(req.index).upper()

        # Initialize cache data as dict if needed
        if ORACLE_CACHE["data"] is None or not isinstance(ORACLE_CACHE["data"], dict) or "ticker" in (ORACLE_CACHE["data"] or {}):
            ORACLE_CACHE["data"] = {}

        if index_upper in ["EGX30", "EGX70", "EGX100"]:
            if index_upper in ORACLE_CACHE["data"] and _cache_is_fresh(ORACLE_CACHE, ttl):
                return {"status": "success", "mode": "MACRO", "data": ORACLE_CACHE["data"][index_upper]}

        data = predictor.check_macro_health(index_upper)

        if index_upper in ["EGX30", "EGX70", "EGX100"]:
            ORACLE_CACHE["data"][index_upper] = data
            _mark_cache_timestamp(ORACLE_CACHE)

        return {"status": "success", "mode": "MACRO", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/whales", summary="Whale Tracking", description="Detects smart money accumulation and distribution patterns.")
async def get_whales():
    ttl = _cache_ttl_seconds("WHALE_CACHE_TTL_SEC", 300)
    vanaheim = _resolve_symbol("Vanaheim", Vanaheim)
    if WHALE_CACHE["data"] and _cache_is_fresh(WHALE_CACHE, ttl):
        return WHALE_CACHE["data"]
    WHALE_CACHE["data"] = await vanaheim.async_hunt_whales()
    _mark_cache_timestamp(WHALE_CACHE)
    return WHALE_CACHE["data"]


@public_router.get("/api/v1/smart-money", summary="Smart Money Flow", description="Tracks institutional money flow using advanced volume analysis.")
@limiter.limit("10/minute")
def get_smart_money(request: Request):
    try:
        from routes.scanner import sanitize_floats
        smart_money = _resolve_symbol("SmartMoneyTracker", SmartMoneyTracker)

        df = smart_money.scan_for_whales()
        if df.empty:
            return {"status": "success", "data": []}

        # Convert to list of dicts
        data = df.to_dict(orient="records")
        return {"status": "success", "data": sanitize_floats(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/seasonality", summary="Ticker Seasonality", description="Analyzes historical seasonality patterns for a specific ticker.")
def get_seasonality(ticker: str = "COMI"):
    helheim = _resolve_symbol("Helheim", Helheim)
    return helheim.analyze_seasonality(ticker)


@public_router.get("/api/v1/seasonality/market", summary="Market Seasonality", description="Analyzes broader market seasonality trends.")
def get_market_seasonality():
    helheim = _resolve_symbol("Helheim", Helheim)
    return helheim.get_market_seasonality()


@public_router.get("/api/v1/rrg", summary="Relative Rotation Graph", description="Provides RRG data for sectors or individual stocks vs Benchmark.")
def get_rrg(view: str = "sectors", sector: str | None = None, trail: int = 10):
    try:
        from routes.scanner import sanitize_floats
        sector_rotation = _resolve_symbol("SectorRotation", SectorRotation)

        if view == "sectors":
            data = sector_rotation.analyze_rotation(trail_days=trail)
        else:
            mode = "SECTOR" if sector else "ALL"
            data = sector_rotation.analyze_stock_rotation(view_mode=mode, sector_name=sector, trail_days=trail)

        return {"status": "success", "data": sanitize_floats(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/confluence", summary="Composite Confluence Score", description="Synthesizes multi-module intelligence (Macro, RRG, Seasonality, Whales, Traps) into 1-to-5 star conviction ratings.")
async def get_confluence(ticker: str = "COMI"):
    try:
        from core.confluence import ConfluenceEngine
        from routes.shared import SECTOR_CACHE, WHALE_CACHE, TRAP_CACHE, ORACLE_CACHE
        
        sector_data = SECTOR_CACHE.get("data")
        whale_data = WHALE_CACHE.get("data")
        trap_data = TRAP_CACHE.get("data")
        oracle_data = ORACLE_CACHE.get("data")
        
        result = ConfluenceEngine.evaluate_ticker(
            ticker=ticker,
            sector_data=sector_data if isinstance(sector_data, dict) else None,
            whale_data=whale_data if isinstance(whale_data, dict) else None,
            trap_data=trap_data if isinstance(trap_data, dict) else None,
            oracle_data=oracle_data if isinstance(oracle_data, dict) else None,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/confluence/market", summary="Market Confluence Rankings", description="Ranks active market assets by multi-module conviction.")
async def get_market_confluence():
    try:
        from core.confluence import ConfluenceEngine
        from core.market import MarketLists
        from routes.shared import SECTOR_CACHE, WHALE_CACHE, TRAP_CACHE, ORACLE_CACHE
        
        sector_data = SECTOR_CACHE.get("data")
        whale_data = WHALE_CACHE.get("data")
        trap_data = TRAP_CACHE.get("data")
        oracle_data = ORACLE_CACHE.get("data")
        
        tickers = list(MarketLists.get_market_list("EGX30"))
        ranked = []
        for t in tickers:
            res = ConfluenceEngine.evaluate_ticker(
                ticker=t,
                sector_data=sector_data if isinstance(sector_data, dict) else None,
                whale_data=whale_data if isinstance(whale_data, dict) else None,
                trap_data=trap_data if isinstance(trap_data, dict) else None,
                oracle_data=oracle_data if isinstance(oracle_data, dict) else None,
            )
            ranked.append(res)
            
        ranked.sort(key=lambda x: -x["raw_score"])
        return {"status": "success", "count": len(ranked), "data": ranked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
