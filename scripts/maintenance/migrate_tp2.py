import os
import sys

sys.path.append(os.getcwd())

from peewee import *
from playhouse.migrate import *
import database

def migrate_db():
    print(f"Migrating database: {database.DB_FILE}")
    migrator = SqliteMigrator(database.real_db)

    # Define new fields
    target_price_2_field = FloatField(null=True)
    tp1_hit_field = BooleanField(default=False)

    try:
        migrate(
            migrator.add_column('position', 'target_price_2', target_price_2_field),
            migrator.add_column('position', 'tp1_hit', tp1_hit_field)
        )
        print("✅ Migration successful: Added target_price_2 and tp1_hit to Position table.")
    except Exception as e:
        print(f"⚠️ Migration failed or already applied: {e}")

if __name__ == "__main__":
    database.real_db.connect()
    migrate_db()
    database.real_db.close()
