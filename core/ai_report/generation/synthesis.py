from __future__ import annotations

from typing import Any

from ..boundary import dedupe_report_sections
from .scoring import (
    _build_promotion_context,
    _build_rule_based_recommendations,
    _derive_local_execution_profile,
    _score_market_direction,
)


def _generate_rule_based_report(snapshot: dict[str, Any]) -> dict[str, Any]:
    score, reasons = _score_market_direction(snapshot)

    if score >= 6:
        label = "BULLISH"
        bias_desc = "STRONGLY BULLISH"
    elif score >= 3:
        label = "BULLISH"
        bias_desc = "MODERATELY BULLISH"
    elif score <= -6:
        label = "BEARISH"
        bias_desc = "STRONGLY BEARISH"
    elif score <= -3:
        label = "BEARISH"
        bias_desc = "MODERATELY BEARISH"
    elif score >= 1:
        label = "NEUTRAL"
        bias_desc = "SLIGHTLY BULLISH LEAN"
    elif score <= -1:
        label = "NEUTRAL"
        bias_desc = "SLIGHTLY BEARISH LEAN"
    else:
        label = "NEUTRAL"
        bias_desc = "FLAT / NO EDGE"

    confidence = max(35, min(95, 45 + abs(score) * 7))
    execution_profile = _derive_local_execution_profile(snapshot, label, score, confidence, reasons)

    summary: list[str] = []
    macro_signal = snapshot.get("oracle", {}).get("macro_signal") or "UNKNOWN"
    macro_msg = snapshot.get("oracle", {}).get("macro_message")
    strategy = snapshot.get("strategy", {})
    strategy_regime = strategy.get("regime") or "UNKNOWN"
    volatility = strategy.get("volatility")
    summary.append(
        f"MARKET STRUCTURE: Composite stance is {label} ({confidence:.1f}% confidence). "
        f"Macro is {macro_signal}, strategy engine is {strategy_regime}"
        + (f", volatility {volatility}" if volatility else "")
        + "."
    )
    summary.append(
        "EXECUTION PROFILE: "
        f"{execution_profile.get('mode')} | selectivity {execution_profile.get('selectivity')} | "
        f"max new positions {execution_profile.get('max_new_positions')} | "
        f"risk per trade <= {execution_profile.get('max_risk_per_trade_pct')}%."
    )

    if macro_msg:
        summary.append(f'ORACLE SAYS: "{macro_msg}"')

    sectors = snapshot.get("sectors", {})
    leading = sectors.get("leading", [])
    lagging = sectors.get("lagging", [])
    if leading:
        leading_names = ", ".join([s.get("sector", s.get("name", "?")) for s in leading[:4]])
        summary.append(f"SECTOR LEADERS: {leading_names}.")
    if lagging:
        lagging_names = ", ".join([s.get("sector", s.get("name", "?")) for s in lagging[:3]])
        summary.append(f"SECTOR LAGGARDS: {lagging_names}.")

    whales = snapshot.get("whales", {})
    acc = int(whales.get("accumulation_count") or 0)
    dist = int(whales.get("distribution_count") or 0)
    if acc + dist > 0:
        top_acc_tickers = [c.get("Ticker", "?") for c in whales.get("top_accumulation", [])[:3]]
        top_dist_tickers = [c.get("Ticker", "?") for c in whales.get("top_distribution", [])[:3]]
        whale_line = f"WHALE FLOW: {acc} accumulating"
        if top_acc_tickers:
            whale_line += f" (top: {', '.join(top_acc_tickers)})"
        whale_line += f", {dist} distributing"
        if top_dist_tickers:
            whale_line += f" (top: {', '.join(top_dist_tickers)})"
        whale_line += "."
        summary.append(whale_line)

    news = snapshot.get("news", {})
    sentiment = float(news.get("sentiment_score") or 50.0)
    sentiment_regime = str(news.get("sentiment_regime") or "N/A")
    headlines = news.get("headlines", [])
    summary.append(f"NEWS MOOD: {sentiment:.0f}/100 ({sentiment_regime}) from {news.get('count', 0)} stories.")
    if headlines:
        top_headline = headlines[0].get("title", "")
        if top_headline:
            summary.append(f'TOP HEADLINE: "{top_headline[:80]}"')

    traps = snapshot.get("traps", {})
    bear_traps = int(traps.get("bear_trap_count") or 0)
    bull_traps = int(traps.get("bull_trap_count") or 0)
    if bear_traps + bull_traps > 0:
        trap_line = f"TRAPS: {bear_traps} bear traps (bullish reversal)"
        if bull_traps:
            trap_line += f", {bull_traps} bull traps (distribution risk)"
        summary.append(trap_line + ".")

    squeeze_count = int(snapshot.get("oracle", {}).get("squeeze_count") or 0)
    if squeeze_count > 0:
        top_squeezes = snapshot.get("oracle", {}).get("top_squeezes", [])
        squeeze_tickers = [s.get("Ticker", "?") for s in top_squeezes[:4]]
        summary.append(f"SQUEEZES: {squeeze_count} stocks coiling - {', '.join(squeeze_tickers)}.")

    signals = snapshot.get("signals", {})
    shadow_context = dict(signals.get("whale_trap_summary") or {})
    enforcement_context = dict(signals.get("enforcement_summary") or {})
    calibration_context = dict(signals.get("calibration_summary") or {})
    promotion_context = _build_promotion_context(calibration_context)
    buy_count = int(signals.get("buy_count") or 0)
    sell_count = int(signals.get("sell_count") or 0)
    avg_score = float(signals.get("avg_score") or 0.0)
    avg_conf = float(signals.get("avg_confidence") or 0.0)
    if buy_count + sell_count > 0:
        summary.append(
            f"SIGNALS: {buy_count} buy / {sell_count} sell recommendations, "
            f"avg score {avg_score:.1f}/10, avg confidence {avg_conf:.0f}%."
        )
    if shadow_context:
        supportive = int(shadow_context.get("supportive_whale_alignments") or 0)
        conflicts = int(shadow_context.get("whale_conflicts") or 0)
        high_risk = int(shadow_context.get("high_trap_risk_count") or 0)
        severe_risk = int(shadow_context.get("severe_trap_risk_count") or 0)
        summary.append(
            f"SHADOW FLOW: {supportive} supportive whale alignments, {conflicts} whale conflicts, "
            f"{high_risk} high-risk and {severe_risk} severe-risk candidates."
        )
        top_supportive = [str(row.get("ticker") or "?") for row in shadow_context.get("top_supportive_names", [])[:2]]
        top_conflicted = [str(row.get("ticker") or "?") for row in shadow_context.get("top_conflicted_or_high_risk_names", [])[:2]]
        if top_supportive or top_conflicted:
            leader_parts: list[str] = []
            if top_supportive:
                leader_parts.append(f"supportive: {', '.join(top_supportive)}")
            if top_conflicted:
                leader_parts.append(f"conflict/risk: {', '.join(top_conflicted)}")
            summary.append(f"SHADOW LEADERS: {' | '.join(leader_parts)}.")
        threshold_analysis = dict(shadow_context.get("threshold_analysis") or {})
        if threshold_analysis:
            would_review = int(threshold_analysis.get("would_review_count") or 0)
            would_block = int(threshold_analysis.get("would_block_count") or 0)
            summary.append(
                f"SHADOW THRESHOLDS: future gates would review {would_review} candidate(s) and block {would_block} candidate(s) under current rules."
            )
    if enforcement_context:
        allow_count = int(enforcement_context.get("allow_count") or 0)
        watch_only_count = int(enforcement_context.get("watch_only_count") or 0)
        block_count = int(enforcement_context.get("block_count") or 0)
        summary.append(
            f"ENFORCEMENT: {allow_count} actionable, {watch_only_count} watch-only, {block_count} blocked candidate(s)."
        )
    if calibration_context:
        top_segments = dict(calibration_context.get("market_segments") or {})
        if top_segments:
            first_segment_summary = next(iter(top_segments.values()))
            active_profile = str(first_segment_summary.get("active_enforcement_profile") or "DEFAULT")
            candidates = dict(first_segment_summary.get("calibration_summary", {}).get("candidates") or {})
            if candidates:
                candidate_name, candidate_summary = next(iter(candidates.items()))
                deltas = dict(candidate_summary.get("deltas") or {})
                summary.append(
                    "CALIBRATION: "
                    f"{active_profile} vs {candidate_name} remains compare-only; "
                    f"candidate drift is {int(deltas.get('allow_delta') or 0):+d} allow / "
                    f"{int(deltas.get('watch_only_delta') or 0):+d} watch / "
                    f"{int(deltas.get('block_delta') or 0):+d} block."
                )
    if promotion_context:
        top_segments = dict(promotion_context.get("market_segments") or {})
        if top_segments:
            first_promotion = next(iter(top_segments.values()))
            previous_profile = str(first_promotion.get("previous_active_profile") or "DEFAULT")
            new_profile = str(first_promotion.get("new_active_profile") or previous_profile)
            rollback_profile = str(first_promotion.get("rollback_profile") or previous_profile)
            summary.append(
                f"PROMOTION: active baseline moved from {previous_profile} to {new_profile}; rollback remains {rollback_profile}."
            )

    portfolio = snapshot.get("portfolio", {})
    open_pos = int(portfolio.get("open_positions") or 0)
    total_pnl = float(portfolio.get("total_pnl") or 0.0)
    if open_pos > 0:
        summary.append(f"PORTFOLIO: {open_pos} open positions, total P&L: {total_pnl:+,.0f}.")

    arb = snapshot.get("arbitrage", {})
    arb_count = int(arb.get("count") or 0)
    if arb_count > 0:
        arb_mirrors = arb.get("top_mirrors", [])
        if arb_mirrors:
            leader = arb_mirrors[0].get("Leader") or arb_mirrors[0].get("leader", "?")
            follower = arb_mirrors[0].get("Follower") or arb_mirrors[0].get("follower", "?")
            summary.append(f"ARBITRAGE: {arb_count} mirror pair(s) detected (e.g. {leader} -> {follower}).")

    cross_tab_findings = reasons[:]
    bullish_count = sum(1 for r in reasons if "[+" in r)
    bearish_count = sum(1 for r in reasons if "[-" in r)
    if bullish_count >= 5:
        cross_tab_findings.insert(0, f"STRONG CONFLUENCE: {bullish_count} of {len(reasons)} modules confirm bullish bias.")
    elif bearish_count >= 5:
        cross_tab_findings.insert(0, f"STRONG CONFLUENCE: {bearish_count} of {len(reasons)} modules confirm bearish bias.")
    elif bullish_count >= 3 and bearish_count >= 2:
        cross_tab_findings.insert(0, f"MIXED SIGNALS: {bullish_count} bullish vs {bearish_count} bearish. Proceed with caution.")

    if not cross_tab_findings:
        cross_tab_findings.append("No decisive cross-tab edge; keep positioning light.")

    recommendations = _build_rule_based_recommendations(
        snapshot=snapshot,
        direction_label=label,
        composite_score=score,
        confidence=float(confidence),
        execution_profile=execution_profile,
    )

    risk_warnings: list[str] = []
    for w in portfolio.get("warnings", []):
        risk_warnings.append(w)
    if total_pnl < 0 and open_pos > 0:
        risk_warnings.append(f"Portfolio is negative ({total_pnl:+,.0f}). Tighten stops and avoid averaging down.")
    top_positions = portfolio.get("top_positions", [])
    if top_positions:
        max_weight = float(top_positions[0].get("weight_pct", 0))
        if max_weight >= 30:
            risk_warnings.append(f"Concentration risk: {top_positions[0]['ticker']} is {max_weight:.0f}% of portfolio.")

    if label == "NEUTRAL":
        risk_warnings.append("Direction confidence low - avoid oversized trades and use tight stops.")
    if bullish_count >= 2 and bearish_count >= 2:
        risk_warnings.append("Conflicting signals across modules - reduce position sizes until clarity emerges.")
    if bull_traps >= 3:
        risk_warnings.append(f"Elevated bull-trap activity ({bull_traps}) - verify entries with volume confirmation.")
    if squeeze_count >= 5:
        risk_warnings.append(f"{squeeze_count} squeezes detected. Expect sharp moves; set wider stops or reduce size.")
    if sentiment <= 35:
        risk_warnings.append("Negative news sentiment - headline risk elevated. Consider defensive positioning.")

    freshness = snapshot.get("data_freshness", {})
    freshness_label = str(freshness.get("label", "")).upper()
    if freshness_label == "STALE":
        risk_warnings.append("Data freshness is STALE. Report accuracy may be degraded - verify with live data.")

    if volatility and "HIGH" in str(volatility).upper():
        risk_warnings.append("Strategy engine detects HIGH volatility. Reduce position sizes by 30-50%.")
    if bool(execution_profile.get("prefer_no_trade")):
        risk_warnings.append("Execution profile is CAPITAL_PRESERVATION. Prefer no-trade or watch-only stance.")
    if str(execution_profile.get("selectivity", "")).upper() in {"HIGH", "VERY_HIGH"}:
        risk_warnings.append("High selectivity mode active. Avoid forcing marginal setups.")
    if shadow_context:
        severe_risk = int(shadow_context.get("severe_trap_risk_count") or 0)
        high_risk = int(shadow_context.get("high_trap_risk_count") or 0)
        conflicts = int(shadow_context.get("whale_conflicts") or 0)
        threshold_analysis = dict(shadow_context.get("threshold_analysis") or {})
        if severe_risk > 0:
            risk_warnings.append(f"Severe trap-risk candidates detected ({severe_risk}) - keep these in watch-only mode until conditions improve.")
        elif high_risk > 0:
            risk_warnings.append(f"High trap-risk candidates detected ({high_risk}) - trim size and demand stronger confirmation.")
        if conflicts > 0:
            risk_warnings.append(f"Whale-flow conflicts present in {conflicts} candidate(s) - prefer names with supportive accumulation.")
        if threshold_analysis:
            would_review = int(threshold_analysis.get("would_review_count") or 0)
            would_block = int(threshold_analysis.get("would_block_count") or 0)
            if would_review > 0 or would_block > 0:
                risk_warnings.append(
                    f"Shadow thresholds would review {would_review} candidate(s) and block {would_block} candidate(s) if future trap/whale gates were enforced."
                )
    if enforcement_context:
        watch_only_count = int(enforcement_context.get("watch_only_count") or 0)
        block_count = int(enforcement_context.get("block_count") or 0)
        if block_count > 0:
            risk_warnings.append(
                f"Blocked candidates detected ({block_count}) - keep these visible for review, but do not treat them as executable ideas."
            )
        elif watch_only_count > 0:
            risk_warnings.append(
                f"Watch-only candidates detected ({watch_only_count}) - commentary may remain useful, but execution should stay deferred."
            )
    if calibration_context:
        top_delta_reasons = list(calibration_context.get("top_delta_reasons") or [])
        top_reclassified = list(calibration_context.get("top_reclassified_names") or [])
        if top_delta_reasons or top_reclassified:
            warning = "Compare-only calibration drift detected"
            if top_delta_reasons:
                top_reason = str(top_delta_reasons[0].get("reason") or "").replace("_", " ")
                top_delta = int(top_delta_reasons[0].get("delta") or 0)
                warning += f": {top_reason} adds {top_delta} candidate(s)"
            if top_reclassified:
                ticker = str(top_reclassified[0].get("ticker") or "?")
                candidate_state = str(top_reclassified[0].get("candidate_state") or "UNKNOWN")
                warning += f"; {ticker} would move to {candidate_state}"
            risk_warnings.append(warning + " under candidate profiles only.")
    if promotion_context:
        top_segments = dict(promotion_context.get("market_segments") or {})
        if top_segments:
            first_promotion = next(iter(top_segments.values()))
            rollback_profile = str(first_promotion.get("rollback_profile") or "").strip()
            if rollback_profile:
                risk_warnings.append(
                    f"Rollback remains available via {rollback_profile} if promoted baseline behavior proves too aggressive."
                )

    checklist: list[str] = []
    if label == "BULLISH":
        checklist.append("Prioritize top scanner BUY signals with score >= 7 and volume confirmation.")
        checklist.append("Set trailing stops on winning positions to lock in gains.")
        if squeeze_count > 0:
            checklist.append("Monitor squeeze candidates for breakout entries after directional confirmation.")
    elif label == "BEARISH":
        checklist.append("Tighten stop-losses on all open positions to protect capital.")
        checklist.append("Avoid new long entries unless score >= 8 with strong volume.")
        checklist.append("Consider reducing overall exposure until macro stabilizes.")
    else:
        checklist.append("Wait for macro clarity before taking new positions.")
        checklist.append("Focus on highest-conviction setups only (score >= 8).")

    checklist.append(
        f"Hard risk caps: <= {execution_profile.get('max_risk_per_trade_pct')}% risk per trade "
        f"and <= {execution_profile.get('max_total_new_risk_pct')}% total new risk."
    )
    checklist.append("Reject setups with risk/reward below 1.8:1 unless trade is a hedge.")
    checklist.append(f"Trade frequency guidance: {execution_profile.get('trade_frequency_guidance')}")
    checklist.append("Re-check macro breadth and oracle signal after the next close.")
    checklist.append("Validate top recommendations against live volume before execution.")
    checklist.append("Review stop-loss placement to keep max risk per trade under your policy.")

    if acc > 3:
        checklist.append("Cross-reference whale accumulation tickers with scanner signals for highest conviction.")
    if arb_count > 0:
        checklist.append("Check arbitrage mirror pairs for lagged entry opportunities.")

    headline = f"{bias_desc} Bias | Composite Score {score:+d} | {buy_count + sell_count} Active Signals"

    report_payload = {
        "headline": headline,
        "market_direction": {
            "label": label,
            "confidence": float(confidence),
            "time_horizon": "Next trading day",
            "composite_score": score,
            "bias_description": bias_desc,
            "reasoning": reasons[:12],
            "execution_mode": execution_profile.get("mode"),
            "trade_selectivity": execution_profile.get("selectivity"),
        },
        "daily_report": {
            "summary": summary[:20],
            "cross_tab_findings": cross_tab_findings[:14],
        },
        "recommendations": recommendations[:10],
        "risk_warnings": risk_warnings[:12],
        "next_checklist": checklist[:10],
        "execution_profile": execution_profile,
        "shadow_context": shadow_context,
        "enforcement_context": enforcement_context,
        "calibration_context": calibration_context,
        "promotion_context": promotion_context,
    }
    return dedupe_report_sections(report_payload)
