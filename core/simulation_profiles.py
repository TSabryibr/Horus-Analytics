from core.pine_lab import (
    get_active_pine_scanner_profile,
    get_pine_scanner_profile,
    run_pine_scanner_profile_scan,
)
from core.price_action.scanner import run_price_action_scanner_profile_scan


def resolve_simulation_scanner_profile(profile_id: int | None = None, use_active_profile: bool = False):
    resolved_profile = (
        get_pine_scanner_profile(profile_id)
        if profile_id is not None
        else (get_active_pine_scanner_profile() if use_active_profile else None)
    )
    if profile_id is not None and resolved_profile is None:
        raise LookupError("Requested simulation scanner profile was not found.")
    if resolved_profile is None:
        return None

    source_type = str(getattr(resolved_profile, "source_type", "") or "").strip().upper()
    if source_type not in {"PINE", "PRICE_ACTION"}:
        raise ValueError("Simulation supports only PINE and PRICE_ACTION scanner profiles.")
    return resolved_profile


def run_selected_simulation_profile_scan(profile):
    source_type = str(getattr(profile, "source_type", "") or "").strip().upper()
    if source_type == "PINE":
        return run_pine_scanner_profile_scan(profile=profile)
    if source_type == "PRICE_ACTION":
        return run_price_action_scanner_profile_scan(profile=profile)
    raise ValueError(f"Unsupported simulation scanner profile source_type '{source_type or 'UNKNOWN'}'.")
