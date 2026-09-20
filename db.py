import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used INTEGER DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS verified (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER NOT NULL UNIQUE,
            username TEXT NOT NULL,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    db.close()

def add_code(username, code):
    db = get_db()
    try:
        db.execute("INSERT INTO codes (username, code) VALUES (?, ?)", (username, code))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        db.close()

def check_code(code):
    db = get_db()
    row = db.execute("SELECT * FROM codes WHERE code = ? AND used = 0", (code,)).fetchone()
    if row:
        db.execute("UPDATE codes SET used = 1 WHERE code = ?", (code,))
        db.commit()
        result = dict(row)
        db.close()
        return result
    db.close()
    return None

def verify_user(uid, username):
    db = get_db()
    try:
        db.execute("INSERT OR REPLACE INTO verified (uid, username) VALUES (?, ?)", (uid, username))
        db.commit()
        return True
    except Exception:
        return False
    finally:
        db.close()

def is_verified(uid):
    db = get_db()
    row = db.execute("SELECT * FROM verified WHERE uid = ?", (uid,)).fetchone()
    db.close()
    return row is not None

def get_verified_user(username):
    db = get_db()
    row = db.execute("SELECT * FROM verified WHERE username = ?", (username,)).fetchone()
    db.close()
    return dict(row) if row else None

def unverify_user(uid):
    db = get_db()
    db.execute("DELETE FROM verified WHERE uid = ?", (uid,))
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
