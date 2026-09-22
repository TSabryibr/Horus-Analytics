"""
CORE SIGNALS SLA TELEMETRY
==========================
Computes signal delivery SLA metrics, round-trip Telegram latency distributions,
breach rates, and destination-level diagnostics for Horus Analytics.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from core import TimeUtils
from database import SignalDelivery, SignalRun
from utils.logger import setup_logger

logger = setup_logger("horus.signals.sla")


def record_delivery_telemetry(delivery: SignalDelivery, latency_ms: float) -> None:
    """Record round-trip latency in milliseconds for a SignalDelivery."""
    delivery.latency_ms = round(float(latency_ms), 2)
    delivery.save()


LATENCY_HISTOGRAM_BUCKETS = (
    ("<250ms", 0.0, 250.0),
    ("250-500ms", 250.0, 500.0),
    ("500-1000ms", 500.0, 1000.0),
    ("1-2.5s", 1000.0, 2500.0),
    ("2.5-5s", 2500.0, 5000.0),
    (">5s", 5000.0, float("inf")),
)


def compute_latency_histogram(latencies: list[float]) -> list[dict[str, Any]]:
    """
    Computes distribution buckets for dispatch latencies.
    Buckets: <250ms, 250-500ms, 500-1000ms, 1-2.5s, 2.5-5s, >5s.
    """
    total = len(latencies)
    histogram = []
    for label, min_val, max_val in LATENCY_HISTOGRAM_BUCKETS:
        if max_val == float("inf"):
            count = sum(1 for lat in latencies if lat >= min_val)
        else:
            count = sum(1 for lat in latencies if min_val <= lat < max_val)
        pct = round((count / total) * 100.0, 2) if total > 0 else 0.0
        histogram.append({
            "bucket": label,
            "min_ms": min_val,
            "max_ms": max_val if max_val != float("inf") else None,
            "count": count,
            "pct": pct,
        })
    return histogram


def compute_delivery_sla_metrics(
    days: int = 7,
    target_latency_ms: float = 5000.0,
) -> dict[str, Any]:
    """
    Computes comprehensive SLA metrics across SignalDelivery records within the given day window.
    
    Returns:
      - window_days: Analyzed window in days
      - target_latency_ms: SLA latency threshold
      - total_deliveries: Count of all deliveries recorded
      - sent_count: Successful dispatches
      - failed_count: Failed dispatches
      - skipped_count: Skipped dispatches (e.g. no recs, missing config)
      - dry_run_count: Dry-run test dispatches
      - success_rate_pct: Sent / (Sent + Failed) %
      - sla_compliant: Boolean indicating whether success rate >= 95% and p95 <= target
      - latency_stats: Latency distribution (avg, p50, p90, p95, p99, min, max, breached_count, breach_rate_pct)
      - by_channel: Breakdown by channel (TELEGRAM, etc.)
      - by_tier: Breakdown by service tier (SIGNALS_ONLY, MANAGED_EXECUTION, etc.)
      - by_destination_type: Breakdown by destination type (PORTFOLIO, SUBSCRIBER, CHANNEL)
    """
    if days < 1:
        days = 1

    cutoff_dt = TimeUtils.now() - datetime.timedelta(days=days)
    deliveries: list[SignalDelivery] = list(
        SignalDelivery.select().where(SignalDelivery.created_at >= cutoff_dt)
    )

    by_status: dict[str, int] = {}
    by_channel: dict[str, dict[str, Any]] = {}
    by_tier: dict[str, dict[str, Any]] = {}
    by_dest_type: dict[str, dict[str, Any]] = {}
    latencies: list[float] = []

    for d in deliveries:
        st = d.status or "UNKNOWN"
        by_status[st] = by_status.get(st, 0) + 1

        lat = getattr(d, "latency_ms", None)
        if lat is not None and lat >= 0:
            latencies.append(float(lat))

        # Grouping helpers
        for group_dict, key in [
            (by_channel, d.channel or "UNKNOWN"),
            (by_tier, d.service_tier or "UNKNOWN"),
            (by_dest_type, d.destination_type or "UNKNOWN"),
        ]:
            if key not in group_dict:
                group_dict[key] = {
                    "total": 0,
                    "sent": 0,
                    "failed": 0,
                    "latencies": [],
                }
            group_dict[key]["total"] += 1
            if st == "SENT":
                group_dict[key]["sent"] += 1
            elif st == "FAILED":
                group_dict[key]["failed"] += 1
            if lat is not None and lat >= 0:
                group_dict[key]["latencies"].append(float(lat))

    sent_count = by_status.get("SENT", 0)
    failed_count = by_status.get("FAILED", 0)
    skipped_count = by_status.get("SKIPPED", 0)
    dry_run_count = by_status.get("DRY_RUN", 0)

    success_rate_pct = 100.0
    if sent_count + failed_count > 0:
        success_rate_pct = round((sent_count / (sent_count + failed_count)) * 100.0, 2)


    histogram = compute_latency_histogram(latencies)

    if latencies:
        avg_ms = round(float(np.mean(latencies)), 2)
        p50_ms = round(float(np.percentile(latencies, 50)), 2)
        p90_ms = round(float(np.percentile(latencies, 90)), 2)
        p95_ms = round(float(np.percentile(latencies, 95)), 2)
        p99_ms = round(float(np.percentile(latencies, 99)), 2)
        min_ms = round(float(np.min(latencies)), 2)
        max_ms = round(float(np.max(latencies)), 2)
        breached_count = sum(1 for l in latencies if l > target_latency_ms)
        breach_rate_pct = round((breached_count / len(latencies)) * 100.0, 2)
    else:
        avg_ms = p50_ms = p90_ms = p95_ms = p99_ms = min_ms = max_ms = None
        breached_count = 0
        breach_rate_pct = 0.0

    sla_compliant = bool(
        success_rate_pct >= 95.0
        and (p95_ms is None or p95_ms <= target_latency_ms)
    )

    def finalize_breakdown(group_dict: dict[str, dict[str, Any]]) -> dict[str, Any]:
        finalized = {}
        for k, v in group_dict.items():
            grp_lats = v.pop("latencies")
            grp_sent = v["sent"]
            grp_failed = v["failed"]
            v["success_rate_pct"] = (
                round((grp_sent / (grp_sent + grp_failed)) * 100.0, 2)
                if grp_sent + grp_failed > 0
                else 100.0
            )
            v["avg_latency_ms"] = round(float(np.mean(grp_lats)), 2) if grp_lats else None
            v["histogram"] = compute_latency_histogram(grp_lats)
            finalized[k] = v
        return finalized

    return {
        "window_days": days,
        "from_date": cutoff_dt.strftime("%Y-%m-%d"),
        "to_date": TimeUtils.now().strftime("%Y-%m-%d"),
        "target_latency_ms": target_latency_ms,
        "total_deliveries": len(deliveries),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "dry_run_count": dry_run_count,
        "success_rate_pct": success_rate_pct,
        "sla_compliant": sla_compliant,
        "by_status": by_status,
        "latency_stats": {
            "count": len(latencies),
            "avg_ms": avg_ms,
            "p50_ms": p50_ms,
            "p90_ms": p90_ms,
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "min_ms": min_ms,
            "max_ms": max_ms,
            "breached_count": breached_count,
            "breach_rate_pct": breach_rate_pct,
            "histogram": histogram,
        },
        "by_channel": finalize_breakdown(by_channel),
        "by_tier": finalize_breakdown(by_tier),
        "by_destination_type": finalize_breakdown(by_dest_type),
    }
