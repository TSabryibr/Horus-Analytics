from __future__ import annotations

from typing import Any, Optional


def _strategy_regime_bias(strategy_regime: str) -> str:
    normalized = str(strategy_regime or "").upper()
    if "BULL" in normalized:
        return "BULLISH"
    if "BEAR" in normalized:
        return "BEARISH"
    return "NEUTRAL"


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
        reasons.append("Oracle macro signal is NEUTRAL - no trend conviction.")

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
        reasons.append(f"Strategy regime: {strategy_regime} - no directional bias.")

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
            reasons.append(f"Strong whale distribution: {dist} vs {acc} accumulation ({1 - whale_ratio:.0%}). [-{weight}]")
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
    if bull_traps >= 30:
        score -= 4
        reasons.append(f"Extreme Bull Trap density ({bull_traps} traps) signals severe distribution risk & retail liquidity absorption. [-4]")
    elif trap_diff >= 3:
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
        reasons.append(f"{squeeze_count} volatility squeezes detected - explosive moves imminent.")
    elif squeeze_count >= 1:
        reasons.append(f"{squeeze_count} volatility squeeze(s) building - watch for breakouts.")

    portfolio = snapshot.get("portfolio", {})
    open_pos = int(portfolio.get("open_positions") or 0)
    total_pnl = float(portfolio.get("total_pnl") or 0.0)
    if total_pnl < 0 and open_pos > 0:
        reasons.append(f"Portfolio under water: {total_pnl:+,.0f} unrealized - consider defensive positioning.")
    elif total_pnl > 0 and open_pos > 0:
        reasons.append(f"Portfolio positive: {total_pnl:+,.0f} - momentum support from existing positions.")

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
    freshness_label = str(freshness.get("label", "N/A")).upper()

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
        trade_frequency_guidance = "Reduce exposure and trade only validated high-conviction entries."
        max_new_positions = 2
        max_risk_per_trade_pct = 0.7
        max_total_new_risk_pct = 2.0
    elif abs_score >= 6 and confidence >= 75:
        mode = "TREND_FOLLOWING"
        selectivity = "MEDIUM"
        trade_frequency_guidance = "Normal frequency with disciplined risk caps; favor momentum-aligned entries."
        max_new_positions = 4
        max_risk_per_trade_pct = 1.25
        max_total_new_risk_pct = 5.0

    traps = snapshot.get("traps", {})
    bull_traps = int(traps.get("bull_trap_count") or 0)
    if bull_traps >= 30:
        mode = "PULLBACK_RETEST_ONLY"
        selectivity = "HIGH"
        trade_frequency_guidance = (
            f"Extreme bull trap density ({bull_traps} traps). Avoid market breakout buys; "
            "require volume-confirmed pullback limit orders."
        )
        max_new_positions = min(int(max_new_positions), 2)
        max_risk_per_trade_pct = min(float(max_risk_per_trade_pct), 1.25)
        max_total_new_risk_pct = min(float(max_total_new_risk_pct), 2.5)

    return {
        "mode": mode,
        "selectivity": selectivity,
        "trade_frequency_guidance": trade_frequency_guidance,
        "max_new_positions": int(max_new_positions),
        "max_risk_per_trade_pct": round(float(max_risk_per_trade_pct), 2),
        "max_total_new_risk_pct": round(float(max_total_new_risk_pct), 2),
        "prefer_no_trade": bool(prefer_no_trade),
        "confluence": {
            "bullish_modules": bullish_count,
            "bearish_modules": bearish_count,
            "mixed_signals": mixed_signals,
        },
    }


def _compute_rr_ratio(entry_price: float, stop_loss: float, take_profit: float) -> Optional[float]:
    try:
        risk_points = abs(float(entry_price) - float(stop_loss))
        reward_points = abs(float(take_profit) - float(entry_price))
        if risk_points <= 0:
            return None
        return round(reward_points / risk_points, 2)
    except Exception:
        return None


def _build_rule_based_recommendations(
    snapshot: dict[str, Any],
    direction_label: str,
    composite_score: int,
    confidence: float,
    execution_profile: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    exec_profile = execution_profile or {}
    prefer_no_trade = bool(exec_profile.get("prefer_no_trade", False))
    max_risk_per_trade_pct = float(exec_profile.get("max_risk_per_trade_pct", 1.0) or 1.0)

    signal_recs = list(snapshot.get("signals", {}).get("active_recommendations", []))
    for row in signal_recs[:6]:
        side = str(row.get("side", "")).upper()
        score_val = float(row.get("score", 0))
        conf_val = float(row.get("confidence", 0))
        entry_price = float(row.get("entry_price", 0.0) or 0.0)
        stop_loss = float(row.get("stop_loss", 0.0) or 0.0)
        target_price = float(row.get("target_price", 0.0) or 0.0)

        raw_action = "BUY" if side == "BUY" else "SELL"
        aligned_with_bias = (
            (direction_label == "BULLISH" and raw_action == "BUY")
            or (direction_label == "BEARISH" and raw_action == "SELL")
        )
        action = raw_action
        if direction_label == "NEUTRAL" or not aligned_with_bias:
            action = "WATCH"

        if score_val >= 8 and conf_val >= 70:
            risk = "LOW"
        elif score_val >= 6:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        if action == "WATCH":
            risk = "HIGH" if direction_label == "NEUTRAL" else "MEDIUM"

        rr_ratio = _compute_rr_ratio(entry_price, stop_loss, target_price)
        if rr_ratio is not None and rr_ratio < 1.5:
            risk = "HIGH"

        whale_alignment = str(row.get("whale_alignment") or "NEUTRAL").upper()
        whale_signal = str(row.get("whale_signal") or "UNKNOWN").upper()
        trap_risk_band = str(row.get("trap_risk_band") or "UNKNOWN").upper()
        trap_risk_reason = str(row.get("trap_risk_reason") or "").strip()
        enforcement_state = str(row.get("enforcement_state") or "ALLOW").upper()
        enforcement_reason = str(row.get("enforcement_reason") or "").strip()
        if trap_risk_band == "SEVERE":
            risk = "HIGH"
        elif trap_risk_band == "HIGH" and risk == "LOW":
            risk = "MEDIUM"

        regime_note = f" | regime: {row.get('regime')}" if row.get("regime") else ""
        validation_checks: list[str] = []
        validation_checks.append(
            "Direction aligned with composite bias."
            if aligned_with_bias
            else "Direction not aligned with composite bias; downgraded to WATCH."
        )
        if rr_ratio is None:
            validation_checks.append("Risk/reward unavailable from signal prices.")
        elif rr_ratio >= 1.8:
            validation_checks.append(f"Risk/reward acceptable ({rr_ratio}:1).")
        else:
            validation_checks.append(f"Risk/reward weak ({rr_ratio}:1).")
        if conf_val >= 70:
            validation_checks.append("Confidence threshold met (>=70%).")
        else:
            validation_checks.append("Confidence below ideal threshold (<70%).")

        rationale_bits = [f"Scanner score {score_val:.0f}/10 with {conf_val:.0f}% confidence{regime_note}."]
        if whale_alignment == "SUPPORTIVE" and whale_signal == "ACCUMULATION":
            rationale_bits.append("Whale accumulation support aligns with the breakout.")
            validation_checks.append("Whale flow supportive (accumulation).")
        elif whale_alignment == "CONFLICT" and whale_signal == "DISTRIBUTION":
            rationale_bits.append("Whale distribution conflict argues for extra caution.")
            validation_checks.append("Whale flow conflicts with the breakout.")
        if trap_risk_band in {"HIGH", "SEVERE"}:
            reason_note = trap_risk_reason.replace("_", " ") if trap_risk_reason else "elevated trap risk"
            rationale_bits.append(f"Shadow trap-risk is {trap_risk_band.lower()} ({reason_note}).")
            validation_checks.append(f"Trap-risk elevated ({trap_risk_band}).")
        if enforcement_state == "BLOCK_EXECUTION":
            action = "WATCH"
            risk = "HIGH"
            reason_note = enforcement_reason.replace("_", " ") if enforcement_reason else "shadow enforcement gate"
            rationale_bits.append(
                f"Technically valid but blocked by whale/trap enforcement ({reason_note})."
            )
            validation_checks.append("Execution blocked by shared whale/trap enforcement gate.")
        elif enforcement_state == "WATCH_ONLY":
            action = "WATCH"
            risk = "HIGH" if risk == "LOW" else risk
            reason_note = enforcement_reason.replace("_", " ") if enforcement_reason else "shadow enforcement gate"
            rationale_bits.append(
                f"Downgraded to watch-only by whale/trap enforcement ({reason_note})."
            )
            validation_checks.append("Shared whale/trap enforcement downgraded the setup to watch-only.")

        recs.append(
            {
                "ticker": row.get("ticker"),
                "action": action,
                "confidence": round(conf_val, 1),
                "risk": risk,
                "rationale": " ".join(rationale_bits),
                "entry_zone": str(round(entry_price, 4)),
                "stop_loss": str(round(stop_loss, 4)),
                "take_profit": str(round(target_price, 4)),
                "horizon": "1-5d",
                "source": "Scanner",
                "enforcement_state": enforcement_state,
                "enforcement_reason": enforcement_reason,
                "position_risk_pct": round(max_risk_per_trade_pct if action in {"BUY", "SELL"} else max_risk_per_trade_pct * 0.5, 2),
                "rr_ratio": rr_ratio if rr_ratio is not None else "N/A",
                "validation_checks": validation_checks[:4],
            }
        )

    if len(recs) < 5:
        top_acc = snapshot.get("whales", {}).get("top_accumulation", [])
        existing_tickers = {r["ticker"] for r in recs}
        for row in top_acc[:5]:
            ticker = row.get("Ticker")
            if ticker in existing_tickers:
                continue
            volume_ratio = float(row.get("Volume_Ratio") or 0)
            price = row.get("Price") or row.get("price")
            sector = row.get("Sector") or row.get("sector", "")
            signal_strength = row.get("Signal_Strength") or row.get("signal_strength", "")

            whale_conf = 50.0
            if volume_ratio >= 3.0:
                whale_conf += 25.0
            elif volume_ratio >= 2.0:
                whale_conf += 18.0
            elif volume_ratio >= 1.5:
                whale_conf += 10.0
            elif volume_ratio >= 1.0:
                whale_conf += 5.0
            if direction_label == "BULLISH":
                whale_conf += 10.0
            whale_conf = min(85.0, whale_conf)

            rationale_parts = ["Institutional accumulation detected"]
            if volume_ratio:
                rationale_parts.append(f"volume {volume_ratio:.1f}x avg")
            if sector:
                rationale_parts.append(f"sector: {sector}")
            if signal_strength:
                rationale_parts.append(f"signal: {signal_strength}")
            rationale = ". ".join([", ".join(rationale_parts) + "."])

            if price:
                try:
                    p = float(price)
                    entry_zone = f"{p * 0.99:.2f} - {p * 1.01:.2f}"
                    stop_loss = f"{p * 0.95:.2f} (5% below current)"
                    take_profit = f"{p * 1.10:.2f} - {p * 1.15:.2f} (10-15% upside)"
                except (ValueError, TypeError):
                    entry_zone = "Confirm breakout above recent high"
                    stop_loss = "Below recent swing low"
                    take_profit = "2R to 3R"
            else:
                entry_zone = "Confirm breakout above recent high"
                stop_loss = "Below recent swing low"
                take_profit = "2R to 3R"

            whale_action = "WATCH" if direction_label != "BULLISH" else "BUY"
            recs.append(
                {
                    "ticker": ticker,
                    "action": whale_action,
                    "confidence": round(whale_conf, 1),
                    "risk": "MEDIUM" if whale_conf >= 65 else "HIGH",
                    "rationale": rationale,
                    "entry_zone": entry_zone,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "horizon": "3-10d",
                    "source": "Whale Tracker",
                    "position_risk_pct": round(max_risk_per_trade_pct * 0.75, 2),
                    "rr_ratio": "2.0:1 est." if price else "N/A",
                    "validation_checks": [
                        "Requires breakout confirmation with volume.",
                        f"Volume ratio: {volume_ratio:.1f}x." if volume_ratio else "Volume data unavailable.",
                        "Cross-reference with scanner signals for confluence.",
                    ],
                }
            )

    if len(recs) < 8:
        top_squeezes = snapshot.get("oracle", {}).get("top_squeezes", [])
        existing_tickers = {r["ticker"] for r in recs}
        for sq in top_squeezes[:3]:
            ticker = sq.get("Ticker")
            if ticker in existing_tickers:
                continue
            bw = float(sq.get("BandWidth", 0) or 0)
            price = sq.get("Price") or sq.get("price")
            sector = sq.get("Sector") or sq.get("sector", "")

            squeeze_conf = 40.0
            if bw > 0 and bw < 0.03:
                squeeze_conf = 60.0
            elif bw > 0 and bw < 0.05:
                squeeze_conf = 52.0
            elif bw > 0 and bw < 0.08:
                squeeze_conf = 45.0

            if price:
                try:
                    p = float(price)
                    entry_zone = f"Breakout above {p * 1.02:.2f} or below {p * 0.98:.2f}"
                    stop_loss = f"{p * 0.96:.2f} (4% from breakout)"
                    take_profit = f"{p * 1.08:.2f} - {p * 1.12:.2f} (ATR extension)"
                except (ValueError, TypeError):
                    entry_zone = "On breakout above BB upper or below BB lower"
                    stop_loss = "Opposite Bollinger Band"
                    take_profit = "1.5-2x ATR extension"
            else:
                entry_zone = "On breakout above BB upper or below BB lower"
                stop_loss = "Opposite Bollinger Band"
                take_profit = "1.5-2x ATR extension"

            rationale = f"Volatility squeeze (BW: {bw:.4f})"
            if sector:
                rationale += f" in {sector}"
            rationale += ". Coiling for explosive move - wait for directional confirmation."

            recs.append(
                {
                    "ticker": ticker,
                    "action": "WATCH",
                    "confidence": round(squeeze_conf, 1),
                    "risk": "HIGH",
                    "rationale": rationale,
                    "entry_zone": entry_zone,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "horizon": "1-7d",
                    "source": "Squeeze Scanner",
                    "position_risk_pct": round(max_risk_per_trade_pct * 0.5, 2),
                    "rr_ratio": "2.0:1 est.",
                    "validation_checks": [
                        "Breakout direction must confirm before entry.",
                        f"Bandwidth {bw:.4f} - {'very tight, high probability' if bw < 0.03 else 'moderate compression'}.",
                        "Avoid pre-breakout entries; wait for candle close.",
                    ],
                }
            )

    if len(recs) < 10:
        mirrors = snapshot.get("arbitrage", {}).get("top_mirrors", [])
        for m in mirrors[:2]:
            leader = m.get("Leader") or m.get("leader")
            follower = m.get("Follower") or m.get("follower")
            corr = m.get("Correlation") or m.get("correlation", 0)
            if follower:
                recs.append(
                    {
                        "ticker": follower,
                        "action": "WATCH",
                        "confidence": round(float(corr or 0) * 100, 1) if corr else 40.0,
                        "risk": "MEDIUM",
                        "rationale": f"Lagged correlation with {leader} (r={corr:.2f}). Follower may replicate leader's move.",
                        "entry_zone": "On confirmation of leader's breakout",
                        "stop_loss": "Per individual chart structure",
                        "take_profit": "Match leader's recent % move",
                        "horizon": "1-3d",
                        "source": "Arbitrage Mirror",
                        "position_risk_pct": round(max_risk_per_trade_pct * 0.6, 2),
                        "rr_ratio": "N/A",
                        "validation_checks": [
                            "Leader move must remain intact.",
                            "Correlation should stay stable intraday.",
                        ],
                    }
                )

    if prefer_no_trade:
        for rec in recs:
            if rec.get("action") in {"BUY", "SELL"}:
                rec["action"] = "WATCH"
                rec["risk"] = "HIGH"
                rec["rationale"] = (
                    f"{rec.get('rationale', '')} "
                    "Execution profile is CAPITAL_PRESERVATION; directional entry downgraded to WATCH."
                ).strip()
        recs.insert(
            0,
            {
                "ticker": "CASH",
                "action": "HOLD",
                "confidence": round(float(confidence), 1),
                "risk": "LOW",
                "rationale": "Low-edge market state. Preserve capital and wait for stronger confluence.",
                "entry_zone": "N/A",
                "stop_loss": "N/A",
                "take_profit": "N/A",
                "horizon": "1-3d",
                "source": "Execution Profile",
                "position_risk_pct": 0.0,
                "rr_ratio": "N/A",
                "validation_checks": [
                    "Composite edge is weak.",
                    "No-trade bias is active.",
                ],
            },
        )
    elif direction_label == "NEUTRAL" and abs(int(composite_score)) <= 2:
        for rec in recs:
            if rec.get("action") in {"BUY", "SELL"} and float(rec.get("confidence", 0)) < 75:
                rec["action"] = "WATCH"

    return recs


def _build_promotion_context(calibration_context: dict[str, Any]) -> dict[str, Any]:
    market_segments = dict(calibration_context.get("market_segments") or {})
    if not market_segments:
        return {}

    promotion_segments: dict[str, Any] = {}
    for segment, segment_summary in market_segments.items():
        previous_profile = (
            segment_summary.get("previous_active_profile")
            or segment_summary.get("rollback_profile")
        )
        new_profile = (
            segment_summary.get("new_active_profile")
            or segment_summary.get("active_enforcement_profile")
        )
        promotion_segments[str(segment)] = {
            "previous_active_profile": previous_profile,
            "new_active_profile": new_profile,
            "rollback_profile": segment_summary.get("rollback_profile"),
            "promotion_scope": segment_summary.get("promotion_scope"),
            "promotion_rationale": segment_summary.get("promotion_rationale"),
            "promotion_evidence": segment_summary.get("promotion_evidence"),
        }

    return {"market_segments": promotion_segments}
