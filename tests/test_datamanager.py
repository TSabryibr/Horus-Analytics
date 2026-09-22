from core.settings import settings
from core.exclusions import get_all_exclusions
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.DataManager import DataManager, invalidate_history_cache, _get_simulation_filtered_history
from core.exclusions import invalidate_exclusion_cache


@pytest.fixture(autouse=True)
def _clear_dm_caches():
    """Ensure each test starts with a clean DataManager cache."""
    invalidate_history_cache()
    invalidate_exclusion_cache()
    yield
    invalidate_history_cache()
    invalidate_exclusion_cache()


@pytest.fixture
def mock_data_engine_api():
    with patch('core.DataManager.data_engine_api') as mock:
        yield mock


def test_get_stock_data_success(mock_data_engine_api):
    # Setup mock data
    df_data = {
        'open': [10.0, 11.0],
        'high': [12.0, 13.0],
        'low': [9.0, 10.0],
        'close': [11.0, 12.0],
        'volume': [1000, 2000]
    }
    dates = pd.to_datetime(['2023-01-01', '2023-01-02'])
    mock_df = pd.DataFrame(df_data, index=dates)
    mock_data_engine_api.get_data.return_value = mock_df
    
    # Call DataManager
    df = DataManager.get_stock_data("TEST_TICKER", include_live=False)
    
    # Assertions
    assert df is not None
    assert not df.empty
    assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
    assert df.index.name == 'Date'
    assert df['Close'].iloc[0] == 11.0
    assert df['Close'].iloc[1] == 12.0

def test_get_stock_data_empty(mock_data_engine_api):
    mock_data_engine_api.get_data.return_value = None
    df = DataManager.get_stock_data("TEST_TICKER")
    assert df is None

def test_list_tickers_filtering(mock_data_engine_api):
    mock_data_engine_api.list_tickers.return_value = ["AAPL", "GOOG", "EXCLUDE_ME"]
    
    with patch('core.exclusions.get_all_exclusions', return_value={"EXCLUDE_ME"}):
        tickers = DataManager.list_tickers()
        assert "AAPL" in tickers
        assert "GOOG" in tickers
        assert "EXCLUDE_ME" not in tickers


def test_list_tickers_filters_non_tradable(mock_data_engine_api):
    mock_data_engine_api.list_tickers.return_value = ["AAPL", "123", "EGX30", "REOPEN123", "FWRY"]
    with patch('core.exclusions.get_all_exclusions', return_value=set()):
        tickers = DataManager.list_tickers()
        assert "AAPL" in tickers
        assert "FWRY" in tickers
        assert "EGX30" in tickers
        assert "123" not in tickers
        assert "REOPEN123" not in tickers


def test_list_tickers_excludes_runtime_quarantined_symbols(mock_data_engine_api):
    mock_data_engine_api.list_tickers.return_value = ["COMI", "ADIB_R3", "MEGM", "TRTO"]

    with patch("core.exclusions.get_all_exclusions", return_value=set()), patch(
        "core.DataManager.get_runtime_ticker_report",
        return_value={
            "runtime_quarantined": [
                {"ticker": "ADIB_R3", "reason": "RIGHTS", "quarantined": True},
                {"ticker": "MEGM", "reason": "DORMANT", "quarantined": True},
            ],
            "review_candidates": [
                {"ticker": "TRTO", "reason": "SOURCE_STALE", "quarantined": False},
            ],
        },
    ):
        tickers = DataManager.list_tickers()

    assert "COMI" in tickers
    assert "TRTO" in tickers
    assert "ADIB_R3" not in tickers
    assert "MEGM" not in tickers


def test_get_intraday_data_refreshes_stale_off_hours(mock_data_engine_api):
    probe_df = pd.DataFrame(
        {
            "open": [0.03],
            "high": [0.03],
            "low": [0.03],
            "close": [0.03],
            "volume": [800.0],
        },
        index=pd.to_datetime(["2026-03-08 12:31:00"]),
    )
    mock_data_engine_api.get_data.side_effect = [probe_df, probe_df]

    with patch("core.DataManager.TimeUtils.is_simulating", return_value=False), \
         patch("core.DataManager.settings.is_market_open", return_value=False), \
         patch("core.DataManager._intraday_is_stale", return_value=True), \
         patch("core.DataManager._should_attempt_intraday_refresh", return_value=True), \
         patch("core.DataManager._refresh_intraday_cache_once") as refresh_mock:
        df = DataManager.get_intraday_data("GTEX", limit=1)

    assert df is not None
    assert not df.empty
    refresh_mock.assert_called_once()


def test_get_stock_data_does_not_merge_previous_session_intraday_as_live(mock_data_engine_api, monkeypatch):
    history = pd.DataFrame(
        {
            "open": [10.0],
            "high": [10.5],
            "low": [9.8],
            "close": [10.0],
            "volume": [100.0],
        },
        index=pd.to_datetime(["2026-06-01"]),
    )
    previous_intraday = pd.DataFrame(
        {
            "Open": [10.0],
            "High": [11.0],
            "Low": [9.9],
            "Close": [11.0],
            "Volume": [500.0],
        },
        index=pd.to_datetime(["2026-06-01 14:28:00"]),
    )
    mock_data_engine_api.get_data.return_value = history

    monkeypatch.setattr("core.DataManager.settings.is_market_open", lambda: True)
    monkeypatch.setattr("core.DataManager.TimeUtils.today", lambda: pd.Timestamp("2026-06-02").date())
    monkeypatch.setattr(
        DataManager,
        "get_intraday_data",
        staticmethod(lambda ticker: previous_intraday),
    )

    df = DataManager.get_stock_data("COMI", include_live=True)

    assert df.index.max() == pd.Timestamp("2026-06-01")
    assert float(df.loc[pd.Timestamp("2026-06-01"), "Close"]) == 10.0


def test_get_universe_data_uses_recent_history_limit(mock_data_engine_api, monkeypatch):
    index_ts = pd.to_datetime(["2026-04-10 00:00:00", "2026-04-11 00:00:00"])
    mock_data_engine_api.get_bulk_data.return_value = pd.DataFrame(
        {
            "ticker": ["COMI", "COMI"],
            "timestamp": index_ts,
            "open": [10.0, 10.5],
            "high": [11.0, 11.5],
            "low": [9.5, 10.0],
            "close": [10.8, 11.2],
            "volume": [1000.0, 1100.0],
        }
    )
    monkeypatch.setenv("UNIVERSE_HISTORY_LIMIT", "45")

    df = DataManager.get_universe_data(["COMI"], include_live=False)

    assert df is not None
    assert not df.empty
    mock_data_engine_api.get_bulk_data.assert_called_once_with(
        ["COMI"],
        timeframe="history",
        realm="EGX",
        limit=45,
    )


def test_get_simulation_filtered_history_reuses_cached_slice_without_leaking_mutation():
    dates = pd.date_range("2023-01-01", periods=6, freq="D")
    df = pd.DataFrame(
        {
            "Open": [1, 2, 3, 4, 5, 6],
            "High": [1, 2, 3, 4, 5, 6],
            "Low": [1, 2, 3, 4, 5, 6],
            "Close": [1, 2, 3, 4, 5, 6],
            "Volume": [10, 20, 30, 40, 50, 60],
        },
        index=dates,
    )
    df.index.name = "Date"

    cutoff = pd.Timestamp("2023-01-03")

    first = _get_simulation_filtered_history("TEST", "EGX", df, cutoff)
    second = _get_simulation_filtered_history("TEST", "EGX", df, cutoff)

    assert list(first.index) == list(pd.date_range("2023-01-01", periods=3, freq="D"))
    assert second.equals(first)

    second.iloc[0, second.columns.get_loc("Close")] = 999

    third = _get_simulation_filtered_history("TEST", "EGX", df, cutoff)
    assert third.iloc[0]["Close"] == 1
