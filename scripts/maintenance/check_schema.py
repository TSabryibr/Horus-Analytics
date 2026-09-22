import sqlite3
import os

db_path = r"c:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\horus.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

print("\n--- Columns in signal ---")
try:
    cursor.execute("PRAGMA table_info(signal)")
    print(cursor.fetchall())
except:
    print("No signal table")

conn.close()
