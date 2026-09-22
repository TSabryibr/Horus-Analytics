"""
TIME UTILS - Central Time Reference
===================================
All modules use this instead of datetime.now().
Enables Global Time Travel Mode for simulation.
Supports Replay Mode for off-hours pipeline testing.
"""
import datetime
import pandas as pd

# Simulation State (In-memory for now, could be persisted if needed)
_SIMULATION_DATE = None
_SIMULATION_ACTIVE = False

# Replay Mode State — distinct from simulation.
# Replay drives its own scans and monitor ticks so scheduler jobs can stay quiet.
_REPLAY_ACTIVE = False
_REPLAY_LIVE_CHANNEL_ROUTING = False

# Market Override — forces is_market_open() to return True during replay/dryrun.
_MARKET_OVERRIDE = False


def _simulation_status_message(state: str, date: datetime.datetime | None = None) -> str:
    normalized = str(state or "").strip().upper()
    if normalized == "ACTIVATED" and date is not None:
        return f"[Time Travel] Activated: {date.strftime('%Y-%m-%d')}"
    return "[Time Travel] Deactivated: Back to Live"

def now() -> datetime.datetime:
    """Returns current datetime (or simulation date if active)."""
    if _SIMULATION_ACTIVE and _SIMULATION_DATE:
        return _SIMULATION_DATE
    return datetime.datetime.now()

def today() -> datetime.date:
    """Returns current date (or simulation date if active)."""
    return now().date()

def pd_now() -> pd.Timestamp:
    """Pandas-compatible timestamp."""
    return pd.Timestamp(now())

def set_simulation(date: datetime.datetime):
    """Activate simulation mode."""
    global _SIMULATION_DATE, _SIMULATION_ACTIVE
    _SIMULATION_DATE = date
    _SIMULATION_ACTIVE = True
    print(_simulation_status_message("ACTIVATED", date))

def clear_simulation():
    """Return to live mode."""
    global _SIMULATION_DATE, _SIMULATION_ACTIVE
    _SIMULATION_DATE = None
    _SIMULATION_ACTIVE = False
    print(_simulation_status_message("DEACTIVATED"))

def is_simulating() -> bool:
    """Check if simulation is active."""
    return _SIMULATION_ACTIVE

def get_simulation_date() -> datetime.datetime:
    """Get the current simulation date."""
    return _SIMULATION_DATE


# ---------------------------------------------------------------------------
# Replay Mode — off-hours pipeline testing
# ---------------------------------------------------------------------------

def set_replay(date: datetime.datetime, market_override: bool = True, live_channel_routing: bool = False):
    """Activate replay mode (distinct from regular simulation).

    Replay owns the accelerated scan/monitor loop. Scheduler jobs should skip
    while replay is active to avoid duplicate Telegram messages and position
    updates. Replay can optionally force ``is_market_open()`` to return True.
    """
    global _REPLAY_ACTIVE, _MARKET_OVERRIDE, _REPLAY_LIVE_CHANNEL_ROUTING
    _REPLAY_ACTIVE = True
    _REPLAY_LIVE_CHANNEL_ROUTING = bool(live_channel_routing)
    if market_override:
        _MARKET_OVERRIDE = True
    set_simulation(date)
    print(
        f"[Replay] Activated: {date.strftime('%Y-%m-%d %H:%M')} "
        f"(market_override={market_override}, live_channel_routing={_REPLAY_LIVE_CHANNEL_ROUTING})"
    )


def clear_replay():
    """Exit replay mode and restore normal operation."""
    global _REPLAY_ACTIVE, _MARKET_OVERRIDE, _REPLAY_LIVE_CHANNEL_ROUTING
    _REPLAY_ACTIVE = False
    _REPLAY_LIVE_CHANNEL_ROUTING = False
    _MARKET_OVERRIDE = False
    clear_simulation()
    print("[Replay] Deactivated: Back to Live")


def is_replay() -> bool:
    """Check if replay mode is active."""
    return _REPLAY_ACTIVE


def is_replay_live_channel_routing() -> bool:
    """Return True when replay notifications should use live channel config."""
    return _REPLAY_ACTIVE and _REPLAY_LIVE_CHANNEL_ROUTING


def advance_simulation(minutes: int):
    """Step the simulated clock forward by N minutes.

    Only works when simulation is active. Used by the replay engine
    to tick the clock forward at accelerated speed.
    """
    global _SIMULATION_DATE
    if _SIMULATION_ACTIVE and _SIMULATION_DATE:
        _SIMULATION_DATE = _SIMULATION_DATE + datetime.timedelta(minutes=minutes)


def set_market_override(enabled: bool = True):
    """Force ``is_market_open()`` to return True (for dryrun/replay)."""
    global _MARKET_OVERRIDE
    _MARKET_OVERRIDE = enabled


def clear_market_override():
    """Remove the market override."""
    global _MARKET_OVERRIDE
    _MARKET_OVERRIDE = False


def get_market_override() -> bool:
    """Check if the market override is active."""
    return _MARKET_OVERRIDE
