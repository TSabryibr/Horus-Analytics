from fastapi.testclient import TestClient
import time
from api import app, scheduler

def main():
    print("\n--- Testing Watchdog Initialization (FastAPI Lifespan) ---")
    
    # Fast forward startup config so it doesn't wait for data syncs:
    import os
    os.environ["SKIP_STARTUP_SYNC"] = "true"
    os.environ["HORUS_DISABLE_STARTUP_THREAD"] = "false"
    
    with TestClient(app) as client:
        print("Waiting for background thread to attach scheduler jobs...")
        time.sleep(10)
        print(f"Jobs currently in scheduler: {[j.id for j in scheduler.get_jobs()]}")
        assert 'market_watchdog' in [j.id for j in scheduler.get_jobs()], "Watchdog job NOT registered!"
        
        watchdog_job = scheduler.get_job('market_watchdog')
        
        print(f"Watchdog Job Found: {watchdog_job}")
        print("Executing watchdog logic manually through APScheduler trigger (simulating 5 minute trick)...")
        
        watchdog_job.func()
        
        print("\nChecking state of heavy jobs:")
        for job_id in ['intraday_scan', 'trade_monitor', 'signal_delivery_retry']:
            job = scheduler.get_job(job_id)
            if job:
                # If next_run_time is None, the job is paused!
                is_paused = job.next_run_time is None
                print(f"Job '{job_id}': Paused={is_paused}")
            else:
                print(f"Job '{job_id}' not found.")
                
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()
