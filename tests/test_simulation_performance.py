import pytest
import pandas as pd
import datetime
import time
from unittest.mock import patch

from api import app
from core import TimeUtils
from core.DataManager import DataManager


def test_time_travel_filtering_performance():
    # Arrange: Create a large mock dataframe
    dates = pd.date_range("2020-01-01", "2025-01-01", freq="D")
    df = pd.DataFrame({"Close": range(len(dates))}, index=dates)

    # Act: Run the filter 1000 times to simulate a large backtest scan
    sim_date = datetime.datetime(2023, 1, 1)
    TimeUtils.set_simulation(sim_date)
    
    start_time = time.time()
    with patch("core.DataManager._get_cached_history", return_value=df):
        # DataManager.get_stock_data expects a ticker string
        for _ in range(1000):
            res = DataManager.get_stock_data("DUMMY", include_live=False)
    duration = time.time() - start_time
    
    TimeUtils.clear_simulation()

    # Assert: Should take less than 0.5 seconds for 1000 iterations
    assert duration < 0.5, f"Performance issue: filtering took {duration:.2f}s"
    
    # Also verify correctness
    assert res is not None
    assert not res.empty
    assert res.index.max() <= pd.Timestamp(sim_date)
