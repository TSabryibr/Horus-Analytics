import datetime

from core.market.LiveFeedManager import  LiveFeedManager


def test_refresh_resistance_levels_uses_shared_analytics_snapshot(monkeypatch):
    rows = [
        {
            "Ticker": "COMI",
            "Resistance_20D": 80.0,
            "Key_Resistance_1": 82.5,
            "Key_Resistance_2": 85.0,
        },
        {
            "Ticker": "FWRY",
            "Resistance_20D": 5.0,
            "Key_Resistance_1": None,
            "Key_Resistance_2": 5.7,
        },
    ]

    monkeypatch.setattr(
        "routes.analytics.ensure_analytics_rows",
        lambda scan_id, allow_stale=True: rows,
    )
    monkeypatch.setattr(
        "core.DataManager.DataManager.list_tickers",
        lambda: (_ for _ in ()).throw(AssertionError("live feed should not list tickers directly")),
    )
    monkeypatch.setattr(
        "core.analyzers.MomentumBreakoutScanner.analyze_stock",
        lambda ticker: (_ for _ in ()).throw(AssertionError("live feed should not recompute MomentumBreakoutScanner rows")),
    )

    LiveFeedManager._resistance_cache = {}
    LiveFeedManager._triggered_today = {"COMI_Resistance_20D"}
    LiveFeedManager._last_refresh_date = None

    LiveFeedManager.refresh_resistance_levels()

    assert LiveFeedManager._resistance_cache == {
        "COMI": {"R20": 80.0, "K1": 82.5, "K2": 85.0},
        "FWRY": {"R20": 5.0, "K1": None, "K2": 5.7},
    }
    assert LiveFeedManager._triggered_today == set()
    assert LiveFeedManager._last_refresh_date == datetime.date.today()
