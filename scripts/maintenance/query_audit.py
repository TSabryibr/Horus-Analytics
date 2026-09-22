import sqlite3
import json
import os
import sys

db_path = r"c:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\horus.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Recent Audit Logs (SIGNAL category) ---")
cursor.execute("""
    SELECT timestamp, category, event, message, metadata 
    FROM auditlog 
    WHERE category = 'SIGNAL' 
    ORDER BY timestamp DESC 
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"[{row[0]}] {row[2]}: {row[3]}")
    if row[4]:
        print(f"   Metadata: {row[4]}")

conn.close()
