from __future__ import annotations

import copy
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import TelegramBot_Alerts, TimeUtils
from core.auth import get_api_key
from core.settings import settings
from database import SignalRun
from routes.data import evaluate_data_freshness_logic

from .periods import (
    _ANALYSIS_REPORT_CACHE,
    _analysis_cache_ttl_sec,
    _build_cache_key,
    _cache_is_fresh,
    _count_trading_days,
    _parse_period,
    _resolve_period_window,
)
from .market_summary import _aggregate_market_summary
from .signals import (
    _aggregate_portfolio_signal_review,
    _aggregate_signal_review,
    _apply_legacy_signal_fallback,
    _resolve_report_portfolio,
)
from .delivery import build_analysis_report_telegram_message

router = APIRouter(tags=["analysis-reports"], dependencies=[Depends(get_api_key)])


class AnalysisBroadcastRequest(BaseModel):
    period: str = Field(..., description="weekly | monthly")
    period_end: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    portfolio_id: Optional[int] = None
    force_refresh: bool = False


def build_analysis_report(
    period: str,
    period_end: Optional[str] = None,
    portfolio_id: Optional[int] = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    normalized_period = _parse_period(period)
    period_start, resolved_end, period_complete, period_notes = _resolve_period_window(normalized_period, period_end)
    portfolio_context = _resolve_report_portfolio(portfolio_id)
    resolved_portfolio_id = portfolio_context.id if portfolio_context else None
    cache_key = _build_cache_key(normalized_period, resolved_end, resolved_portfolio_id)
    ttl_sec = _analysis_cache_ttl_sec(normalized_period)

    cache_entry = _ANALYSIS_REPORT_CACHE.get(cache_key)
    if not force_refresh and _cache_is_fresh(cache_entry, ttl_sec):
        payload = copy.deepcopy(cache_entry["payload"])
        payload["cached"] = True
        payload["cache_ttl_sec"] = ttl_sec
        payload["cache_age_sec"] = int((TimeUtils.now() - cache_entry["generated_at"]).total_seconds())
        return payload

    runs = list(
        SignalRun.select()
        .where(
            (SignalRun.scan_type == "DAILY")
            & (SignalRun.status == "COMPLETED")
            & (SignalRun.run_date >= period_start)
            & (SignalRun.run_date <= resolved_end)
        )
        .order_by(SignalRun.run_date.asc(), SignalRun.completed_at.asc())
    )

    freshness = {}
    freshness_notes: list[str] = []
    try:
        import routes.analysis_reports as _pkg
        _freshness_fn = getattr(_pkg, "evaluate_data_freshness_logic", evaluate_data_freshness_logic)
        freshness = _freshness_fn(scan_type="DAILY")
    except Exception as exc:
        freshness = {"overall_ok": False, "issues": [f"freshness_check_error: {exc}"]}
        freshness_notes.append("Data freshness check failed during report generation.")

    market_summary, market_notes = _aggregate_market_summary(runs, period_start, resolved_end)
    signal_review, signal_notes, warnings, recommendations = _aggregate_signal_review(runs)
    signal_review, signal_notes, warnings = _apply_legacy_signal_fallback(
        review=signal_review,
        notes=signal_notes,
        warnings=warnings,
        period_start=period_start,
        period_end=resolved_end,
    )
    if portfolio_context is not None:
        signal_review, signal_notes, warnings, portfolio_recommendations = _aggregate_portfolio_signal_review(
            portfolio_context,
            period_start,
            resolved_end,
        )
        if portfolio_recommendations:
            recommendations = portfolio_recommendations

    expected_trading_days = _count_trading_days(period_start, resolved_end)
    covered_run_days = len({run.run_date for run in runs if getattr(run, "run_date", None) is not None})
    if expected_trading_days > 0 and covered_run_days < expected_trading_days:
        warnings.append(
            f"Daily replay coverage is incomplete for this period ({covered_run_days}/{expected_trading_days} trading days)."
        )

    notes: list[str] = []
    notes.extend(period_notes)
    notes.extend(freshness_notes)
    notes.extend(market_notes)
    notes.extend(signal_notes)
    if any("Benchmark market return/volatility data is unavailable" in note for note in market_notes):
        warnings.append("Benchmark context is unavailable; report confidence is reduced.")
    if not period_complete:
        warnings.append("Selected period is incomplete; interpretation should be conservative.")
    if not bool(freshness.get("overall_ok", True)):
        warnings.append("Freshness gate reports stale inputs; confidence should be reduced.")

    status = "success"
    if warnings or not bool(freshness.get("overall_ok", True)):
        status = "partial"

    payload = {
        "status": status,
        "period_type": normalized_period,
        "period_start": period_start.isoformat(),
        "period_end": resolved_end.isoformat(),
        "period_complete": period_complete,
        "generated_at": TimeUtils.now().isoformat(),
        "portfolio": (
            {
                "id": portfolio_context.id,
                "name": portfolio_context.name,
                "type": portfolio_context.type,
            }
            if portfolio_context
            else None
        ),
        "data_freshness": {
            "overall_ok": bool(freshness.get("overall_ok", True)),
            "notes": list(freshness.get("issues", []) or []),
        },
        "market_summary": market_summary,
        "signal_review": signal_review,
        "recommendations": recommendations,
        "warnings": warnings[:8],
        "notes": notes[:12],
        "cached": False,
        "cache_ttl_sec": ttl_sec,
        "cache_age_sec": 0,
    }

    _ANALYSIS_REPORT_CACHE[cache_key] = {
        "generated_at": TimeUtils.now(),
        "payload": copy.deepcopy(payload),
    }
    return payload


def dispatch_analysis_report(
    period: str,
    period_end: Optional[str] = None,
    portfolio_id: Optional[int] = None,
    force_refresh: bool = True,
) -> dict[str, Any]:
    token = str(getattr(settings, "TELEGRAM_TOKEN", "") or "").strip()
    chat_id = str(getattr(settings, "CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram is not configured.")

    payload = build_analysis_report(
        period=period,
        period_end=period_end,
        portfolio_id=portfolio_id,
        force_refresh=force_refresh,
    )
    if not isinstance(payload, dict) or payload.get("status") not in {"success", "partial"}:
        raise HTTPException(status_code=500, detail="Failed to generate analysis report.")

    message = build_analysis_report_telegram_message(
        payload,
        language=getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN"),
    )
    result = TelegramBot_Alerts.send_message(message)
    if not result or not result.get("ok"):
        raise HTTPException(
            status_code=502,
            detail=f"Telegram API Failed: {(result or {}).get('description', 'No response')}",
        )

    return {
        "status": "sent",
        "period_type": payload.get("period_type"),
        "period_start": payload.get("period_start"),
        "period_end": payload.get("period_end"),
        "generated_at": payload.get("generated_at"),
        "telegram_response": result,
    }


@router.get("/api/v1/reports/analysis")
def get_analysis_report(
    period: str = Query(..., description="weekly|monthly"),
    period_end: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    portfolio_id: Optional[int] = Query(default=None),
    force_refresh: bool = Query(default=False),
):
    return build_analysis_report(
        period=period,
        period_end=period_end,
        portfolio_id=portfolio_id,
        force_refresh=force_refresh,
    )


@router.post("/api/v1/reports/analysis/broadcast")
def broadcast_analysis_report(req: AnalysisBroadcastRequest):
    return dispatch_analysis_report(
        period=req.period,
        period_end=req.period_end,
        portfolio_id=req.portfolio_id,
        force_refresh=req.force_refresh,
    )
