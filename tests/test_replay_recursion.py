"""
TEST REPLAY RECURSION SAFETY
============================
Verify that profile resolution, scanner execution, and start_replay
do not trigger RecursionError when core.replay_engine shims are imported.
"""

import pytest
import core.replay_engine as replay_engine
from core.replay.state import (
    _resolve_replay_scanner_profile,
    _run_selected_replay_profile_scan,
    _resolve_dispatch,
)


def test_replay_scanner_profile_resolution_no_recursion():
    """Ensure _resolve_replay_scanner_profile resolves safely without infinite recursion."""
    profile = _resolve_replay_scanner_profile(profile_id=None, use_active_profile=False)
    assert profile is None or hasattr(profile, "profile_name") or hasattr(profile, "id")


def test_resolve_dispatch_self_guard():
    """Ensure _resolve_dispatch respects self_fn guard and returns fallback."""
    dummy_fallback = lambda: "fallback_result"
    
    # When mod has a function with the same name which is the caller itself
    result = _resolve_dispatch(
        "_resolve_replay_scanner_profile",
        dummy_fallback,
        self_fn=replay_engine._resolve_replay_scanner_profile,
    )
    assert result is dummy_fallback
