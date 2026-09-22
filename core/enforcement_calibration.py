from __future__ import annotations
"""
Shared compare-only calibration helpers for whale/trap enforcement profiles.

TC-P2 evaluates candidate profiles against the same candidate set as the active
baseline without changing the actual enforced state.
"""


from typing import Any

from core.enforcement_gates import (
    assess_enforcement_gate_with_profile,
    summarize_enforcement_diagnostics,
)
from core.enforcement_profiles import (
    get_promotion_decision,
    list_candidate_calibration_profiles,
    resolve_active_enforcement_profile,
    resolve_market_segment,
)


def compare_enforcement_profiles(
    rows: list[dict[str, Any]] | None,
    *,
    route_profile: Any = None,
    market_segment: Any = None,
    candidate_profiles: list[str] | None = None,
) -> dict[str, Any]:
    """Compare the active enforcement profile against candidate profiles."""

    source_rows = list(rows or [])
    active_profile = resolve_active_enforcement_profile(route_profile, market_segment)
    promotion_decision = get_promotion_decision(
        route_profile=route_profile,
        market_segment=market_segment,
    )
    candidates = list(candidate_profiles or list_candidate_calibration_profiles(route_profile, market_segment))

    baseline_rows = _evaluate_rows_with_profile(source_rows, active_profile)
    baseline_counts = summarize_enforcement_diagnostics(baseline_rows)

    candidate_summaries: dict[str, Any] = {}
    for candidate_name in candidates:
        candidate_rows = _evaluate_rows_with_profile(source_rows, candidate_name)
        candidate_counts = summarize_enforcement_diagnostics(candidate_rows)
        candidate_summaries[candidate_name] = {
            "counts": candidate_counts,
            "deltas": _build_count_deltas(baseline_counts, candidate_counts),
            "top_delta_reasons": _build_top_delta_reasons(baseline_counts, candidate_counts),
            "top_reclassified_names": _build_top_reclassified_names(
                baseline_rows,
                candidate_rows,
            ),
        }

    return {
        "active_enforcement_profile": active_profile,
        "previous_active_profile": promotion_decision.get("previous_active_profile"),
        "new_active_profile": promotion_decision.get("new_active_profile"),
        "rollback_profile": promotion_decision.get("rollback_profile"),
        "promotion_scope": promotion_decision.get("promotion_scope"),
        "promotion_rationale": promotion_decision.get("promotion_rationale"),
        "promotion_evidence": promotion_decision.get("promotion_evidence"),
        "candidate_calibration_profiles": candidates,
        "calibration_summary": {
            "baseline_counts": baseline_counts,
            "candidates": candidate_summaries,
        },
    }


def summarize_calibration_diagnostics(
    rows: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Build compare-only calibration diagnostics grouped by market segment."""

    diagnostics: dict[str, Any] = {
        "rollout_mode": "compare_only",
        "market_segments": {},
        "top_delta_reasons": [],
        "top_reclassified_names": [],
    }

    source_rows = list(rows or [])
    segment_route_profiles = {
        "EGX30": "EGX30_TREND_PROFILE",
        "EGX70": "EGX70_TACTICAL_PROFILE",
    }

    aggregate_reason_deltas: dict[str, int] = {}
    aggregate_reclassifications: list[dict[str, Any]] = []

    for segment, route_profile in segment_route_profiles.items():
        segment_rows = [
            row for row in source_rows
            if resolve_market_segment(
                route_profile=_read_value(row, "route_profile"),
                market_segment=_read_value(row, "market_segment"),
            ) == segment
        ]
        if not segment_rows:
            continue

        comparison = compare_enforcement_profiles(
            segment_rows,
            route_profile=route_profile,
        )
        diagnostics["market_segments"][segment] = comparison

        for candidate_summary in comparison["calibration_summary"]["candidates"].values():
            for reason, delta in dict(candidate_summary["deltas"].get("reason_deltas") or {}).items():
                aggregate_reason_deltas[reason] = int(aggregate_reason_deltas.get(reason, 0)) + int(delta)
            for reclassified in list(candidate_summary.get("top_reclassified_names") or []):
                aggregate_reclassifications.append(
                    {
                        **reclassified,
                        "market_segment": segment,
                    }
                )

    ranked_reasons = sorted(
        aggregate_reason_deltas.items(),
        key=lambda item: (-int(item[1]), str(item[0])),
    )
    diagnostics["top_delta_reasons"] = [
        {"reason": reason, "delta": delta}
        for reason, delta in ranked_reasons[:5]
    ]
    diagnostics["top_reclassified_names"] = sorted(
        aggregate_reclassifications,
        key=lambda item: (str(item.get("market_segment") or ""), str(item.get("ticker") or "")),
    )[:5]
    return diagnostics


def _evaluate_rows_with_profile(
    rows: list[dict[str, Any]],
    profile_name: str,
) -> list[dict[str, Any]]:
    evaluated_rows: list[dict[str, Any]] = []
    for row in rows:
        evaluated = dict(row)
        evaluated.update(
            assess_enforcement_gate_with_profile(
                trap_risk_band=row.get("trap_risk_band"),
                whale_alignment=row.get("whale_alignment"),
                enforcement_profile=profile_name,
            )
        )
        evaluated_rows.append(evaluated)
    return evaluated_rows


def _build_count_deltas(
    baseline_counts: dict[str, Any],
    candidate_counts: dict[str, Any],
) -> dict[str, Any]:
    reason_deltas: dict[str, int] = {}
    baseline_reasons = dict(baseline_counts.get("counts_by_reason") or {})
    candidate_reasons = dict(candidate_counts.get("counts_by_reason") or {})
    for reason in sorted(set(baseline_reasons) | set(candidate_reasons)):
        delta = int(candidate_reasons.get(reason, 0)) - int(baseline_reasons.get(reason, 0))
        if delta > 0:
            reason_deltas[reason] = delta

    return {
        "allow_delta": int(candidate_counts.get("allow_count", 0)) - int(baseline_counts.get("allow_count", 0)),
        "watch_only_delta": int(candidate_counts.get("watch_only_count", 0)) - int(baseline_counts.get("watch_only_count", 0)),
        "block_delta": int(candidate_counts.get("block_count", 0)) - int(baseline_counts.get("block_count", 0)),
        "reason_deltas": reason_deltas,
    }


def _build_top_delta_reasons(
    baseline_counts: dict[str, Any],
    candidate_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    reason_deltas = _build_count_deltas(baseline_counts, candidate_counts)["reason_deltas"]
    ranked = sorted(
        reason_deltas.items(),
        key=lambda item: (-int(item[1]), str(item[0])),
    )
    return [{"reason": reason, "delta": delta} for reason, delta in ranked[:5]]


def _build_top_reclassified_names(
    baseline_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reclassified: list[dict[str, Any]] = []
    baseline_by_ticker = {str(row.get("ticker") or row.get("Ticker") or ""): row for row in baseline_rows}
    candidate_by_ticker = {str(row.get("ticker") or row.get("Ticker") or ""): row for row in candidate_rows}

    for ticker in sorted(set(baseline_by_ticker) | set(candidate_by_ticker)):
        if not ticker:
            continue
        baseline_row = baseline_by_ticker.get(ticker) or {}
        candidate_row = candidate_by_ticker.get(ticker) or {}
        baseline_state = str(baseline_row.get("enforcement_state") or "ALLOW").upper()
        candidate_state = str(candidate_row.get("enforcement_state") or "ALLOW").upper()
        if baseline_state == candidate_state:
            continue
        reclassified.append(
            {
                "ticker": ticker,
                "baseline_state": baseline_state,
                "candidate_state": candidate_state,
                "baseline_reason": str(baseline_row.get("enforcement_reason") or "not_enforced"),
                "candidate_reason": str(candidate_row.get("enforcement_reason") or "not_enforced"),
            }
        )

    return reclassified[:5]


def _read_value(row: dict[str, Any], snake_key: str) -> Any:
    title_key = snake_key.title().replace("_", "_")
    return row.get(snake_key, row.get(title_key))
