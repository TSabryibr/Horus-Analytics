"""Tests for core.session_mode — auto-detection and mode transitions."""

from core.settings import settings
import datetime
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.session_mode import compute_session_mode, apply_mode_transition, resolve_startup_session_mode


# ---------------------------------------------------------------------------
# EGX constants used by all tests
# ---------------------------------------------------------------------------
MARKET_START = "1000"
MARKET_END = "1430"
WEEKEND_DAYS = [4, 5]  # Friday, Saturday


# ---------------------------------------------------------------------------
# compute_session_mode — pure function tests
# ---------------------------------------------------------------------------


class TestComputeSessionMode:
    """Tests for the pure compute_session_mode function."""

    def test_during_market_hours(self):
        """10:30 on Sunday (weekday=6) → LIVE."""
        now = datetime.datetime(2026, 3, 22, 10, 30)  # Sunday
        assert now.weekday() == 6
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "LIVE"

    def test_pre_market_window(self):
        """09:35 on Sunday → within 30 min of market open → LIVE."""
        now = datetime.datetime(2026, 3, 22, 9, 35)
        assert now.weekday() == 6
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "LIVE"

    def test_after_hours(self):
        """15:00 on Sunday → after market close → ANALYSIS."""
        now = datetime.datetime(2026, 3, 22, 15, 0)
        assert now.weekday() == 6
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "ANALYSIS"

    def test_before_pre_market(self):
        """09:00 on Sunday → before pre-market window → ANALYSIS."""
        now = datetime.datetime(2026, 3, 22, 9, 0)
        assert now.weekday() == 6
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "ANALYSIS"

    def test_weekend_friday(self):
        """10:30 on Friday (weekday=4) → weekend → ANALYSIS."""
        now = datetime.datetime(2026, 3, 27, 10, 30)  # Friday
        assert now.weekday() == 4
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "ANALYSIS"

    def test_weekend_saturday(self):
        """Any time on Saturday (weekday=5) → ANALYSIS."""
        now = datetime.datetime(2026, 3, 28, 12, 0)  # Saturday
        assert now.weekday() == 5
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "ANALYSIS"

    def test_registered_holiday(self):
        now = datetime.datetime(2026, 5, 28, 10, 30)
        result = compute_session_mode(
            now,
            MARKET_START,
            MARKET_END,
            WEEKEND_DAYS,
            holiday_dates={now.date()},
        )
        assert result == "ANALYSIS"

    def test_exact_pre_market_boundary(self):
        """09:30 on Sunday → exact pre-market start → LIVE."""
        now = datetime.datetime(2026, 3, 22, 9, 30)
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "LIVE"

    def test_exact_market_close_boundary(self):
        """14:30 on Sunday → exact market close → LIVE (inclusive)."""
        now = datetime.datetime(2026, 3, 22, 14, 30)
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "LIVE"

    def test_one_minute_after_close(self):
        """14:31 on Sunday → just after close → ANALYSIS."""
        now = datetime.datetime(2026, 3, 22, 14, 31)
        result = compute_session_mode(now, MARKET_START, MARKET_END, WEEKEND_DAYS)
        assert result == "ANALYSIS"


# ---------------------------------------------------------------------------
# apply_mode_transition — side-effect tests
# ---------------------------------------------------------------------------


class TestApplyModeTransition:
    """Tests for apply_mode_transition with mocked dependencies."""

    @patch("core.session_mode.LiveFeedManager")
    @patch("core.session_mode.settings")
    def test_transition_to_live(self, mock_settings, mock_lfm):
        """ANALYSIS → LIVE sets SESSION_MODE and returns transitioned."""
        mock_settings.SESSION_MODE = "ANALYSIS"
        mock_settings.is_market_open.return_value = True
        mock_lfm.is_running.return_value = False

        result = apply_mode_transition("LIVE")

        assert result["status"] == "transitioned"
        assert result["to"] == "LIVE"
        assert mock_settings.SESSION_MODE == "LIVE"

    @patch("core.session_mode.LiveFeedManager")
    @patch("core.session_mode.settings")
    def test_transition_to_analysis(self, mock_settings, mock_lfm):
        """LIVE → ANALYSIS sets SESSION_MODE and returns transitioned."""
        mock_settings.SESSION_MODE = "LIVE"
        mock_lfm.is_running.return_value = True

        result = apply_mode_transition("ANALYSIS")

        assert result["status"] == "transitioned"
        assert result["to"] == "ANALYSIS"
        assert mock_settings.SESSION_MODE == "ANALYSIS"

    @patch("core.session_mode.LiveFeedManager")
    @patch("core.session_mode.settings")
    def test_transition_noop(self, mock_settings, mock_lfm):
        """Already in target mode → noop."""
        mock_settings.SESSION_MODE = "LIVE"

        result = apply_mode_transition("LIVE")

        assert result["status"] == "noop"
        assert result["mode"] == "LIVE"


class TestResolveStartupSessionMode:
    def test_settings_imports_without_session_mode_env(self, tmp_path):
        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("SESSION_MODE", None)
        env.pop("RAMADAN_MODE", None)
        env.pop("DATA_ROOT_OVERRIDE", None)
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in [str(repo_root), env.get("PYTHONPATH", "")] if part
        )

        code = (
            "import core.settings as settings_mod\n"
            "mode = settings_mod.settings.SESSION_MODE\n"
            "assert mode in {'LIVE', 'ANALYSIS'}, mode\n"
            "assert hasattr(settings_mod.settings, 'RAMADAN_MODE')\n"
            "assert hasattr(settings_mod.settings, 'MARKET_WEEKEND')\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )

        assert result.returncode == 0, result.stderr + result.stdout

    def test_packaged_after_hours_ignores_unforced_configured_live(self):
        now = datetime.datetime(2026, 3, 22, 15, 0)

        result = resolve_startup_session_mode(
            configured_mode="LIVE",
            is_frozen=True,
            force_session_mode=False,
            now=now,
            market_start_hhmm=MARKET_START,
            market_end_hhmm=MARKET_END,
            weekend_days=WEEKEND_DAYS,
        )

        assert result["configured_session_mode"] == "LIVE"
        assert result["effective_session_mode"] == "ANALYSIS"
        assert result["forced_mode"] is False
        assert result["reason"] == "market_closed"

    def test_packaged_forced_mode_honors_configured_live_after_hours(self):
        now = datetime.datetime(2026, 3, 22, 15, 0)

        result = resolve_startup_session_mode(
            configured_mode="LIVE",
            is_frozen=True,
            force_session_mode=True,
            now=now,
            market_start_hhmm=MARKET_START,
            market_end_hhmm=MARKET_END,
            weekend_days=WEEKEND_DAYS,
        )

        assert result["configured_session_mode"] == "LIVE"
        assert result["effective_session_mode"] == "LIVE"
        assert result["forced_mode"] is True
        assert result["reason"] == "forced_configured_mode"

    def test_packaged_premarket_live_reports_live_window_not_market_open(self):
        now = datetime.datetime(2026, 3, 22, 9, 35)

        result = resolve_startup_session_mode(
            configured_mode="ANALYSIS",
            is_frozen=True,
            force_session_mode=False,
            now=now,
            market_start_hhmm=MARKET_START,
            market_end_hhmm=MARKET_END,
            weekend_days=WEEKEND_DAYS,
        )

        assert result["effective_session_mode"] == "LIVE"
        assert result["reason"] == "live_window"

    def test_source_run_keeps_configured_mode(self):
        now = datetime.datetime(2026, 3, 22, 15, 0)

        result = resolve_startup_session_mode(
            configured_mode="LIVE",
            is_frozen=False,
            force_session_mode=False,
            now=now,
            market_start_hhmm=MARKET_START,
            market_end_hhmm=MARKET_END,
            weekend_days=WEEKEND_DAYS,
        )

        assert result["configured_session_mode"] == "LIVE"
        assert result["effective_session_mode"] == "LIVE"
        assert result["forced_mode"] is False
        assert result["reason"] == "configured_mode"
