import os
from pyinstrument import Profiler
from data_engine.ingest_history import ingest_history
from data_engine.ingest_intraday import ingest_intraday
import database

def main():
    database.initialize_db()
    # Force sync
    os.environ["FORCE_BOOTSTRAP_SYNC"] = "1"
    
    profiler = Profiler(interval=0.001)
    print("Starting serial ingestion profile...")
    profiler.start()
    
    try:
        print("Starting ingest_intraday...")
        ingest_intraday("MUBASHER_DB")
        print("Starting ingest_history...")
        ingest_history("MUBASHER_DB", force_recent_days=-1)
    except Exception as e:
        print(f"Error during ingestion: {e}")
        
    profiler.stop()
    
    print(profiler.output_text(unicode=True, color=False))
    
    with open("sync_profile.txt", "w", encoding="utf-8") as f:
        f.write(profiler.output_text(unicode=True, color=False))
    print("Profile written to sync_profile.txt")

if __name__ == "__main__":
    main()
