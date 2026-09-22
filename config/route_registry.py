import logging
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from core import TimeUtils
from core.auth import get_api_key
from core.websocket import ws_manager
from database import db
from routes.shared import get_durable_provisioning_state
from routes import (
    system, data, portfolio, analytics, settings, simulation,
    scanner, strategy, live, signals, reports, ai_report,
    notifications, audit, analysis_reports, replay, dryrun, subscriptions,
    compliance, telemetry
)

logger = logging.getLogger("horus.api")
API_VERSION = "1.3.0"


def register_routes(app: FastAPI) -> None:
    auth_dep = [Depends(get_api_key)]

    app.include_router(system.public_router)
    app.include_router(system.router)
    app.include_router(data.public_router)
    app.include_router(data.router)
    app.include_router(portfolio.router, dependencies=auth_dep)
    app.include_router(subscriptions.router, dependencies=auth_dep)
    app.include_router(reports.router, dependencies=auth_dep)
    app.include_router(analytics.public_router)
    app.include_router(analytics.router)
    app.include_router(settings.public_router)
    app.include_router(settings.router)
    app.include_router(simulation.public_router)
    app.include_router(simulation.router)
    app.include_router(scanner.router, dependencies=auth_dep)
    app.include_router(strategy.router, dependencies=auth_dep)
    app.include_router(live.public_router)
    app.include_router(live.router)
    app.include_router(signals.public_router)
    app.include_router(signals.router)
    app.include_router(ai_report.router, dependencies=auth_dep)
    app.include_router(analysis_reports.router, dependencies=auth_dep)
    app.include_router(notifications.router)
    app.include_router(audit.router)
    app.include_router(compliance.router)
    app.include_router(replay.public_router)
    app.include_router(replay.router)
    app.include_router(dryrun.public_router)
    app.include_router(dryrun.router)
    app.include_router(telemetry.router)


def register_websocket(app: FastAPI) -> None:
    from core.auth import is_auth_enforced, is_valid_api_key

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        if is_auth_enforced():
            api_key = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key")
            if not is_valid_api_key(api_key):
                await websocket.close(code=1008, reason="Unauthorized")
                return

        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            ws_manager.disconnect(websocket)


def register_legacy_aliases(app: FastAPI) -> None:
    import api
    auth_dep = [Depends(get_api_key)]

    @app.get("/api/v1/health")
    def health_check():
        system_state = api.refresh_pipeline_state()
        system_status = system_state.get("status", "STARTING")
        system_message = system_state.get("message", "")
        system_step = system_state.get("step", "")
        system_progress = system_state.get("progress", 0)

        db_status = "DISCONNECTED"
        try:
            db.connect(reuse_if_open=True)
            db_status = "CONNECTED"
        except Exception as e:
            logger.error(f"Health check DB connection failed: {e}")
            db_status = "ERROR"

        payload = {
            "system": "Horus Analytics",
            "version": API_VERSION,
            "state": system_status,
            "message": system_message,
            "step": system_step,
            "progress": system_progress,
            "provisioning_status": system_state.get("provisioning_status"),
            "provisioning_target_trading_days": system_state.get("provisioning_target_trading_days"),
            "provisioning_completed_trading_days": system_state.get("provisioning_completed_trading_days"),
            "provisioning_error": system_state.get("provisioning_error"),
            "pipeline_state": system_state.get("pipeline_state", "UNKNOWN"),
            "stale_mode": bool(system_state.get("stale_mode", False)),
            "freshness": system_state.get("freshness", {}),
            "database": db_status,
            "timestamp": TimeUtils.now().isoformat(),
        }
        payload.update(get_durable_provisioning_state())

        if system_status == "ERROR":
            payload["status"] = "error"
            return JSONResponse(status_code=503, content=payload)
        elif system_status == "PROVISIONING":
            payload["status"] = "provisioning"
            return JSONResponse(status_code=503, content=payload, headers={"Retry-After": "5"})
        elif system_status == "STARTING":
            payload["status"] = "starting"
            return JSONResponse(status_code=503, content=payload, headers={"Retry-After": "5"})
        else:
            payload["status"] = "ok"
            return payload

    @app.get("/health")
    def health_check_legacy_alias():
        return health_check()

    @app.get("/api/status")
    def system_status_legacy_alias():
        from routes.system import get_system_status
        return get_system_status()

    @app.get("/api/v1/positions", dependencies=auth_dep)
    def get_positions_alias(portfolio_id: int | None = None):
        from routes.portfolio import get_positions
        return get_positions(portfolio_id)

    @app.get("/api/v1/intraday/{ticker}")
    def get_intraday_alias(ticker: str, limit: int = 100):
        from routes.data import get_intraday_data
        return get_intraday_data(ticker, limit)

    @app.get("/api/v1/trades", dependencies=auth_dep)
    def get_trades_alias():
        from routes.portfolio import get_trades
        return get_trades()

    @app.get("/api/v1/draupnir/status", dependencies=auth_dep)
    def legacy_draupnir_status(portfolio_id: int | None = None):
        from routes.portfolio import get_portfolio
        return get_portfolio(portfolio_id)

    @app.get("/api/v1/ratatoskr/news")
    async def legacy_ratatoskr_news():
        from routes.analytics import get_market_news
        return await get_market_news()

    @app.get("/api/v1/fenrir/proposal")
    async def legacy_fenrir_proposal():
        from routes.analytics import get_strategy_proposal
        return await get_strategy_proposal()

    @app.get("/api/v1/jotunheim/arbitrage")
    def legacy_jotunheim_arbitrage(universe: str = "default"):
        from routes.analytics import get_arbitrage
        return get_arbitrage(universe)
