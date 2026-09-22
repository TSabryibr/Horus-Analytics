from core.settings import settings
import database
from playhouse.migrate import *
import traceback

def migrate():
    print("Migrating Database for Multi-Portfolio Cash Support...")
    try:
        database.initialize_db()
        db = database.real_db
        migrator = SqliteMigrator(db)

        # 1. Add Columns if they don't exist
        try:
            cash_egp_field = FloatField(default=0.0)
            cash_usd_field = FloatField(default=0.0)
            
            # Check if columns exist
            columns = [c.name for c in db.get_columns('portfolio')]
            print(f"Current columns: {columns}")
            
            if 'cash_egp' not in columns:
                print("Adding cash_egp column...")
                try:
                    migrator.add_column('portfolio', 'cash_egp', cash_egp_field).run()
                except Exception as e:
                    print(f"Error adding cash_egp: {e}")
                
            if 'cash_usd' not in columns:
                print("Adding cash_usd column...")
                try:
                    migrator.add_column('portfolio', 'cash_usd', cash_usd_field).run()
                except Exception as e:
                    print(f"Error adding cash_usd: {e}")
                
            print("Schema check complete.")

        except Exception as e:
            print(f"Schema Migration Error: {e}")
            traceback.print_exc()

        # 2. Migrate Data
        print("Migrating Cash Data...")
        try:
            # Ensure a USER portfolio exists
            default_portfolio = database.Portfolio.get_or_none(type="USER")
            if not default_portfolio:
                print("Creating default User Portfolio...")
                default_portfolio = database.Portfolio.create(name="My Portfolio", type="USER")
            
            if default_portfolio.cash_egp == 0 and settings.ACCOUNT_BALANCE > 0:
                print(f"Transferring {settings.ACCOUNT_BALANCE} EGP from GlobalSettings to Portfolio {default_portfolio.id}")
                default_portfolio.cash_egp = settings.ACCOUNT_BALANCE
            
            if default_portfolio.cash_usd == 0 and settings.ACCOUNT_BALANCE_USD > 0:
                print(f"Transferring {settings.ACCOUNT_BALANCE_USD} USD from GlobalSettings to Portfolio {default_portfolio.id}")
                default_portfolio.cash_usd = settings.ACCOUNT_BALANCE_USD
                
            default_portfolio.save()
            
            # 3. Ensure System Portfolios
            sys_portfolios = database.Portfolio.select().where(database.Portfolio.type == 'SYSTEM')
            for p in sys_portfolios:
                if p.cash_egp == 0:
                    p.cash_egp = 1000000 
                    p.save()
                    print(f"Seeded System Portfolio '{p.name}' with 1M EGP")

            print("Migration Complete.")
            
        except Exception as e:
             print(f"Data Migration Error: {e}")
             traceback.print_exc()

    except Exception as e:
        print(f"Critical Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    migrate()
