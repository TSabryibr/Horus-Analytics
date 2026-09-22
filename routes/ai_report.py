from __future__ import annotations
from core.settings import settings

import copy
import datetime
import json
import logging
import os
from typing import Any, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.analyzers import ExecutionWatchdog
from core.analyzers import SandboxRegistry
from core import MarketPredictor
from core.analyzers import SentimentCrawler
from core.market import SectorRotation
from core.analyzers import Svartalfheim
from core import TelegramBot_Alerts
from core import TimeUtils
from core.analyzers import Vanaheim
from database import Portfolio, Position, Signal, SignalRecommendation, SignalRun, Trade
from routes.shared import (
    ARBITRAGE_CACHE,
    NEWS_CACHE,
    ORACLE_CACHE,
    SECTOR_CACHE,
    STRATEGY_CACHE,
    TRAP_CACHE,
    WHALE_CACHE,
)

router = APIRouter(tags=["ai-report"])
logger = logging.getLogger("horus.ai_report")


class AiDailyBroadcastRequest(BaseModel):
    force_refresh: bool = True
    use_llm: bool = True
    provider: Optional[str] = None
    portfolio_id: Optional[int] = None

_AI_REPORT_CACHE: dict[str, dict[str, Any]] = {}
 
from core.ai_report import (
    normalize_source_module as _normalize_source_module,
    int_env as _int_env,
    float_env as _float_env,
    bool_env as _bool_env,
    parse_csv_models as _parse_csv_models,
    ollama_model_candidates as _ollama_model_candidates,
    canonical_text as _canonical_text,
    dedupe_strings as _dedupe_strings,
    remove_overlaps as _remove_overlaps,
    dedupe_recommendations as _dedupe_recommendations,
    dedupe_report_sections as _dedupe_report_sections,
    safe_call as _safe_call,
    cache_is_fresh as _cache_is_fresh,
    ai_report_cache_ttl_sec as _ai_report_cache_ttl_sec,
    error_context as _error_context,
    module_issue as _module_issue,
    safe_call_with_error as _safe_call_with_error,
    seconds_age_from_time as _seconds_age_from_time,
    rule_engine_instruction_text as _rule_engine_instruction_text,
    _RULE_ENGINE_THINKING_CONTRACT,
    collect_cross_tab_snapshot as _core_collect_cross_tab_snapshot,
    score_market_direction as _core_score_market_direction,
    derive_local_execution_profile as _core_derive_local_execution_profile,
    extract_sector_leaders as _core_extract_sector_leaders,
    resolve_portfolio_id as _core_resolve_portfolio_id,
    collect_signal_snapshot as _core_collect_signal_snapshot,
    collect_portfolio_snapshot as _core_collect_portfolio_snapshot,
    compute_data_freshness as _core_compute_data_freshness,
    compute_rr_ratio as _core_compute_rr_ratio,
    build_rule_based_recommendations as _core_build_rule_based_recommendations,
    generate_rule_based_report as _core_generate_rule_based_report,
    strip_code_fences as _core_strip_code_fences,
    safe_string_list as _core_safe_string_list,
    safe_recommendations as _core_safe_recommendations,
    normalize_llm_report as _core_normalize_llm_report,
    build_llm_prompts as _core_build_llm_prompts,
    call_ollama_report as _core_call_ollama_report,
    test_ollama_endpoint as _core_test_ollama_endpoint,
    maybe_generate_llm_report as _core_maybe_generate_llm_report,
    sanitize_telegram_text as _core_sanitize_telegram_text,
    build_ai_report_telegram_message as _core_build_ai_report_telegram_message,
    normalize_asset_choice as _core_normalize_asset_choice,
    get_highest_scoring_ticker as _core_get_highest_scoring_ticker,
    collect_asset_snapshot as _core_collect_asset_snapshot,
    generate_asset_report as _core_generate_asset_report,
    asset_report_requires_refresh as _core_asset_report_requires_refresh,
)
from database import AssetAiReport
from core.ai_report.lifecycle import run_ollama_report_session
from utils.ollama_manager import OllamaManager
 
_RULE_ENGINE_REASONING_PROFILE = "gpt-5.3-codex"
_ALLOWED_SOURCE_MODULES = {"OLLAMA", "LOCAL"}


def _build_ollama_manager(base_url: Optional[str] = None) -> OllamaManager:
    resolved_base_url = str(
        base_url
        or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        or "http://127.0.0.1:11434"
    ).strip()
    return OllamaManager(base_url=resolved_base_url)


def _default_ollama_lifecycle_metadata() -> dict[str, Any]:
    return {
        "report_mode": "LOCAL",
        "ollama_start_attempted": False,
        "ollama_ready": False,
        "ollama_shutdown_attempted": False,
        "ollama_shutdown_ok": False,
        "ollama_lifecycle_reason": None,
    }


def _generate_ollama_report_with_lifecycle(
    snapshot: dict[str, Any],
    fallback_report: dict[str, Any],
) -> tuple[Optional[dict[str, Any]], Optional[str], Optional[str], Optional[str], dict[str, Any]]:
    setattr(_maybe_generate_llm_report, "last_source_module", None)
    setattr(_maybe_generate_llm_report, "last_fallback_reason", None)
    ready_timeout_sec = max(3.0, _float_env("AI_REPORT_OLLAMA_START_TIMEOUT_SEC", 20.0))
    manager = _build_ollama_manager()

    def _generate() -> tuple[Optional[dict[str, Any]], Optional[str]]:
        return _maybe_generate_llm_report(snapshot, fallback_report)

    report, err, lifecycle_metadata = run_ollama_report_session(
        generate_report=_generate,
        manager=manager,
        ready_timeout_sec=ready_timeout_sec,
    )
    return (
        report,
        err,
        getattr(_maybe_generate_llm_report, "last_source_module", None),
        getattr(_maybe_generate_llm_report, "last_fallback_reason", None),
        lifecycle_metadata,
    )


def _compute_data_freshness() -> dict[str, Any]:
    return _core_compute_data_freshness(
        {
            "NEWS_CACHE": NEWS_CACHE,
            "SECTOR_CACHE": SECTOR_CACHE,
            "WHALE_CACHE": WHALE_CACHE,
            "TRAP_CACHE": TRAP_CACHE,
            "ARBITRAGE_CACHE": ARBITRAGE_CACHE,
            "STRATEGY_CACHE": STRATEGY_CACHE,
            "ORACLE_CACHE": ORACLE_CACHE,
        }
    )


def _extract_sector_leaders(sector_data: list[dict[str, Any]], status: str, limit: int = 5) -> list[dict[str, Any]]:
    return _core_extract_sector_leaders(sector_data, status, limit)


def _resolve_portfolio_id(portfolio_id: Optional[int]) -> Optional[int]:
    return _core_resolve_portfolio_id(portfolio_id)


def _collect_portfolio_snapshot(portfolio_id: Optional[int]) -> dict[str, Any]:
    return _core_collect_portfolio_snapshot(portfolio_id)


def _collect_signal_snapshot() -> dict[str, Any]:
    return _core_collect_signal_snapshot()


def _collect_cross_tab_snapshot(portfolio_id: Optional[int]) -> dict[str, Any]:
    return _core_collect_cross_tab_snapshot(
        portfolio_id,
        {
            "NEWS_CACHE": NEWS_CACHE,
            "SECTOR_CACHE": SECTOR_CACHE,
            "WHALE_CACHE": WHALE_CACHE,
            "TRAP_CACHE": TRAP_CACHE,
            "ARBITRAGE_CACHE": ARBITRAGE_CACHE,
            "STRATEGY_CACHE": STRATEGY_CACHE,
            "ORACLE_CACHE": ORACLE_CACHE,
        },
        collect_signal_snapshot=_collect_signal_snapshot,
        collect_portfolio_snapshot=_collect_portfolio_snapshot,
    )


def _score_market_direction(snapshot: dict[str, Any]) -> tuple[int, list[str]]:
    return _core_score_market_direction(snapshot)


def _derive_local_execution_profile(
    snapshot: dict[str, Any],
    direction_label: str,
    score: int,
    confidence: float,
    reasons: list[str],
) -> dict[str, Any]:
    return _core_derive_local_execution_profile(snapshot, direction_label, score, confidence, reasons)


def _compute_rr_ratio(entry_price: float, stop_loss: float, take_profit: float) -> Optional[float]:
    return _core_compute_rr_ratio(entry_price, stop_loss, take_profit)


def _build_rule_based_recommendations(
    snapshot: dict[str, Any],
    direction_label: str,
    composite_score: int,
    confidence: float,
    execution_profile: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    return _core_build_rule_based_recommendations(
        snapshot,
        direction_label,
        composite_score,
        confidence,
        execution_profile,
    )


def _generate_rule_based_report(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _core_generate_rule_based_report(snapshot)


def _strip_code_fences(text: str) -> str:
    return _core_strip_code_fences(text)


def _safe_string_list(value: Any) -> list[str]:
    return _core_safe_string_list(value)


def _safe_recommendations(value: Any) -> list[dict[str, Any]]:
    return _core_safe_recommendations(value)


def _normalize_llm_report(candidate: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    return _core_normalize_llm_report(candidate, fallback)


def _build_llm_prompts(snapshot: dict[str, Any], fallback_report: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return _core_build_llm_prompts(snapshot, fallback_report)


def _call_ollama_report(
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_sec: float,
    num_ctx: Optional[int],
    snapshot: dict[str, Any],
    fallback_report: dict[str, Any],
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    return _core_call_ollama_report(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_sec=timeout_sec,
        num_ctx=num_ctx,
        snapshot=snapshot,
        fallback_report=fallback_report,
    )


def _test_ollama_endpoint(
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_sec: float,
) -> tuple[bool, str]:
    return _core_test_ollama_endpoint(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_sec=timeout_sec,
    )


def _maybe_generate_llm_report(snapshot: dict[str, Any], fallback_report: dict[str, Any]) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    setattr(_maybe_generate_llm_report, "last_source_module", None)
    setattr(_maybe_generate_llm_report, "last_fallback_reason", None)
    report, err, last_source_module, last_fallback_reason = _core_maybe_generate_llm_report(
        snapshot,
        fallback_report,
        call_ollama_report=_call_ollama_report,
    )
    setattr(_maybe_generate_llm_report, "last_source_module", last_source_module)
    setattr(_maybe_generate_llm_report, "last_fallback_reason", last_fallback_reason)
    return report, err


@router.post("/api/v1/ai/provider/test")
def test_ai_provider_key(payload: dict):
    provider = str(payload.get("provider", "OLLAMA")).strip().upper() or "OLLAMA"
    if provider != "OLLAMA":
        raise HTTPException(
            status_code=400,
            detail=_error_context(
                "validation",
                "unsupported_provider",
                "provider must be OLLAMA",
                provider=provider,
            ),
        )

    provided_key = str(payload.get("api_key", "")).strip()
    api_key = provided_key or str(getattr(settings, "OLLAMA_API_KEY", "") or "").strip()

    timeout_sec = max(3.0, _float_env("AI_REPORT_TEST_TIMEOUT_SEC", 8.0))
    base_url = str(payload.get("base_url", "")).strip() or str(
        getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "http://127.0.0.1:11434"
    ).strip()
    model = str(payload.get("model", "")).strip() or str(
        getattr(settings, "AI_REPORT_OLLAMA_MODEL", "qwen3-coder:30b") or "qwen3-coder:30b"
    ).strip()
    ok, detail = _test_ollama_endpoint(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_sec=timeout_sec,
    )

    if not ok:
        raise HTTPException(
            status_code=400,
            detail=_error_context(
                "provider_check",
                "ollama_connectivity_failed",
                detail,
                provider=provider,
                base_url=base_url,
                model=model,
                provider_detail=detail,
            ),
        )

    return {
        "status": "success",
        "provider": provider,
        "message": detail,
    }


@router.get("/api/v1/ai/daily-report")
def get_ai_daily_report(
    portfolio_id: Optional[int] = None,
    force_refresh: bool = False,
    use_llm: bool = False,
    provider: Optional[str] = None,
):
    try:
        requested_provider = str(provider or "").strip().upper()
        valid_provider_overrides = {"OLLAMA", "LOCAL"}
        if requested_provider and requested_provider not in valid_provider_overrides:
            raise HTTPException(
                status_code=400,
                detail=_error_context(
                    "validation",
                    "unsupported_provider",
                    "provider must be OLLAMA or LOCAL",
                    provider=requested_provider,
                ),
            )

        if requested_provider == "OLLAMA":
            use_llm = True
            force_refresh = True
        elif requested_provider == "LOCAL":
            use_llm = False
            force_refresh = True

        return _get_ai_daily_report_inner(portfolio_id, force_refresh, use_llm)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "AI daily report failed unexpectedly: portfolio_id=%s provider=%s use_llm=%s",
            portfolio_id,
            requested_provider or None,
            use_llm,
        )
        raise HTTPException(
            status_code=500,
            detail=_error_context(
                "generation",
                "ai_daily_report_failed",
                f"AI daily report failed: {e}",
                portfolio_id=portfolio_id,
                provider=requested_provider or None,
                use_llm=bool(use_llm),
            ),
        )


def _get_ai_daily_report_inner(
    portfolio_id: Optional[int],
    force_refresh: bool,
    use_llm: bool,
):
    provider = "OLLAMA"
    resolved_portfolio_id = _resolve_portfolio_id(portfolio_id)
    cache_ttl_sec = _ai_report_cache_ttl_sec()
    cache_key = f"portfolio:{resolved_portfolio_id or portfolio_id or 'auto'}:llm:{int(bool(use_llm))}:provider:{provider}"
    cached = _AI_REPORT_CACHE.get(cache_key)
    if not force_refresh and _cache_is_fresh(cached):
        payload = copy.deepcopy(cached["payload"])
        payload["source_module"] = _normalize_source_module(payload.get("source_module"))
        payload["cached"] = True
        payload["cache_ttl_sec"] = cache_ttl_sec
        payload["cache_age_sec"] = _seconds_age_from_time(cached.get("generated_at")) or 0
        return payload

    snapshot = _collect_cross_tab_snapshot(resolved_portfolio_id)
    snapshot_degradation = snapshot.get("snapshot_degradation") or {
        "degraded": False,
        "issues": [],
        "module_status": {},
    }
    snapshot_degraded = bool(snapshot_degradation.get("degraded"))
    if snapshot_degraded:
        logger.warning(
            "AI daily report snapshot degraded: portfolio_id=%s issues=%s",
            resolved_portfolio_id if resolved_portfolio_id is not None else portfolio_id,
            [issue.get("reason") for issue in snapshot_degradation.get("issues", [])],
        )
    rule_report = _generate_rule_based_report(snapshot)

    report = copy.deepcopy(rule_report)
    source = "rule_based"
    source_module = "LOCAL"
    llm_error = None
    fallback_reason = None
    lifecycle_metadata = _default_ollama_lifecycle_metadata()

    if use_llm:
        llm_report, llm_error, llm_source_module, llm_fallback_reason, lifecycle_metadata = _generate_ollama_report_with_lifecycle(
            snapshot,
            rule_report,
        )
        if llm_report:
            report = llm_report
            source = "llm"
            source_module = _normalize_source_module(llm_source_module)
            fallback_reason = llm_fallback_reason
        elif llm_error:
            fallback_reason = llm_error

    degraded = bool(use_llm and llm_error)
    degradation_stage = "llm_generation" if degraded else None
    degradation_reason = "llm_provider_failed" if degraded else None
    provider_fallback_used = bool(use_llm and source == "llm" and fallback_reason)

    if degraded:
        logger.warning(
            "AI daily report degraded to rule-based output after LLM failure: portfolio_id=%s provider=%s reason=%s",
            portfolio_id,
            provider,
            llm_error,
        )
    elif provider_fallback_used:
        logger.info(
            "AI daily report used LLM provider fallback: portfolio_id=%s provider=%s reason=%s",
            portfolio_id,
            provider,
            fallback_reason,
        )

    report = _dedupe_report_sections(report)

    response_payload = {
        "status": "success",
        "generated_at": TimeUtils.now().isoformat(),
        "source": source,
        "source_module": _normalize_source_module(source_module),
        "reasoning_profile": _RULE_ENGINE_REASONING_PROFILE,
        "rule_engine_instruction": _rule_engine_instruction_text(),
        "cache_ttl_sec": cache_ttl_sec,
        "cache_age_sec": 0,
        "headline": report["headline"],
        "market_direction": report["market_direction"],
        "daily_report": report["daily_report"],
        "recommendations": report["recommendations"],
        "risk_warnings": report["risk_warnings"],
        "next_checklist": report["next_checklist"],
        "execution_profile": report.get("execution_profile", {}),
        "shadow_context": report.get("shadow_context", {}),
        "enforcement_context": report.get("enforcement_context", {}),
        "calibration_context": report.get("calibration_context", {}),
        "promotion_context": report.get("promotion_context", {}),
        "data_freshness": snapshot.get("data_freshness"),
        "input_snapshot": snapshot,
        "snapshot_degraded": snapshot_degraded,
        "snapshot_degradation": snapshot_degradation,
        "degraded": degraded,
        "degradation_stage": degradation_stage,
        "degradation_reason": degradation_reason,
        "provider_fallback_used": provider_fallback_used,
        "cached": False,
    }
    response_payload.update(lifecycle_metadata)
    if llm_error:
        response_payload["llm_error"] = llm_error
    if fallback_reason:
        response_payload["fallback_reason"] = fallback_reason

    _AI_REPORT_CACHE[cache_key] = {
        "generated_at": TimeUtils.now(),
        "payload": copy.deepcopy(response_payload),
    }
    return response_payload


def _sanitize_telegram_text(value: object) -> str:
    return _core_sanitize_telegram_text(value)


def build_ai_report_telegram_message(report_payload: dict, *, language: str | None = None) -> str:
    report_language = language or getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN")
    return _core_build_ai_report_telegram_message(report_payload, language=report_language)


@router.post("/api/v1/ai/daily-report/broadcast")
def broadcast_ai_daily_report(req: AiDailyBroadcastRequest):
    token = str(getattr(settings, "TELEGRAM_TOKEN", "") or "").strip()
    chat_id = str(getattr(settings, "CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        logger.warning("AI daily report broadcast blocked: Telegram is not configured")
        raise HTTPException(
            status_code=400,
            detail=_error_context(
                "configuration",
                "telegram_not_configured",
                "Telegram is not configured.",
            ),
        )

    payload = get_ai_daily_report(
        portfolio_id=req.portfolio_id,
        force_refresh=req.force_refresh,
        use_llm=req.use_llm,
        provider=req.provider,
    )
    if not isinstance(payload, dict) or payload.get("status") != "success":
        logger.error("AI daily report broadcast failed: report generation returned invalid payload")
        raise HTTPException(
            status_code=500,
            detail=_error_context(
                "generation",
                "ai_daily_report_generation_failed",
                "Failed to generate AI daily report.",
            ),
        )

    message = build_ai_report_telegram_message(payload)
    result = TelegramBot_Alerts.send_message(message)
    if not result or not result.get("ok"):
        description = (result or {}).get("description", "No response")
        logger.error(
            "AI daily report broadcast delivery failed: source_module=%s degraded=%s degradation_reason=%s telegram=%s",
            payload.get("source_module"),
            payload.get("degraded"),
            payload.get("degradation_reason"),
            description,
        )
        raise HTTPException(
            status_code=502,
            detail=_error_context(
                "delivery",
                "telegram_delivery_failed",
                f"Telegram API Failed: {description}",
                telegram_description=description,
                source_module=payload.get("source_module"),
                degraded=bool(payload.get("degraded")),
                degradation_reason=payload.get("degradation_reason"),
                fallback_reason=payload.get("fallback_reason"),
                snapshot_degraded=bool(payload.get("snapshot_degraded")),
                snapshot_degradation=payload.get("snapshot_degradation"),
            ),
        )

    return {
        "status": "sent",
        "source_module": payload.get("source_module"),
        "generated_at": payload.get("generated_at"),
        "degraded": bool(payload.get("degraded")),
        "degradation_reason": payload.get("degradation_reason"),
        "fallback_reason": payload.get("fallback_reason"),
        "provider_fallback_used": bool(payload.get("provider_fallback_used")),
        "snapshot_degraded": bool(payload.get("snapshot_degraded")),
        "snapshot_degradation": payload.get("snapshot_degradation"),
        "report_mode": payload.get("report_mode"),
        "ollama_start_attempted": bool(payload.get("ollama_start_attempted")),
        "ollama_ready": bool(payload.get("ollama_ready")),
        "ollama_shutdown_attempted": bool(payload.get("ollama_shutdown_attempted")),
        "ollama_shutdown_ok": bool(payload.get("ollama_shutdown_ok")),
        "ollama_lifecycle_reason": payload.get("ollama_lifecycle_reason"),
        "telegram_response": result,
    }


@router.get("/api/v1/ai/asset-reports/default")
def get_default_ticker():
    ticker = _core_get_highest_scoring_ticker()
    if not ticker:
        # Fallback to a common index ticker if no scanner results
        ticker = "EGX30"
    return {"ticker": ticker}


@router.get("/api/v1/ai/asset-report")
def get_asset_report(ticker: str, force_refresh: bool = False):
    try:
        ticker = _core_normalize_asset_choice(ticker)
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker is required.")

        # Check for latest stored report if not forcing refresh
        if not force_refresh:
            latest = (
                AssetAiReport.select()
                .where(AssetAiReport.ticker == ticker)
                .order_by(AssetAiReport.generated_at.desc())
                .first()
            )
            if latest:
                payload = json.loads(latest.payload_json)
                if not _core_asset_report_requires_refresh(payload):
                    payload["cached"] = True
                    payload["generated_at"] = latest.generated_at.isoformat()
                    return payload

        # Generate fresh report
        payload = _core_generate_asset_report(
            ticker,
            save=True,
            caches={
                "NEWS_CACHE": NEWS_CACHE,
                "WHALE_CACHE": WHALE_CACHE,
                "TRAP_CACHE": TRAP_CACHE,
                "ARBITRAGE_CACHE": ARBITRAGE_CACHE,
                "ORACLE_CACHE": ORACLE_CACHE,
            },
        )
        payload["cached"] = False
        return payload
    except Exception as e:
        logger.exception("Failed to generate asset report for %s: %s", ticker, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/ai/asset-reports/history")
def get_asset_report_history(ticker: str, limit: int = 10):
    try:
        ticker = _core_normalize_asset_choice(ticker)
        reports = (
            AssetAiReport.select()
            .where(AssetAiReport.ticker == ticker)
            .order_by(AssetAiReport.generated_at.desc())
            .limit(limit)
        )
        
        history = []
        for r in reports:
            # We don't return the full payload in the history list to keep it light
            history.append({
                "id": r.id,
                "ticker": r.ticker,
                "generated_at": r.generated_at.isoformat(),
                "confidence_score": r.confidence_score,
                "source_module": r.source_module
            })
        return history
    except Exception as e:
        logger.exception("Failed to fetch history for %s: %s", ticker, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/ai/asset-report/{report_id}")
def get_historical_asset_report(report_id: int):
    try:
        report = AssetAiReport.get_or_none(AssetAiReport.id == report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        
        payload = json.loads(report.payload_json)
        payload["cached"] = True
        payload["generated_at"] = report.generated_at.isoformat()
        return payload
    except Exception as e:
        logger.exception("Failed to fetch historical report %s: %s", report_id, e)
        raise HTTPException(status_code=500, detail=str(e))
