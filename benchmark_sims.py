
import time
import numpy as np
from core import MonteCarlo
from core import RagnarokSimulator
def benchmark_monte_carlo():
    print("Benchmarking MonteCarlo.py...")
    # Generate 500 mock trades
    trades = [{'pnl_pct': np.random.normal(0.1, 2.0)} for _ in range(500)]
    initial_equity = 100000
    simulations = 5000
    
    start_time = time.time()
    results = MonteCarlo.run_monte_carlo(trades, initial_equity, simulations=simulations)
    end_time = time.time()
    
    print(f"Monte Carlo ({simulations} sims, {len(trades)} trades): {end_time - start_time:.4f}s")
    return results

def benchmark_ragnarok():
    print("\nBenchmarking RagnarokSimulator.py...")
    # Mock some data since DataManager.get_stock_data requires real files
    # We'll monkeypatch _prepare_returns for the benchmark
    
    original_prepare = RagnarokSimulator._prepare_returns
    
    def mock_prepare(tickers):
        dates = pd.date_range("2020-01-01", periods=1000)
        data = {t: np.random.normal(0.001, 0.02, 1000) for t in tickers}
        return pd.DataFrame(data, index=dates)
    
    import pandas as pd
    RagnarokSimulator._prepare_returns = mock_prepare
    
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    iterations = 5000
    days = 252 # 1 year
    
    start_time = time.time()
    results = RagnarokSimulator.run_ragnarok_simulation(tickers, iterations=iterations, days=days)
    end_time = time.time()
    
    print(f"Ragnarok ({iterations} iterations, {days} days, {len(tickers)} assets): {end_time - start_time:.4f}s")
    
    # Restore
    RagnarokSimulator._prepare_returns = original_prepare
    return results

if __name__ == "__main__":
    benchmark_monte_carlo()
    benchmark_ragnarok()
