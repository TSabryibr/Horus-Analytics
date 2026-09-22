from core.settings import settings
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
import copy
import os
import time
from core.DataManager import DataManager
from data_engine.freshness import evaluate_freshness, get_runtime_ticker_report
from data_engine.provider_selection import (
    normalize_provider,
    resolve_timeframe_provider,
    resolved_provider_context,
)
from data_engine.observability import maybe_emit_freshness_alerts, snapshot_metrics
from data_engine.run_metadata import list_runs
from data_engine.sync import sync_all
from core import Heimdall
from core import TimeUtils
import datetime
from typing import Optional, List
import threading
from core.exclusions import assert_ticker_allowed, filter_excluded_symbols
from pydantic import BaseModel
from core.auth import get_api_key
from routes.shared import get_system_state_snapshot
from utils.logger import setup_logger

public_router = APIRouter(prefix="/api/v1/data", tags=["data"])
router = APIRouter(prefix="/api/v1/data", tags=["data"], dependencies=[Depends(get_api_key)])
logger = setup_logger("horus.data_routes")

class SyncRequest(BaseModel):
    ticker: Optional[str] = None
    force: bool = False

class WarmupRequest(BaseModel):
    tickers: Optional[List[str]] = None
    include_adv: bool = False

DATA_SYNC_STATE = {
    "status": "IDLE",  # IDLE, RUNNING, COMPLETED, ERROR
    "started_at": None,
    "finished_at": None,
    "last_error": None,
}
DATA_SYNC_LOCK = threading.Lock()
DATA_STATUS_CACHE_LOCK = threading.Lock()
DATA_STATUS_CACHE = {"key": None, "payload": None, "ts": 0.0}
VALID_SYNC_RUN_STAGES = {"ingest_intraday", "ingest_history", "ingest_ticks"}
VALID_SYNC_RUN_PROVIDERS = {"AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}


def _runtime_universe_source_context() -> dict:
    try:
        status = get_data_status_logic()
    except Exception as exc:
        return {
            "archive_intraday_stale": False,
            "realtime_overlay_active": False,
            "runtime_review_note": f"Source context unavailable: {exc}",
        }

    intraday_status = str((status.get("intraday") or {}).get("status") or "").upper()
    source = status.get("source") or {}
    decision = source.get("intraday_decision") or {}
    overlay = source.get("realtime_overlay") or {}
    archive_intraday_stale = str(decision.get("reason") or "").lower() == "upstream_intraday_stale"
    realtime_overlay_active = intraday_status == "LIVE" and bool(overlay.get("active"))
    note = (
        "Realtime overlay is live; SOURCE_STALE review candidates indicate archive/source lag, not live-feed quarantine."
        if archive_intraday_stale and realtime_overlay_active
        else "SOURCE_STALE review candidates indicate local archive/source lag requiring review."
    )
    return {
        "archive_intraday_stale": archive_intraday_stale,
        "realtime_overlay_active": realtime_overlay_active,
        "intraday_status": intraday_status or "UNKNOWN",
        "intraday_decision_reason": decision.get("reason"),
        "realtime_overlay_status": overlay.get("status"),
        "runtime_review_note": note,
    }


def _data_status_cache_ttl_sec() -> int:
    raw = os.getenv("DATA_STATUS_CACHE_TTL_SEC")
    if raw is not None:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    try:
        from core.settings import settings
        if settings.is_market_open():
            return 30
    except Exception:
        pass
    return 180


def reset_data_status_cache() -> None:
    with DATA_STATUS_CACHE_LOCK:
        DATA_STATUS_CACHE["key"] = None
        DATA_STATUS_CACHE["payload"] = None
        DATA_STATUS_CACHE["ts"] = 0.0


def _set_data_sync_state(**updates):
    with DATA_SYNC_LOCK:
        DATA_SYNC_STATE.update(updates)


def _get_data_sync_state():
    with DATA_SYNC_LOCK:
        return dict(DATA_SYNC_STATE)


def _run_ingest_summary(run: dict) -> dict:
    provider_context = dict(run.get("provider_context") or {})
    ingest_summary = provider_context.get("ingest_summary")
    return dict(ingest_summary) if isinstance(ingest_summary, dict) else {}


def _run_has_selection_fallback(run: dict) -> bool:
    provider_context = dict(run.get("provider_context") or {})
    return bool(provider_context.get("fallback_from"))


def _run_has_runtime_fallback(run: dict) -> bool:
    ingest_summary = _run_ingest_summary(run)
    return bool(ingest_summary.get("fallback_from")) or str(ingest_summary.get("status") or "").lower() == "completed_with_fallback"


def _run_has_provider_fallback(run: dict) -> bool:
    return _run_has_selection_fallback(run) or _run_has_runtime_fallback(run)


def _run_problem_type(run: dict) -> Optional[str]:
    status = str(run.get("status") or "").upper()
    if status == "ERROR":
        return "error"
    if status == "WARNING":
        return "warning"
    if _run_has_runtime_fallback(run):
        return "runtime_fallback"
    if _run_has_selection_fallback(run):
        return "selection_fallback"
    return None


def _run_is_problem(run: dict) -> bool:
    return _run_problem_type(run) is not None


def _normalize_fallback_type(fallback_type: Optional[str]) -> Optional[str]:
    if fallback_type is None:
        return None
    normalized = str(fallback_type).strip().lower()
    if not normalized:
        return None
    if normalized not in {"selection", "runtime"}:
        raise HTTPException(status_code=400, detail="fallback_type must be 'selection' or 'runtime'")
    return normalized


def _normalize_problem_type(problem_type: Optional[str]) -> Optional[str]:
    if problem_type is None:
        return None
    normalized = str(problem_type).strip().lower()
    if not normalized:
        return None
    if normalized not in {"error", "warning", "selection_fallback", "runtime_fallback"}:
        raise HTTPException(
            status_code=400,
            detail="problem_type must be 'error', 'warning', 'selection_fallback', or 'runtime_fallback'",
        )
    return normalized


def _normalize_stage_filter(stage: Optional[str]) -> Optional[str]:
    if stage is None:
        return None
    normalized = str(stage).strip().lower()
    if not normalized:
        return None
    if normalized not in VALID_SYNC_RUN_STAGES:
        raise HTTPException(
            status_code=400,
            detail="stage must be 'ingest_intraday', 'ingest_history', or 'ingest_ticks'",
        )
    return normalized


def _normalize_provider_filter(provider: Optional[str]) -> Optional[str]:
    if provider is None:
        return None
    normalized = str(provider).strip().upper()
    if not normalized:
        return None
    if normalized not in VALID_SYNC_RUN_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail="provider must be 'AUTO', 'CSV', 'MUBASHER_DB', 'DIRECTFN', or 'METASTOCK_DAT'",
        )
    return normalized


def _present_sync_run(run: dict) -> dict:
    presented = dict(run)
    provider_context = dict(run.get("provider_context") or {})
    ingest_summary = _run_ingest_summary(run)
    presented["provider_context"] = provider_context
    presented["problem_type"] = _run_problem_type(run)
    presented["has_selection_fallback"] = _run_has_selection_fallback(run)
    presented["has_runtime_fallback"] = _run_has_runtime_fallback(run)
    presented["has_provider_fallback"] = _run_has_provider_fallback(run)
    presented["selection_fallback_from"] = provider_context.get("fallback_from")
    presented["runtime_used_provider"] = ingest_summary.get("used_provider")
    presented["runtime_fallback_from"] = ingest_summary.get("fallback_from")
    presented["runtime_failure_mode"] = ingest_summary.get("failure_mode")
    presented["runtime_status"] = ingest_summary.get("status")
    return presented


def _problem_type_counts(runs: list[dict]) -> dict[str, int]:
    counts = {
        "error": 0,
        "warning": 0,
        "selection_fallback": 0,
        "runtime_fallback": 0,
    }
    for run in runs:
        problem_type = _run_problem_type(run)
        if problem_type is not None:
            counts[problem_type] += 1
    return counts


def _fallback_type_counts(runs: list[dict]) -> dict[str, int]:
    counts = {
        "selection": 0,
        "runtime": 0,
    }
    for run in runs:
        if _run_has_selection_fallback(run):
            counts["selection"] += 1
        if _run_has_runtime_fallback(run):
            counts["runtime"] += 1
    return counts


def _stage_counts(runs: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        stage = str(run.get("stage") or "").strip()
        if not stage:
            continue
        counts[stage] = int(counts.get(stage, 0) + 1)
    return counts


def _provider_counts(runs: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        provider = str(run.get("provider") or "").strip()
        if not provider:
            continue
        counts[provider] = int(counts.get(provider, 0) + 1)
    return counts


def _summarize_sync_runs(runs: list[dict], returned_runs: int) -> dict:
    error_runs = 0
    warning_runs = 0
    fallback_runs = 0
    selection_fallback_runs = 0
    runtime_fallback_runs = 0
    problem_runs = 0
    problem_type_counts = _problem_type_counts(runs)
    stage_counts = _stage_counts(runs)
    provider_counts = _provider_counts(runs)

    for run in runs:
        status = str(run.get("status") or "").upper()
        has_selection_fallback = _run_has_selection_fallback(run)
        has_runtime_fallback = _run_has_runtime_fallback(run)
        has_fallback = has_selection_fallback or has_runtime_fallback
        if status == "ERROR":
            error_runs += 1
        if status == "WARNING":
            warning_runs += 1
        if has_fallback:
            fallback_runs += 1
        if has_selection_fallback:
            selection_fallback_runs += 1
        if has_runtime_fallback:
            runtime_fallback_runs += 1
        if status in {"ERROR", "WARNING"} or has_fallback:
            problem_runs += 1

    return {
        "total_runs": len(runs),
        "returned_runs": int(returned_runs),
        "error_runs": error_runs,
        "warning_runs": warning_runs,
        "fallback_runs": fallback_runs,
        "selection_fallback_runs": selection_fallback_runs,
        "runtime_fallback_runs": runtime_fallback_runs,
        "problem_runs": problem_runs,
        "problem_type_counts": problem_type_counts,
        "stage_counts": stage_counts,
        "provider_counts": provider_counts,
    }


def _build_realtime_overlay_status(status: dict) -> dict:
    source = dict(status.get("source") or {})
    intraday = dict(status.get("intraday") or {})
    decision = dict(source.get("intraday_decision") or {})
    reason = str(decision.get("reason") or "")
    provider = str(source.get("intraday_provider") or "").upper()
    enabled = provider == "MUBASHER_DB" and reason == "upstream_intraday_stale"
    active = enabled and bool(intraday.get("ok")) and str(intraday.get("status") or "").upper() == "LIVE"
    return {
        "enabled": enabled,
        "active": active,
        "status": "ACTIVE" if active else "STANDBY" if enabled else "DISABLED",
        "provider": "MUBASHER_REALTIME",
        "price_field": "55",
        "guard": "session_range",
        "reason": reason or None,
        "last_bar": intraday.get("last_bar"),
    }


def _run_data_sync_task(force_history_recent_days: int = 0):
    started_at = TimeUtils.now().isoformat()
    _set_data_sync_state(
        status="RUNNING",
        started_at=started_at,
        finished_at=None,
        last_error=None
    )
    try:
        # Runs intraday + history (+ ticks if enabled) using existing sync policy.
        sync_all(force_history_recent_days=force_history_recent_days)
        try:
            from data_engine.freshness import invalidate_freshness_cache
            invalidate_freshness_cache()
        except Exception as cache_exc:
            logger.warning("[DataSync] Freshness cache invalidation failed: %s", cache_exc)
        try:
            from core import scheduling
            scheduling.maybe_run_pending_daily_signal_after_data_update()
            scheduling.maybe_dispatch_pending_ai_daily_report_after_data_update()
        except Exception as report_exc:
            logger.error("[DataSync] Pending scheduled report dispatch failed: %s", report_exc)
        _set_data_sync_state(
            status="COMPLETED",
            finished_at=TimeUtils.now().isoformat(),
            last_error=None
        )
    except Exception as e:
        _set_data_sync_state(
            status="ERROR",
            finished_at=TimeUtils.now().isoformat(),
            last_error=str(e)
        )

@public_router.get("/tickers")
def get_tickers():
    """List all available tickers in the Data Lake."""
    return filter_excluded_symbols(DataManager.list_tickers())

def get_data_status_logic():
    """Shared logic to fetch data freshness."""
    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    run_date = TimeUtils.today()
    policy_provider = normalize_provider(getattr(settings, "LOCAL_FEED_PROVIDER", "AUTO"))
    history_provider, history_report = resolve_timeframe_provider("history")
    intraday_provider, intraday_report = resolve_timeframe_provider("intraday")
    selection_report = history_report or intraday_report
    cache_key = (
        realm,
        run_date.isoformat(),
        int((get_system_state_snapshot() or {}).get("data_version", 0) or 0),
        policy_provider,
        history_provider,
        intraday_provider,
    )
    ttl_sec = _data_status_cache_ttl_sec()
    now_ts = time.time()

    with DATA_STATUS_CACHE_LOCK:
        cached_key = DATA_STATUS_CACHE.get("key")
        cached_payload = DATA_STATUS_CACHE.get("payload")
        cached_ts = float(DATA_STATUS_CACHE.get("ts", 0.0) or 0.0)
        if (
            ttl_sec > 0
            and cached_payload is not None
            and cached_key == cache_key
            and (now_ts - cached_ts) < ttl_sec
        ):
            return copy.deepcopy(cached_payload)

    status = evaluate_freshness(realm=realm, run_date=run_date, scan_type="DAILY")
    status["source"] = {
        "policy_provider": policy_provider,
        "history_provider": history_provider,
        "intraday_provider": intraday_provider,
        "selection_mode": "UNIFIED" if history_provider == intraday_provider else "TIMEFRAME",
        "history_decision": resolved_provider_context(
            timeframe="history",
            selected_provider=history_provider,
            unified_policy_provider=policy_provider,
            selection_report=selection_report,
        ),
        "intraday_decision": resolved_provider_context(
            timeframe="intraday",
            selected_provider=intraday_provider,
            unified_policy_provider=policy_provider,
            selection_report=selection_report,
        ),
    }
    if selection_report:
        status["source"]["recommended_provider"] = selection_report.get("recommended_provider")
        status["source"]["recommended_history_provider"] = selection_report.get("recommended_history_provider")
        status["source"]["recommended_intraday_provider"] = selection_report.get("recommended_intraday_provider")
    status["source"]["realtime_overlay"] = _build_realtime_overlay_status(status)
    status["evaluated_at"] = TimeUtils.now().isoformat()
    maybe_emit_freshness_alerts(status)
    completed_ts = time.time()

    with DATA_STATUS_CACHE_LOCK:
        DATA_STATUS_CACHE["key"] = cache_key
        DATA_STATUS_CACHE["payload"] = copy.deepcopy(status)
        DATA_STATUS_CACHE["ts"] = completed_ts

    return copy.deepcopy(status)

def evaluate_data_freshness_logic(run_date: Optional[str] = None, scan_type: str = "DAILY"):
    """
    Evaluates data freshness suitability for a signal run.
    DAILY requires history date to match the last completed EGX working day.
    INTRADAY requires fresh history + intraday last bar from run_date and <= 60 minutes old.
    """
    scan_type = (scan_type or "DAILY").upper()

    target_date = TimeUtils.today()
    if run_date:
        try:
            target_date = datetime.datetime.strptime(run_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="run_date must be YYYY-MM-DD")

    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    return evaluate_freshness(realm=realm, run_date=target_date, scan_type=scan_type)

@public_router.get("/status")
def get_data_status():
    """
    Returns the freshness of History and Intraday data.
    Used by the sidebar NETWORK STATUS indicator.
    """
    return get_data_status_logic()


@public_router.get("/status/portfolio")
def get_portfolio_freshness():
    """
    Returns portfolio-wide freshness KPIs across all tracked symbols.
    """
    status = get_data_status_logic()
    return {
        "run_date": status.get("run_date"),
        "history_kpis": (status.get("history") or {}).get("kpis", {}),
        "intraday_kpis": (status.get("intraday") or {}).get("kpis", {}),
        "overall_ok": status.get("overall_ok", False),
    }


@public_router.get("/sync/status")
def get_data_sync_status():
    """Returns background data sync state."""
    return _get_data_sync_state()


@router.get(
    "/sync/runs",
    summary="List recent ingestion runs",
    description=(
        "Returns recent ingestion-run metadata with derived problem classification, "
        "provider fallback diagnostics, and filtered facets for operator-facing tooling."
    ),
    response_description="Recent sync runs with derived diagnostics",
    responses={
        400: {
            "description": "Invalid filter value for fallback_type, problem_type, stage, or provider",
        }
    },
)
def get_sync_runs(
    limit: int = Query(
        50,
        description="Maximum number of recent runs loaded before any filters are applied.",
    ),
    problems_only: bool = Query(
        False,
        description="When true, only runs with a non-null derived problem_type are returned.",
    ),
    fallback_type: Optional[str] = Query(
        None,
        description="Filter to selection-time or runtime provider fallback runs.",
        json_schema_extra={"enum": ["selection", "runtime"]},
    ),
    problem_type: Optional[str] = Query(
        None,
        description="Filter to rows whose derived problem_type exactly matches the requested class.",
        json_schema_extra={"enum": ["error", "warning", "selection_fallback", "runtime_fallback"]},
    ),
    stage: Optional[str] = Query(
        None,
        description="Filter to one ingestion stage. Input is trimmed and normalized to lowercase.",
        json_schema_extra={"enum": ["ingest_intraday", "ingest_history", "ingest_ticks"]},
    ),
    provider: Optional[str] = Query(
        None,
        description="Filter to one persisted run provider. Input is trimmed and normalized to uppercase.",
        json_schema_extra={"enum": ["AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"]},
    ),
):
    """Returns ingestion run metadata (latest first)."""
    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    normalized_fallback_type = _normalize_fallback_type(fallback_type)
    normalized_problem_type = _normalize_problem_type(problem_type)
    normalized_stage = _normalize_stage_filter(stage)
    normalized_provider = _normalize_provider_filter(provider)
    runs = list_runs(realm=realm, limit=max(1, min(int(limit), 500)))
    filtered_runs = [run for run in runs if _run_is_problem(run)] if problems_only else list(runs)
    if normalized_fallback_type == "selection":
        filtered_runs = [run for run in filtered_runs if _run_has_selection_fallback(run)]
    elif normalized_fallback_type == "runtime":
        filtered_runs = [run for run in filtered_runs if _run_has_runtime_fallback(run)]
    if normalized_problem_type is not None:
        filtered_runs = [run for run in filtered_runs if _run_problem_type(run) == normalized_problem_type]
    if normalized_stage is not None:
        filtered_runs = [
            run for run in filtered_runs if str(run.get("stage") or "").strip().lower() == normalized_stage
        ]
    if normalized_provider is not None:
        filtered_runs = [
            run for run in filtered_runs if str(run.get("provider") or "").strip().upper() == normalized_provider
        ]
    return {
        "runs": [_present_sync_run(run) for run in filtered_runs],
        "summary": _summarize_sync_runs(runs, returned_runs=len(filtered_runs)),
        "facets": {
            "problem_type_counts": _problem_type_counts(filtered_runs),
            "fallback_type_counts": _fallback_type_counts(filtered_runs),
            "stage_counts": _stage_counts(filtered_runs),
            "provider_counts": _provider_counts(filtered_runs),
        },
        "filters": {
            "problems_only": bool(problems_only),
            "fallback_type": normalized_fallback_type,
            "problem_type": normalized_problem_type,
            "stage": normalized_stage,
            "provider": normalized_provider,
        },
    }


@router.get("/observability")
def get_pipeline_observability():
    """Returns in-memory pipeline counters/gauges."""
    return snapshot_metrics()


@router.post("/sync/start")
def start_data_sync(background_tasks: BackgroundTasks, force_history_recent_days: int = -1):
    """Triggers Data Lake sync (intraday + history) in background."""
    state = _get_data_sync_state()
    if state.get("status") == "RUNNING":
        return {"started": False, "message": "Data sync already running"}
    if force_history_recent_days is None:
        force_history_recent_days = -1
    days = int(force_history_recent_days)
    background_tasks.add_task(_run_data_sync_task, days)
    _set_data_sync_state(status="RUNNING", started_at=TimeUtils.now().isoformat(), finished_at=None, last_error=None)
    return {"started": True, "message": "Data sync started", "force_history_recent_days": days}

@public_router.get("/freshness")
def get_data_freshness(run_date: Optional[str] = None, scan_type: str = "DAILY"):
    """Returns pass/fail freshness gate details for a proposed signal run."""
    return evaluate_data_freshness_logic(run_date=run_date, scan_type=scan_type)


@public_router.get("/runtime-universe")
def get_runtime_universe_report():
    """Returns runtime-only ticker quarantine and review candidates."""
    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    report = get_runtime_ticker_report(realm=realm, ref_date=TimeUtils.today())
    report["source_context"] = _runtime_universe_source_context()
    return report

@router.get("/ticker/{ticker}")
def get_ticker_data(ticker: str, limit: int = 100, obv: bool = False):
    """Get OHLCV data for charts (Daily)."""
    ticker = assert_ticker_allowed(ticker)
    # Source is resolved by DataManager/GlobalSettings policy.
    df = DataManager.get_stock_data(ticker, limit=max(1, int(limit)), enrich_obv=obv)
    if df is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    df = df.tail(limit).reset_index()
    if 'Date' not in df.columns:
        if 'index' in df.columns:
            df = df.rename(columns={'index': 'Date'})
        else:
            first_col = df.columns[0]
            df = df.rename(columns={first_col: 'Date'})
    df['Date'] = df['Date'].astype(str)
    return df.to_dict(orient="records")

@router.get("/intraday/{ticker}")
def get_intraday_data(ticker: str, limit: int = 300):
    """Get Intraday OHLCV (1-min/5-min) from Intraday Folder."""
    ticker = assert_ticker_allowed(ticker)
    df = DataManager.get_intraday_data(ticker, limit=limit)
    if df is None:
        raise HTTPException(status_code=404, detail="Intraday Data not found")
        
    df = df.tail(limit).reset_index()
    # Handle Date conversion
    if 'Date' in df.columns:
         df['Date'] = df['Date'].astype(str)
    return df.to_dict(orient="records")

@router.post("/warmup")
def warmup_cache(req: WarmupRequest):
    """
    Triggers a bulk pre-calculation of indicators for the specified tickers.
    If no tickers provided, warms up the entire supported universe.
    """
    try:
        from core import StockLoader
        stats = StockLoader.warm_up_universe(tickers=req.tickers, include_adv=req.include_adv)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Warm-up failed: {e}")
