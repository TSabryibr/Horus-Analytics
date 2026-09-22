from peewee import *
import database

db = database.real_db

def run_migration():
    print("🔄 Starting Database Migration (V3: Missing Schema Updates)...")
    db.connect(reuse_if_open=True)

    try:
        with db.atomic():
            columns_pos = [c.name for c in db.get_columns('position')]
            if 'slippage_bps' not in columns_pos:
                print("🛠️ Adding slippage_bps to Position table...")
                db.execute_sql("ALTER TABLE position ADD COLUMN slippage_bps REAL DEFAULT NULL")
            if 'execution_latency_ms' not in columns_pos:
                print("🛠️ Adding execution_latency_ms to Position table...")
                db.execute_sql("ALTER TABLE position ADD COLUMN execution_latency_ms INTEGER DEFAULT NULL")

            columns_trade = [c.name for c in db.get_columns('trade')]
            if 'slippage_bps' not in columns_trade:
                print("🛠️ Adding slippage_bps to Trade table...")
                db.execute_sql("ALTER TABLE trade ADD COLUMN slippage_bps REAL DEFAULT NULL")
            if 'execution_latency_ms' not in columns_trade:
                print("🛠️ Adding execution_latency_ms to Trade table...")
                db.execute_sql("ALTER TABLE trade ADD COLUMN execution_latency_ms INTEGER DEFAULT NULL")

            columns_signal = [c.name for c in db.get_columns('signal')]
            if 'rationale' not in columns_signal:
                print("🛠️ Adding rationale to Signal table...")
                db.execute_sql("ALTER TABLE signal ADD COLUMN rationale TEXT DEFAULT NULL")

        print("✅ Migration V3 Complete.")
    except Exception as e:
        print(f"❌ Migration Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
