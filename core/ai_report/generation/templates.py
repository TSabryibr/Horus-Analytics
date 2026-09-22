from __future__ import annotations

from typing import Any

from ..boundary import (
    _RULE_ENGINE_THINKING_CONTRACT,
    rule_engine_instruction_text,
)

_RULE_ENGINE_REASONING_PROFILE = "gpt-5.3-codex"


def _get_rule_engine_instruction_text() -> str:
    import sys
    mod = sys.modules.get("core.ai_report.generation")
    if mod and hasattr(mod, "rule_engine_instruction_text"):
        return mod.rule_engine_instruction_text()
    return rule_engine_instruction_text()


def _build_llm_prompts(snapshot: dict[str, Any], fallback_report: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    as_of = snapshot.get("as_of", "unknown")
    freshness = snapshot.get("data_freshness", {})
    freshness_label = str(freshness.get("label", "N/A")).upper()
    exec_profile = fallback_report.get("execution_profile", {})
    exec_mode = exec_profile.get("mode", "BALANCED")
    exec_selectivity = exec_profile.get("selectivity", "MEDIUM")
    composite_score = fallback_report.get("market_direction", {}).get("composite_score", 0)
    bias_desc = fallback_report.get("market_direction", {}).get("bias_description", "UNKNOWN")

    system_prompt = (
        "You are GPT-5.3-codex, an elite institutional-grade multi-asset market analyst "
        "specializing in Egyptian Exchange (EGX) equities, sector rotation, and tactical positioning. "
        "You synthesize 9 independent data modules into a unified daily market intelligence report.\n\n"
        "ANALYTICAL METHODOLOGY - 9-Module Cross-Correlation Framework:\n"
        "You must analyze and cross-reference ALL of the following modules in priority order:\n"
        "  1. Oracle Macro (weight: HIGH) - Primary trend indicator. Macro health signal and breadth correlation.\n"
        "  2. Strategy Engine (weight: HIGH) - Algorithmic regime detection with regime score and volatility.\n"
        "  3. Whale Flow (weight: HIGH) - Smart money accumulation/distribution patterns.\n"
        "  4. Scanner Signals (weight: MEDIUM) - Active buy/sell recommendations with scores and confidence.\n"
        "  5. News Sentiment (weight: MEDIUM) - Headline sentiment score, regime, and top stories.\n"
        "  6. Sector Rotation (weight: MEDIUM) - Leading vs lagging sectors for breadth assessment.\n"
        "  7. Trap Analysis (weight: MODERATE) - Bear traps (bullish reversal) and bull traps (distribution risk).\n"
        "  8. Arbitrage Mirrors (weight: LOW) - Lagged correlation pairs for opportunistic entries.\n"
        "  9. Portfolio Health (weight: CONTEXT) - Current exposure, P&L, and concentration risk.\n\n"
        "REASONING CONTRACT (apply strictly):\n"
        f"{_get_rule_engine_instruction_text()}\n\n"
        "OUTPUT RULES:\n"
        "- Return valid JSON only. No markdown, no code fences, no commentary outside the JSON.\n"
        "- Every recommendation must have concrete entry_zone, stop_loss, and take_profit derived from snapshot data.\n"
        "- Risk/reward ratio must be >= 1.8:1 for BUY/SELL actions (or explicitly state why an exception is made).\n"
        "- Headline must be punchy and informative: include bias direction, composite score, and signal count.\n"
        "- Summary lines should be data-dense one-liners, not paragraphs.\n"
        "- Cross-tab findings must cite which modules agree/disagree and quantify the confluence.\n"
        "- Risk warnings should be ordered by severity (portfolio-specific first, then market-level)."
    )

    user_prompt = {
        "task": (
            "Create a comprehensive daily market intelligence report. "
            "Synthesize ALL 9 data modules from the snapshot into a cohesive, "
            "actionable analysis following the GPT-5.3-codex reasoning contract."
        ),
        "context": {
            "report_timestamp": as_of,
            "data_freshness": freshness_label,
            "current_execution_mode": exec_mode,
            "current_selectivity": exec_selectivity,
            "composite_direction_score": composite_score,
            "bias_description": bias_desc,
        },
        "analytical_instructions": [
            "Step 1 - REGIME ASSESSMENT: Determine market regime by cross-referencing Oracle macro signal, Strategy engine regime, and sector breadth. State the regime clearly.",
            "Step 2 - SMART MONEY FLOW: Analyze whale accumulation vs distribution ratios. Identify top tickers under institutional flow. Critically, evaluate 'Shadow Flow' and 'Enforcement Context' (if present) to quantify high trap-risk or whale-conflicted candidates.",
            "Step 3 - SENTIMENT & TRAP SYNTHESIS: Cross-reference Trap Analysis with News Sentiment and Whale Flow. If Retail Sentiment is greedy (>80) and Bull Traps are high, explicitly warn of a possible 'Distribution Phase', where smart money sells into retail liquidity regardless of total whale counts.",
            "Step 4 - SOVEREIGN HEDGE: If `sovereign_warnings` are present, prioritize them. These represent high-conviction traps where social sentiment and institutional volume are in conflict.",
            "Step 5 - SQUEEZE TARGETING: Check for volatility squeezes. DO NOT just list them. Cross-reference squeeze tickers with Whale Flow or Sector Leaders to infer the probable breakout direction. Give the trader specific directional context.",
            "Step 6 - SIGNAL QUALITY AUDIT: Review scanner buy/sell counts, average score, and average confidence. Filter for high-conviction setups (score >= 7, confidence >= 75%). Discard marginal signals.",
            "Step 7 - CONFLUENCE SCORING: Count how many modules align bullish vs bearish. Apply confidence calibration: 1-2 modules = low conviction (35-55%), 3-4 = medium (55-75%), 5+ = high (75-95%).",
            "Step 8 - RISK-FIRST ANALYSIS: List all risk warnings BEFORE opportunities. Include portfolio-specific risks (concentration, drawdown) and market-level risks (volatility, stale data). Include warnings for blocked/watched candidates from 'Enforcement Context'.",
            "Step 9 - RECOMMENDATIONS: Generate actionable recommendations adapted to the current execution profile. "
            f"Current mode is {exec_mode} with {exec_selectivity} selectivity. "
            "Each recommendation MUST include: ticker, action, confidence, risk level, entry_zone, stop_loss, take_profit, rationale citing specific data sources, and time horizon.",
            "Step 10 - CHECKLIST: Provide a prioritized next-action checklist for the trader. Include regime-specific actions, risk cap reminders, and data verification steps.",
        ],
        "recommendation_quality_rules": [
            "Entry zones must be specific price ranges, not vague directions.",
            "Stop-loss must reflect actual risk tolerance from the execution profile "
            f"(max {exec_profile.get('max_risk_per_trade_pct', 1.0)}% risk per trade).",
            "Take-profit must yield >= 1.8:1 risk/reward ratio vs stop-loss.",
            "Confidence must be calibrated to module confluence, not inflated.",
            "WATCH is the appropriate action when conviction is below 60% or data is insufficient.",
            "Never recommend a ticker not present in the snapshot data (signals, whales, squeezes, or arbitrage).",
            "Maximum 8 recommendations. Quality over quantity.",
        ],
        "risk_warnings_rules": [
            "DEDUPLICATE: Combine related risks (e.g., portfolio P&L and string concentration) into a single, high-impact warning.",
            f"OBEY EXECUTION MODE: Current execution mode is {exec_mode}. Your risk advice MUST reflect this. (e.g., In CAPITAL_PRESERVATION, never advise widening stops for volatility—mandate tight stops or no trade).",
            "BE EXPLICIT: Avoid vague maxims like 'Consider reducing'. Give concrete directives (e.g., 'Mandatory risk reduction: Sell ACAP into strength').",
            "NO HALLUCINATIONS: Do not miscount 'missing modules'. If you cite Whale or Squeeze data, that module is NOT missing. accurately state which modules are STALE.",
        ],
        "summary_style_guide": [
            "Each summary line should be a data-dense one-liner starting with a category tag (e.g., MARKET STRUCTURE:, WHALE FLOW:).",
            "Use concrete numbers, not vague qualifiers. Say '4 accumulating vs 1 distributing' not 'mostly accumulating'.",
            "Include the execution mode and key risk caps in the summary.",
            "If data is stale, note it prominently in the summary.",
        ],
        "reasoning_profile": _RULE_ENGINE_REASONING_PROFILE,
        "reasoning_contract": _RULE_ENGINE_THINKING_CONTRACT,
        "required_schema": {
            "headline": "string - punchy, includes bias + score + signal count",
            "market_direction": {
                "label": "BULLISH|BEARISH|NEUTRAL",
                "confidence": "number 0-100 calibrated to module confluence",
                "time_horizon": "string e.g. 'Next trading day' or '1-3 days'",
                "reasoning": ["string - each citing specific data module evidence"],
            },
            "daily_report": {
                "summary": ["string - data-dense one-liners with category tags"],
                "cross_tab_findings": ["string - cross-module confluence observations"],
            },
            "recommendations": [
                {
                    "ticker": "string - must exist in snapshot",
                    "action": "BUY|SELL|HOLD|WATCH",
                    "confidence": "number 0-100",
                    "risk": "LOW|MEDIUM|HIGH",
                    "rationale": "string - cite specific data sources",
                    "entry_zone": "string - specific price range",
                    "stop_loss": "string - price level with rationale",
                    "take_profit": "string - price level, >=1.8:1 R:R",
                    "horizon": "string - e.g. '1-5d' or 'intraday'",
                }
            ],
            "risk_warnings": ["string - severity-ordered, portfolio risks first"],
            "next_checklist": ["string - prioritized trader action items"],
        },
        "snapshot": snapshot,
        "rule_based_reference": fallback_report,
    }
    return system_prompt, user_prompt
