import sqlite3
import os

db_path = r"c:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\horus.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Signals in Database for Today (2026-03-15) ---")
# Use '2026-03-15' literal or strftime
cursor.execute("""
    SELECT timestamp, ticker, score, source 
    FROM signal 
    WHERE date = '2026-03-15'
    ORDER BY timestamp DESC
""")

for row in cursor.fetchall():
    print(row)

conn.close()
