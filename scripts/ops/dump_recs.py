
import sys
import os

# Add the project root to sys.path
sys.path.append(r'c:\Users\TSabr\Horus\Horus-Analytics-II')

from database import SignalRecommendation, SignalRun, db, initialize_db

def dump_recs():
    # Initialize DB (Sqlite)
    initialize_db()
    
    latest_run = (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
        .first()
    )
    
    if not latest_run:
        print("No completed runs found.")
        return

    print(f"Latest Run: {latest_run.run_date} {latest_run.completed_at} (ID: {latest_run.id})")
    
    recs = (
        SignalRecommendation.select()
        .where(SignalRecommendation.run == latest_run)
        .order_by(SignalRecommendation.score.desc())
    )
    
    print(f"{'Ticker':<10} | {'Side':<5} | {'Entry':<10} | {'Stop':<10} | {'Target':<10} | {'Score':<5}")
    print("-" * 60)
    for rec in recs:
        print(f"{rec.ticker:<10} | {rec.side:<5} | {rec.entry_price:<10} | {rec.stop_loss:<10} | {rec.target_price:<10} | {rec.score:<5}")

if __name__ == "__main__":
    dump_recs()
