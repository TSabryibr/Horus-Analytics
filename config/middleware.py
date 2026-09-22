import os
import uuid
import traceback
import logging
from typing import Any, cast

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.gzip import GZipMiddleware

from core import TimeUtils
from core.settings import settings as core_settings
from routes.shared import limiter

logger = logging.getLogger("horus.api")

READINESS_PROBE_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/health",
    "/api/status",
    "/api/v1/system/boot-status",
    "/api/v1/system/status",
    "/api/v1/system/full-status",
    "/api/v1/health",
    "/api/v1/simulate/status",
    "/api/v1/simulation/status",
    "/api/v1/system/confirm-holiday",
}

STALE_BLOCKED_ACTION_PATHS = {
    "/api/v1/scanner/start",
    "/api/v1/live/start",
    "/api/v1/live/stop",
    "/api/v1/control/scan",
    "/api/v1/strategy/apply",
    "/api/v1/signals/publish",
    "/api/v1/signals/publish/retry",
    "/api/v1/signals/publish/retry-latest",
    "/api/v1/signals/outcomes/rebuild",
    "/api/v1/signals/validation/walkforward/run",
}

STALE_BLOCKED_ACTION_PREFIXES = (
    "/api/v1/portfolio/add",
    "/api/v1/trade/add",
    "/api/v1/portfolio/close",
    "/api/v1/trade/close",
    "/api/v1/portfolio/update",
    "/api/v1/portfolio/seed",
    "/api/v1/portfolios",
)


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    import api
    default_origins = getattr(api, "allowed_origins", [
        "http://127.0.0.1:8200",
        "http://localhost:8200",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ])
    env_origins = [x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if x.strip()]
    allowed_origins = list(dict.fromkeys(default_origins + [o for o in env_origins if o != "*"]))
    if origin and (origin in allowed_origins or os.getenv("HORUS_ALLOW_ANY_CORS_ORIGIN", "").strip().lower() in {"1", "true", "yes", "on"}):
        allow_origin = origin
    else:
        allow_origin = allowed_origins[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }


def _readiness_gate_disabled() -> bool:
    raw = os.getenv("HORUS_DISABLE_READINESS_GATE", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    return "PYTEST_CURRENT_TEST" in os.environ


def _is_non_trading_day() -> bool:
    try:
        now = TimeUtils.now()
        weekend_days = getattr(core_settings, "MARKET_WEEKEND", [4, 5])
        if now.weekday() in weekend_days:
            return True
        return core_settings._is_db_holiday(now.date())
    except Exception:
        return False


def _is_stale_blocked_action(method: str, path: str) -> bool:
    if method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    if path == "/api/v1/portfolios/default":
        return False
    if path in STALE_BLOCKED_ACTION_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in STALE_BLOCKED_ACTION_PREFIXES)


def _unwrap_exception(exc: Exception) -> Exception:
    current = exc
    while hasattr(current, "exceptions"):
        nested = getattr(current, "exceptions", None) or ()
        if not nested:
            break
        first = nested[0]
        if not isinstance(first, Exception) or first is current:
            break
        current = first
    return current


def setup_cors_middleware(app: FastAPI) -> None:
    import api
    default_origins = getattr(api, "allowed_origins", [
        "http://127.0.0.1:8200",
        "http://localhost:8200",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ])
    env_origins = [x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if x.strip()]
    allow_any_cors_origin = os.getenv("HORUS_ALLOW_ANY_CORS_ORIGIN", "").strip().lower() in {"1", "true", "yes", "on"}
    if allow_any_cors_origin:
        allowed_origins = ["*"]
    else:
        allowed_origins = list(dict.fromkeys(default_origins + [origin for origin in env_origins if origin != "*"]))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_custom_middleware(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def request_id_tracing_middleware(request: Request, call_next):
        from core.tracing import generate_request_id, set_request_id
        req_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(req_id)
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    @app.middleware("http")
    async def readiness_gate_middleware(request: Request, call_next):
        import api
        import config.app_factory as app_factory

        gate_disabled_fn = getattr(api, "_readiness_gate_disabled", None) or getattr(app_factory, "_readiness_gate_disabled", _readiness_gate_disabled)
        if gate_disabled_fn():
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        request_context = {
            "method": request.method,
            "path": path,
        }
        if path in READINESS_PROBE_PATHS:
            return await call_next(request)

        system_state = api.refresh_pipeline_state()
        bootstrap_complete = bool(system_state.get("bootstrap_complete", False))
        cors_headers_fn = getattr(app_factory, "_cors_headers_for_request", _cors_headers_for_request)
        cors_headers = cors_headers_fn(request)

        if not bootstrap_complete:
            message = system_state.get("message", "System is starting up")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "system_state": system_state.get("status", "STARTING"),
                    "bootstrap_complete": False,
                    "pipeline_state": str(system_state.get("pipeline_state", "STARTING")).upper(),
                    "provisioning_status": system_state.get("provisioning_status"),
                    "provisioning_target_trading_days": system_state.get("provisioning_target_trading_days"),
                    "provisioning_completed_trading_days": system_state.get("provisioning_completed_trading_days"),
                    "provisioning_error": system_state.get("provisioning_error"),
                    "message": message,
                    "retry_after": 5,
                    **request_context,
                },
                headers={"Retry-After": "5", **cors_headers},
            )

        pipeline_state = str(system_state.get("pipeline_state", "DEGRADED")).upper()
        stale_overridden = bool(system_state.get("stale_override", False))
        is_non_trading_fn = getattr(app_factory, "_is_non_trading_day", _is_non_trading_day)
        if not stale_overridden and pipeline_state == "STALE" and is_non_trading_fn():
            stale_overridden = True

        stale_blocked_fn = getattr(app_factory, "_is_stale_blocked_action", _is_stale_blocked_action)
        if stale_blocked_fn(request.method, path) and pipeline_state != "FRESH" and not stale_overridden:
            message = system_state.get("message", "Pipeline is not fresh enough for active operations.")
            freshness = system_state.get("freshness") or {}
            last_updated = freshness.get("last_updated") or None
            expected_date = freshness.get("expected_last_working_day") or None
            if last_updated is None:
                try:
                    from routes.data import get_data_status_logic
                    ds = get_data_status_logic()
                    last_updated = ds.get("last_updated")
                    history = ds.get("history") or {}
                    expected_date = history.get("expected_last_working_day") or expected_date
                except Exception:
                    pass
            return JSONResponse(
                status_code=503,
                content={
                    "status": "stale_mode",
                    "system_state": system_state.get("status", "READY"),
                    "bootstrap_complete": True,
                    "pipeline_state": pipeline_state,
                    "message": message,
                    "last_updated": last_updated,
                    "expected_date": expected_date,
                    "retry_after": 15,
                    **request_context,
                },
                headers={"Retry-After": "15", **cors_headers},
            )

        return await call_next(request)

    @app.middleware("http")
    async def api_no_cache_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/") or request.url.path in {"/health", "/api/status"}:
            response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            response.headers.setdefault("Pragma", "no-cache")
            response.headers.setdefault("Expires", "0")
        return response


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler_wrapper(request: Request, exc: Exception):
        error_id = getattr(getattr(request, "state", None), "request_id", None) or str(uuid.uuid4())
        tb = traceback.format_exc()
        logger.error(f"[{error_id}] {request.method} {request.url.path}\n{tb}")
        root_exc = _unwrap_exception(exc)

        status_code = 500
        if isinstance(root_exc, HTTPException):
            status_code = getattr(root_exc, "status_code", 500)
        elif hasattr(root_exc, "status_code"):
            try:
                status_code = int(getattr(root_exc, "status_code", 500))
            except (ValueError, TypeError):
                status_code = 500

        cors_headers = _cors_headers_for_request(request)

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": str(root_exc),
                "error_id": error_id,
                "request_id": error_id,
                "error_type": type(root_exc).__name__,
                "method": request.method,
                "path": request.url.path,
            },
            headers={"X-Request-ID": error_id, **cors_headers}
        )
