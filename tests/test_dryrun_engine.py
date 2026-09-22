import datetime

from database import ScannerStrategyProfile


def _make_profile(**overrides):
    defaults = {
        "profile_name": "Dry Run Test Profile",
        "source_type": "PRICE_ACTION",
        "script_source": '{"strategy_id":"ascending_triangle_breakout"}',
        "script_hash": f"hash-{datetime.datetime.now().timestamp()}",
        "market": "EGX30",
        "timeframe": "1D",
        "profile_state": "ACTIVE",
    }
    defaults.update(overrides)
    return ScannerStrategyProfile.create(**defaults)


def test_start_dryrun_records_selected_profile(monkeypatch):
    import core.dryrun_engine as dryrun_engine

    profile = _make_profile()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None, name=None):
            self.target = target
            self.args = args

        def start(self):
            return None

    monkeypatch.setattr(dryrun_engine, "_resolve_dryrun_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(dryrun_engine.threading, "Thread", DummyThread)

    result = dryrun_engine.start_dryrun(
        target_date="2026-04-30",
        notify=False,
        report=False,
        ai_report=False,
        profile_id=profile.id,
        use_active_profile=False,
    )

    assert result["status"] == "started"
    assert result["profile_id"] == profile.id
    assert result["profile_name"] == profile.profile_name
    assert dryrun_engine._DRYRUN_STATE["profile_id"] == profile.id
    assert dryrun_engine._DRYRUN_STATE["profile_name"] == profile.profile_name


def test_run_dryrun_scan_uses_selected_profile(monkeypatch):
    import core.dryrun_engine as dryrun_engine

    profile = _make_profile(profile_name="Dry Run Daily Profile", profile_state="READY")
    core_calls = []
    profile_calls = []

    monkeypatch.setattr(
        dryrun_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday: (core_calls.append((index_choice, is_intraday)) or ([], [], 0.0, "UNKNOWN")),
    )
    monkeypatch.setattr(
        dryrun_engine,
        "_run_selected_dryrun_profile_scan",
        lambda selected_profile: (
            profile_calls.append(selected_profile.id)
            or ([], [], 0.0, "BULLISH", {"profile_name": selected_profile.profile_name, "source_type": selected_profile.source_type})
        ),
    )

    result = dryrun_engine._run_dryrun_scan(replay_profile=profile, replay_market="EGX30")

    assert result["signals_count"] == 0
    assert result["regime"] == "BULLISH"
    assert result["strategy_profile"]["profile_name"] == profile.profile_name
    assert core_calls == []
    assert profile_calls == [profile.id]
