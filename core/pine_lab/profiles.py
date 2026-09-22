from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any

from peewee import DateTimeField, IntegerField, PostgresqlDatabase, TextField
from playhouse.migrate import PostgresqlMigrator, SqliteMigrator, migrate

from database import ScannerStrategyProfile, db

READY_COMPATIBILITY_MIN = 70.0
READY_COMBINED_SCORE_MIN = 60.0
READY_TRADE_COUNT_MIN = 30
READY_TOTAL_RETURN_MIN = 0.0
READY_MAX_DRAWDOWN_MAX = 35.0
READY_RISK_OF_RUIN_MAX = 1.0
READY_OOS_TRADE_COUNT_MIN = 10

PROMOTION_THRESHOLDS = {
    "compatibility_score": READY_COMPATIBILITY_MIN,
    "combined_score": READY_COMBINED_SCORE_MIN,
    "trade_count": READY_TRADE_COUNT_MIN,
    "total_return": READY_TOTAL_RETURN_MIN,
    "max_drawdown": READY_MAX_DRAWDOWN_MAX,
    "risk_of_ruin_pct": READY_RISK_OF_RUIN_MAX,
    "oos_trade_count": READY_OOS_TRADE_COUNT_MIN,
}


def ensure_pine_scanner_profile_schema() -> None:
    db.connect(reuse_if_open=True)

    table_name = ScannerStrategyProfile._meta.table_name
    existing_tables = set(db.get_tables())
    if table_name not in existing_tables:
        db.create_tables([ScannerStrategyProfile], safe=True)

    existing_columns = {column.name for column in db.get_columns(table_name)}
    missing_columns = []
    if "ready_at" not in existing_columns:
        missing_columns.append(("ready_at", DateTimeField(null=True)))
    if "activated_at" not in existing_columns:
        missing_columns.append(("activated_at", DateTimeField(null=True)))
    if "activation_count" not in existing_columns:
        missing_columns.append(("activation_count", IntegerField(default=0)))
    if "activation_history_json" not in existing_columns:
        missing_columns.append(("activation_history_json", TextField(default="[]")))
    if "import_rule_spec_json" not in existing_columns:
        missing_columns.append(("import_rule_spec_json", TextField(default="{}")))

    if not missing_columns:
        return

    live_db = getattr(db, "obj", db)
    migrator = PostgresqlMigrator(live_db) if isinstance(live_db, PostgresqlDatabase) else SqliteMigrator(live_db)
    operations = [migrator.add_column(table_name, column_name, field) for column_name, field in missing_columns]
    migrate(*operations)


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload or {}, sort_keys=True)


def _json_loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _json_loads_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _build_promotion_artifacts(backtest_summary: dict[str, Any] | None) -> dict[str, Any]:
    backtest = dict(backtest_summary or {})
    artifacts = backtest.get("promotion_artifacts")
    if isinstance(artifacts, dict) and artifacts:
        source = dict(artifacts)
    else:
        source = {
            "artifact_version": "promotion_v1",
            "date_from": backtest.get("date_from"),
            "date_to": backtest.get("date_to"),
            "market": backtest.get("market"),
            "timeframe": backtest.get("timeframe"),
            "tickers": backtest.get("tickers", []),
            "data_version": backtest.get("data_version"),
            "costs": backtest.get("costs", {}),
            "parameters": backtest.get("parameters", {}),
            "metrics": {
                "trade_count": backtest.get("trade_count"),
                "total_return": backtest.get("total_return"),
                "max_drawdown": backtest.get("max_drawdown"),
                "risk_of_ruin_pct": backtest.get("risk_of_ruin_pct"),
            },
            "failed_gates": backtest.get("failed_gates", []),
        }
    payload_for_hash = json.dumps(source, sort_keys=True)
    source["artifact_hash"] = hashlib.sha256(payload_for_hash.encode("utf-8")).hexdigest()
    return source


def create_pine_scanner_profile(
    *,
    profile_name: str,
    script_source: str,
    market: str,
    timeframe: str,
    backtest_summary: dict[str, Any] | None,
    compatibility_summary: dict[str, Any] | None,
    ranking_summary: dict[str, Any] | None,
) -> ScannerStrategyProfile:
    ensure_pine_scanner_profile_schema()
    script_hash = hashlib.sha256(str(script_source).strip().encode("utf-8")).hexdigest()
    backtest_payload = dict(backtest_summary or {})
    backtest_payload["promotion_artifacts"] = _build_promotion_artifacts(backtest_payload)
    promotion_summary = build_promotion_summary(
        backtest_summary=backtest_payload,
        compatibility_summary=compatibility_summary,
        ranking_summary=ranking_summary,
    )
    profile_state = str(promotion_summary["profile_state"])
    ready_at = datetime.datetime.now() if profile_state == "READY" else None
    return ScannerStrategyProfile.create(
        profile_name=str(profile_name).strip(),
        source_type="PINE",
        script_source=str(script_source).strip(),
        script_hash=script_hash,
        market=str(market).strip().upper() or "EGX30",
        timeframe=str(timeframe).strip() or "1D",
        profile_state=profile_state,
        backtest_summary_json=_json_dumps(backtest_payload),
        compatibility_summary_json=_json_dumps(compatibility_summary),
        ranking_summary_json=_json_dumps(ranking_summary),
        ready_at=ready_at,
        activation_count=0,
        activation_history_json="[]",
        import_rule_spec_json="{}",
    )


def create_imported_pine_profile(
    *,
    profile_name: str,
    script_source: str,
    market: str,
    timeframe: str,
    rule_spec: dict[str, Any],
    backtest_summary: dict[str, Any] | None,
    compatibility_summary: dict[str, Any] | None,
    ranking_summary: dict[str, Any] | None,
) -> ScannerStrategyProfile:
    ensure_pine_scanner_profile_schema()
    script_hash = hashlib.sha256(str(script_source).strip().encode("utf-8")).hexdigest()
    backtest_payload = dict(backtest_summary or {})
    backtest_payload["promotion_artifacts"] = _build_promotion_artifacts(backtest_payload)
    promotion_summary = build_promotion_summary(
        backtest_summary=backtest_payload,
        compatibility_summary=compatibility_summary,
        ranking_summary=ranking_summary,
    )
    profile_state = str(promotion_summary["profile_state"])
    ready_at = datetime.datetime.now() if profile_state == "READY" else None
    return ScannerStrategyProfile.create(
        profile_name=str(profile_name).strip(),
        source_type="PINE_LOGIC_IMPORT",
        script_source=str(script_source).strip(),
        script_hash=script_hash,
        market=str(market).strip().upper() or "EGX30",
        timeframe=str(timeframe).strip() or "1D",
        profile_state=profile_state,
        backtest_summary_json=_json_dumps(backtest_payload),
        compatibility_summary_json=_json_dumps(compatibility_summary),
        ranking_summary_json=_json_dumps(ranking_summary),
        ready_at=ready_at,
        activation_count=0,
        activation_history_json="[]",
        import_rule_spec_json=_json_dumps(rule_spec),
    )


def build_promotion_summary(
    *,
    backtest_summary: dict[str, Any] | None,
    compatibility_summary: dict[str, Any] | None,
    ranking_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    backtest = backtest_summary or {}
    compatibility = compatibility_summary or {}
    ranking = ranking_summary or {}

    readiness = str(compatibility.get("readiness", "")).strip().upper()
    compatibility_score = float(compatibility.get("compatibility_score", 0.0) or 0.0)
    combined_score = float(ranking.get("combined_score", 0.0) or 0.0)
    total_return = float(backtest.get("total_return", 0.0) or 0.0)
    trade_count = int(backtest.get("trade_count", 0) or 0)
    max_drawdown = float(backtest.get("max_drawdown", 0.0) or 0.0)
    risk_of_ruin_pct = float(backtest.get("risk_of_ruin_pct", 0.0) or 0.0)
    monte_carlo_pass = bool(backtest.get("monte_carlo_pass", True))
    walk_forward_pass = bool(backtest.get("walk_forward_pass", False))
    oos_trade_count = int(backtest.get("oos_trade_count", 0) or 0)
    costs = backtest.get("costs") if isinstance(backtest.get("costs"), dict) else {}
    cost_commission = backtest.get("commission_pct", costs.get("commission_pct", 0.0))
    cost_slippage = backtest.get("slippage_pct", costs.get("slippage_pct", 0.0))
    artifacts = backtest.get("promotion_artifacts") if isinstance(backtest.get("promotion_artifacts"), dict) else {}
    failed_gates: list[str] = []

    if readiness != "READY":
        failed_gates.append("readiness")
    if compatibility_score < READY_COMPATIBILITY_MIN:
        failed_gates.append("compatibility_score")
    if combined_score < READY_COMBINED_SCORE_MIN:
        failed_gates.append("combined_score")
    if total_return <= READY_TOTAL_RETURN_MIN:
        failed_gates.append("total_return")
    if trade_count < READY_TRADE_COUNT_MIN:
        failed_gates.append("trade_count")
    if max_drawdown > READY_MAX_DRAWDOWN_MAX:
        failed_gates.append("max_drawdown")
    if risk_of_ruin_pct > READY_RISK_OF_RUIN_MAX:
        failed_gates.append("risk_of_ruin_pct")
    if not monte_carlo_pass:
        failed_gates.append("monte_carlo")
    if not walk_forward_pass:
        failed_gates.append("walk_forward")
    if oos_trade_count < READY_OOS_TRADE_COUNT_MIN:
        failed_gates.append("oos_trade_count")
    if float(cost_commission or 0.0) <= 0 or float(cost_slippage or 0.0) <= 0:
        failed_gates.append("realistic_costs")
    if not artifacts.get("artifact_hash"):
        failed_gates.append("promotion_artifacts")

    profile_state = "READY" if not failed_gates else "DRAFT"
    return {
        "profile_state": profile_state,
        "failed_gates": failed_gates,
        "thresholds": PROMOTION_THRESHOLDS,
        "actuals": {
            "readiness": readiness or "UNKNOWN",
            "compatibility_score": compatibility_score,
            "combined_score": combined_score,
            "trade_count": trade_count,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "risk_of_ruin_pct": risk_of_ruin_pct,
            "monte_carlo_pass": monte_carlo_pass,
            "walk_forward_pass": walk_forward_pass,
            "oos_trade_count": oos_trade_count,
            "commission_pct": float(cost_commission or 0.0),
            "slippage_pct": float(cost_slippage or 0.0),
            "artifact_hash": artifacts.get("artifact_hash"),
        },
    }


def get_pine_scanner_profile(profile_id: int) -> ScannerStrategyProfile | None:
    ensure_pine_scanner_profile_schema()
    try:
        normalized_id = int(profile_id)
    except (TypeError, ValueError):
        return None
    return ScannerStrategyProfile.get_or_none(ScannerStrategyProfile.id == normalized_id)


def get_active_pine_scanner_profile() -> ScannerStrategyProfile | None:
    ensure_pine_scanner_profile_schema()
    return (
        ScannerStrategyProfile
        .select()
        .where(ScannerStrategyProfile.profile_state == "ACTIVE")
        .order_by(ScannerStrategyProfile.created_at.desc())
        .first()
    )


def activate_pine_scanner_profile(profile_id: int) -> ScannerStrategyProfile:
    profile = get_pine_scanner_profile(profile_id)
    if profile is None:
        raise LookupError("Requested Pine scanner profile was not found.")
    if str(profile.source_type or "").upper() != "PINE":
        raise ValueError("Only native Pine runtime profiles can be activated in Scanner.")
    if profile.profile_state not in {"READY", "ACTIVE"}:
        raise ValueError("Only READY Pine scanner profiles can be activated.")
    if profile.profile_state == "ACTIVE":
        return profile

    previous_active_profile = get_active_pine_scanner_profile()
    activated_at = datetime.datetime.now()
    activation_history = _json_loads_list(profile.activation_history_json)
    activation_history.insert(0, {
        "event_type": "ACTIVATED",
        "activated_at": activated_at.isoformat(),
        "previous_state": profile.profile_state,
        "previous_active_profile_id": previous_active_profile.id if previous_active_profile and previous_active_profile.id != profile.id else None,
        "previous_active_profile_name": previous_active_profile.profile_name if previous_active_profile and previous_active_profile.id != profile.id else None,
    })

    with db.atomic():
        (
            ScannerStrategyProfile
            .update(profile_state="READY")
            .where(
                (ScannerStrategyProfile.profile_state == "ACTIVE")
                & (ScannerStrategyProfile.id != profile.id)
            )
            .execute()
        )
        profile.profile_state = "ACTIVE"
        profile.ready_at = profile.ready_at or activated_at
        profile.activated_at = activated_at
        profile.activation_count = int(profile.activation_count or 0) + 1
        profile.activation_history_json = _json_dumps(activation_history)
        profile.save()
    return profile


def serialize_pine_scanner_profile(row: ScannerStrategyProfile) -> dict[str, Any]:
    backtest_summary = _json_loads(row.backtest_summary_json)
    compatibility_summary = _json_loads(row.compatibility_summary_json)
    ranking_summary = _json_loads(row.ranking_summary_json)
    promotion_summary = build_promotion_summary(
        backtest_summary=backtest_summary,
        compatibility_summary=compatibility_summary,
        ranking_summary=ranking_summary,
    )
    ready_at = row.ready_at or (row.created_at if row.profile_state in {"READY", "ACTIVE"} else None)
    activation_history = _json_loads_list(getattr(row, "activation_history_json", None))
    if row.profile_state == "ACTIVE":
        promotion_summary = {
            **promotion_summary,
            "profile_state": "ACTIVE",
            "failed_gates": [],
        }

    return {
        "profile_id": row.id,
        "profile_name": row.profile_name,
        "source_type": row.source_type,
        "market": row.market,
        "timeframe": row.timeframe,
        "profile_state": row.profile_state,
        "is_active": row.profile_state == "ACTIVE",
        "script_hash": row.script_hash,
        "backtest_summary": backtest_summary,
        "compatibility_summary": compatibility_summary,
        "ranking_summary": ranking_summary,
        "promotion_summary": promotion_summary,
        "ready_at": ready_at.isoformat() if ready_at else None,
        "activated_at": row.activated_at.isoformat() if row.activated_at else None,
        "activation_count": int(row.activation_count or 0),
        "activation_history": activation_history,
        "has_import_rule_spec": bool(_json_loads(getattr(row, "import_rule_spec_json", None))),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_pine_scanner_profiles() -> list[dict[str, Any]]:
    ensure_pine_scanner_profile_schema()
    profiles: list[dict[str, Any]] = []
    query = ScannerStrategyProfile.select().order_by(ScannerStrategyProfile.created_at.desc())
    for row in query:
        profiles.append(serialize_pine_scanner_profile(row))
    profiles.sort(key=lambda item: (item["profile_state"] != "ACTIVE", item["profile_name"]))
    return profiles
