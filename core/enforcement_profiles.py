from __future__ import annotations
"""
Shared threshold profile configuration for whale/trap enforcement.

TC-P1 extracts active and candidate profile definitions into explicit,
named configuration so later calibration work can compare profiles without
hard-coding threshold behavior in every consumer.
"""


from copy import deepcopy
from typing import Any


ACTIVE_ENFORCEMENT_PROFILES = {
    "DEFAULT": "DEFAULT",
    "EGX30": "EGX30_GUARDED",
    "EGX70": "EGX70_HARDENED",
}

CALIBRATION_CANDIDATE_PROFILES = {
    "DEFAULT": ["DEFAULT_COMPARE_ONLY"],
    "EGX30": ["EGX30_BALANCED"],
    "EGX70": ["EGX70_STRICT"],
}

PROMOTION_DECISION_DEFAULTS = {
    "GLOBAL": {
        "promotion_scope": "GLOBAL",
        "promotion_rationale": "baseline_unchanged",
        "promotion_evidence": {},
    },
    "EGX30": {
        "promotion_scope": "EGX30",
        "promotion_rationale": "baseline_unchanged",
        "promotion_evidence": {},
    },
    "EGX70": {
        "promotion_scope": "EGX70",
        "promotion_rationale": "baseline_unchanged",
        "promotion_evidence": {},
    },
}

PROMOTION_DECISIONS = {
    "EGX30": {
        "previous_active_profile": "EGX30_BALANCED",
        "new_active_profile": "EGX30_GUARDED",
        "promotion_scope": "EGX30",
        "promotion_rationale": "candidate_profile_promoted",
        "promotion_evidence": {
            "source": "threshold_calibration_review",
        },
        "rollback_profile": "EGX30_BALANCED",
    },
    "EGX70": {
        "previous_active_profile": "EGX70_STRICT",
        "new_active_profile": "EGX70_HARDENED",
        "promotion_scope": "EGX70",
        "promotion_rationale": "candidate_profile_promoted",
        "promotion_evidence": {
            "source": "threshold_calibration_review",
        },
        "rollback_profile": "EGX70_STRICT",
    },
}

ENFORCEMENT_PROFILES = {
    "DEFAULT": {
        "name": "DEFAULT",
        "market_segment": "DEFAULT",
        "block_on_trap_bands": ("SEVERE",),
        "block_on_conflict_trap_bands": ("HIGH",),
        "profile_conflict_block_bands": (),
        "watch_on_trap_bands": ("HIGH",),
        "watch_on_alignments": ("CONFLICT",),
    },
    "EGX30_BALANCED": {
        "name": "EGX30_BALANCED",
        "market_segment": "EGX30",
        "block_on_trap_bands": ("SEVERE",),
        "block_on_conflict_trap_bands": ("HIGH",),
        "profile_conflict_block_bands": (),
        "watch_on_trap_bands": ("HIGH",),
        "watch_on_alignments": ("CONFLICT",),
    },
    "EGX70_STRICT": {
        "name": "EGX70_STRICT",
        "market_segment": "EGX70",
        "block_on_trap_bands": ("SEVERE",),
        "block_on_conflict_trap_bands": ("HIGH",),
        "profile_conflict_block_bands": ("MEDIUM",),
        "watch_on_trap_bands": ("HIGH",),
        "watch_on_alignments": ("CONFLICT",),
    },
    "DEFAULT_COMPARE_ONLY": {
        "name": "DEFAULT_COMPARE_ONLY",
        "market_segment": "DEFAULT",
        "block_on_trap_bands": ("SEVERE",),
        "block_on_conflict_trap_bands": ("HIGH",),
        "profile_conflict_block_bands": (),
        "watch_on_trap_bands": ("MEDIUM", "HIGH"),
        "watch_on_alignments": ("CONFLICT",),
    },
    "EGX30_GUARDED": {
        "name": "EGX30_GUARDED",
        "market_segment": "EGX30",
        "block_on_trap_bands": ("SEVERE",),
        "block_on_conflict_trap_bands": ("HIGH",),
        "profile_conflict_block_bands": ("MEDIUM",),
        "watch_on_trap_bands": ("MEDIUM", "HIGH"),
        "watch_on_alignments": ("CONFLICT",),
    },
    "EGX70_HARDENED": {
        "name": "EGX70_HARDENED",
        "market_segment": "EGX70",
        "block_on_trap_bands": ("HIGH", "SEVERE"),
        "block_on_conflict_trap_bands": ("MEDIUM", "HIGH"),
        "profile_conflict_block_bands": ("MEDIUM",),
        "watch_on_trap_bands": ("MEDIUM", "HIGH"),
        "watch_on_alignments": ("CONFLICT",),
    },
}


def get_enforcement_profile(profile_name: str | None) -> dict[str, Any]:
    normalized_name = str(profile_name or "DEFAULT").strip().upper() or "DEFAULT"
    profile = ENFORCEMENT_PROFILES.get(normalized_name, ENFORCEMENT_PROFILES["DEFAULT"])
    return deepcopy(profile)


def resolve_active_enforcement_profile(
    route_profile: Any = None,
    market_segment: Any = None,
) -> str:
    segment = resolve_market_segment(route_profile=route_profile, market_segment=market_segment)
    return ACTIVE_ENFORCEMENT_PROFILES.get(segment or "DEFAULT", "DEFAULT")


def list_candidate_calibration_profiles(
    route_profile: Any = None,
    market_segment: Any = None,
) -> list[str]:
    segment = resolve_market_segment(route_profile=route_profile, market_segment=market_segment)
    return list(CALIBRATION_CANDIDATE_PROFILES.get(segment or "DEFAULT", []))


def get_promotion_decision(
    route_profile: Any = None,
    market_segment: Any = None,
) -> dict[str, Any]:
    segment = resolve_market_segment(route_profile=route_profile, market_segment=market_segment)
    promoted_decision = PROMOTION_DECISIONS.get(segment or "")
    if promoted_decision:
        return deepcopy(promoted_decision)

    active_profile = resolve_active_enforcement_profile(
        route_profile=route_profile,
        market_segment=market_segment,
    )
    decision_defaults = deepcopy(
        PROMOTION_DECISION_DEFAULTS.get(segment or "GLOBAL", PROMOTION_DECISION_DEFAULTS["GLOBAL"])
    )
    decision_defaults["previous_active_profile"] = active_profile
    decision_defaults["new_active_profile"] = active_profile
    decision_defaults["rollback_profile"] = active_profile
    return decision_defaults


def resolve_rollback_profile(
    route_profile: Any = None,
    market_segment: Any = None,
) -> str:
    decision = get_promotion_decision(
        route_profile=route_profile,
        market_segment=market_segment,
    )
    return str(decision.get("rollback_profile") or "DEFAULT")


def resolve_market_segment(
    route_profile: Any = None,
    market_segment: Any = None,
) -> str | None:
    for value in (market_segment, route_profile):
        normalized = str(value or "").strip().upper()
        if not normalized:
            continue
        if "70" in normalized:
            return "EGX70"
        if "30" in normalized:
            return "EGX30"
        return normalized
    return None
