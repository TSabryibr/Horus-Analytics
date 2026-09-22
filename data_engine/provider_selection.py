from __future__ import annotations
from core.settings import settings



VALID_PROVIDERS = {"AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}


def normalize_provider(provider: str | None) -> str:
    raw = (provider or "").strip().upper()
    if raw in VALID_PROVIDERS:
        return raw
    return "AUTO"


def _timeframe_policy_provider(timeframe: str) -> str:
    tf = timeframe.strip().lower()
    if tf == "history":
        return normalize_provider(getattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO"))
    if tf == "intraday":
        return normalize_provider(getattr(settings, "LOCAL_INTRADAY_PROVIDER", "AUTO"))
    if tf == "ticks":
        raw = (getattr(settings, "LOCAL_TICKS_PROVIDER", "MUBASHER_DB") or "").strip().upper()
        if raw == "MUBASHER_DB":
            return raw
    return "AUTO"


def resolved_provider_context(
    *,
    timeframe: str,
    selected_provider: str,
    selection_report: dict | None = None,
    unified_policy_provider: str | None = None,
) -> dict:
    tf = timeframe.strip().lower()
    detail_key = f"recommended_{tf}_details"
    if selection_report and isinstance(selection_report.get(detail_key), dict):
        detail = dict(selection_report[detail_key])
        detail.setdefault("provider", selected_provider)
        detail.setdefault("fallback_from", None)
        detail.setdefault("evidence", {})
        return detail

    if tf == "ticks":
        return {
            "provider": selected_provider,
            "reason": "configured_ticks_provider",
            "fallback_from": None,
            "evidence": {"configured_provider": selected_provider},
        }

    explicit_timeframe = normalize_provider(
        getattr(
            settings,
            "LOCAL_HISTORY_PROVIDER" if tf == "history" else "LOCAL_INTRADAY_PROVIDER",
            "AUTO",
        )
    )
    if explicit_timeframe != "AUTO":
        return {
            "provider": selected_provider,
            "reason": "explicit_timeframe_policy",
            "fallback_from": None,
            "evidence": {"configured_provider": explicit_timeframe},
        }

    unified_policy = normalize_provider(
        unified_policy_provider or getattr(settings, "LOCAL_FEED_PROVIDER", "AUTO")
    )
    if unified_policy != "AUTO":
        return {
            "provider": selected_provider,
            "reason": "explicit_unified_policy",
            "fallback_from": None,
            "evidence": {"configured_provider": unified_policy},
        }

    return {
        "provider": selected_provider,
        "reason": "policy_selected",
        "fallback_from": None,
        "evidence": {},
    }


def format_quality_report(report: dict) -> str:
    csv = report["csv"]
    db = report["mubasher_db"]
    dfn = report["directfn"]
    msd = report.get("metastock_dat", {})
    history_details = report.get("recommended_history_details") or {}
    intraday_details = report.get("recommended_intraday_details") or {}
    history_reason = history_details.get("reason")
    intraday_reason = intraday_details.get("reason")
    intraday_fallback_from = intraday_details.get("fallback_from")
    lines = [
        "[LocalFeed] Source quality check:",
        f"  CSV         score={csv['score']} hist={csv['history_symbols']} latest={csv['history_latest']} "
        f"intra={csv['intraday_symbols']} intra_latest={csv['intraday_latest']}",
        f"  MUBASHER_DB score={db['score']} hist={db['history_symbols']} latest={db['history_latest']} "
        f"intra={db['intraday_symbols']} intra_latest={db['intraday_latest']}",
        f"  DIRECTFN    score={dfn['score']} hist={dfn['history_symbols']} latest={dfn['history_latest']} "
        f"intra={dfn['intraday_symbols']} intra_latest={dfn['intraday_latest']}",
        f"  METASTOCK_DAT score={msd.get('score', 0)} hist={msd.get('history_symbols', 0)} "
        f"latest={msd.get('history_latest')} intra={msd.get('intraday_symbols', 0)} "
        f"intra_latest={msd.get('intraday_latest')}",
        f"  Recommended provider: {report['recommended_provider']}",
        f"  Recommended history provider: {report['recommended_history_provider']}",
        f"  Recommended intraday provider: {report['recommended_intraday_provider']}",
    ]
    if history_reason:
        lines.append(f"  History decision: {report['recommended_history_provider']} ({history_reason})")
    if intraday_reason:
        suffix = f" from {intraday_fallback_from}" if intraday_fallback_from else ""
        lines.append(
            f"  Intraday decision: {report['recommended_intraday_provider']} ({intraday_reason}{suffix})"
        )
    return "\n".join(lines)


def resolve_timeframe_provider(timeframe: str, provider: str | None = None) -> tuple[str, dict | None]:
    # Lazy import to avoid circular imports with local_feed_selector wrappers.
    from data_engine.local_feed_selector import compare_local_sources, recommend_provider_for_timeframe

    # Explicit call argument has highest precedence.
    if provider is not None:
        requested = normalize_provider(provider)
        if requested in {"CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}:
            return requested, None

    # Timeframe-specific policy should override the legacy unified provider setting.
    policy = _timeframe_policy_provider(timeframe)
    if policy in {"CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}:
        if timeframe.strip().lower() == "intraday" and policy == "MUBASHER_DB":
            raw_fallback = getattr(settings, "LOCAL_INTRADAY_ALLOW_STALE_FALLBACK", False)
            if isinstance(raw_fallback, str):
                allow_stale_fallback = raw_fallback.strip().lower() in {"1", "true", "yes", "on"}
            else:
                allow_stale_fallback = bool(raw_fallback)

            report = compare_local_sources()
            selected = recommend_provider_for_timeframe(report, timeframe="intraday")
            if allow_stale_fallback and selected != "MUBASHER_DB":
                return selected, report
            details = report.get("recommended_intraday_details") or {}
            if (
                str(details.get("provider") or "").upper() == "MUBASHER_DB"
                and str(details.get("reason") or "") == "upstream_intraday_stale"
            ):
                return policy, report
        return policy, None

    # Legacy unified policy is fallback only when no explicit timeframe policy exists.
    requested_unified = normalize_provider(getattr(settings, "LOCAL_FEED_PROVIDER", "AUTO"))
    if requested_unified in {"CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}:
        return requested_unified, None

    report = compare_local_sources()
    selected = recommend_provider_for_timeframe(report, timeframe=timeframe)
    return selected, report


def stage_provider_context(
    provider_context: dict | None,
    ingest_summary: dict | None = None,
) -> dict | None:
    if not provider_context and not ingest_summary:
        return None
    merged = dict(provider_context or {})
    if ingest_summary:
        merged["ingest_summary"] = dict(ingest_summary)
    return merged
