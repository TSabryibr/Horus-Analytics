import duckdb
import pandas as pd

f = r"C:\Antigravity Projects\Horus Analytics II\data\EGX\history\EGX30.parquet"
db = duckdb.connect(database=':memory:')

print(f"Inspecting File: {f}")
try:
    cols = db.execute(f"DESCRIBE SELECT * FROM read_parquet('{f.replace('\\', '/')}')").df()
    print("Columns found:")
    print(cols[['column_name', 'column_type']])
    
    print("\nFirst 5 rows:")
    df = db.execute(f"SELECT * FROM read_parquet('{f.replace('\\', '/')}') LIMIT 5").df()
    print(df)
    
except Exception as e:
    print(f"FAILED to inspect with DuckDB: {e}")
