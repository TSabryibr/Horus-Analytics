from __future__ import annotations
"""
Shared enforcement-gates metadata contract helpers.

EF-P1 defines the enforcement vocabulary, neutral defaults, and diagnostics
shape before any scanner or publishing consumer begins changing behavior.
"""


from copy import deepcopy
from typing import Any

from core.enforcement_profiles import (
    get_enforcement_profile,
    resolve_active_enforcement_profile,
    resolve_market_segment,
)


ENFORCEMENT_METADATA_FIELDS = (
    "enforcement_state",
    "enforcement_visibility",
    "enforcement_reason",
    "enforcement_notes",
    "enforcement_profile",
)

_ENFORCEMENT_STATES = ("ALLOW", "WATCH_ONLY", "BLOCK_EXECUTION")
_TRAP_RISK_BANDS = ("LOW", "MEDIUM", "HIGH", "SEVERE", "UNKNOWN")
_WHALE_ALIGNMENTS = ("SUPPORTIVE", "CONFLICT", "NEUTRAL")


def build_enforcement_defaults() -> dict[str, Any]:
    """Return visible-but-safe enforcement defaults."""

    return {
        "enforcement_state": "ALLOW",
        "enforcement_visibility": "VISIBLE",
        "enforcement_reason": "not_enforced",
        "enforcement_notes": None,
        "enforcement_profile": "DEFAULT",
    }


def build_enforcement_diagnostics() -> dict[str, Any]:
    """Return zeroed enforcement diagnostics."""

    return {
        "rollout_mode": "visible_but_blocked",
        "allow_count": 0,
        "watch_only_count": 0,
        "block_count": 0,
        "counts_by_reason": {},
        "counts_by_profile": {},
        "counts_by_market_segment": {
            "EGX30": _build_state_counter(),
            "EGX70": _build_state_counter(),
        },
    }


def build_enforcement_contract(
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the shared enforcement metadata contract."""

    resolved_diagnostics = diagnostics or build_enforcement_diagnostics()
    return {
        "metadata_fields": [*ENFORCEMENT_METADATA_FIELDS],
        "defaults": build_enforcement_defaults(),
        "diagnostics": deepcopy(resolved_diagnostics),
    }


def assess_enforcement_gate(
    trap_risk_band: Any,
    whale_alignment: Any,
    route_profile: Any = None,
    market_segment: Any = None,
) -> dict[str, Any]:
    """Return a deterministic enforcement decision from shared shadow metadata."""

    profile_name = resolve_active_enforcement_profile(route_profile, market_segment)
    return assess_enforcement_gate_with_profile(
        trap_risk_band=trap_risk_band,
        whale_alignment=whale_alignment,
        enforcement_profile=profile_name,
    )


def assess_enforcement_gate_with_profile(
    trap_risk_band: Any,
    whale_alignment: Any,
    enforcement_profile: Any,
) -> dict[str, Any]:
    """Return an enforcement decision for one explicit profile name."""

    result = build_enforcement_defaults()
    result["enforcement_notes"] = "No whale/trap enforcement threshold breached."

    profile_name = str(enforcement_profile or "DEFAULT").strip().upper() or "DEFAULT"
    profile = get_enforcement_profile(profile_name)
    result["enforcement_profile"] = profile_name

    normalized_band = _normalize_trap_risk_band(trap_risk_band)
    normalized_alignment = _normalize_whale_alignment(whale_alignment)

    if normalized_band in profile["block_on_trap_bands"]:
        result["enforcement_state"] = "BLOCK_EXECUTION"
        result["enforcement_reason"] = "severe_trap_risk"
        result["enforcement_notes"] = (
            "Blocked for execution because severe trap risk breached the shadow threshold."
        )
        return result

    if (
        normalized_alignment == "CONFLICT"
        and normalized_band in profile["block_on_conflict_trap_bands"]
    ):
        result["enforcement_state"] = "BLOCK_EXECUTION"
        result["enforcement_reason"] = "stacked_shadow_threshold"
        result["enforcement_notes"] = (
            "Blocked for execution because high trap risk stacks with whale conflict."
        )
        return result

    if (
        normalized_alignment == "CONFLICT"
        and normalized_band in profile["profile_conflict_block_bands"]
        and profile_name != "DEFAULT"
    ):
        result["enforcement_state"] = "BLOCK_EXECUTION"
        result["enforcement_reason"] = "profile_threshold_breach"
        result["enforcement_notes"] = (
            f"Blocked for execution because {profile_name.lower()} thresholds escalate "
            "medium trap risk with whale conflict."
        )
        return result

    if normalized_band in profile["watch_on_trap_bands"]:
        result["enforcement_state"] = "WATCH_ONLY"
        result["enforcement_reason"] = "high_trap_risk"
        result["enforcement_notes"] = (
            "Downgraded to watch-only because shadow trap risk is high."
        )
        return result

    if normalized_alignment in profile["watch_on_alignments"]:
        result["enforcement_state"] = "WATCH_ONLY"
        result["enforcement_reason"] = "distribution_conflict"
        result["enforcement_notes"] = (
            "Downgraded to watch-only because whale flow conflicts with the setup."
        )
        return result

    return result


def _build_state_counter() -> dict[str, int]:
    return {
        "allow_count": 0,
        "watch_only_count": 0,
        "block_count": 0,
    }


def _increment_state_bucket(bucket: dict[str, Any], state: str) -> None:
    if state == "BLOCK_EXECUTION":
        bucket["block_count"] = int(bucket.get("block_count", 0)) + 1
    elif state == "WATCH_ONLY":
        bucket["watch_only_count"] = int(bucket.get("watch_only_count", 0)) + 1
    else:
        bucket["allow_count"] = int(bucket.get("allow_count", 0)) + 1


def _normalize_state(value: Any) -> str:
    state = str(value or "").strip().upper()
    if state in _ENFORCEMENT_STATES:
        return state
    return "ALLOW"


def _normalize_trap_risk_band(value: Any) -> str:
    band = str(value or "").strip().upper()
    if band in _TRAP_RISK_BANDS:
        return band
    return "UNKNOWN"


def _normalize_whale_alignment(value: Any) -> str:
    alignment = str(value or "").strip().upper()
    if alignment in _WHALE_ALIGNMENTS:
        return alignment
    return "NEUTRAL"


def _normalize_market_segment(value: Any) -> str | None:
    return resolve_market_segment(market_segment=value)


def _read_value(row: dict[str, Any], snake_key: str) -> Any:
    title_key = snake_key.title().replace("_", "_")
    return row.get(snake_key, row.get(title_key))


def summarize_enforcement_diagnostics(
    rows: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Roll up enforcement counters across candidate-like rows."""

    diagnostics = build_enforcement_diagnostics()

    for row in rows or []:
        state = _normalize_state(_read_value(row, "enforcement_state"))
        reason = str(_read_value(row, "enforcement_reason") or "").strip()
        profile = str(_read_value(row, "enforcement_profile") or "").strip().upper()
        market_segment = _normalize_market_segment(
            _read_value(row, "market_segment")
            or _read_value(row, "route_profile")
            or profile
        )

        _increment_state_bucket(diagnostics, state)

        if state in {"WATCH_ONLY", "BLOCK_EXECUTION"} and reason:
            diagnostics["counts_by_reason"][reason] = (
                int(diagnostics["counts_by_reason"].get(reason, 0)) + 1
            )

        if profile:
            profile_bucket = diagnostics["counts_by_profile"].setdefault(
                profile,
                _build_state_counter(),
            )
            _increment_state_bucket(profile_bucket, state)

        if market_segment:
            segment_bucket = diagnostics["counts_by_market_segment"].setdefault(
                market_segment,
                _build_state_counter(),
            )
            _increment_state_bucket(segment_bucket, state)

    return diagnostics
