import sqlite3
from pathlib import Path

DB_PATH = Path("data/mediassist_data/db/mediassist.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("TABLES:")
for table in tables:
    print("-", table[0])

print("\nSCHEMA DETAILS:")
for table in tables:
    table_name = table[0]
    print("\n" + "=" * 80)
    print(table_name)
    print("=" * 80)

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    for col in columns:
        print(col)

    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cursor.fetchall()

    print("\nSample rows:")
    for row in rows:
        print(row)

conn.close()