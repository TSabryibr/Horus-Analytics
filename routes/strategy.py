import time
import copy
import pandas as pd
from core import SignalAccuracyChecker
from fastapi import APIRouter, HTTPException, BackgroundTasks
import copy
import json
import os
import pandas as pd
import logging
import threading
import time
from pathlib import Path
from typing import Any
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from peewee import IntegrityError

logger = logging.getLogger("StrategyAPI")

from core.simulation import Optimizer
from core.simulation import PortfolioSimulator
from core import SignalAccuracyChecker
from core import TimeUtils
from core.auditor_service import auditor
from core.pine_lab import (
    activate_pine_scanner_profile,
    run_pine_import_backtest,
    build_pine_import_preview,
    build_promotion_summary,
    create_imported_pine_profile,
    create_pine_scanner_profile,
    get_active_pine_scanner_profile,
    get_pine_scanner_profile,
    list_pine_scanner_profiles,
    preflight_pine_script,
    run_pine_backtest,
    serialize_pine_scanner_profile,
)
from core.price_action import get_price_action_strategy, list_price_action_strategies
from core.price_action.backtest import activate_price_action_profile, promote_price_action_strategy, run_price_action_backtest
from core.price_action.executor import evaluate_price_action_catalog
from core.price_action.models import PriceActionStrategyFamily, PriceActionStrategyStatus
from core.strategy_profile_portfolios import ensure_strategy_profile_portfolio, serialize_strategy_profile_portfolio
from core.DataManager import DataManager
from routes import shared
from routes.settings import get_settings
from core.exclusions import filter_excluded_from_payload
from core.settings import settings as core_settings

router = APIRouter(tags=["strategy"])
from core.strategy.health_cache import (
    STRATEGY_HEALTH_CACHE,
    STRATEGY_HEALTH_CACHE_LOCK,
    _strategy_health_cache_ttl_sec,
    _strategy_health_disk_grace_ttl_sec,
    _current_data_version,
    reset_strategy_health_cache,
    _serialize_strategy_health_cache_key,
    _deserialize_strategy_health_cache_key,
    _persist_strategy_health_cache_to_disk,
    _load_strategy_health_cache_from_disk,
    _RECOMPUTE_LOCK,
)
from core.strategy.normalize import (
    _normalize_index_choice,
    _coerce_float,
    _require_nonzero_cost_assumptions,
    _coerce_bool,
    _normalize_strategy_params,
    _normalize_capital,
    _normalize_date_field,
    _resolve_backtest_window,
    _normalize_optional_positive_int,
    _require_text_field,
    _coerce_object,
    _normalize_backtest_summary_payload,
    _normalize_price_action_family,
    _normalize_price_action_status,
)
from core.strategy.optimize import (
    background_optimize_task,
    _safe_log_exception,
    _load_price_action_frame,
)


def _compute_strategy_health_sync(days: int, cache_key: tuple) -> dict:
    """Computes strategy health metrics synchronously and updates the cache."""
    try:
        end_date = TimeUtils.now()
        start_date = end_date - pd.Timedelta(days=days)
        results = SignalAccuracyChecker.run_accuracy_check(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            window_days=5
        )
        payload = {
            "win_rate": results['summary'].get('win_rate', 0),
            "total_signals": results['summary'].get('total_signals', 0),
            "avg_gain": results['summary'].get('avg_gain_pct', 0),
            "period_days": days
        }
        completed_ts = time.time()
        with STRATEGY_HEALTH_CACHE_LOCK:
            STRATEGY_HEALTH_CACHE["key"] = cache_key
            STRATEGY_HEALTH_CACHE["payload"] = copy.deepcopy(payload)
            STRATEGY_HEALTH_CACHE["ts"] = completed_ts
            STRATEGY_HEALTH_CACHE["source"] = "memory"
        _persist_strategy_health_cache_to_disk(key=cache_key, payload=payload, timestamp=completed_ts)
        return payload
    except Exception as e:
        logger.error(f"Strategy Health Check Error: {e}", exc_info=True)
        return {"win_rate": 0, "total_signals": 0, "avg_gain": 0}


def _trigger_background_recompute(days: int, cache_key: tuple):
    """Triggers background recompute of strategy health if not already running."""
    import sys
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        return
        
    if not _RECOMPUTE_LOCK.acquire(blocking=False):
        return  # Recomputation is already in progress
    
    def _worker():
        try:
            logger.info("Starting background recomputation of strategy health cache")
            _compute_strategy_health_sync(days, cache_key)
        finally:
            _RECOMPUTE_LOCK.release()
            logger.info("Finished background recomputation of strategy health cache")

    t = threading.Thread(target=_worker, name="strategy-health-recompute", daemon=True)
    t.start()


@router.get("/api/v1/strategy/health")
def get_strategy_health(days: int = 60):
    cache_key = (
        days or 0,
        _current_data_version(),
        TimeUtils.today().isoformat(),
    )
    ttl_sec = _strategy_health_cache_ttl_sec()
    now_ts = time.time()

    with STRATEGY_HEALTH_CACHE_LOCK:
        cache_loaded = STRATEGY_HEALTH_CACHE.get("payload") is not None
    if not cache_loaded:
        _load_strategy_health_cache_from_disk()

    with STRATEGY_HEALTH_CACHE_LOCK:
        cached_key = STRATEGY_HEALTH_CACHE.get("key")
        cached_payload = STRATEGY_HEALTH_CACHE.get("payload")
        cached_ts = STRATEGY_HEALTH_CACHE.get("ts") or 0.0
        cached_source = STRATEGY_HEALTH_CACHE.get("source")

        is_fresh = (
            ttl_sec > 0
            and cached_payload is not None
            and cached_key == cache_key
            and (now_ts - cached_ts) < ttl_sec
        )
        
        is_disk_grace_fresh = (
            cached_source == "disk"
            and cached_payload is not None
            and isinstance(cached_key, tuple)
            and len(cached_key) == 3
            and cached_key[0] == cache_key[0]
            and cached_key[2] == cache_key[2]
            and (now_ts - cached_ts) < _strategy_health_disk_grace_ttl_sec()
        )

    # If cache is completely fresh (by memory or disk grace rule), return it immediately
    if is_fresh or is_disk_grace_fresh:
        return copy.deepcopy(cached_payload)

    # Stale-while-revalidate: if we have a matching key whose TTL expired, return stale and recompute in background
    import sys
    is_testing = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
    if cached_payload is not None and cached_key == cache_key and not is_testing:
        _trigger_background_recompute(days, cache_key)
        return copy.deepcopy(cached_payload)

    # Cold start or cache key invalidation: compute synchronously
    logger.info("Computing strategy health synchronously")
    return _compute_strategy_health_sync(days, cache_key)

@router.post("/api/v1/optimizer/start")
@router.post("/api/v1/strategy/start")
async def start_optimization(background_tasks: BackgroundTasks, index: str = "ALL"):
    normalized_index = _normalize_index_choice(index)
    with shared.OPTIMIZATION_STATE_LOCK:
        if shared.OPTIMIZATION_STATE["status"] in ["RUNNING", "PREPARING"]:
             return {"message": "Optimization already running", "started": False, "index": shared.OPTIMIZATION_STATE.get("index")}
        shared.OPTIMIZATION_STATE["status"] = "PREPARING"
        shared.OPTIMIZATION_STATE["progress"] = 0
        shared.OPTIMIZATION_STATE["result"] = None
        shared.OPTIMIZATION_STATE["error"] = None
        shared.OPTIMIZATION_STATE["index"] = normalized_index
        background_tasks.add_task(background_optimize_task, normalized_index)
    return {"message": "Optimization started", "started": True, "index": normalized_index}

@router.get("/api/v1/optimizer/status")
@router.get("/api/v1/strategy/status")
def get_optimization_status():
    return shared.OPTIMIZATION_STATE


@router.post("/api/v1/strategy/pine/preflight")
def run_pine_preflight(payload: dict):
    try:
        script_source = _require_text_field(payload, "script_source")
        # Validate the market selection even though phase 1 preflight does not execute yet.
        _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        return preflight_pine_script(script_source, timeframe=timeframe)
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Pine preflight failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/import-preview")
def run_pine_import_preview(payload: dict):
    try:
        script_source = _require_text_field(payload, "script_source")
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        date_from = _normalize_date_field(payload, "date_from")
        date_to = _normalize_date_field(payload, "date_to")
        signal_overrides = _coerce_object(payload, "signal_overrides") if "signal_overrides" in payload else {}
        return build_pine_import_preview(
            script_source,
            market=market,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            signal_overrides=signal_overrides,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Pine import preview failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/import-backtest")
def backtest_pine_import_strategy(payload: dict):
    try:
        rule_spec = _coerce_object(payload, "rule_spec")
        operator_approved = bool(payload.get("operator_approved", False))
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        date_from = _normalize_date_field(payload, "date_from")
        date_to = _normalize_date_field(payload, "date_to")
        capital = _normalize_capital(payload.get("capital", 100000))
        commission_pct, slippage_pct = _require_nonzero_cost_assumptions(payload)

        return run_pine_import_backtest(
            rule_spec=rule_spec,
            operator_approved=operator_approved,
            market=market,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            capital=capital,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Pine import backtest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/import-profile")
def create_strategy_pine_import_profile(payload: dict):
    try:
        profile_name = _require_text_field(payload, "profile_name")
        script_source = _require_text_field(payload, "script_source")
        rule_spec = _coerce_object(payload, "rule_spec")
        operator_approved = bool(payload.get("operator_approved", False))
        if not operator_approved:
            raise HTTPException(status_code=400, detail="Operator approval is required before saving an imported rule profile.")

        source = rule_spec.get("source")
        if not isinstance(source, dict) or str(source.get("import_mode") or "").strip().upper() != "LOGIC_IMPORT":
            raise HTTPException(status_code=400, detail="rule_spec must come from the Logic Import workflow.")
        if not isinstance(rule_spec.get("execution_plan"), dict):
            raise HTTPException(status_code=400, detail="Imported rule profile requires an executable rule_spec.")

        market = _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        backtest_summary = _normalize_backtest_summary_payload(_coerce_object(payload, "backtest_summary"))
        ranking_summary = _coerce_object(payload, "ranking_summary")

        confidence = rule_spec.get("confidence") if isinstance(rule_spec.get("confidence"), dict) else {}
        compatibility_summary = {
            "readiness": "READY",
            "compatibility_score": round(float(confidence.get("overall", 0.0) or 0.0) * 100.0, 4),
            "messages": list(rule_spec.get("warnings") or []),
            "import_mode": "LOGIC_IMPORT",
        }

        profile = create_imported_pine_profile(
            profile_name=profile_name,
            script_source=script_source,
            market=market,
            timeframe=timeframe,
            rule_spec=rule_spec,
            backtest_summary=backtest_summary,
            compatibility_summary=compatibility_summary,
            ranking_summary=ranking_summary,
        )
        serialized_profile = serialize_pine_scanner_profile(profile)
        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "source_type": profile.source_type,
            "created_at": serialized_profile["created_at"],
            "ready_at": serialized_profile["ready_at"],
        }
    except IntegrityError:
        raise HTTPException(status_code=409, detail="An imported Pine profile with this name or script already exists")
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Create imported Pine profile failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/strategy/pine/scanner-profiles")
def get_pine_scanner_profiles():
    try:
        active_profile = get_active_pine_scanner_profile()
        return {
            "status": "success",
            "active_profile_id": active_profile.id if active_profile else None,
            "profiles": list_pine_scanner_profiles(),
        }
    except Exception as e:
        _safe_log_exception("List Pine scanner profiles failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/strategy/pine/scanner-profile/{profile_id}")
def get_pine_scanner_profile_detail(profile_id: int):
    try:
        profile = get_pine_scanner_profile(profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Requested Pine scanner profile was not found.")

        try:
            import_rule_spec = json.loads(getattr(profile, "import_rule_spec_json", "{}") or "{}")
        except json.JSONDecodeError:
            import_rule_spec = {}

        return {
            "status": "success",
            "profile": serialize_pine_scanner_profile(profile),
            "script_source": profile.script_source,
            "import_rule_spec": import_rule_spec if isinstance(import_rule_spec, dict) else {},
        }
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Fetch Pine scanner profile detail failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/create-scanner-profile")
def create_strategy_pine_scanner_profile(payload: dict):
    try:
        profile_name = _require_text_field(payload, "profile_name")
        script_source = _require_text_field(payload, "script_source")
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        backtest_summary = _normalize_backtest_summary_payload(_coerce_object(payload, "backtest_summary"))
        compatibility_summary = _coerce_object(payload, "compatibility_summary")
        ranking_summary = _coerce_object(payload, "ranking_summary")

        profile = create_pine_scanner_profile(
            profile_name=profile_name,
            script_source=script_source,
            market=market,
            timeframe=timeframe,
            backtest_summary=backtest_summary,
            compatibility_summary=compatibility_summary,
            ranking_summary=ranking_summary,
        )
        promotion_summary = build_promotion_summary(
            backtest_summary=backtest_summary,
            compatibility_summary=compatibility_summary,
            ranking_summary=ranking_summary,
        )
        if profile.profile_state == "ACTIVE":
            promotion_summary["profile_state"] = "ACTIVE"
            promotion_summary["failed_gates"] = []
        serialized_profile = serialize_pine_scanner_profile(profile)

        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "created_at": serialized_profile["created_at"],
            "ready_at": serialized_profile["ready_at"],
            "activated_at": serialized_profile["activated_at"],
            "activation_count": serialized_profile["activation_count"],
            "activation_history": serialized_profile["activation_history"],
            "promotion_summary": {
                "market": profile.market,
                "timeframe": profile.timeframe,
                "failed_gates": promotion_summary["failed_gates"],
                "thresholds": promotion_summary["thresholds"],
                "actuals": promotion_summary["actuals"],
            },
        }
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A Pine scanner profile with this name or script already exists")
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Create Pine scanner profile failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/activate-scanner-profile")
def activate_strategy_pine_scanner_profile(payload: dict):
    try:
        raw_profile_id = payload.get("profile_id")
        if raw_profile_id is None:
            raise HTTPException(status_code=400, detail="profile_id is required")
        try:
            profile_id = int(raw_profile_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="profile_id must be numeric") from exc

        profile = activate_pine_scanner_profile(profile_id)
        portfolio = ensure_strategy_profile_portfolio(profile)
        serialized_profile = serialize_pine_scanner_profile(profile)
        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "created_at": serialized_profile["created_at"],
            "ready_at": serialized_profile["ready_at"],
            "activated_at": serialized_profile["activated_at"],
            "activation_count": serialized_profile["activation_count"],
            "activation_history": serialized_profile["activation_history"],
            "portfolio": serialize_strategy_profile_portfolio(portfolio),
        }
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Activate Pine scanner profile failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/pine/backtest")
def backtest_pine_strategy(payload: dict):
    try:
        script_source = _require_text_field(payload, "script_source")
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        timeframe = _require_text_field(payload, "timeframe")
        date_from = _normalize_date_field(payload, "date_from")
        date_to = _normalize_date_field(payload, "date_to")
        capital = _normalize_capital(payload.get("capital", 100000))
        commission_pct, slippage_pct = _require_nonzero_cost_assumptions(payload)

        return run_pine_backtest(
            script_source=script_source,
            market=market,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            capital=capital,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Pine backtest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/strategy/price-action/catalog")
def get_price_action_catalog(
    family: str | None = None,
    include_warning_only: bool = True,
    status: str | None = None,
):
    try:
        selected_family = _normalize_price_action_family(family) if family else None
        selected_status = _normalize_price_action_status(status) if status else None
        strategies = list_price_action_strategies(
            family=selected_family,
            include_warning_only=include_warning_only,
            status=selected_status,
        )
        family_counts: dict[str, int] = {}
        for item in list_price_action_strategies():
            family_counts[item.family.value] = family_counts.get(item.family.value, 0) + 1
        return {
            "status": "success",
            "count": len(strategies),
            "counts_by_family": family_counts,
            "strategies": [strategy.to_dict() for strategy in strategies],
        }
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("List price-action catalog failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/price-action/evaluate")
def evaluate_price_action(payload: dict):
    try:
        ticker = _require_text_field(payload, "ticker").upper()
        family = payload.get("family")
        families = (_normalize_price_action_family(family),) if family else None
        include_warning_only = bool(payload.get("include_warning_only", True))
        intraday_data_available = bool(payload.get("intraday_data_available", False))
        intraday = any(fam is PriceActionStrategyFamily.INTRADAY for fam in families or ())
        frame = _load_price_action_frame(ticker, intraday=intraday)
        signals = evaluate_price_action_catalog(
            frame,
            ticker=ticker,
            families=families,
            include_warning_only=include_warning_only,
            intraday_data_available=intraday_data_available,
        )
        return {
            "status": "success",
            "ticker": ticker,
            "signal_count": len(signals),
            "signals": [signal.to_dict() for signal in signals],
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        _safe_log_exception("Evaluate price-action strategy failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/price-action/backtest")
def backtest_price_action(payload: dict):
    try:
        strategy_id = _require_text_field(payload, "strategy_id").lower()
        if get_price_action_strategy(strategy_id) is None:
            raise HTTPException(status_code=400, detail=f"Unknown price-action strategy '{strategy_id}'")
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        date_from = _normalize_date_field(payload, "date_from")
        date_to = _normalize_date_field(payload, "date_to")
        capital = _normalize_capital(payload.get("capital", 100000))
        commission_pct, slippage_pct = _require_nonzero_cost_assumptions(payload)
        ticker_limit = _normalize_optional_positive_int(payload, "ticker_limit")
        max_bars_per_ticker = _normalize_optional_positive_int(payload, "max_bars_per_ticker")
        max_trades = _normalize_optional_positive_int(payload, "max_trades")
        recent_sessions_only = _normalize_optional_positive_int(payload, "recent_sessions_only")
        return run_price_action_backtest(
            strategy_id=strategy_id,
            market=market,
            date_from=date_from,
            date_to=date_to,
            capital=capital,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
            ticker_limit=ticker_limit,
            max_bars_per_ticker=max_bars_per_ticker,
            max_trades=max_trades,
            recent_sessions_only=recent_sessions_only,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        _safe_log_exception("Price-action backtest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/price-action/promote")
def promote_price_action(payload: dict):
    try:
        profile_name = _require_text_field(payload, "profile_name")
        strategy_id = _require_text_field(payload, "strategy_id").lower()
        market = _normalize_index_choice(payload.get("market", "EGX30"))
        date_from = _normalize_date_field(payload, "date_from")
        date_to = _normalize_date_field(payload, "date_to")
        capital = _normalize_capital(payload.get("capital", 100000))
        commission_pct, slippage_pct = _require_nonzero_cost_assumptions(payload)
        ticker_limit = _normalize_optional_positive_int(payload, "ticker_limit")
        max_bars_per_ticker = _normalize_optional_positive_int(payload, "max_bars_per_ticker")
        max_trades = _normalize_optional_positive_int(payload, "max_trades")
        recent_sessions_only = _normalize_optional_positive_int(payload, "recent_sessions_only")
        profile = promote_price_action_strategy(
            profile_name=profile_name,
            strategy_id=strategy_id,
            market=market,
            date_from=date_from,
            date_to=date_to,
            capital=capital,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
            ticker_limit=ticker_limit,
            max_bars_per_ticker=max_bars_per_ticker,
            max_trades=max_trades,
            recent_sessions_only=recent_sessions_only,
        )
        portfolio = ensure_strategy_profile_portfolio(profile)
        serialized_profile = serialize_pine_scanner_profile(profile)
        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "source_type": profile.source_type,
            "created_at": serialized_profile["created_at"],
            "ready_at": serialized_profile["ready_at"],
            "activated_at": serialized_profile["activated_at"],
            "activation_count": serialized_profile["activation_count"],
            "activation_history": serialized_profile["activation_history"],
            "portfolio": serialize_strategy_profile_portfolio(portfolio),
        }
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A price-action scanner profile with this name or strategy already exists")
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        _safe_log_exception("Price-action promotion failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/strategy/price-action/activate-profile")
def activate_price_action_scanner_profile(payload: dict):
    try:
        raw_profile_id = payload.get("profile_id")
        if raw_profile_id is None:
            raise HTTPException(status_code=400, detail="profile_id is required")
        try:
            profile_id = int(raw_profile_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="profile_id must be numeric") from exc

        profile = activate_price_action_profile(profile_id)
        portfolio = ensure_strategy_profile_portfolio(profile)
        serialized_profile = serialize_pine_scanner_profile(profile)
        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "source_type": profile.source_type,
            "created_at": serialized_profile["created_at"],
            "ready_at": serialized_profile["ready_at"],
            "activated_at": serialized_profile["activated_at"],
            "activation_count": serialized_profile["activation_count"],
            "activation_history": serialized_profile["activation_history"],
            "portfolio": serialize_strategy_profile_portfolio(portfolio),
        }
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Activate price-action scanner profile failed")
        raise HTTPException(status_code=500, detail=str(e))

ALLOWED_STRATEGY_PARAMS = {
    'LOOKBACK', 'VOL_SPIKE', 'MOMENTUM', 'RSI_MIN', 'RSI_MAX', 'SL_PCT', 'TP1_PCT',
    'MIN_TURNOVER', 'TRICKSTER_RSI_MAX', 'TRICKSTER_REL_VOL_MIN', 'TRICKSTER_STRETCH_ATR',
    'MAX_POSITIONS', 'MAX_DAILY_TRADES', 'MAX_PORTFOLIO_HEAT', 'PENDING_ENTRY_MAX_GAP_PCT',
    'RISK_PER_TRADE', 'MIN_RISK_REWARD', 'MIN_SIGNAL_SCORE', 'MIN_SIGNAL_CONFIDENCE',
    'COMMISSION_PCT', 'SLIPPAGE_PCT', 'TRAILING_STOP_ENABLED', 'TRAILING_STOP_TYPE',
    'TRAILING_STOP_VALUE', 'REGIME_FILTER_ENABLED', 'REGIME_MODE', 'SECTOR_LIMIT_ENABLED',
    'MAX_PER_SECTOR', 'USE_ATR_EXITS', 'ATR_TP_MULTIPLIER', 'ATR_SL_MULTIPLIER',
    'AUTO_TRADE_ENABLED', 'ACCOUNT_BALANCE', 'ACCOUNT_BALANCE_USD'
}

@router.post("/api/v1/strategy/apply")
def apply_optimization_result(payload: dict):
    try:
        params = payload.get("params")
        if not params and isinstance(payload.get("proposed_settings"), dict):
            params = payload.get("proposed_settings")
        if not params and isinstance(payload.get("changes"), list):
            extracted_params: dict[str, Any] = {}
            for item in payload.get("changes", []):
                if not isinstance(item, dict):
                    continue
                if not item.get("changed"):
                    continue
                key = str(item.get("parameter") or "").strip()
                if not key:
                    continue
                extracted_params[key] = item.get("new_value")
            if extracted_params:
                params = extracted_params
        if not params and payload.get("manual"):
            params = {k: v for k, v in payload.items() if k != "manual"}
        if not params:
            params = {
                k: v for k, v in payload.items()
                if k not in ("params", "manual", "proposed_settings", "changes")
            }
        if not params:
            raise HTTPException(status_code=400, detail="No params provided")

        params = _normalize_strategy_params(params)
        applied_count = 0
        for key, value in params.items():
            if key in ALLOWED_STRATEGY_PARAMS and hasattr(core_settings, key):
                setattr(core_settings, key, value)
                applied_count += 1

        if applied_count <= 0:
            raise HTTPException(status_code=400, detail="No valid params provided")
        core_settings.save_settings("optimized")
        shared.STRATEGY_CACHE.update({"data": [], "timestamp": None, "version": -1})
        return {"status": "applied", "count": applied_count, "settings": get_settings()}
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Apply optimization result failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/strategy/backtest")
def run_backtest_simulation(payload: dict):
    try:
        index = _normalize_index_choice(payload.get("index", "EGX30"))
        capital = _normalize_capital(payload.get("capital", 100000))
        safe_params = _normalize_strategy_params(payload.get("params", {}))
        commission_pct, slippage_pct = _require_nonzero_cost_assumptions(payload)
        safe_params["COMMISSION_PCT"] = commission_pct
        safe_params["SLIPPAGE_PCT"] = slippage_pct
        start_date, end_date = _resolve_backtest_window(payload)
        
        max_pos = None
        if "MAX_POSITIONS" in safe_params:
            max_pos = int(safe_params["MAX_POSITIONS"])

        # PortfolioSimulator is verbose and writes directly to stdio; isolate that output
        # so API responses remain stable in headless/packaged runtimes.
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = PortfolioSimulator.run_simulation(
                cap=capital,
                index_choice=index,
                start_date=start_date,
                end_date=end_date,
                max_positions=max_pos,
                params=safe_params,
            )
        
        if result is None:
             logger.error("PortfolioSimulator returned None. Check engine logs.")
             raise HTTPException(status_code=500, detail="Backtest engine returned an empty result. Please check connectivity or data availability.")

        trades = filter_excluded_from_payload(result.get("trades", []))
        warnings: list[str] = []
        if len(trades) == 0:
            warnings.append("Backtest completed with 0 trades in the selected date window and filters.")
        return {
            "status": "success",
            "config": {
                "index": index,
                "capital": capital,
                "start_date": start_date,
                "end_date": end_date,
                "params": safe_params,
            },
            "metrics": {
                "total_return": result.get("total_return", 0),
                "final_value": result.get("final_value", 0),
                "trade_count": len(trades)
            },
            "assumptions": {
                "commission_pct": commission_pct,
                "slippage_pct": slippage_pct,
                "holding_period_days": int(getattr(PortfolioSimulator, "HOLDING_PERIOD", 20)),
            },
            "equity_curve": result.get("daily_values", []),
            "trades": trades,
            "warnings": warnings,
        }
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Backtest Execution Error")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/api/v1/ai/audit")
async def run_ai_strategy_audit(payload: dict | None = None):
    """
    Triggers an AI-driven audit of the latest backtest report.
    """
    try:
        report_path = None
        if payload:
            report_path = payload.get("report_path")
            
        result = await auditor.run_audit(report_path)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("AI Audit Error")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/strategy/propose-from-lab")
def propose_from_lab(payload: dict):
    """
    Commits an AI-audit result to the core strategy proposal cache.
    """
    try:
        audit_result = payload.get("audit_result")
        if not audit_result:
            raise HTTPException(status_code=400, detail="Missing audit_result in payload")
            
        success = auditor.save_proposal(audit_result)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save strategy proposal")
            
        return {"status": "success", "message": "Proposal committed to Strategy Core."}
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Propose From Lab Error")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/analytics/slippage-report")
def get_slippage_report(limit: int = 50):
    """
    Retrieves the reconciled execution slippage and decay report.
    """
    try:
        from core.analyzers.SlippageReconciler import SlippageReconciler
        report = SlippageReconciler.generate_reconciliation_report(limit=limit)
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        return report
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Slippage Report Error")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/analytics/signal-snapshots/{signal_id}")
def get_signal_snapshot(signal_id: str):
    """
    Retrieves the archived execution snapshot for a specific signal ID.
    """
    try:
        from database import SignalStateArchive
        archive = SignalStateArchive.get_or_none(SignalStateArchive.signal_id == signal_id)
        if not archive:
            raise HTTPException(status_code=404, detail="Signal snapshot not found")
        
        import json
        snapshot = json.loads(archive.filter_snapshot_json or "{}")
        return {
            "signal_id": archive.signal_id,
            "ticker": archive.ticker,
            "timestamp": archive.timestamp.isoformat() if archive.timestamp else None,
            "final_status": archive.final_status,
            "signal_score": archive.signal_score,
            "kill_reason": archive.kill_reason,
            "snapshot": snapshot
        }
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_exception("Get Signal Snapshot Error")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/risk/kill-switch")
def get_kill_switch_status():
    """
    Checks if the global emergency risk kill switch is active.
    """
    try:
        from core.risk.kill_switch import is_kill_switch_active
        return {"active": is_kill_switch_active()}
    except Exception as e:
        _safe_log_exception("Get Kill Switch Error")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/risk/kill-switch")
def post_toggle_kill_switch(payload: dict):
    """
    Sets the global emergency risk kill switch state.
    Payload: {"active": true} or {"active": false}
    """
    try:
        from core.risk.kill_switch import set_kill_switch
        active = bool(payload.get("active", False))
        set_kill_switch(active)
        return {"status": "success", "active": active}
    except Exception as e:
        _safe_log_exception("Toggle Kill Switch Error")
        raise HTTPException(status_code=500, detail=str(e))
