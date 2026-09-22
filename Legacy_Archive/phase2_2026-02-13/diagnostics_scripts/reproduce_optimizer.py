
from core.simulation import Optimizer
import multiprocessing
import time

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("Running reproduction script for Optimizer...")
    
    # Patch PARAM_GRID to be small
    Optimizer.PARAM_GRID = {
        'VOL_SPIKE': [1.5],
        'MOMENTUM': [1.0],
        'RSI_MIN': [40], 
        'RSI_MAX': [80],
        'SL_PCT': [2.0],
        'TP1_PCT': [5.0], 
        'LOOKBACK': [30]
    }
    print("Patched PARAM_GRID for speed.")

    try:
        progress = {}
        print("Calling run_optimization_api...")
        # running for EGX30 to be faster
        results = Optimizer.run_optimization_api("EGX30", progress)
        
        print("\nOptimization finished.")
        print(f"Status: {progress.get('status')}")
        print(f"Error: {progress.get('error')}")
        print(f"Results found: {len(results)}")
        
        if results:
            print("Top Result:", results[0])
            
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
