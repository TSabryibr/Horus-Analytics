from core.enforcement_gates import (
    ENFORCEMENT_METADATA_FIELDS,
    build_enforcement_contract,
    build_enforcement_defaults,
    build_enforcement_diagnostics,
    summarize_enforcement_diagnostics,
)
from core.trap_risk import (
    TRAP_RISK_METADATA_FIELDS,
    build_trap_risk_defaults,
)
from core.whale_flow import (
    WHALE_FLOW_METADATA_FIELDS,
    build_whale_flow_defaults,
    build_whale_trap_contract,
    build_whale_trap_diagnostics,
    summarize_whale_trap_diagnostics,
)


def test_whale_flow_defaults_contract():
    defaults = build_whale_flow_defaults()

    assert WHALE_FLOW_METADATA_FIELDS == (
        "whale_signal",
        "whale_strength",
        "whale_alignment",
        "whale_reason",
    )
    assert defaults == {
        "whale_signal": "UNKNOWN",
        "whale_strength": None,
        "whale_alignment": "NEUTRAL",
        "whale_reason": "no_whale_signal",
    }


def test_trap_risk_defaults_contract():
    defaults = build_trap_risk_defaults()

    assert TRAP_RISK_METADATA_FIELDS == (
        "trap_risk_score",
        "trap_risk_band",
        "trap_risk_reason",
        "trap_risk_components",
    )
    assert defaults == {
        "trap_risk_score": None,
        "trap_risk_band": "UNKNOWN",
        "trap_risk_reason": "not_computed",
        "trap_risk_components": None,
    }


def test_enforcement_defaults_contract():
    defaults = build_enforcement_defaults()

    assert ENFORCEMENT_METADATA_FIELDS == (
        "enforcement_state",
        "enforcement_visibility",
        "enforcement_reason",
        "enforcement_notes",
        "enforcement_profile",
    )
    assert defaults == {
        "enforcement_state": "ALLOW",
        "enforcement_visibility": "VISIBLE",
        "enforcement_reason": "not_enforced",
        "enforcement_notes": None,
        "enforcement_profile": "DEFAULT",
    }


def test_enforcement_diagnostics_contract_defaults():
    diagnostics = build_enforcement_diagnostics()

    assert diagnostics == {
        "rollout_mode": "visible_but_blocked",
        "allow_count": 0,
        "watch_only_count": 0,
        "block_count": 0,
        "counts_by_reason": {},
        "counts_by_profile": {},
        "counts_by_market_segment": {
            "EGX30": {"allow_count": 0, "watch_only_count": 0, "block_count": 0},
            "EGX70": {"allow_count": 0, "watch_only_count": 0, "block_count": 0},
        },
    }


def test_whale_trap_shadow_diagnostics_contract_defaults():
    diagnostics = build_whale_trap_diagnostics()

    assert diagnostics == {
        "rollout_mode": "shadow",
        "supportive_whale_alignments": 0,
        "whale_conflicts": 0,
        "high_trap_risk_count": 0,
        "severe_trap_risk_count": 0,
        "top_trap_risk_reasons": {},
        "threshold_analysis": {
            "rollout_mode": "shadow",
            "would_review_count": 0,
            "would_block_count": 0,
            "top_block_reasons": {},
        },
    }


def test_whale_trap_metadata_contract_shape():
    contract = build_whale_trap_contract()

    assert contract["metadata_fields"] == [
        *WHALE_FLOW_METADATA_FIELDS,
        *TRAP_RISK_METADATA_FIELDS,
    ]
    assert contract["defaults"] == {
        **build_whale_flow_defaults(),
        **build_trap_risk_defaults(),
    }
    assert contract["diagnostics"] == build_whale_trap_diagnostics()


def test_enforcement_metadata_contract_shape():
    contract = build_enforcement_contract()

    assert contract["metadata_fields"] == [*ENFORCEMENT_METADATA_FIELDS]
    assert contract["defaults"] == build_enforcement_defaults()
    assert contract["diagnostics"] == build_enforcement_diagnostics()


def test_summarize_whale_trap_diagnostics_rolls_up_shadow_counts():
    diagnostics = summarize_whale_trap_diagnostics(
        [
            {
                "whale_alignment": "SUPPORTIVE",
                "trap_risk_band": "LOW",
                "trap_risk_reason": "low_risk_alignment",
            },
            {
                "Whale_Alignment": "CONFLICT",
                "Trap_Risk_Band": "SEVERE",
                "Trap_Risk_Reason": "distribution_against_breakout",
            },
            {
                "Whale_Alignment": "CONFLICT",
                "Trap_Risk_Band": "HIGH",
                "Trap_Risk_Reason": "illiquid_breakout",
            },
        ]
    )

    assert diagnostics == {
        "rollout_mode": "shadow",
        "supportive_whale_alignments": 1,
        "whale_conflicts": 2,
        "high_trap_risk_count": 1,
        "severe_trap_risk_count": 1,
        "top_trap_risk_reasons": {
            "distribution_against_breakout": 1,
            "illiquid_breakout": 1,
        },
        "threshold_analysis": {
            "rollout_mode": "shadow",
            "would_review_count": 2,
            "would_block_count": 2,
            "top_block_reasons": {
                "distribution_against_breakout": 1,
                "illiquid_breakout": 1,
            },
        },
    }


def test_summarize_enforcement_diagnostics_rolls_up_state_reason_and_profile_counts():
    diagnostics = summarize_enforcement_diagnostics(
        [
            {
                "enforcement_state": "ALLOW",
                "enforcement_reason": "not_enforced",
                "enforcement_profile": "EGX30_BALANCED",
                "route_profile": "EGX30",
            },
            {
                "Enforcement_State": "WATCH_ONLY",
                "Enforcement_Reason": "distribution_conflict",
                "Enforcement_Profile": "EGX70_STRICT",
                "Route_Profile": "EGX70",
            },
            {
                "enforcement_state": "BLOCK_EXECUTION",
                "enforcement_reason": "severe_trap_risk",
                "enforcement_profile": "EGX70_STRICT",
                "market_segment": "EGX70",
            },
        ]
    )

    assert diagnostics == {
        "rollout_mode": "visible_but_blocked",
        "allow_count": 1,
        "watch_only_count": 1,
        "block_count": 1,
        "counts_by_reason": {
            "distribution_conflict": 1,
            "severe_trap_risk": 1,
        },
        "counts_by_profile": {
            "EGX30_BALANCED": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
            "EGX70_STRICT": {"allow_count": 0, "watch_only_count": 1, "block_count": 1},
        },
        "counts_by_market_segment": {
            "EGX30": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
            "EGX70": {"allow_count": 0, "watch_only_count": 1, "block_count": 1},
        },
    }
