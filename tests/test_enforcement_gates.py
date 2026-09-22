from core.enforcement_gates import assess_enforcement_gate
from core.enforcement_profiles import (
    get_promotion_decision,
    get_enforcement_profile,
    list_candidate_calibration_profiles,
    resolve_rollback_profile,
    resolve_active_enforcement_profile,
)


def test_assess_enforcement_gate_blocks_severe_trap_risk():
    result = assess_enforcement_gate(
        trap_risk_band="SEVERE",
        whale_alignment="NEUTRAL",
        route_profile="EGX30_TREND_PROFILE",
    )

    assert result["enforcement_state"] == "BLOCK_EXECUTION"
    assert result["enforcement_visibility"] == "VISIBLE"
    assert result["enforcement_reason"] == "severe_trap_risk"
    assert result["enforcement_profile"] == "EGX30_GUARDED"
    assert "severe trap risk" in result["enforcement_notes"].lower()


def test_assess_enforcement_gate_blocks_high_risk_conflict():
    result = assess_enforcement_gate(
        trap_risk_band="HIGH",
        whale_alignment="CONFLICT",
        route_profile="EGX30_TREND_PROFILE",
    )

    assert result["enforcement_state"] == "BLOCK_EXECUTION"
    assert result["enforcement_reason"] == "stacked_shadow_threshold"
    assert result["enforcement_profile"] == "EGX30_GUARDED"
    assert "whale conflict" in result["enforcement_notes"].lower()


def test_assess_enforcement_gate_marks_high_risk_as_watch_only():
    result = assess_enforcement_gate(
        trap_risk_band="HIGH",
        whale_alignment="SUPPORTIVE",
        route_profile="EGX30_TREND_PROFILE",
    )

    assert result["enforcement_state"] == "WATCH_ONLY"
    assert result["enforcement_reason"] == "high_trap_risk"
    assert result["enforcement_profile"] == "EGX30_GUARDED"


def test_assess_enforcement_gate_allows_low_risk_supportive_setup():
    result = assess_enforcement_gate(
        trap_risk_band="LOW",
        whale_alignment="SUPPORTIVE",
        route_profile="EGX30_TREND_PROFILE",
    )

    assert result == {
        "enforcement_state": "ALLOW",
        "enforcement_visibility": "VISIBLE",
        "enforcement_reason": "not_enforced",
        "enforcement_notes": "No whale/trap enforcement threshold breached.",
        "enforcement_profile": "EGX30_GUARDED",
    }


def test_assess_enforcement_gate_uses_promoted_segment_specific_thresholds():
    egx30 = assess_enforcement_gate(
        trap_risk_band="MEDIUM",
        whale_alignment="CONFLICT",
        route_profile="EGX30_TREND_PROFILE",
    )
    egx70 = assess_enforcement_gate(
        trap_risk_band="MEDIUM",
        whale_alignment="CONFLICT",
        route_profile="EGX70_TACTICAL_PROFILE",
    )

    assert egx30["enforcement_state"] == "BLOCK_EXECUTION"
    assert egx30["enforcement_reason"] == "profile_threshold_breach"
    assert egx30["enforcement_profile"] == "EGX30_GUARDED"

    assert egx70["enforcement_state"] == "BLOCK_EXECUTION"
    assert egx70["enforcement_reason"] == "stacked_shadow_threshold"
    assert egx70["enforcement_profile"] == "EGX70_HARDENED"
    assert "blocked for execution" in egx70["enforcement_notes"].lower()


def test_resolve_active_enforcement_profile_uses_promoted_segment_specific_baselines():
    assert resolve_active_enforcement_profile(route_profile="EGX30_TREND_PROFILE") == "EGX30_GUARDED"
    assert resolve_active_enforcement_profile(route_profile="EGX70_TACTICAL_PROFILE") == "EGX70_HARDENED"
    assert resolve_active_enforcement_profile(route_profile="UNKNOWN_PROFILE") == "DEFAULT"


def test_candidate_calibration_profiles_remain_compare_only_after_promotion():
    egx30_active = resolve_active_enforcement_profile(route_profile="EGX30_TREND_PROFILE")
    egx70_active = resolve_active_enforcement_profile(route_profile="EGX70_TACTICAL_PROFILE")
    egx30_candidates = list_candidate_calibration_profiles(route_profile="EGX30_TREND_PROFILE")
    egx70_candidates = list_candidate_calibration_profiles(route_profile="EGX70_TACTICAL_PROFILE")

    assert egx30_candidates
    assert egx70_candidates
    assert egx30_active not in egx30_candidates
    assert egx70_active not in egx70_candidates
    assert egx30_candidates == ["EGX30_BALANCED"]
    assert egx70_candidates == ["EGX70_STRICT"]


def test_get_enforcement_profile_returns_explicit_threshold_configuration():
    profile = get_enforcement_profile("EGX70_STRICT")

    assert profile["name"] == "EGX70_STRICT"
    assert "SEVERE" in profile["block_on_trap_bands"]
    assert "HIGH" in profile["block_on_conflict_trap_bands"]
    assert "MEDIUM" in profile["profile_conflict_block_bands"]


def test_promotion_decision_tracks_segment_promotions_and_rollback_targets():
    decision = get_promotion_decision(route_profile="EGX30_TREND_PROFILE")

    assert decision == {
        "previous_active_profile": "EGX30_BALANCED",
        "new_active_profile": "EGX30_GUARDED",
        "promotion_scope": "EGX30",
        "promotion_rationale": "candidate_profile_promoted",
        "promotion_evidence": {"source": "threshold_calibration_review"},
        "rollback_profile": "EGX30_BALANCED",
    }


def test_promotion_decision_is_segment_aware_and_preserves_default_baseline():
    egx70_decision = get_promotion_decision(route_profile="EGX70_TACTICAL_PROFILE")
    default_decision = get_promotion_decision(route_profile="UNKNOWN_PROFILE")

    assert egx70_decision["previous_active_profile"] == "EGX70_STRICT"
    assert egx70_decision["new_active_profile"] == "EGX70_HARDENED"
    assert egx70_decision["rollback_profile"] == "EGX70_STRICT"
    assert egx70_decision["promotion_scope"] == "EGX70"

    assert default_decision["new_active_profile"] == "DEFAULT"
    assert default_decision["rollback_profile"] == "DEFAULT"
    assert default_decision["promotion_scope"] == "GLOBAL"


def test_resolve_rollback_profile_uses_promotion_decision_contract():
    assert resolve_rollback_profile(route_profile="EGX30_TREND_PROFILE") == "EGX30_BALANCED"
    assert resolve_rollback_profile(route_profile="EGX70_TACTICAL_PROFILE") == "EGX70_STRICT"
