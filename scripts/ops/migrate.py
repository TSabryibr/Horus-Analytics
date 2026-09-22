from peewee_migrate import Router
from peewee import SqliteDatabase
from database import db, real_db, Portfolio, Position, Trade, Signal

# Ensure migration directory exists
MIGRATION_DIR = 'migrations'

def run_migrations():
    """
    Run database migrations.
    """
    # Initialize the router with the database and migration directory
    router = Router(real_db, migrate_dir=MIGRATION_DIR)

    # Convert database proxy to real connection for router
    # Note: Router expects a direct database instance
    
    # Create tables if they don't exist (legacy support)
    real_db.connect(reuse_if_open=True)
    real_db.create_tables([Portfolio, Position, Trade, Signal], safe=True)
    real_db.close()

    print("Checking for migrations...")
    
    # Run migrations
    router.run()
    
    print("Migrations complete.")

def create_migration(name="initial"):
    """
    Create a new migration based on changes in models.
    """
    router = Router(real_db, migrate_dir=MIGRATION_DIR)
    
    print(f"Creating migration: {name}")
    router.create(name, auto=[Portfolio, Position, Trade, Signal])
    print(f"Migration '{name}' created in {MIGRATION_DIR}/")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create":
            name = sys.argv[2] if len(sys.argv) > 2 else "auto_update"
            create_migration(name)
        elif command == "run":
            run_migrations()
        else:
            print("Usage: python migrate.py [create <name> | run]")
    else:
        run_migrations()
