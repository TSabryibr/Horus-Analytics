from __future__ import annotations

from typing import Any


_SUPPORTED_SIGNAL_ROLES = {"long_entry", "short_entry", "long_exit", "short_exit"}


def validate_import_rule_spec(rule_spec: dict[str, Any], reduced_source_pack: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(rule_spec, dict):
        raise ValueError("Rule spec must be an object.")

    signals = rule_spec.get("signals")
    if not isinstance(signals, dict):
        raise ValueError("Rule spec signals must be an object.")

    source_names = {
        str(item.get("name") or "").strip()
        for item in list(reduced_source_pack.get("candidate_signals") or []) + list(reduced_source_pack.get("definitions") or [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }

    for role in _SUPPORTED_SIGNAL_ROLES:
        payload = signals.get(role)
        if not isinstance(payload, dict):
            raise ValueError(f"Signal payload for {role} must be an object.")

        status = str(payload.get("status") or "missing").strip().lower()
        if status not in {"mapped", "missing"}:
            raise ValueError(f"Signal payload for {role} has an unsupported status.")

        source_name = payload.get("source_name")
        if status == "mapped":
            if not source_name or str(source_name).strip() not in source_names:
                raise ValueError(f"Signal payload for {role} references an unknown source variable.")
            if not str(payload.get("expression") or "").strip():
                raise ValueError(f"Signal payload for {role} must include an expression.")

    unresolved_references = list(reduced_source_pack.get("unresolved_references") or [])
    has_mapped_long_entry = signals.get("long_entry", {}).get("status") == "mapped"

    return {
        "ok": True,
        "review_status": (
            "READY_FOR_REVIEW"
            if has_mapped_long_entry and not unresolved_references
            else "NEEDS_MANUAL_REVIEW"
        ),
    }


def validate_import_backtest_request(rule_spec: dict[str, Any], *, operator_approved: bool) -> dict[str, Any]:
    if not operator_approved:
        raise ValueError("Operator approval is required before import backtest can run.")
    if not isinstance(rule_spec, dict):
        raise ValueError("rule_spec must be an object.")

    source = rule_spec.get("source")
    if not isinstance(source, dict) or str(source.get("import_mode") or "").strip().upper() != "LOGIC_IMPORT":
        raise ValueError("rule_spec must come from the Logic Import workflow.")

    execution_plan = rule_spec.get("execution_plan")
    if not isinstance(execution_plan, dict):
        raise ValueError("Approved import rule spec is not executable yet.")

    definitions = execution_plan.get("definitions")
    entry_expression = execution_plan.get("entry_expression")
    exit_expression = execution_plan.get("exit_expression")
    if not isinstance(definitions, dict) or not isinstance(entry_expression, dict) or not isinstance(exit_expression, dict):
        raise ValueError("Approved import rule spec is missing execution plan fields.")

    return {
        "ok": True,
        "execution_mode": str(execution_plan.get("execution_mode") or "LONG_ONLY").upper(),
    }
