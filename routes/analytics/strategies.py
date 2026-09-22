import sys
from fastapi import APIRouter, HTTPException

from core import Heimdall
from core.analyzers import ExecutionWatchdog, Midgard
from core.settings import settings
from database import TickerStrategyMetrics
from routes.analytics.cache import _cache_is_fresh, _cache_ttl_seconds, _mark_cache_timestamp
from routes.shared import STRATEGY_CACHE

public_router = APIRouter(tags=["analytics"])


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback


@public_router.get("/api/v1/strategy", summary="Strategy Proposals", description="Generates AI-driven strategy modification proposals based on recent performance.")
async def get_strategy_proposal():
    try:
        ttl = _cache_ttl_seconds("STRATEGY_CACHE_TTL_SEC", 300)
        watchdog = _resolve_symbol("ExecutionWatchdog", ExecutionWatchdog)
        if STRATEGY_CACHE["data"] and _cache_is_fresh(STRATEGY_CACHE, ttl):
            return {"status": "success", "data": STRATEGY_CACHE["data"], "source": "cache"}
        proposal = await watchdog.async_generate_strategy_proposal()
        STRATEGY_CACHE["data"] = proposal
        _mark_cache_timestamp(STRATEGY_CACHE)
        return {"status": "success", "data": proposal}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get(
    "/api/v1/analytics/health",
    summary="Portfolio Health",
    description="Returns portfolio diagnostics from Heimdall without overriding the operational health probe.",
)
def get_health():
    heimdall = _resolve_symbol("Heimdall", Heimdall)
    return heimdall.get_portfolio_health()


@public_router.get("/api/v1/audit", summary="Strategy Audit", description="Audits the performance of active strategies.")
def get_audit(days: int | None = None):
    midgard = _resolve_symbol("Midgard", Midgard)
    return midgard.audit_strategies(days_limit=days)


@public_router.get("/api/v1/watcher/status", summary="Watcher Status", description="Returns the status of background monitoring services.")
def get_watcher_status():
    from routes.shared import scheduler

    return {
        "status": "success",
        "watcher": {
            "running": scheduler.running if scheduler else False,
            "intraday_enabled": settings.ENABLE_INTRADAY_ALERTS,
            "auto_trade_enabled": settings.AUTO_TRADE_ENABLED,
            "market_open": settings.is_market_open(),
        },
    }


@public_router.get("/api/v1/strategy/metrics", summary="Strategy Accuracy Metrics", description="Returns weekly WFA validation results for all tickers.")
def get_strategy_metrics():
    try:
        metrics_model = _resolve_symbol("TickerStrategyMetrics", TickerStrategyMetrics)
        metrics = list(metrics_model.select().dicts().iterator())
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
