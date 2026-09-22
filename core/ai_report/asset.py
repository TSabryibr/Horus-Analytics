from __future__ import annotations
import datetime
import asyncio
import json
import logging
import math
from typing import Any, Optional

from core import TimeUtils, MarketPredictor
from core.analyzers import SentimentCrawler
from core.analyzers import Vanaheim
from core.analyzers import Svartalfheim
from core.analyzers import SandboxRegistry
from core.market import MarketLists
from database import SignalRecommendation, SignalRun, AssetAiReport
from core.ai_report.boundary import safe_call_with_error

logger = logging.getLogger("horus.ai_report.asset")

_ORACLE_SCOPE_ALIASES = {
    "EGX30": "EGX30",
    "EGX70": "EGX70",
    "EGX100": "EGX100",
    "ALL": "ALL",
    "UNIVERSE": "ALL",
    "UNIVERS": "ALL",
    "FULL": "ALL",
}


def _normalize_sentiment_regime(value: Any) -> str:
    regime = str(value or "").strip().upper()
    if not regime or regime == "BORING MORTALS":
        return "NEUTRAL"
    return regime


def normalize_asset_choice(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return ""
    return _ORACLE_SCOPE_ALIASES.get(normalized, normalized)


def _is_market_scope(asset_choice: str) -> bool:
    return asset_choice in {"EGX30", "EGX70", "EGX100", "ALL"}


def _scope_tickers(asset_choice: str) -> set[str]:
    if not _is_market_scope(asset_choice):
        return set()
    return {str(t).upper() for t in (MarketLists.get_market_list(asset_choice) or set())}


def _row_price(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except Exception:
        return None
    return numeric if numeric > 0 else None


def _has_complete_recommendation_levels(recommendation: Any) -> bool:
    if not isinstance(recommendation, dict):
        return False
    return all(
        _row_price(recommendation.get(field)) is not None
        for field in ("entry", "stop", "target")
    )


def _build_asset_evidence(snapshot: dict[str, Any]) -> dict[str, Any]:
    sources: list[str] = []
    if snapshot.get("scope"):
        sources.append("scope_breadth")

    recommendation = snapshot.get("recommendation") if isinstance(snapshot.get("recommendation"), dict) else {}
    if recommendation:
        rec_score = float(recommendation.get("score") or 0.0)
        rec_confidence = float(recommendation.get("confidence") or 0.0)
        rec_side = str(recommendation.get("side") or "").strip()
        if rec_side or rec_score > 0 or rec_confidence > 0:
            sources.append("recommendation")
        if _has_complete_recommendation_levels(recommendation):
            sources.append("levels")

    technical_context = snapshot.get("technical_context") if isinstance(snapshot.get("technical_context"), dict) else {}
    if technical_context.get("is_bull_trap") or technical_context.get("is_bear_trap"):
        sources.append("trap")
    if snapshot.get("whale_flow"):
        sources.append("whale_flow")
    if snapshot.get("news_mentions"):
        sources.append("news")
    arbitrage = snapshot.get("arbitrage")
    if isinstance(arbitrage, dict) and bool(arbitrage):
        sources.append("mirror")

    unique_sources = list(dict.fromkeys(sources))
    return {
        "has_specific_signal": bool(unique_sources),
        "sources": unique_sources,
    }


def _has_asset_specific_signal(snapshot: dict[str, Any]) -> bool:
    existing = snapshot.get("asset_evidence")
    if isinstance(existing, dict) and "has_specific_signal" in existing:
        return bool(existing.get("has_specific_signal"))
    return bool(_build_asset_evidence(snapshot).get("has_specific_signal"))


def _cache_data(caches: Optional[dict[str, Any]], key: str) -> Any:
    if not isinstance(caches, dict):
        return None
    cache_entry = caches.get(key)
    if not isinstance(cache_entry, dict):
        return None
    return cache_entry.get("data")


def _has_cache_entry(caches: Optional[dict[str, Any]], key: str) -> bool:
    if not isinstance(caches, dict):
        return False
    cache_entry = caches.get(key)
    if not isinstance(cache_entry, dict):
        return False
    return "data" in cache_entry or cache_entry.get("timestamp") is not None


def _news_stories_from_cache(caches: Optional[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    if not _has_cache_entry(caches, "NEWS_CACHE"):
        return False, []
    cached_news = _cache_data(caches, "NEWS_CACHE")
    if isinstance(cached_news, dict):
        stories = cached_news.get("stories")
        return True, stories if isinstance(stories, list) else []
    if isinstance(cached_news, list):
        return True, cached_news
    return True, []


def _macro_from_cache(caches: Optional[dict[str, Any]], macro_target: str) -> Optional[dict[str, Any]]:
    cached_oracle = _cache_data(caches, "ORACLE_CACHE")
    if not isinstance(cached_oracle, dict):
        return None
    macro = cached_oracle.get(str(macro_target or "").upper())
    return macro if isinstance(macro, dict) else None


def _score_recommendation_completeness(row: Any) -> int:
    fields = (
        getattr(row, "entry_price", None),
        getattr(row, "stop_loss", None),
        getattr(row, "target_price", None),
    )
    return sum(1 for field in fields if _row_price(field) is not None)


def _coerce_query_rows(query: Any) -> list[Any]:
    if query is None:
        return []
    try:
        return list(query)
    except Exception:
        pass
    first = query.first() if hasattr(query, "first") else None
    return [first] if first is not None else []


def _pick_lead_ticker(
    recommendation_rows: list[Any],
    scope_tickers: set[str],
    whale_rows: list[dict[str, Any]],
) -> Optional[str]:
    ranked_rows = sorted(
        recommendation_rows,
        key=lambda row: (
            float(getattr(row, "confidence", 0.0) or 0.0),
            float(getattr(row, "score", 0.0) or 0.0),
            _score_recommendation_completeness(row),
        ),
        reverse=True,
    )
    for row in ranked_rows:
        ticker = str(getattr(row, "ticker", "") or "").upper()
        if ticker and ticker in scope_tickers:
            return ticker

    for whale_row in whale_rows:
        ticker = str(whale_row.get("Ticker", "")).upper()
        if ticker and ticker in scope_tickers:
            return ticker
    return None


def _build_scope_level_clusters(
    recommendation_rows: list[Any],
    *,
    cluster_gap_ratio: float = 0.025,
) -> dict[str, list[dict[str, Any]]]:
    support_inputs: list[tuple[float, float]] = []
    resistance_inputs: list[tuple[float, float]] = []

    for row in recommendation_rows:
        confidence = float(getattr(row, "confidence", 0.0) or 0.0)
        score = float(getattr(row, "score", 0.0) or 0.0)
        strength = max(0.2, min(1.0, ((confidence / 100.0) * 0.6) + ((score / 10.0) * 0.4)))

        stop = _row_price(getattr(row, "stop_loss", None))
        target = _row_price(getattr(row, "target_price", None))
        side = str(getattr(row, "side", "") or "").upper()

        if stop is not None:
            support_inputs.append((stop, strength))
        if target is not None:
            resistance_inputs.append((target, strength))
        if side == "SELL":
            entry = _row_price(getattr(row, "entry_price", None))
            if entry is not None:
                resistance_inputs.append((entry, max(0.15, strength * 0.85)))

    def _cluster(points: list[tuple[float, float]], label_prefix: str) -> list[dict[str, Any]]:
        if not points:
            return []
        ordered = sorted(points, key=lambda item: item[0])
        clusters: list[list[tuple[float, float]]] = []
        current_cluster: list[tuple[float, float]] = [ordered[0]]

        for price, strength in ordered[1:]:
            current_avg = sum(item[0] for item in current_cluster) / len(current_cluster)
            allowed_gap = max(current_avg * cluster_gap_ratio, 0.35)
            if abs(price - current_avg) <= allowed_gap:
                current_cluster.append((price, strength))
            else:
                clusters.append(current_cluster)
                current_cluster = [(price, strength)]
        clusters.append(current_cluster)

        ranked_clusters = sorted(
            clusters,
            key=lambda cluster: (
                len(cluster),
                sum(item[1] for item in cluster) / len(cluster),
            ),
            reverse=True,
        )[:3]

        return [
            {
                "price": round(sum(item[0] for item in cluster) / len(cluster), 4),
                "strength": round(sum(item[1] for item in cluster) / len(cluster), 4),
                "label": f"{label_prefix}_{index}",
                "members": len(cluster),
            }
            for index, cluster in enumerate(ranked_clusters, start=1)
        ]

    return {
        "supports": _cluster(support_inputs, "support_cluster"),
        "resistances": _cluster(resistance_inputs, "resistance_cluster"),
    }


def _build_price_history_levels(ticker: str) -> dict[str, Any]:
    try:
        from core.DataManager import DataManager

        df = DataManager.get_stock_data(ticker, limit=90)
    except Exception:
        logger.exception("Failed to load price history levels for %s", ticker)
        return {"current_price": None, "supports": [], "resistances": [], "source": "history"}

    if df is None or getattr(df, "empty", True):
        return {"current_price": None, "supports": [], "resistances": [], "source": "history"}

    try:
        recent = df.tail(60).copy()
        current_price = _row_price(recent["Close"].iloc[-1])
    except Exception:
        return {"current_price": None, "supports": [], "resistances": [], "source": "history"}

    if current_price is None:
        return {"current_price": None, "supports": [], "resistances": [], "source": "history"}

    def _numeric_prices(column: str, predicate: Any) -> list[float]:
        if column not in recent:
            return []
        values: list[float] = []
        for raw in recent[column].tail(45).tolist():
            price = _row_price(raw)
            if price is not None and predicate(price):
                values.append(price)
        return values

    supports = _cluster_history_levels(
        _numeric_prices("Low", lambda price: price <= current_price),
        current_price=current_price,
        level_type="support",
    )
    resistances = _cluster_history_levels(
        _numeric_prices("High", lambda price: price >= current_price),
        current_price=current_price,
        level_type="resistance",
    )

    return {
        "current_price": round(current_price, 4),
        "supports": supports,
        "resistances": resistances,
        "source": "history",
    }


def _cluster_history_levels(
    prices: list[float],
    *,
    current_price: float,
    level_type: str,
    gap_ratio: float = 0.018,
) -> list[dict[str, Any]]:
    clean_prices = sorted(price for price in prices if math.isfinite(price) and price > 0)
    if not clean_prices:
        return []

    clusters: list[list[float]] = []
    current_cluster: list[float] = [clean_prices[0]]
    for price in clean_prices[1:]:
        cluster_avg = sum(current_cluster) / len(current_cluster)
        allowed_gap = max(cluster_avg * gap_ratio, 0.03)
        if abs(price - cluster_avg) <= allowed_gap:
            current_cluster.append(price)
        else:
            clusters.append(current_cluster)
            current_cluster = [price]
    clusters.append(current_cluster)

    ranked = sorted(
        clusters,
        key=lambda cluster: (
            -abs((sum(cluster) / len(cluster)) - current_price),
            len(cluster),
        ),
        reverse=True,
    )

    candidates = []
    for cluster in ranked:
        avg_price = sum(cluster) / len(cluster)
        if level_type == "support" and avg_price > current_price:
            continue
        if level_type == "resistance" and avg_price < current_price:
            continue
        candidates.append(
            {
                "price": round(avg_price, 4),
                "strength": round(max(0.25, min(0.95, 0.35 + (len(cluster) * 0.12))), 4),
                "label": f"{level_type}_history_{len(candidates) + 1}",
                "members": len(cluster),
            }
        )

    candidates.sort(key=lambda item: abs(float(item["price"]) - current_price))
    return candidates[:3]


def _derive_asset_verdict(snapshot: dict[str, Any]) -> tuple[str, float]:
    if not snapshot.get("scope") and not _has_asset_specific_signal(snapshot):
        return "NEUTRAL", 35.0

    score = 0.0
    recommendation = snapshot.get("recommendation", {})
    technical_context = snapshot.get("technical_context", {})
    sentiment = snapshot.get("sentiment", {})
    whale_flow = snapshot.get("whale_flow") or []
    arbitrage = snapshot.get("arbitrage") or {}

    rec_score = float(recommendation.get("score") or 0.0)
    rec_side = str(recommendation.get("side") or "").upper()
    if rec_score >= 7.5:
        score += 3.0
    elif rec_score >= 6.0:
        score += 2.0
    elif rec_score <= 3.0 and rec_score > 0:
        score -= 3.0
    elif rec_score <= 4.5 and rec_score > 0:
        score -= 1.5
    if rec_side == "BUY":
        score += 1.0
    elif rec_side == "SELL":
        score -= 1.0

    macro_regime = str(technical_context.get("macro_regime") or "").upper()
    if "BULL" in macro_regime or "UPTREND" in macro_regime:
        score += 2.0
    elif "BEAR" in macro_regime or "DOWNTREND" in macro_regime:
        score -= 2.0

    sentiment_score = float(sentiment.get("score") or 50.0)
    if sentiment_score >= 65:
        score += 1.5
    elif sentiment_score <= 35:
        score -= 1.5

    if technical_context.get("is_bull_trap"):
        score -= 2.0
    if technical_context.get("is_bear_trap"):
        score += 2.0

    if whale_flow:
        score += 1.0

    corr = arbitrage.get("correlation")
    try:
        corr_value = abs(float(corr))
    except Exception:
        corr_value = 0.0
    if corr_value >= 0.8:
        score += 0.5

    if score >= 2.0:
        verdict = "BULLISH"
    elif score <= -2.0:
        verdict = "BEARISH"
    else:
        verdict = "NEUTRAL"

    base_confidence = float(recommendation.get("confidence") or 0.0)
    if base_confidence <= 0:
        base_confidence = 42.0 + min(abs(score) * 9.0, 28.0)
    if technical_context.get("is_bull_trap") or technical_context.get("is_bear_trap"):
        base_confidence -= 8.0
    if whale_flow:
        base_confidence += 6.0
    confidence = max(28.0, min(92.0, round(base_confidence, 1)))
    return verdict, confidence


def _build_asset_analysis(snapshot: dict[str, Any], verdict: str, confidence: float) -> dict[str, str]:
    technical_context = snapshot.get("technical_context", {})
    recommendation = snapshot.get("recommendation", {})
    sentiment = snapshot.get("sentiment", {})
    whale_flow = snapshot.get("whale_flow") or []
    arbitrage = snapshot.get("arbitrage") or {}
    news_mentions = snapshot.get("news_mentions") or []

    macro_regime = str(technical_context.get("macro_regime") or "NEUTRAL").upper()
    sentiment_regime = _normalize_sentiment_regime(sentiment.get("regime"))
    sentiment_score = float(sentiment.get("score") or 50.0)
    ticker = str(snapshot.get("ticker") or "Asset").upper()

    if not snapshot.get("scope") and not _has_asset_specific_signal(snapshot):
        macro_label = macro_regime.lower()
        return {
            "short_term": (
                f"No {ticker}-specific signal is active yet; the broad market backdrop is {macro_label}, "
                "so Oracle is keeping this asset neutral until price, flow, or news confirms."
            ),
            "tactical_edge": (
                f"No recommendation levels, whale flow, news hit, trap flag, or mirror signal is currently attached to {ticker}."
            ),
            "risk_profile": (
                f"Avoid treating broad macro strength as an entry for {ticker} until Oracle receives ticker-specific confirmation."
            ),
        }

    if verdict == "BULLISH":
        short_term = (
            f"{snapshot.get('ticker', 'Asset')} is tilting constructive with {macro_regime.lower()} macro pressure "
            f"and {confidence:.0f}% tactical conviction."
        )
    elif verdict == "BEARISH":
        short_term = (
            f"{snapshot.get('ticker', 'Asset')} is losing traction under {macro_regime.lower()} conditions, "
            f"so near-term follow-through remains vulnerable."
        )
    else:
        short_term = (
            f"{snapshot.get('ticker', 'Asset')} is in a mixed tactical state with {macro_regime.lower()} conditions "
            f"and no decisive short-term edge yet."
        )

    if whale_flow:
        tactical_edge = (
            f"Whale flow is active with {len(whale_flow)} accumulation signal(s), while sentiment sits at "
            f"{sentiment_score:.0f}/100 ({sentiment_regime})."
        )
    elif news_mentions:
        tactical_edge = (
            f"News flow is driving the edge right now with {len(news_mentions)} relevant headline(s) and "
            f"{sentiment_score:.0f}/100 sentiment ({sentiment_regime})."
        )
    else:
        tactical_edge = (
            f"Cross-module confirmation is light, so wait for cleaner alignment between sentiment, flow, and price structure."
        )

    risk_bits: list[str] = []
    if technical_context.get("is_bull_trap"):
        risk_bits.append("bull-trap risk is elevated")
    if technical_context.get("is_bear_trap"):
        risk_bits.append("bear-trap dynamics can reverse the move quickly")
    entry = recommendation.get("entry")
    stop = recommendation.get("stop")
    target = recommendation.get("target")
    if entry and stop and target:
        risk_bits.append(
            f"active levels are {float(entry):.2f} entry, {float(stop):.2f} stop, and {float(target):.2f} target"
        )
    corr = arbitrage.get("correlation")
    try:
        corr_value = float(corr)
    except Exception:
        corr_value = 0.0
    if corr_value:
        risk_bits.append(f"mirror correlation is {corr_value * 100:.1f}%, so related names can amplify the move")
    if not risk_bits:
        risk_bits.append("confirmation is still shallow, so failed follow-through remains the main risk")

    return {
        "short_term": short_term,
        "tactical_edge": tactical_edge,
        "risk_profile": ". ".join(risk_bits).strip().capitalize() + ".",
    }


def asset_report_requires_refresh(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return True
    analysis = payload.get("analysis")
    sentiment = payload.get("snapshot", {}).get("sentiment", {})
    legacy_analysis = {
        "Assessing price action...",
        "Monitoring whale flow...",
        "Evaluating traps...",
    }
    if not isinstance(analysis, dict):
        return True
    if any(str(analysis.get(key) or "").strip() in legacy_analysis for key in ("short_term", "tactical_edge", "risk_profile")):
        return True
    if _normalize_sentiment_regime(sentiment.get("regime")) != str(sentiment.get("regime") or "").strip().upper():
        return True
    snapshot = payload.get("snapshot", {})
    verdict = str(payload.get("verdict") or "").upper()
    if isinstance(snapshot, dict) and not snapshot.get("scope"):
        price_levels = snapshot.get("price_levels")
        if not isinstance(price_levels, dict) or _row_price(price_levels.get("current_price")) is None:
            return True
        if verdict in {"BULLISH", "BEARISH"} and not _has_asset_specific_signal(snapshot):
            return True
    return False

def get_highest_scoring_ticker() -> Optional[str]:
    """Retrieves the ticker with the highest score from the latest completed scan."""
    latest_run = (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
        .first()
    )
    if not latest_run:
        return None
    
    top_rec = (
        SignalRecommendation.select()
        .where((SignalRecommendation.run == latest_run) & (SignalRecommendation.state == "ACTIVE"))
        .order_by(SignalRecommendation.score.desc())
        .first()
    )
    return top_rec.ticker if top_rec else None

def collect_asset_snapshot(ticker: str, caches: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Aggregates all known tactical intelligence for a specific ticker."""
    ticker = normalize_asset_choice(ticker)
    scope_tickers = _scope_tickers(ticker)
    is_scope_view = bool(scope_tickers)
    macro_target = ticker if is_scope_view else "EGX30"
    
    # 1. Technical Health (Macro + Local)
    macro = _macro_from_cache(caches, macro_target)
    if not isinstance(macro, dict):
        macro, _ = safe_call_with_error({"signal": "UNKNOWN"}, MarketPredictor.check_macro_health, macro_target)
    
    # 2. Whale Flow
    whales = _cache_data(caches, "WHALE_CACHE")
    if not _has_cache_entry(caches, "WHALE_CACHE") or not isinstance(whales, dict):
        whales, _ = safe_call_with_error({"candidates": []}, Vanaheim.hunt_whales)
    whale_candidates = whales.get("candidates", []) if isinstance(whales, dict) else []
    if is_scope_view:
        ticker_whales = [
            c for c in whale_candidates
            if str(c.get("Ticker", "")).upper() in scope_tickers
        ]
        ticker_whales.sort(key=lambda row: float(row.get("Volume_Ratio") or 0.0), reverse=True)
    else:
        ticker_whales = [c for c in whale_candidates if str(c.get("Ticker", "")).upper() == ticker]
    
    # 3. Traps
    traps = _cache_data(caches, "TRAP_CACHE")
    if not _has_cache_entry(caches, "TRAP_CACHE") or not isinstance(traps, dict):
        traps, _ = safe_call_with_error({"bull_traps": [], "bear_traps": []}, Svartalfheim.hunt_traps)
    bull_traps = traps.get("bull_traps", []) if isinstance(traps, dict) else []
    bear_traps = traps.get("bear_traps", []) if isinstance(traps, dict) else []
    if is_scope_view:
        matched_bull_traps = [t for t in bull_traps if str(t.get("ticker", "")).upper() in scope_tickers]
        matched_bear_traps = [t for t in bear_traps if str(t.get("ticker", "")).upper() in scope_tickers]
        is_bull_trap = bool(matched_bull_traps)
        is_bear_trap = bool(matched_bear_traps)
    else:
        matched_bull_traps = [t for t in bull_traps if str(t.get("ticker", "")).upper() == ticker]
        matched_bear_traps = [t for t in bear_traps if str(t.get("ticker", "")).upper() == ticker]
        is_bull_trap = bool(matched_bull_traps)
        is_bear_trap = bool(matched_bear_traps)
    
    # 4. Sentiment (News)
    has_cached_news, gossip_stories = _news_stories_from_cache(caches)
    if not has_cached_news:
        gather_gossip = getattr(SentimentCrawler, "gather_gossip", None)
        async_gather_gossip = getattr(SentimentCrawler, "async_gather_gossip", None)
        if callable(async_gather_gossip):
            gossip, _ = safe_call_with_error([], lambda: asyncio.run(async_gather_gossip()))
        elif callable(gather_gossip):
            gossip, _ = safe_call_with_error([], gather_gossip)
        else:
            gossip = []
        gossip_stories = gossip.get("stories", []) if isinstance(gossip, dict) else (gossip if isinstance(gossip, list) else [])
    # Filter gossip stories mentioning this ticker
    # We use SentimentCrawler's extract_tickers logic implicitly or filter by the 'tickers' list
    relevant_stories = []
    for story in gossip_stories:
        story_tickers = {str(item).upper() for item in (story.get("tickers", []) or [])}
        if is_scope_view:
            if ticker == "ALL":
                if story_tickers or story.get("title") or story.get("summary"):
                    relevant_stories.append(story)
            elif ticker in story_tickers or story_tickers.intersection(scope_tickers):
                relevant_stories.append(story)
        elif ticker in story_tickers:
            relevant_stories.append(story)
    
    ticker_sentiment = SentimentCrawler.get_bifrost_sentiment(relevant_stories) if relevant_stories else {"score": 50.0, "regime": "NEUTRAL"}

    # 5. Arbitrage (Mirrors)
    arbitrage = _cache_data(caches, "ARBITRAGE_CACHE")
    if not _has_cache_entry(caches, "ARBITRAGE_CACHE") or not isinstance(arbitrage, dict):
        arbitrage, _ = safe_call_with_error({"mirrors": []}, SandboxRegistry.get_lagged_correlations)
    mirrors = arbitrage.get("mirrors", []) if isinstance(arbitrage, dict) else []
    if is_scope_view:
        eligible_mirrors = []
        for mirror_row in mirrors:
            mirror_symbols = {
                str(mirror_row.get("symbol", "")).upper(),
                str(mirror_row.get("leader", "")).upper(),
                str(mirror_row.get("follower", "")).upper(),
                str(mirror_row.get("lagged_symbol", "")).upper(),
            }
            if mirror_symbols.intersection(scope_tickers):
                eligible_mirrors.append(mirror_row)
        eligible_mirrors.sort(key=lambda row: abs(float(row.get("correlation") or 0.0)), reverse=True)
        mirror = eligible_mirrors[0] if eligible_mirrors else None
    else:
        mirror = next((m for m in mirrors if str(m.get("symbol", "")).upper() == ticker), None)

    # 6. Recommendation Context
    recommendation_query = SignalRecommendation.select()
    if is_scope_view:
        scope_query = (
            recommendation_query
            .where(SignalRecommendation.ticker.in_(sorted(scope_tickers)))
            .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc(), SignalRecommendation.created_at.desc())
        )
        recommendation_rows = _coerce_query_rows(scope_query)
        latest_rec = recommendation_rows[0] if recommendation_rows else None
    else:
        ticker_query = (
            recommendation_query
            .where(SignalRecommendation.ticker == ticker)
            .order_by(SignalRecommendation.created_at.desc())
        )
        recommendation_rows = _coerce_query_rows(ticker_query)
        latest_rec = recommendation_rows[0] if recommendation_rows else None

    lead_ticker = _pick_lead_ticker(recommendation_rows, scope_tickers, ticker_whales) if is_scope_view else ticker
    lead_row = next(
        (row for row in recommendation_rows if str(getattr(row, "ticker", "") or "").upper() == lead_ticker),
        latest_rec,
    )
    scope_levels = _build_scope_level_clusters(recommendation_rows) if is_scope_view else None
    lead_ticker_levels = (
        {
            "ticker": lead_ticker,
            "entry": _row_price(getattr(lead_row, "entry_price", None)) if lead_row else None,
            "stop": _row_price(getattr(lead_row, "stop_loss", None)) if lead_row else None,
            "target": _row_price(getattr(lead_row, "target_price", None)) if lead_row else None,
        }
        if lead_ticker
        else None
    )

    scope_news_mentions = relevant_stories[:5] if is_scope_view else []
    lead_ticker_news_mentions = []
    if is_scope_view and lead_ticker:
        for story in relevant_stories:
            story_tickers = {str(item).upper() for item in (story.get("tickers", []) or [])}
            if lead_ticker in story_tickers:
                lead_ticker_news_mentions.append(story)
    
    snapshot = {
        "ticker": ticker,
        "as_of": TimeUtils.now().isoformat(),
        "scope": ticker if is_scope_view else None,
        "lead_ticker": lead_ticker if is_scope_view else None,
        "scope_levels": scope_levels,
        "lead_ticker_levels": lead_ticker_levels,
        "technical_context": {
            "macro_regime": macro.get("signal"),
            "is_bull_trap": is_bull_trap,
            "is_bear_trap": is_bear_trap,
            "bull_trap_count": len(matched_bull_traps),
            "bear_trap_count": len(matched_bear_traps),
        },
        "whale_flow": ticker_whales[:8],
        "sentiment": ticker_sentiment,
        "news_mentions": relevant_stories[:5],
        "scope_news_mentions": scope_news_mentions,
        "lead_ticker_news_mentions": lead_ticker_news_mentions[:3],
        "arbitrage": mirror,
        "price_levels": None if is_scope_view else _build_price_history_levels(ticker),
        "recommendation": {
            "ticker": latest_rec.ticker if latest_rec else ticker,
            "side": latest_rec.side if latest_rec else None,
            "score": float(latest_rec.score) if latest_rec else 0.0,
            "confidence": float(latest_rec.confidence) if latest_rec else 0.0,
            "entry": _row_price(getattr(latest_rec, "entry_price", None)) if latest_rec else None,
            "stop": _row_price(getattr(latest_rec, "stop_loss", None)) if latest_rec else None,
            "target": _row_price(getattr(latest_rec, "target_price", None)) if latest_rec else None,
            "rationale": latest_rec.rationale_json if latest_rec else None,
        }
    }
    snapshot["asset_evidence"] = _build_asset_evidence(snapshot)
    return snapshot

def generate_asset_report(
    ticker: str,
    save: bool = True,
    caches: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Generates an AI synthesis for a specific asset and persists it."""
    ticker = normalize_asset_choice(ticker)
    snapshot = collect_asset_snapshot(ticker, caches=caches)
    snapshot["ticker"] = ticker
    if isinstance(snapshot.get("sentiment"), dict):
        snapshot["sentiment"] = {
            **snapshot["sentiment"],
            "regime": _normalize_sentiment_regime(snapshot["sentiment"].get("regime")),
        }
    snapshot["asset_evidence"] = _build_asset_evidence(snapshot)
    
    from routes.ai_report import _maybe_generate_llm_report, _generate_rule_based_report
    
    # We use a custom prompt for assets if needed, but for now we follow the daily report pattern
    # and adapt the snapshot for the LLM.
    # Actually, _maybe_generate_llm_report expects a "Global" snapshot. 
    # We should probably define an ASSET_PROMPT template in core/ai_report/generation.py
    
    # For now, let's use a rule-based synthesis as a baseline
    verdict, confidence = _derive_asset_verdict(snapshot)
    report_payload = {
        "status": "success",
        "ticker": ticker,
        "generated_at": TimeUtils.now().isoformat(),
        "snapshot": snapshot,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": "Tactical synthesis derived from scanner, macro, sentiment, whale-flow, and trap context.",
        "analysis": _build_asset_analysis(snapshot, verdict, confidence),
    }
    
    if save:
        AssetAiReport.create(
            ticker=ticker,
            payload_json=json.dumps(report_payload),
            source_module="LOCAL",
            confidence_score=report_payload["confidence"]
        )
        
    return report_payload
