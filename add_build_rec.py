from core.settings import settings
import sys

filepath = r'c:\Users\TSabr\Horus\Horus-Analytics-II\core\signals\desk.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add GlobalSettings to database import
if 'GlobalSettings' not in content:
    content = content.replace('SignalDelivery', 'SignalDelivery, GlobalSettings')

# Add exclusions imports
if 'from exclusions' not in content:
    content = content.replace('from database', 'from core.exclusions import normalize_ticker, is_excluded_ticker\nfrom database')

code = '''
def build_recommendation(signal: dict, run: SignalRun, regime: str):
    ticker = normalize_ticker(signal.get("Ticker"))
    if not ticker or is_excluded_ticker(ticker):
        return None

    score = int(signal.get("Score", 0))
    raw_confidence = signal.get("Confidence", signal.get("confidence", float(score) * 10.0))
    confidence = max(0.0, min(100.0, float(raw_confidence)))
    min_score = float(getattr(settings, "MIN_SIGNAL_SCORE", 0.0))
    min_confidence = float(getattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0))
    if float(score) < min_score:
        return None
    if confidence < min_confidence:
        return None
    entry = float(signal.get("Entry_Price", 0))
    sl = float(signal.get("Stop_Loss", 0))
    tp = float(signal.get("Target_Price", 0))
    side = "BUY" if str(signal.get("Signal_Type", "BUY")).upper() == "BUY" else str(signal.get("Signal_Type")).upper()
    raw_tp2 = signal.get("Target_Price_2")
    try:
        tp2 = float(raw_tp2) if raw_tp2 is not None else _compute_tp2(side, tp)
    except (TypeError, ValueError):
        tp2 = _compute_tp2(side, tp)
    if tp2 <= 0:
        tp2 = _compute_tp2(side, tp)
    rationale = {
        "score": score,
        "rsi": signal.get("RSI"),
        "volume_x": signal.get("Volume_x", signal.get("Volume_Spike")),
        "confirmation": signal.get("Confirmation"),
        "sector": signal.get("Sector"),
        "source_module": "SCANNER",
        "source": signal.get("Signal_Type"),
        "signal_side": side,
        "target_price_2": tp2,
        "whale_signal": signal.get("Whale_Signal"),
        "whale_strength": signal.get("Whale_Strength"),
        "whale_alignment": signal.get("Whale_Alignment"),
        "whale_reason": signal.get("Whale_Reason"),
        "trap_risk_score": signal.get("Trap_Risk_Score"),
        "trap_risk_band": signal.get("Trap_Risk_Band"),
        "trap_risk_reason": signal.get("Trap_Risk_Reason"),
        "enforcement_state": signal.get("Enforcement_State"),
        "enforcement_visibility": signal.get("Enforcement_Visibility"),
        "enforcement_reason": signal.get("Enforcement_Reason"),
        "enforcement_notes": signal.get("Enforcement_Notes"),
        "enforcement_profile": signal.get("Enforcement_Profile"),
        "strategy_profile_id": signal.get("Scanner_Profile_Id"),
        "strategy_profile_name": signal.get("Scanner_Profile_Name"),
        "strategy_profile_source_type": signal.get("Scanner_Profile_Source_Type"),
        "strategy_profile_market": signal.get("Scanner_Profile_Market"),
        "strategy_profile_timeframe": signal.get("Scanner_Profile_Timeframe"),
        "preview_mode": signal.get("Preview_Mode"),
        "preview_source": signal.get("Preview_Source"),
        "preview_close": signal.get("Preview_Close"),
        "preview_volume": signal.get("Preview_Volume"),
        "preview_date": str(signal.get("Preview_Date")) if signal.get("Preview_Date") is not None else None,
    }
    invalidation_rule = f"Invalidate if close below {sl:.4f}" if side == "BUY" else f"Invalidate if close above {sl:.4f}"
    horizon_days = 1 if run.scan_type in {"INTRADAY", "PRE_CLOSE"} else 5

    return SignalRecommendation(
        run=run,
        ticker=ticker,
        side=side,
        entry_price=entry,
        stop_loss=sl,
        target_price=tp,
        score=score,
        confidence=confidence,
        rationale_json=json.dumps(rationale),
        invalidation_rule=invalidation_rule,
        horizon_days=horizon_days,
        regime=regime,
        data_cutoff_at=TimeUtils.now(),
        state="ACTIVE",
    )
'''

content += '\n' + code + '\n'

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Added build_recommendation')
