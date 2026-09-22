
from core.simulation import Optimizer
import time
from multiprocessing import Manager, freeze_support

def test_run():
    print("Testing Optimizer Logic directly...")
    
    # Create shared dict
    mgr = Manager()
    progress = mgr.dict()
    progress['status'] = 'IDLE'
    
    # Run in main thread for this test to debug errors visible
    # But Optimizer uses Pool internally, so we must be careful.
    
    try:
        print("Calling Optimizer.run_optimization_api('EGX30')...")
        results = Optimizer.run_optimization_api("EGX30", progress)
        
        print("\n--- RESULTS ---")
        print(f"Status: {progress.get('status')}")
        print(f"Error: {progress.get('error')}")
        print(f"Results Found: {len(results)}")
        
        if results:
            print(f"Top Result Score: {results[0]['score']}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    freeze_support()
    test_run()
