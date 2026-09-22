from core.trap_risk import assess_trap_risk
from core.whale_flow import evaluate_whale_flow


def test_evaluate_whale_flow_maps_accumulation_to_supportive_long_alignment():
    metadata = evaluate_whale_flow(
        ticker="COMI",
        whale_candidates=[
            {"Ticker": "COMI", "Signal": "ACCUMULATION", "Strength": 8.0},
            {"Ticker": "FWRY", "Signal": "DISTRIBUTION", "Strength": 4.0},
        ],
        candidate_side="BUY",
    )

    assert metadata["whale_signal"] == "ACCUMULATION"
    assert metadata["whale_alignment"] == "SUPPORTIVE"
    assert metadata["whale_reason"] == "accumulation_support"
    assert 0.0 <= metadata["whale_strength"] <= 1.0


def test_evaluate_whale_flow_maps_distribution_to_conflict_for_longs():
    metadata = evaluate_whale_flow(
        ticker="COMI",
        whale_candidates=[
            {"Ticker": "COMI", "Signal": "DISTRIBUTION", "Strength": 6.0},
            {"Ticker": "HRHO", "Signal": "ACCUMULATION", "Strength": 10.0},
        ],
        candidate_side="BUY",
    )

    assert metadata["whale_signal"] == "DISTRIBUTION"
    assert metadata["whale_alignment"] == "CONFLICT"
    assert metadata["whale_reason"] == "distribution_conflict"


def test_evaluate_whale_flow_returns_neutral_defaults_when_data_missing():
    metadata = evaluate_whale_flow(
        ticker="COMI",
        whale_candidates=[],
        candidate_side="BUY",
    )

    assert metadata == {
        "whale_signal": "UNKNOWN",
        "whale_strength": None,
        "whale_alignment": "NEUTRAL",
        "whale_reason": "no_whale_signal",
    }


def test_assess_trap_risk_scores_low_risk_when_supportive_conditions_align():
    metadata = assess_trap_risk(
        ticker="COMI",
        liquidity_tier="LIQUID",
        sector_rs_14=0.18,
        vsa_valid=True,
        whale_alignment="SUPPORTIVE",
        bull_traps=[],
        bear_traps=[],
    )

    assert metadata["trap_risk_band"] == "LOW"
    assert metadata["trap_risk_reason"] == "low_risk_alignment"
    assert metadata["trap_risk_score"] <= 24


def test_assess_trap_risk_increases_on_whale_conflict():
    aligned = assess_trap_risk(
        ticker="COMI",
        liquidity_tier="LIQUID",
        sector_rs_14=0.12,
        vsa_valid=True,
        whale_alignment="SUPPORTIVE",
        bull_traps=[],
        bear_traps=[],
    )
    conflicted = assess_trap_risk(
        ticker="COMI",
        liquidity_tier="LIQUID",
        sector_rs_14=0.12,
        vsa_valid=True,
        whale_alignment="CONFLICT",
        bull_traps=[],
        bear_traps=[],
    )

    assert conflicted["trap_risk_score"] > aligned["trap_risk_score"]
    assert conflicted["trap_risk_reason"] == "distribution_against_breakout"


def test_assess_trap_risk_penalizes_illiquid_breakouts():
    metadata = assess_trap_risk(
        ticker="COMI",
        liquidity_tier="ILLIQUID",
        sector_rs_14=0.04,
        vsa_valid=True,
        whale_alignment="NEUTRAL",
        bull_traps=[],
        bear_traps=[],
    )

    assert metadata["trap_risk_band"] in {"HIGH", "SEVERE"}
    assert metadata["trap_risk_reason"] == "illiquid_breakout"


def test_assess_trap_risk_reaches_severe_band_when_multiple_risks_stack():
    metadata = assess_trap_risk(
        ticker="COMI",
        liquidity_tier="ILLIQUID",
        sector_rs_14=-0.05,
        vsa_valid=False,
        whale_alignment="CONFLICT",
        bull_traps=[{"Ticker": "COMI", "Fakeout_Depth_%": 3.2}],
        bear_traps=[],
    )

    assert metadata["trap_risk_band"] == "SEVERE"
    assert metadata["trap_risk_score"] >= 75
    assert metadata["trap_risk_components"]["whale_conflict_risk"] > 0
