import sqlite3
import os
import hashlib
import base64
from cryptography.fernet import Fernet

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
KEY_PATH = os.path.join(os.path.dirname(__file__), ".secret.key")

def get_key():
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    return key

fernet = Fernet(get_key())

def _decrypt_db():
    if not os.path.exists(DB_PATH):
        return
    with open(DB_PATH, "rb") as f:
        encrypted = f.read()
    if not encrypted:
        return
    try:
        decrypted = fernet.decrypt(encrypted)
        with open(DB_PATH, "wb") as f:
            f.write(decrypted)
    except Exception:
        pass

def _encrypt_db():
    if not os.path.exists(DB_PATH):
        return
    with open(DB_PATH, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(DB_PATH, "wb") as f:
        f.write(encrypted)

def get_db():
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    conn.close()
    _encrypt_db()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verified (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER NOT NULL UNIQUE,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    _encrypt_db()

def add_code(username, code):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO codes (username, code) VALUES (?, ?)", (username, code))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
        _encrypt_db()

def check_code(code):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM codes WHERE code = ? AND used = 0", (code,)).fetchone()
    if row:
        conn.execute("UPDATE codes SET used = 1 WHERE code = ?", (code,))
        conn.commit()
        result = dict(row)
        conn.close()
        _encrypt_db()
        return result
    conn.close()
    _encrypt_db()
    return None

def verify_user(uid, username, password):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT OR REPLACE INTO verified (uid, username, password) VALUES (?, ?, ?)",
                    (uid, username, hash_pw(password)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
        _encrypt_db()

def check_login(username, password):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM verified WHERE username = ? AND password = ?",
                     (username, hash_pw(password))).fetchone()
    conn.close()
    _encrypt_db()
    return row is not None

def is_verified(uid):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM verified WHERE uid = ?", (uid,)).fetchone()
    conn.close()
    _encrypt_db()
    return row is not None

def get_verified_user(username):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM verified WHERE username = ?", (username,)).fetchone()
    conn.close()
    _encrypt_db()
    return dict(row) if row else None

def unverify_user(uid):
    _decrypt_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM verified WHERE uid = ?", (uid,))
    conn.commit()
    conn.close()
    _encrypt_db()

if __name__ == "__main__":
    init_db()
    print("Database initialized and encrypted.")
