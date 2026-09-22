
from peewee import *
from playhouse.migrate import *
import database
from database import Portfolio, Position, Trade

db = database.db
migrator = SqliteMigrator(db)

def run_migration():
    print("🔄 Starting Database Migration (V2: Multi-Portfolio)...")
    
    # 1. Create Portfolio Table
    db.connect()
    db.create_tables([Portfolio], safe=True)
    print("✅ Created Portfolio Table")
    
    # 2. Add System Portfolios
    daily_port, created = Portfolio.get_or_create(
        name="Daily Simulation",
        defaults={
            "type": "SYSTEM",
            "auto_manage": True,
            "description": "Auto-trading based on Daily Signals"
        }
    )
    
    intraday_port, created = Portfolio.get_or_create(
        name="Intraday Simulation",
        defaults={
            "type": "SYSTEM",
            "auto_manage": True,
            "description": "Auto-trading based on Intraday Signals"
        }
    )
    print(f"✅ Verified System Portfolios: IDs {daily_port.id}, {intraday_port.id}")
    
    # 3. Migrate Existing Positions/Trades
    # Add 'portfolio_id' column if missing
    try:
        with db.atomic():
            # Check if column exists by inspecting
            columns = [c.name for c in db.get_columns('position')]
            if 'portfolio_id' not in columns:
                print("🛠️ Adding portfolio_id to Position table (Raw SQL)...")
                # SQLite doesn't support adding FK constraint easily in one go, so adding as INTEGER first
                db.execute_sql("ALTER TABLE position ADD COLUMN portfolio_id INTEGER DEFAULT 1")
                print("✅ Added portfolio_id to Position")
                
            columns_trade = [c.name for c in db.get_columns('trade')]
            if 'portfolio_id' not in columns_trade:
                print("🛠️ Adding portfolio_id to Trade table (Raw SQL)...")
                db.execute_sql("ALTER TABLE trade ADD COLUMN portfolio_id INTEGER DEFAULT 1")
                print("✅ Added portfolio_id to Trade")
                
        print("✅ Migration Complete: All existing records assigned to 'Daily Simulation'")
        
    except Exception as e:
        print(f"❌ Migration Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
