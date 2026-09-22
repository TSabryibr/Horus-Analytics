"""
FastAPI Application Factory for Horus Analytics.
Modularized into lifespan, scheduler, middleware, route registry, and static mounts.
"""

from fastapi import FastAPI

# Config & Observability
from config.observability import init_observability
from config.lifespan import (
    lifespan,
    _initialize_ai_report_ollama_runtime,
    _run_startup_provisioning_if_enabled,
    _finalize_startup_ready_state,
    _is_loopback_host,
    _warn_if_auth_disabled_on_non_loopback,
)
from config.middleware import (
    setup_cors_middleware,
    setup_custom_middleware,
    setup_exception_handlers,
    _cors_headers_for_request,
    _readiness_gate_disabled,
    _is_non_trading_day,
    _is_stale_blocked_action,
    _unwrap_exception,
)
from config.scheduler_setup import (
    register_scheduled_jobs,
    _wal_checkpoint,
)
from config.route_registry import (
    register_routes,
    register_websocket,
    register_legacy_aliases,
    API_VERSION,
)
from config.static_mounts import (
    mount_frontend_static,
    ImmutableStaticFiles,
)

from core.app_state import GLOBAL_APP_STATE, AppStateManager

__all__ = [
    "create_app",
    "get_app_state",
    "lifespan",
    "API_VERSION",
    "ImmutableStaticFiles",
    "_cors_headers_for_request",
    "_readiness_gate_disabled",
    "_is_non_trading_day",
    "_is_stale_blocked_action",
    "_unwrap_exception",
    "_wal_checkpoint",
    "_initialize_ai_report_ollama_runtime",
    "_run_startup_provisioning_if_enabled",
    "_finalize_startup_ready_state",
    "_is_loopback_host",
    "_warn_if_auth_disabled_on_non_loopback",
    "register_scheduled_jobs",
    "register_routes",
    "register_websocket",
    "register_legacy_aliases",
    "mount_frontend_static",
]


def get_app_state(app: FastAPI | None = None) -> AppStateManager:
    """Dependency helper to access the typed AppStateManager."""
    if app is not None and hasattr(app.state, "app_state"):
        return app.state.app_state
    return GLOBAL_APP_STATE


def create_app() -> FastAPI:
    """
    Constructs and configures the main FastAPI application.
    """
    app = FastAPI(
        title="Horus Analytics API",
        version=API_VERSION,
        lifespan=lifespan,
    )

    # 0. Typed Application State
    app.state.app_state = GLOBAL_APP_STATE

    # 1. Observability
    init_observability(app)

    # 2. CORS & Middleware
    setup_cors_middleware(app)
    setup_custom_middleware(app)

    # 3. Global Exception Handlers
    setup_exception_handlers(app)

    # 4. API Routers & Aliases
    register_routes(app)
    register_websocket(app)
    register_legacy_aliases(app)

    # 5. Frontend Static SPA
    mount_frontend_static(app)

    return app
