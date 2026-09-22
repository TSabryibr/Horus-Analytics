import os
import asyncio
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.settings import settings as core_settings
from core.pipeline import (
    _env_bool, _env_int, _pipeline_worker_mode,
    _sync_all_with_timeout, set_pipeline_state
)
import core.pipeline as pipeline
from core import TelegramBot_Alerts
from data_engine.local_feed_selector import apply_startup_recommended_provider, format_quality_report
from routes.shared import scheduler, update_system_state
from routes import analytics, strategy
from utils.ollama_manager import OllamaManager
from config.scheduler_setup import register_scheduled_jobs

logger = logging.getLogger("horus.api")


def _initialize_ai_report_ollama_runtime(ollama) -> dict:
    del ollama
    logger.info("[Startup] Ollama AI report runtime is managed on demand. Startup warmup skipped.")
    return {
        "warmup_skipped": True,
        "reason": "on_demand_ai_report_lifecycle",
    }


def _run_startup_provisioning_if_enabled() -> dict | None:
    raw = os.getenv("HORUS_ENABLE_STARTUP_PROVISIONING", "false").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        import api
        if hasattr(api, "_run_startup_provisioning_if_needed"):
            return api._run_startup_provisioning_if_needed()
    return None


def _finalize_startup_ready_state(provisioning_result: dict | None = None) -> None:
    provisioning_result = dict(provisioning_result or {})
    provisioning_status = str(provisioning_result.get("status", "") or "").upper()

    if provisioning_status == "COMPLETED_WITH_WARNINGS":
        ready_message = "Horus Terminal Online (historical provisioning completed with warnings)"
    else:
        ready_message = "Horus Terminal Online"

    update_system_state(
        {
            "status": "READY",
            "message": ready_message,
            "progress": 100,
            "step": "Ready",
            "bootstrap_complete": True,
        }
    )


def _is_loopback_host(host: str) -> bool:
    normalized = (host or "").strip().lower()
    return normalized in {"127.0.0.1", "localhost", "::1"}


def _warn_if_auth_disabled_on_non_loopback(host: str) -> None:
    try:
        from core.auth import is_auth_enforced
    except Exception:
        is_auth_enforced = lambda: False

    if _is_loopback_host(host):
        return
    if is_auth_enforced():
        return
    logger.warning(
        "[Security] Auth is disabled and HOST=%s is non-loopback. "
        "Use HOST=127.0.0.1 or enable auth (HORUS_AUTH_MODE=api_key).",
        host,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Resolve api dynamically at lifespan startup to support test monkeypatching
    import api

    loop = asyncio.get_running_loop()
    previous_exception_handler = loop.get_exception_handler()

    def _loop_exception_handler(event_loop, context):
        exc = context.get("exception")
        message = str(context.get("message", ""))
        winerror = getattr(exc, "winerror", None)

        if isinstance(exc, ConnectionResetError) and (winerror == 10054 or "_call_connection_lost" in message):
            logger.debug(f"[AsyncIO] Ignored client connection reset: {exc}")
            return

        if previous_exception_handler:
            previous_exception_handler(event_loop, context)
        else:
            event_loop.default_exception_handler(context)

    loop.set_exception_handler(_loop_exception_handler)

    # 1. Unconditional schema initialization: guarantee tables & migrations exist
    # before any requests, background threads, or test short-circuits run.
    import database
    database.initialize_db()

    from core.audit import initialize_audit_table
    initialize_audit_table()

    disable_startup_thread = os.getenv("HORUS_DISABLE_STARTUP_THREAD", "").strip().lower() in ("1", "true", "yes", "on")
    if disable_startup_thread:
        logger.info("[Startup] Startup thread disabled (HORUS_DISABLE_STARTUP_THREAD).")
        update_system_state({
            "message": "Horus Terminal Online (test mode)",
            "progress": 100,
            "step": "Ready",
            "bootstrap_complete": True,
        })
        set_pipeline_state("FRESH")
        yield
        try:
            from utils.power import set_market_keepalive
            set_market_keepalive(False)
        except Exception:
            pass
        if pipeline._SYNC_WORKER:
            pipeline._SYNC_WORKER.stop()
            pipeline._SYNC_WORKER = None
        if scheduler.running:
            scheduler.shutdown()
        loop.set_exception_handler(previous_exception_handler)
        return

    _warn_if_auth_disabled_on_non_loopback(os.getenv("HOST", "127.0.0.1"))

    def background_startup():
        try:
            ollama = OllamaManager(base_url=core_settings.OLLAMA_BASE_URL)
            _initialize_ai_report_ollama_runtime(ollama)
            startup_mode_resolution = api._resolve_startup_session_mode()

            update_system_state({
                "status": "STARTING",
                "message": "Syncing Data Lake...",
                "step": "Data Sync",
                "progress": 10,
                "bootstrap_complete": False,
            })

            auto_select = os.getenv("LOCAL_FEED_AUTO_SELECT_ON_STARTUP", "1").strip().lower() in ("1", "true", "yes", "on")
            scope = os.getenv("LOCAL_FEED_AUTO_SELECT_SCOPE", "AUTO").strip().upper()
            if scope not in {"AUTO", "SMART", "TIMEFRAME", "UNIFIED"}:
                scope = "AUTO"
            force_unified = _env_bool("LOCAL_FEED_AUTO_SELECT_FORCE_UNIFIED", False)
            if auto_select:
                try:
                    want_unified = scope in {"AUTO", "SMART", "UNIFIED"}
                    want_force_unified = force_unified
                    if scope in {"AUTO", "SMART"}:
                        want_force_unified = False
                    selection = apply_startup_recommended_provider(
                        unified=want_unified,
                        force_unified=want_force_unified,
                    )
                    report = selection.get("report")
                    if report:
                        for ln in format_quality_report(report).splitlines():
                            logger.info(ln)
                    logger.info(
                        "[Startup] Local provider selection applied: "
                        f"scope={scope} "
                        f"force_unified={force_unified} "
                        f"mode={selection.get('mode')} "
                        f"selected={selection.get('selected_provider')} "
                        f"history={selection.get('history_provider')} "
                        f"intraday={selection.get('intraday_provider')}"
                    )
                except Exception as provider_e:
                    logger.error(f"[Startup] Local provider auto-selection failed: {provider_e}")
            else:
                logger.info(
                    "[Startup] Local provider auto-selection disabled. "
                    f"LOCAL_FEED_PROVIDER={getattr(core_settings, 'LOCAL_FEED_PROVIDER', 'AUTO')}"
                )

            skip_startup_sync = os.getenv("SKIP_STARTUP_SYNC", "true").lower() in ("1", "true", "yes")
            if _pipeline_worker_mode() != "off" and not _env_bool("FORCE_BOOTSTRAP_SYNC", False):
                skip_startup_sync = True
            strict_startup_sync = _env_bool("STRICT_STARTUP_SYNC", False)
            sync_timeout_seconds = _env_int("STARTUP_SYNC_TIMEOUT_SEC", 120)
            if not skip_startup_sync:
                try:
                    _sync_all_with_timeout(sync_timeout_seconds)
                except Exception as sync_e:
                    if strict_startup_sync:
                        raise RuntimeError(f"Data sync failed: {sync_e}") from sync_e
                    logger.error(f"[Startup] Data sync failed (continuing): {sync_e}")

            api.purge_excluded_tickers()
            update_system_state({"progress": 30})

            update_system_state({
                "message": "Warming Analytics Caches...",
                "step": "Analytics"
            })

            logger.info("[Startup] Global initialization complete.")
            update_system_state({"progress": 95, "step": "Orchestration"})

            try:
                analytics._load_news_cache_from_disk()
            except Exception as cache_e:
                logger.debug(f"[Startup] News cache rehydrate skipped: {cache_e}")
            try:
                strategy._load_strategy_health_cache_from_disk()
            except Exception as cache_e:
                logger.debug(f"[Startup] Strategy health cache rehydrate skipped: {cache_e}")

            register_scheduled_jobs(scheduler)

            provisioning_result = _run_startup_provisioning_if_enabled()
            _finalize_startup_ready_state(provisioning_result)
            api.refresh_pipeline_state(force=True)

            port = api._resolve_api_port()
            logger.info(
                "[Startup] Session mode "
                f"config={startup_mode_resolution.get('configured_session_mode')} "
                f"forced={str(startup_mode_resolution.get('forced_mode', False)).lower()} "
                f"effective={startup_mode_resolution.get('effective_session_mode')} "
                f"reason={startup_mode_resolution.get('reason')}"
            )

            eff_mode = startup_mode_resolution.get("effective_session_mode", "")
            if eff_mode == "LIVE" or core_settings.is_market_open():
                try:
                    from utils.power import set_market_keepalive
                    set_market_keepalive(True)
                except Exception as p_err:
                    logger.warning(f"[Startup] Failed to engage Windows keep-alive: {p_err}")

            def _start_post_ready_services():
                worker_mode = _pipeline_worker_mode()
                if worker_mode == "internal":
                    pipeline._SYNC_WORKER = pipeline.AdaptiveSyncWorker(logger=logger)
                    pipeline._SYNC_WORKER.start()
                    logger.info("[Startup] Adaptive sync worker started (mode=internal).")
                elif worker_mode == "external":
                    logger.info("[Startup] Adaptive sync worker is expected externally (mode=external).")
                else:
                    logger.info("[Startup] Adaptive sync worker disabled (mode=off).")

                # --- Mubasher persistent feed daemon ---
                # Read env directly: core/settings.py is frozen in PyInstaller
                # and may not have the MUBASHER_FEED_DAEMON_ENABLED attribute.
                _daemon_enabled = (
                    getattr(core_settings, "MUBASHER_FEED_DAEMON_ENABLED", None)
                    if hasattr(core_settings, "MUBASHER_FEED_DAEMON_ENABLED")
                    else os.getenv("MUBASHER_FEED_DAEMON_ENABLED", "0").strip().lower()
                          in ("1", "true", "yes", "on")
                )
                if _daemon_enabled:
                    try:
                        # Try source location first, then frozen-safe config location
                        try:
                            from data_engine.mubasher_feed_daemon import start_feed_daemon
                        except ImportError:
                            from config.mubasher_feed_daemon import start_feed_daemon
                        _mubasher_root = getattr(
                            core_settings, "MUBASHER_ROOT_DIR",
                            os.getenv("MUBASHER_ROOT_DIR", r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt"),
                        )
                        _daemon = start_feed_daemon(
                            mubasher_root=_mubasher_root,
                            realm="EGX",
                        )
                        logger.info("[Startup] Mubasher feed daemon started (persistent TCP stream).")
                    except Exception as daemon_err:
                        logger.error("[Startup] Failed to start Mubasher feed daemon: %s", daemon_err, exc_info=True)
                else:
                    logger.info("[Startup] Mubasher feed daemon disabled (MUBASHER_FEED_DAEMON_ENABLED=0).")
                # ----------------------------------------

                TelegramBot_Alerts.start_polling()
                logger.info("[Startup] Telegram command listener started.")

            api._complete_startup_interaction(port, _start_post_ready_services)

        except Exception as e:
            logger.critical(f"[Startup] CRITICAL ERROR: {e}")
            update_system_state({
                "status": "ERROR",
                "message": f"Startup Failed: {str(e)}"
            })

    threading.Thread(target=background_startup, daemon=True).start()
    yield
    try:
        from utils.power import set_market_keepalive
        set_market_keepalive(False)
    except Exception:
        pass
    if pipeline._SYNC_WORKER:
        pipeline._SYNC_WORKER.stop()
        pipeline._SYNC_WORKER = None
    try:
        try:
            from data_engine.mubasher_feed_daemon import stop_feed_daemon
        except ImportError:
            from config.mubasher_feed_daemon import stop_feed_daemon
        stop_feed_daemon()
    except Exception:
        pass
    if scheduler.running:
        try:
            scheduler.shutdown(wait=False)
        except Exception as shutdown_e:
            logger.debug(f"[Lifespan] Scheduler shutdown noise suppressed: {shutdown_e}")
    from core.worker_pool import shutdown_worker_pools
    shutdown_worker_pools(wait=False, cancel_futures=True)

    loop.set_exception_handler(previous_exception_handler)

