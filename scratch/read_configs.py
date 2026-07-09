import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'vagasync.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM configs")
rows = cursor.fetchall()

print("--- Configs ---")
for key, value in rows:
    if key == 'resume_text':
        print(f"key: {key}, length: {len(value) if value else 0}")
        print(f"preview: {value[:100] if value else 'None'}")
    else:
        print(f"key: {key}, value: {value}")

conn.close()
