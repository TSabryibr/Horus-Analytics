import sqlite3
import os

db_path = r"c:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\horus.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- All Signals (Latest 20) ---")
cursor.execute("""
    SELECT * 
    FROM signal 
    ORDER BY timestamp DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(row)

conn.close()
