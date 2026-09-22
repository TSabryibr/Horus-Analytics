"""
HORUS ANALYTICS API (Refactored)
================================
Backend API for the Next.js Frontend.
Structured with modular routing for better maintainability.
"""

import os
import sys
import socket
import builtins
import uvicorn
import datetime
import tracemalloc

# Ensure Windows CP1256 console or redirected pipes never crash on Unicode emojis or symbols
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Optional memory profiling support
if os.getenv("TRACEMALLOC", "").lower() in ("1", "true", "yes"):
    tracemalloc.start(25)

# Compatibility imports for test monkeypatches
from core import TimeUtils
from core.pipeline import refresh_pipeline_state
from core.exclusions import get_excluded_tickers_upper
from core.market.HistoricalBackfill import run_backfill
from config.app_factory import (
    _readiness_gate_disabled,
    ImmutableStaticFiles,
    _is_stale_blocked_action,
)


def _should_run_startup_provisioning() -> bool:
    from database import ProvisioningState
    try:
        row = ProvisioningState.get_or_none(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
        if not row:
            return True
        target = int(getattr(row, "target_trading_days", 252) or 252)
        completed = int(getattr(row, "completed_trading_days", 0) or 0)
        status = str(getattr(row, "status", "IDLE")).upper()

        if status in ("COMPLETED", "COMPLETED_WITH_WARNINGS"):
            return False
        if status == "ERROR":
            return False
        if completed >= target and target > 0:
            return False
        return True
    except Exception as exc:
        import logging
        logging.getLogger("horus.api").warning(
            f"Failed to check provisioning state, defaulting to skip backfill to prevent accidental re-run: {exc}"
        )
        return False


def _finalize_startup_ready_state(backfill_result: dict, target_trading_days: int | None = None) -> None:
    from routes import shared
    status = backfill_result.get("status")
    durable_status = "COMPLETED_WITH_WARNINGS" if status == "COMPLETED_WITH_WARNINGS" else ("COMPLETED" if status == "COMPLETED" else "ERROR")
    total_days = backfill_result.get("total_days", 252)
    target_days = target_trading_days if target_trading_days is not None else total_days
    err = backfill_result.get("error")

    if durable_status == "COMPLETED":
        msg = "Horus Terminal Online"
        ready_status = "READY"
        bootstrap = True
        progress = 100
        step = "Ready"
    elif durable_status == "COMPLETED_WITH_WARNINGS":
        msg = "Horus Terminal Online (historical provisioning completed with warnings)"
        ready_status = "READY"
        bootstrap = True
        progress = 100
        step = "Ready"
    else:
        msg = f"Startup provisioning error: {err}"
        ready_status = "ERROR"
        bootstrap = False
        progress = 0
        step = "Error"

    shared.update_system_state({
        "status": ready_status,
        "bootstrap_complete": bootstrap,
        "progress": progress,
        "step": step,
        "message": msg,
        "provisioning_status": durable_status,
        "provisioning_target_trading_days": target_days,
        "provisioning_completed_trading_days": total_days,
        "provisioning_error": err,
    })


def _run_startup_provisioning_if_needed() -> dict:
    from core.market.HistoricalBackfill import run_backfill
    from database import ProvisioningState
    row = ProvisioningState.get_or_none(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
    if row and str(row.status).upper() == "COMPLETED_WITH_WARNINGS":
        result = {
            "status": "COMPLETED_WITH_WARNINGS",
            "total_days": getattr(row, "completed_trading_days", 252) or row.target_trading_days,
            "signals_found": 0,
            "target_kind": "TRADING_DAYS",
            "error": row.last_error,
        }
        _finalize_startup_ready_state(result, target_trading_days=row.target_trading_days)
        return result
    target_days = row.target_trading_days if row else 252
    run_fn = getattr(sys.modules.get("api"), "run_backfill", run_backfill)
    result = run_fn(days=target_days, mode="AUTOMATIC")
    _finalize_startup_ready_state(result, target_trading_days=target_days)
    return result


def _run_startup_provisioning_if_enabled() -> dict | None:
    raw = os.getenv("HORUS_ENABLE_STARTUP_PROVISIONING", "false").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return _run_startup_provisioning_if_needed()
    return None


# Enforce UTF-8 for Windows console
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Guard against stdout/stderr write failures in packaged/headless hosts.
_ORIGINAL_PRINT = builtins.print


def _safe_print(*args, **kwargs):
    try:
        _ORIGINAL_PRINT(*args, **kwargs)
    except OSError as exc:
        if getattr(exc, "errno", None) == 22:
            return
        raise


builtins.print = _safe_print


# Prevent repeated colorama stream wrapping from imported modules.
try:
    import colorama  # type: ignore
    colorama.init(autoreset=True, strip=False, convert=False, wrap=False)

    def _colorama_init_noop(*args, **kwargs):
        return None

    colorama.init = _colorama_init_noop
except Exception:
    pass

# Load FastAPI app and startup dependencies
from config.startup import (
    _resolve_api_port,
    _resolve_startup_session_mode,
    _startup_prompt,
    _maybe_prompt_to_open_browser,
    _complete_startup_interaction,
    _register_market_watchdog_jobs,
    _register_signal_scan_jobs,
    purge_excluded_tickers,
    _has_interactive_console,
)
from core.settings import settings, init_app_settings
init_app_settings()

allowed_origins = [
    f"http://127.0.0.1:{_resolve_api_port()}",
    f"http://localhost:{_resolve_api_port()}",
    "http://127.0.0.1:8100",
    "http://localhost:8100",
    "http://127.0.0.1:3100",
    "http://localhost:3100",
    "http://127.0.0.1:8200",
    "http://localhost:8200",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

from config.app_factory import create_app

app = create_app()


def _is_loopback_host(host: str) -> bool:
    normalized = str(host or "").strip().lower()
    return normalized in {"127.0.0.1", "localhost", "::1"}


def _is_port_available(host: str, port: int) -> bool:
    probe_host = host or "127.0.0.1"
    family = socket.AF_INET6 if ":" in probe_host else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.bind((probe_host, port))
        return True
    except OSError:
        return False


def _build_uvicorn_run_kwargs(
    *,
    host: str,
    port: int,
    is_debug: bool,
    is_frozen: bool,
    project_root: str,
) -> dict:
    should_reload = is_debug and not is_frozen
    kwargs = {
        "app": "api:app",
        "host": host,
        "port": port,
        "reload": should_reload,
    }

    if not should_reload:
        return kwargs

    reload_dirs = [
        os.path.join(project_root, "routes"),
        os.path.join(project_root, "data_engine"),
    ]
    from core.pipeline import _env_bool
    if _env_bool("RELOAD_INCLUDE_PROJECT_ROOT", False):
        reload_dirs.insert(0, project_root)
    reload_dirs = [p for p in reload_dirs if os.path.isdir(p)]
    if not reload_dirs:
        reload_dirs = [project_root]

    kwargs.update(
        {
            "reload_dirs": reload_dirs,
            "reload_includes": ["*.py"],
            "reload_excludes": [
                "__pycache__",
                "*.pyc",
                "*.log",
                "tests/*",
                ".git/*",
                ".venv/*",
                "venv/*",
                "frontend/*",
                "data/*",
            ],
        }
    )
    return kwargs


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    
    # Configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = _resolve_api_port()
    is_frozen = getattr(sys, 'frozen', False)
    is_debug = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    
    if not _is_port_available(host, port):
        print(
            f"Horus Analytics cannot start because {host}:{port} is already in use. "
            "Close the existing Horus/API process or choose a different PORT."
        )
        sys.exit(98)
    
    from config.app_factory import _warn_if_auth_disabled_on_non_loopback
    _warn_if_auth_disabled_on_non_loopback(host)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run(
        **_build_uvicorn_run_kwargs(
            host=host,
            port=port,
            is_debug=is_debug,
            is_frozen=is_frozen,
            project_root=project_root,
        )
    )
