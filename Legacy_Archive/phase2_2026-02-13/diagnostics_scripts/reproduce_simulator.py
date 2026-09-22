
from core.simulation import PortfolioSimulator
import pandas as pd
import datetime

# Mock GlobalSettings if needed, or rely on defaults
print("Running reproduction script...")

try:
    # Use default params from PortfolioSimulator
    # Simulating what the API does
    params = {
        'RSI_MIN': 40, 
        'RSI_MAX': 80,
        'VOL_SPIKE': 1.5,
        'MOMENTUM': 1.0,
        'SL_PCT': 2.0,
        'TP1_PCT': 5.0,
        'TRAILING_STOP_ENABLED': False
    }

    print("Calling run_simulation...")
    result = PortfolioSimulator.run_simulation(
        cap=100000, 
        start_date="2025-01-01", 
        end_date="2025-12-31", 
        index_choice="EGX30", 
        params=params
    )
    
    print("Simulation finished.")
    if result:
        print(f"Total Return: {result.get('total_return')}")
        print(f"Trades: {len(result.get('trades', []))}")
        print(f"Daily Values: {len(result.get('daily_values', []))}")
    else:
        print("Result is None")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
