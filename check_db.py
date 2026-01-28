import sqlite3
import os

DB_NAME = 'ats.db'

def check_db():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found!")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # List tables
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # Check activity_logs columns
    try:
        cols = c.execute("PRAGMA table_info(activity_logs);").fetchall()
        print("activity_logs columns:", [col[1] for col in cols])
    except Exception as e:
        print(f"Error checking activity_logs: {e}")

    conn.close()

if __name__ == "__main__":
    check_db()
