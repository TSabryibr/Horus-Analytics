from __future__ import annotations
import datetime
import json
import asyncio
from typing import Any, Callable, Optional

from core import TimeUtils, MarketPredictor, TelegramBot_Alerts
from core.analyzers import SentimentCrawler
from core.market import SectorRotation
from core.analyzers import Vanaheim
from core.analyzers import Svartalfheim
from core.analyzers import SandboxRegistry
from core.analyzers import ExecutionWatchdog
from database import Portfolio, Position, Signal, SignalRecommendation, SignalRun, Trade
from core.horus.identity import resolve_preferred_user_portfolio
from core.enforcement_calibration import summarize_calibration_diagnostics
from core.enforcement_gates import summarize_enforcement_diagnostics
from core.whale_flow import summarize_whale_trap_diagnostics

from .boundary import (
    safe_call_with_error,
    module_issue,
    seconds_age_from_time,
    int_env,
)


def _strategy_regime_bias(strategy_regime: str) -> str:
    normalized = str(strategy_regime or "").upper()
    if "BULL" in normalized:
        return "BULLISH"
    if "BEAR" in normalized:
        return "BEARISH"
    return "NEUTRAL"

def _extract_sector_leaders(
    sector_data: list[dict[str, Any]],
    status: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    rows = [s for s in sector_data if str(s.get("Status", "")).upper() == status.upper()]
    rows.sort(key=lambda x: float(x.get("y", 0.0)), reverse=True)
    return [
        {
            "sector": str(r.get("Sector", "")),
            "x": float(r.get("x", 0.0)),
            "y": float(r.get("y", 0.0)),
        }
        for r in rows[:limit]
    ]

def _collect_signal_snapshot() -> dict[str, Any]:
    latest_run = (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
        .first()
    )
    run_meta = None
    rec_rows: list[dict[str, Any]] = []
    if latest_run:
        run_meta = {
            "run_id": latest_run.id,
            "run_date": latest_run.run_date.strftime("%Y-%m-%d") if latest_run.run_date else None,
            "scan_type": latest_run.scan_type,
            "signals_count": latest_run.signals_count,
        }
        recs = (
            SignalRecommendation.select()
            .where((SignalRecommendation.run == latest_run) & (SignalRecommendation.state == "ACTIVE"))
            .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc())
            .limit(15)
        )
        for rec in recs:
            rationale_payload: dict[str, Any] = {}
            if rec.rationale_json:
                try:
                    rationale_payload = json.loads(rec.rationale_json)
                except Exception:
                    rationale_payload = {}
            rec_rows.append(
                {
                    "ticker": rec.ticker,
                    "side": rec.side,
                    "entry_price": float(rec.entry_price),
                    "stop_loss": float(rec.stop_loss),
                    "target_price": float(rec.target_price),
                    "score": float(rec.score or 0.0),
                    "confidence": float(rec.confidence or 0.0),
                    "regime": rec.regime,
                    "whale_signal": rationale_payload.get("whale_signal"),
                    "whale_strength": rationale_payload.get("whale_strength"),
                    "whale_alignment": rationale_payload.get("whale_alignment"),
                    "whale_reason": rationale_payload.get("whale_reason"),
                    "trap_risk_score": rationale_payload.get("trap_risk_score"),
                    "trap_risk_band": rationale_payload.get("trap_risk_band"),
                    "trap_risk_reason": rationale_payload.get("trap_risk_reason"),
                    "enforcement_state": rationale_payload.get("enforcement_state"),
                    "enforcement_visibility": rationale_payload.get("enforcement_visibility"),
                    "enforcement_reason": rationale_payload.get("enforcement_reason"),
                    "enforcement_notes": rationale_payload.get("enforcement_notes"),
                    "enforcement_profile": rationale_payload.get("enforcement_profile"),
                }
            )

    latest_signals = list(
        Signal.select()
        .where(Signal.date <= TimeUtils.today())
        .order_by(Signal.date.desc(), Signal.score.desc())
        .limit(20)
        .dicts()
    )

    buy_count = sum(1 for r in rec_rows if str(r.get("side", "")).upper() == "BUY")
    sell_count = sum(1 for r in rec_rows if str(r.get("side", "")).upper() == "SELL")
    avg_score = round(sum(float(r.get("score", 0.0)) for r in rec_rows) / len(rec_rows), 2) if rec_rows else 0.0
    avg_conf = round(sum(float(r.get("confidence", 0.0)) for r in rec_rows) / len(rec_rows), 2) if rec_rows else 0.0

    return {
        "latest_run": run_meta,
        "active_recommendations": rec_rows,
        "latest_scanner_signals": latest_signals,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "avg_score": avg_score,
        "avg_confidence": avg_conf,
    }


def _summarize_signal_whale_trap_metadata(
    signal_data: dict[str, Any],
) -> dict[str, Any]:
    summary = summarize_whale_trap_diagnostics(
        list(signal_data.get("active_recommendations") or [])
    )
    active_recommendations = list(signal_data.get("active_recommendations") or [])
    supportive_names: list[dict[str, Any]] = []
    conflicted_or_high_risk: list[dict[str, Any]] = []

    for row in active_recommendations:
        whale_alignment = str(row.get("whale_alignment") or "").upper()
        trap_risk_band = str(row.get("trap_risk_band") or "UNKNOWN").upper()
        trap_risk_score = int(row.get("trap_risk_score") or 0)
        trap_risk_reason = str(row.get("trap_risk_reason") or "")
        score = float(row.get("score") or 0.0)
        ticker = str(row.get("ticker") or "")

        if whale_alignment == "SUPPORTIVE":
            supportive_names.append(
                {
                    "ticker": ticker,
                    "whale_signal": row.get("whale_signal"),
                    "whale_strength": row.get("whale_strength"),
                    "score": score,
                    "trap_risk_band": trap_risk_band,
                }
            )

        if trap_risk_band in {"HIGH", "SEVERE"}:
            conflicted_or_high_risk.append(
                {
                    "ticker": ticker,
                    "trap_risk_band": trap_risk_band,
                    "trap_risk_score": trap_risk_score,
                    "trap_risk_reason": trap_risk_reason,
                    "whale_alignment": whale_alignment or "NEUTRAL",
                    "score": score,
                }
            )
        elif whale_alignment == "CONFLICT":
            conflicted_or_high_risk.append(
                {
                    "ticker": ticker,
                    "trap_risk_band": trap_risk_band,
                    "trap_risk_score": trap_risk_score,
                    "trap_risk_reason": trap_risk_reason,
                    "whale_alignment": whale_alignment,
                    "score": score,
                }
            )

    supportive_names.sort(
        key=lambda row: (
            float(row.get("whale_strength") or 0.0),
            float(row.get("score") or 0.0),
        ),
        reverse=True,
    )
    conflicted_or_high_risk.sort(
        key=lambda row: (
            int(row.get("trap_risk_score") or 0),
            float(row.get("score") or 0.0),
        ),
        reverse=True,
    )
    summary["top_supportive_names"] = supportive_names[:5]
    summary["top_conflicted_or_high_risk_names"] = conflicted_or_high_risk[:5]
    return summary

def _collect_portfolio_snapshot(portfolio_id: Optional[int]) -> dict[str, Any]:
    target_id = _resolve_portfolio_id(portfolio_id)
    if not target_id:
        return {
            "portfolio_id": None,
            "portfolio_name": None,
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "top_positions": [],
            "warnings": ["No USER portfolio found."],
            "degraded": True,
            "degradation_reason": "user_portfolio_missing",
            "issues": [
                module_issue(
                    "portfolio",
                    "user_portfolio_missing",
                    "No USER portfolio found.",
                )
            ],
        }

    portfolio = Portfolio.get_or_none(Portfolio.id == target_id)
    open_positions = list(
        Position.select().where((Position.portfolio == target_id) & (Position.status == "OPEN"))
    )
    closed_trades = list(Trade.select().where(Trade.portfolio == target_id))

    realized_pnl = float(sum(float(t.pnl or 0.0) for t in closed_trades))
    unrealized_pnl = 0.0
    top_positions: list[dict[str, Any]] = []
    total_value = 0.0
    for pos in open_positions:
        entry = float(pos.entry_price or 0.0)
        current = float(pos.current_price if pos.current_price is not None else entry)
        shares = int(pos.shares or 0)
        value = current * shares
        cost = entry * shares
        pnl = value - cost
        unrealized_pnl += pnl
        total_value += value
        top_positions.append(
            {
                "ticker": pos.ticker,
                "market_value": round(value, 2),
                "unrealized_pnl": round(pnl, 2),
                "weight_pct": 0.0,
                "stop_loss": float(pos.stop_loss or 0.0),
                "target_price": float(pos.target_price or 0.0),
            }
        )

    if total_value > 0:
        for row in top_positions:
            row["weight_pct"] = round((float(row["market_value"]) / total_value) * 100.0, 2)
    top_positions.sort(key=lambda x: float(x.get("market_value", 0.0)), reverse=True)

    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    degradation_reason: Optional[str] = None
    if not portfolio:
        warnings.append("Requested USER portfolio not found.")
        issues.append(
            module_issue(
                "portfolio",
                "user_portfolio_not_found",
                "Requested USER portfolio not found.",
                portfolio_id=target_id,
            )
        )
        degradation_reason = "user_portfolio_not_found"
    if top_positions and float(top_positions[0]["weight_pct"]) >= 40:
        warnings.append(f"High concentration in {top_positions[0]['ticker']} ({top_positions[0]['weight_pct']}%).")

    return {
        "portfolio_id": target_id,
        "portfolio_name": portfolio.name if portfolio else None,
        "open_positions": len(open_positions),
        "realized_pnl": round(realized_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "total_pnl": round(realized_pnl + unrealized_pnl, 2),
        "top_positions": top_positions[:5],
        "warnings": warnings,
        "degraded": bool(issues),
        "degradation_reason": degradation_reason,
        "issues": issues,
    }


def _resolve_portfolio_id(portfolio_id: Optional[int]) -> Optional[int]:
    if portfolio_id:
        return portfolio_id
    portfolio = resolve_preferred_user_portfolio()
    return portfolio.id if portfolio else None

def _remember_live_cache(cache_obj: Any, data: Any) -> None:
    if not isinstance(cache_obj, dict):
        return
    cache_obj["data"] = data
    cache_obj["timestamp"] = TimeUtils.now()

def _collect_cross_tab_snapshot(
    portfolio_id: Optional[int],
    caches: dict[str, Any],
    *,
    collect_signal_snapshot: Optional[Callable[[], dict[str, Any]]] = None,
    collect_portfolio_snapshot: Optional[Callable[[Optional[int]], dict[str, Any]]] = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    module_status: dict[str, dict[str, Any]] = {}

    news_cache = caches.get("NEWS_CACHE", {})
    news = news_cache.get("data")
    if news:
        module_status["news"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        news, news_error = safe_call_with_error([], SentimentCrawler.gather_gossip)
        if news_error:
            news = []
            module_status["news"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(
                module_issue(
                    "news",
                    "collection_failed",
                    f"News collection failed: {news_error}",
                    source="default",
                )
            )
        else:
            module_status["news"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(news_cache, news)
    
    news_stories = news.get("stories", []) if isinstance(news, dict) else (news if isinstance(news, list) else [])
    
    news_sentiment, news_sentiment_error = safe_call_with_error(
        {"score": 50.0, "regime": "BORING MORTALS", "sample_size": len(news_stories)},
        SentimentCrawler.get_bifrost_sentiment,
        news,
    )
    if not news_sentiment_error:
        module_status["news_sentiment"] = {"status": "ok", "source": "derived"}
    else:
        module_status["news_sentiment"] = {"status": "degraded", "source": "default"}
        news_sentiment = {"score": 50.0, "regime": "BORING MORTALS", "sample_size": len(news_stories)}
        issues.append(module_issue("news_sentiment", "collection_failed", str(news_sentiment_error)))

    sector_cache = caches.get("SECTOR_CACHE", {})
    sectors = sector_cache.get("data")
    if sectors:
        module_status["sectors"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        sectors, sectors_error = safe_call_with_error([], SectorRotation.analyze_rotation)
        if sectors_error:
            sectors = []
            module_status["sectors"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(module_issue("sectors", "collection_failed", str(sectors_error)))
        else:
            module_status["sectors"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(sector_cache, sectors)
    sectors = sectors if isinstance(sectors, list) else []
    leading_sectors = _extract_sector_leaders(sectors, "LEADING")
    lagging_sectors = _extract_sector_leaders(sectors, "LAGGING")

    whale_cache = caches.get("WHALE_CACHE", {})
    whales = whale_cache.get("data")
    if whales:
        module_status["whales"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        whales, whales_error = safe_call_with_error(
            {"status": "error", "count": 0, "candidates": []},
            Vanaheim.hunt_whales,
        )
        if whales_error:
            module_status["whales"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(module_issue("whales", "collection_failed", str(whales_error)))
        else:
            module_status["whales"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(whale_cache, whales)
    whale_candidates = whales.get("candidates", []) if isinstance(whales, dict) else []
    accumulation = [c for c in whale_candidates if str(c.get("Signal", "")).upper() == "ACCUMULATION"]
    distribution = [c for c in whale_candidates if str(c.get("Signal", "")).upper() == "DISTRIBUTION"]

    trap_cache = caches.get("TRAP_CACHE", {})
    traps = trap_cache.get("data")
    if traps:
        module_status["traps"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        traps, traps_error = safe_call_with_error(
            {"status": "none", "bull_traps": [], "bear_traps": []},
            Svartalfheim.hunt_traps,
        )
        if traps_error:
            module_status["traps"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(module_issue("traps", "collection_failed", str(traps_error)))
        else:
            module_status["traps"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(trap_cache, traps)
    bull_traps = traps.get("bull_traps", []) if isinstance(traps, dict) else []
    bear_traps = traps.get("bear_traps", []) if isinstance(traps, dict) else []

    arbitrage_cache = caches.get("ARBITRAGE_CACHE", {})
    arbitrage = arbitrage_cache.get("data")
    if arbitrage:
        module_status["arbitrage"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        arbitrage, arbitrage_error = safe_call_with_error(
            {"status": "error", "count": 0, "mirrors": []},
            SandboxRegistry.get_lagged_correlations,
        )
        if arbitrage_error:
            module_status["arbitrage"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(module_issue("arbitrage", "collection_failed", str(arbitrage_error)))
        else:
            module_status["arbitrage"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(arbitrage_cache, arbitrage)
    mirrors = arbitrage.get("mirrors", []) if isinstance(arbitrage, dict) else []

    strategy_cache = caches.get("STRATEGY_CACHE", {})
    strategy = strategy_cache.get("data")
    if strategy:
        module_status["strategy"] = {"status": "ok", "source": "cache", "fallback_used": False}
    else:
        strategy, strategy_error = safe_call_with_error({}, ExecutionWatchdog.generate_strategy_proposal)
        if strategy_error:
            module_status["strategy"] = {"status": "degraded", "source": "default", "fallback_used": True}
            issues.append(module_issue("strategy", "collection_failed", str(strategy_error)))
        else:
            module_status["strategy"] = {"status": "ok", "source": "live", "fallback_used": True}
            _remember_live_cache(strategy_cache, strategy)

    oracle_cache = caches.get("ORACLE_CACHE", {})
    oracle_cache_data = oracle_cache.get("data") if isinstance(oracle_cache, dict) else {}
    if not isinstance(oracle_cache_data, dict):
        oracle_cache_data = {}
    macro, macro_error = safe_call_with_error(None, MarketPredictor.check_macro_health, "EGX30")
    if not macro_error:
        module_status["oracle_macro"] = {"status": "ok", "source": "live"}
        oracle_cache_data["EGX30"] = macro
        _remember_live_cache(oracle_cache, oracle_cache_data)
    else:
        module_status["oracle_macro"] = {"status": "degraded", "source": "default"}
        issues.append(module_issue("oracle_macro", "collection_failed", str(macro_error)))
    
    squeeze, squeeze_error = safe_call_with_error(
        {"status": "none", "count": 0, "candidates": []},
        MarketPredictor.hunt_the_coil,
    )
    if not squeeze_error:
        module_status["oracle_squeeze"] = {"status": "ok", "source": "live"}
        oracle_cache_data["SQUEEZE"] = squeeze
        _remember_live_cache(oracle_cache, oracle_cache_data)
    else:
        module_status["oracle_squeeze"] = {"status": "degraded", "source": "default"}
        issues.append(module_issue("oracle_squeeze", "collection_failed", str(squeeze_error)))

    signal_data = (collect_signal_snapshot or _collect_signal_snapshot)()
    signal_data["whale_trap_summary"] = _summarize_signal_whale_trap_metadata(signal_data)
    signal_data["enforcement_summary"] = summarize_enforcement_diagnostics(
        list(signal_data.get("active_recommendations") or [])
    )
    signal_data["calibration_summary"] = summarize_calibration_diagnostics(
        list(signal_data.get("active_recommendations") or [])
    )
    module_status["signals"] = {"status": "ok", "source": "database"}

    portfolio_data = (collect_portfolio_snapshot or _collect_portfolio_snapshot)(portfolio_id)
    module_status["portfolio"] = {
        "status": "degraded" if portfolio_data.get("degraded") else "ok",
        "source": "database",
    }
    if portfolio_data.get("issues"):
        issues.extend(list(portfolio_data.get("issues") or []))

    top_headlines = []
    for item in news_stories[:5]:
        title = item.get("title") or item.get("Headline") or "Untitled"
        src = item.get("source") or item.get("Source") or "Unknown"
        top_headlines.append({"title": str(title), "source": str(src)})

    # Sovereign Hedge Analysis
    from core.sovereign_confluence import sovereign_confluence_engine as confluence_engine
    sovereign_alerts = []
    module_status["sovereign_confluence"] = {"status": "skipped", "source": "derived"}
    if news and whales and news_sentiment.get("sample_size", 0) > 0 and whales.get("count", 0) > 0:
        try:
            # We use a wrapper or direct call depending on how it's integrated
            # In the route it was asyncio.run(confluence_engine.analyze_sovereign_confluence(news, whales))
            sovereign_alerts = asyncio.run(confluence_engine.analyze_sovereign_confluence(news, whales))
            module_status["sovereign_confluence"] = {"status": "ok", "source": "derived"}
        except Exception as e:
            module_status["sovereign_confluence"] = {"status": "degraded", "source": "default"}
            issues.append(module_issue("sovereign_confluence", "collection_failed", str(e)))

    data_freshness = _compute_data_freshness(caches)
    module_status["data_freshness"] = {
        "status": "degraded" if data_freshness.get("degraded") else "ok",
        "source": "derived",
    }
    if data_freshness.get("issues"):
        issues.extend(list(data_freshness.get("issues") or []))

    snapshot_degradation = {
        "degraded": bool(issues),
        "issues": issues,
        "module_status": module_status,
    }

    return {
        "as_of": TimeUtils.now().isoformat(),
        "data_freshness": data_freshness,
        "news": {
            "count": len(news),
            "sentiment_score": float(news_sentiment.get("score", 50.0)),
            "sentiment_regime": str(news_sentiment.get("regime", "BORING MORTALS")),
            "headlines": top_headlines,
        },
        "sovereign_warnings": sovereign_alerts,
        "total_active_signals": len(signal_data.get("active_recommendations", [])),
        "sectors": {
            "count": len(sectors),
            "leading": leading_sectors,
            "lagging": lagging_sectors,
        },
        "whales": {
            "count": int(whales.get("count", len(whale_candidates))) if isinstance(whales, dict) else len(whale_candidates),
            "accumulation_count": len(accumulation),
            "distribution_count": len(distribution),
            "top_accumulation": [
                {
                    "Ticker": c.get("Ticker"),
                    "Signal": c.get("Signal"),
                    "Strength": c.get("Strength"),
                    "Price_Slope": c.get("Price_Slope"),
                    "OBV_Slope": c.get("OBV_Slope"),
                    "Sector": c.get("Sector")
                } for c in accumulation[:5]
            ],
            "top_distribution": [
                {
                    "Ticker": c.get("Ticker"),
                    "Signal": c.get("Signal"),
                    "Strength": c.get("Strength"),
                    "Price_Slope": c.get("Price_Slope"),
                    "OBV_Slope": c.get("OBV_Slope"),
                    "Sector": c.get("Sector")
                } for c in distribution[:5]
            ],
        },
        "traps": {
            "bull_trap_count": len(bull_traps),
            "bear_trap_count": len(bear_traps),
            "recent_bull_traps": bull_traps[:5],
            "recent_bear_traps": bear_traps[:5],
        },
        "arbitrage": {
            "count": int(arbitrage.get("count", len(mirrors))) if isinstance(arbitrage, dict) else len(mirrors),
            "top_mirrors": mirrors[:5],
        },
        "strategy": {
            "regime": strategy.get("regime"),
            "regime_score": strategy.get("regime_score"),
            "volatility": strategy.get("volatility"),
            "reasoning": strategy.get("reasoning"),
            "changes": strategy.get("changes", [])[:5],
        },
        "oracle": {
            "macro_signal": macro.get("signal") if isinstance(macro, dict) else None,
            "macro_message": macro.get("message") if isinstance(macro, dict) else None,
            "macro_correlation": macro.get("correlation") if isinstance(macro, dict) else None,
            "squeeze_count": int(squeeze.get("count", 0)) if isinstance(squeeze, dict) else 0,
            "top_squeezes": (squeeze.get("candidates", []) if isinstance(squeeze, dict) else [])[:5],
        },
        "signals": signal_data,
        "portfolio": portfolio_data,
        "snapshot_degradation": snapshot_degradation,
    }

def _compute_data_freshness(caches: dict[str, Any]) -> dict[str, Any]:
    sources = {
        "news": caches.get("NEWS_CACHE"),
        "sectors": caches.get("SECTOR_CACHE"),
        "whales": caches.get("WHALE_CACHE"),
        "traps": caches.get("TRAP_CACHE"),
        "arbitrage": caches.get("ARBITRAGE_CACHE"),
        "strategy": caches.get("STRATEGY_CACHE"),
        "oracle": caches.get("ORACLE_CACHE"),
    }
    max_age_sec = max(60, int_env("AI_REPORT_FRESHNESS_MAX_AGE_SEC", 1800))

    ages_sec: dict[str, Optional[int]] = {}
    source_status: dict[str, dict[str, Any]] = {}
    normalized_scores: list[float] = []
    missing_sources: list[str] = []
    stale_sources: list[str] = []
    for name, cache_obj in sources.items():
        age = seconds_age_from_time((cache_obj or {}).get("timestamp"))
        ages_sec[name] = age
        if age is None:
            normalized_scores.append(0.40)
            missing_sources.append(name)
            source_status[name] = {"status": "missing", "age_sec": None}
        else:
            normalized_scores.append(max(0.0, min(1.0, 1.0 - (float(age) / float(max_age_sec)))))
            if age > max_age_sec:
                stale_sources.append(name)
                source_status[name] = {"status": "stale", "age_sec": age}
            else:
                source_status[name] = {"status": "fresh", "age_sec": age}

    if not normalized_scores:
        score = 50.0
    else:
        score = round((sum(normalized_scores) / len(normalized_scores)) * 100.0, 1)

    if score >= 75:
        label = "FRESH"
    elif score >= 50:
        label = "WARM"
    else:
        label = "STALE"

    issues: list[dict[str, Any]] = []
    for name in missing_sources:
        issues.append(
            module_issue(
                name,
                "freshness_missing",
                f"{name} freshness is unavailable.",
            )
        )
    for name in stale_sources:
        issues.append(
            module_issue(
                name,
                "freshness_stale",
                f"{name} freshness exceeded max age threshold.",
                age_sec=ages_sec.get(name),
                max_age_sec=max_age_sec,
            )
        )

    return {
        "score": score,
        "label": label,
        "max_age_sec": max_age_sec,
        "ages_sec": ages_sec,
        "source_status": source_status,
        "missing_sources": missing_sources,
        "stale_sources": stale_sources,
        "degraded": bool(missing_sources or stale_sources),
        "issues": issues,
    }

def _score_market_direction(snapshot: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    macro_signal = str(snapshot.get("oracle", {}).get("macro_signal") or "").upper()
    macro_corr = snapshot.get("oracle", {}).get("macro_correlation")
    if "BULLISH" in macro_signal or "UPTREND" in macro_signal:
        weight = 3
        score += weight
        corr_note = f" (breadth correlation: {macro_corr})" if macro_corr else ""
        reasons.append(f"Oracle macro signal is BULLISH{corr_note}. [+{weight}]")
    elif "BEARISH" in macro_signal or "DOWNTREND" in macro_signal:
        weight = 3
        score -= weight
        reasons.append(f"Oracle macro signal is BEARISH. [-{weight}]")
    else:
        reasons.append("Oracle macro signal is NEUTRAL — no trend conviction.")

    strategy = snapshot.get("strategy", {})
    strategy_regime = str(strategy.get("regime") or "").upper()
    regime_score_raw = strategy.get("regime_score")
    strategy_bias = _strategy_regime_bias(strategy_regime)
    if strategy_bias == "BULLISH":
        weight = 2
        score += weight
        extra = f" (regime score: {regime_score_raw})" if regime_score_raw else ""
        reasons.append(f"Strategy engine regime is BULLISH{extra}. [+{weight}]")
    elif strategy_bias == "BEARISH":
        weight = 2
        score -= weight
        reasons.append(f"Strategy engine regime is BEARISH. [-{weight}]")
    elif strategy_regime:
        reasons.append(f"Strategy regime: {strategy_regime} — no directional bias.")

    whales = snapshot.get("whales", {})
    acc = int(whales.get("accumulation_count") or 0)
    dist = int(whales.get("distribution_count") or 0)
    whale_total = acc + dist
    if whale_total > 0:
        whale_ratio = acc / whale_total
        if whale_ratio >= 0.65:
            weight = 2
            score += weight
            reasons.append(f"Strong whale accumulation: {acc} vs {dist} distribution ({whale_ratio:.0%}). [+{weight}]")
        elif whale_ratio >= 0.55:
            score += 1
            reasons.append(f"Modest whale accumulation: {acc} vs {dist}. [+1]")
        elif whale_ratio <= 0.35:
            weight = 2
            score -= weight
            reasons.append(f"Strong whale distribution: {dist} vs {acc} accumulation ({1-whale_ratio:.0%}). [-{weight}]")
        elif whale_ratio <= 0.45:
            score -= 1
            reasons.append(f"Modest whale distribution pressure: {dist} vs {acc}. [-1]")
        else:
            reasons.append(f"Whale flow is balanced ({acc} accumulation, {dist} distribution).")
    else:
        reasons.append("No whale activity detected.")

    news = snapshot.get("news", {})
    sentiment = float(news.get("sentiment_score") or 50.0)
    sentiment_regime = str(news.get("sentiment_regime") or "N/A")
    if sentiment >= 70:
        score += 2
        reasons.append(f"News sentiment strongly positive: {sentiment:.0f}/100 ({sentiment_regime}). [+2]")
    elif sentiment >= 60:
        score += 1
        reasons.append(f"News sentiment positive: {sentiment:.0f}/100 ({sentiment_regime}). [+1]")
    elif sentiment <= 30:
        score -= 2
        reasons.append(f"News sentiment strongly negative: {sentiment:.0f}/100 ({sentiment_regime}). [-2]")
    elif sentiment <= 40:
        score -= 1
        reasons.append(f"News sentiment negative: {sentiment:.0f}/100 ({sentiment_regime}). [-1]")
    else:
        reasons.append(f"News sentiment neutral: {sentiment:.0f}/100.")

    sectors = snapshot.get("sectors", {})
    leading = sectors.get("leading", [])
    lagging = sectors.get("lagging", [])
    leading_n = len(leading)
    lagging_n = len(lagging)
    sector_net = leading_n - lagging_n
    if sector_net >= 3:
        score += 2
        reasons.append(f"Wide sector breadth: {leading_n} leading vs {lagging_n} lagging. [+2]")
    elif sector_net >= 1:
        score += 1
        reasons.append(f"Positive sector breadth: {leading_n} leading vs {lagging_n} lagging. [+1]")
    elif sector_net <= -3:
        score -= 2
        reasons.append(f"Weak sector breadth: {lagging_n} lagging vs {leading_n} leading. [-2]")
    elif sector_net <= -1:
        score -= 1
        reasons.append(f"Negative sector breadth: {lagging_n} lagging vs {leading_n} leading. [-1]")
    else:
        reasons.append(f"Sector breadth balanced ({leading_n} leading, {lagging_n} lagging).")

    traps = snapshot.get("traps", {})
    bear_traps = int(traps.get("bear_trap_count") or 0)
    bull_traps = int(traps.get("bull_trap_count") or 0)
    trap_diff = bear_traps - bull_traps
    if trap_diff >= 3:
        score += 2
        reasons.append(f"High bear-trap count ({bear_traps}) signals strong support and reversal. [+2]")
    elif trap_diff >= 1:
        score += 1
        reasons.append(f"Bear traps ({bear_traps}) > bull traps ({bull_traps}): reversal support. [+1]")
    elif trap_diff <= -3:
        score -= 2
        reasons.append(f"High bull-trap count ({bull_traps}) signals distribution risk. [-2]")
    elif trap_diff <= -1:
        score -= 1
        reasons.append(f"Bull traps ({bull_traps}) > bear traps ({bear_traps}): distribution risk. [-1]")

    signals = snapshot.get("signals", {})
    buy_count = int(signals.get("buy_count") or 0)
    sell_count = int(signals.get("sell_count") or 0)
    avg_score = float(signals.get("avg_score") or 0.0)
    avg_conf = float(signals.get("avg_confidence") or 0.0)
    if buy_count > sell_count and avg_score >= 7:
        score += 2
        reasons.append(f"High-quality buy signals: {buy_count} buys (avg score {avg_score}, avg conf {avg_conf:.0f}%). [+2]")
    elif buy_count > sell_count:
        score += 1
        reasons.append(f"Active recommendations buy-skewed: {buy_count} buy vs {sell_count} sell. [+1]")
    elif sell_count > buy_count:
        score -= 1
        reasons.append(f"Active recommendations sell-skewed: {sell_count} sell vs {buy_count} buy. [-1]")

    oracle = snapshot.get("oracle", {})
    squeeze_count = int(oracle.get("squeeze_count") or 0)
    if squeeze_count >= 5:
        reasons.append(f"⚡ {squeeze_count} volatility squeezes detected — explosive moves imminent.")
    elif squeeze_count >= 1:
        reasons.append(f"{squeeze_count} volatility squeeze(s) building — watch for breakouts.")

    portfolio = snapshot.get("portfolio", {})
    open_pos = int(portfolio.get("open_positions") or 0)
    total_pnl = float(portfolio.get("total_pnl") or 0.0)
    if total_pnl < 0 and open_pos > 0:
        reasons.append(f"Portfolio under water: {total_pnl:+,.0f} unrealized — consider defensive positioning.")
    elif total_pnl > 0 and open_pos > 0:
        reasons.append(f"Portfolio positive: {total_pnl:+,.0f} — momentum support from existing positions.")

    return score, reasons

def _derive_local_execution_profile(
    snapshot: dict[str, Any],
    direction_label: str,
    score: int,
    confidence: float,
    reasons: list[str],
) -> dict[str, Any]:
    strategy = snapshot.get("strategy", {})
    volatility = str(strategy.get("volatility") or "NORMAL").upper()
    freshness = snapshot.get("data_freshness", {})
    freshness_label = str(freshness.get("label", "FRESH")).upper()

    bullish_count = sum(1 for r in reasons if "[+" in r)
    bearish_count = sum(1 for r in reasons if "[-" in r)
    mixed_signals = bullish_count >= 2 and bearish_count >= 2
    abs_score = abs(score)

    mode = "BALANCED"
    selectivity = "MEDIUM"
    trade_frequency_guidance = "Moderate frequency; prioritize top-ranked setups."
    max_new_positions = 3
    max_risk_per_trade_pct = 1.0
    max_total_new_risk_pct = 4.0
    prefer_no_trade = False

    if direction_label == "NEUTRAL" and abs_score <= 1:
        mode = "CAPITAL_PRESERVATION"
        selectivity = "VERY_HIGH"
        trade_frequency_guidance = "Minimal frequency (0-2 setups max) until regime clarity improves."
        max_new_positions = 1
        max_risk_per_trade_pct = 0.5
        max_total_new_risk_pct = 1.5
        prefer_no_trade = True
    elif mixed_signals and abs_score <= 2:
        mode = "DEFENSIVE"
        selectivity = "HIGH"
        trade_frequency_guidance = "Low frequency; only take setups with strong confluence and clean risk/reward."
        max_new_positions = 2
        max_risk_per_trade_pct = 0.75
        max_total_new_risk_pct = 2.5
    elif "HIGH" in volatility or freshness_label == "STALE":
        mode = "RISK_OFF"
        selectivity = "HIGH"
        trade_frequency_guidance = "Strict risk-off mode; prioritize preserving capital over chasing gains."
        max_new_positions = 1
        max_risk_per_trade_pct = 0.5
        max_total_new_risk_pct = 1.0
        prefer_no_trade = True

    return {
        "mode": mode,
        "selectivity": selectivity,
        "trade_frequency_guidance": trade_frequency_guidance,
        "max_new_positions": max_new_positions,
        "risk_limits": {
            "max_risk_per_trade_pct": max_risk_per_trade_pct,
            "max_total_new_risk_pct": max_total_new_risk_pct,
        },
        "prefer_no_trade": prefer_no_trade,
    }
