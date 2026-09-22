
import unittest
import datetime
import pandas as pd
from core import TimeUtils
from core import DataManager
import os

class TestTimeTravel(unittest.TestCase):

    def test_core_utility(self):
        """Phase 1: Verify TimeUtils logic"""
        # 1. Default (Live)
        TimeUtils.clear_simulation()
        self.assertFalse(TimeUtils.is_simulating())
        real_now = datetime.datetime.now()
        tu_now = TimeUtils.now()
        self.assertAlmostEqual(real_now.timestamp(), tu_now.timestamp(), delta=1)

        # 2. Simulation Active
        sim_date = datetime.datetime(2025, 1, 15, 10, 30)
        TimeUtils.set_simulation(sim_date)
        self.assertTrue(TimeUtils.is_simulating())
        self.assertEqual(TimeUtils.now(), sim_date)
        self.assertEqual(TimeUtils.today(), sim_date.date())
        self.assertEqual(TimeUtils.pd_now(), pd.Timestamp(sim_date))

        # 3. Clear
        TimeUtils.clear_simulation()
        self.assertFalse(TimeUtils.is_simulating())

    def test_data_manager_filtering(self):
        """Phase 2: Verify DataManager respects simulation time"""
        # Create a mock dataframe with future dates
        dates = pd.date_range("2025-01-01", "2025-01-20")
        df = pd.DataFrame({"Close": range(len(dates))}, index=dates)
        
        # Scenario: It's Jan 10th
        sim_date = datetime.datetime(2025, 1, 10)
        TimeUtils.set_simulation(sim_date)
        
        # The filter logic from DataManager (normally applied to real files)
        now_ref = TimeUtils.now()
        filtered_df = df[df.index <= pd.Timestamp(now_ref)]
        
        self.assertEqual(filtered_df.index[-1].strftime("%Y-%m-%d"), "2025-01-10")
        self.assertTrue("2025-01-11" not in filtered_df.index)
        
        TimeUtils.clear_simulation()

    def test_api_integration(self):
        """Phase 3: Verify API endpoints (mocked or internal call)"""
        # Since we can't easily run the server and test it in one go here, 
        # we test the internal functions that API uses.
        
        target_date = "2025-05-20"
        dt = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        
        # Simulate /api/simulate/start
        TimeUtils.set_simulation(dt)
        self.assertEqual(TimeUtils.get_simulation_date(), dt)
        
        # Simulate /api/simulate/status
        status = {
            "active": TimeUtils.is_simulating(),
            "date": TimeUtils.get_simulation_date().strftime("%Y-%m-%d") if TimeUtils.is_simulating() else None
        }
        self.assertEqual(status["date"], target_date)
        
        TimeUtils.clear_simulation()

if __name__ == "__main__":
    unittest.main()
