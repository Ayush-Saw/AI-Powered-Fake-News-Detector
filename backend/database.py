import sqlite3
from .config import DB_PATH

def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS analyses (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, article_text TEXT NOT NULL,
          prediction TEXT NOT NULL, confidence REAL, language TEXT, translated INTEGER DEFAULT 0,
          explanation TEXT, source TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, user_id INTEGER)''')
        # Safe migration for databases created by earlier project versions.
        columns = {r[1] for r in db.execute("PRAGMA table_info(analyses)").fetchall()}
        if "user_id" not in columns:
            db.execute("ALTER TABLE analyses ADD COLUMN user_id INTEGER")
        db.execute('''CREATE TABLE IF NOT EXISTS feedback (
          id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_id INTEGER, feedback_type TEXT,
          details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

def create_user(name, email, password_hash, role="user"):
    with connect() as db:
        cur = db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                         (name, email.lower().strip(), password_hash, role))
        return cur.lastrowid

def get_user_by_email(email):
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None

def get_user(user_id):
    with connect() as db:
        row = db.execute("SELECT id,name,email,role,created_at FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

def list_users(limit=500):
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()]

def save_analysis(title, text, prediction, confidence, language, translated, explanation, source="", user_id=None):
    with connect() as db:
        cur = db.execute("INSERT INTO analyses(title,article_text,prediction,confidence,language,translated,explanation,source,user_id) VALUES(?,?,?,?,?,?,?,?,?)",
          (title, text, prediction, confidence, language, int(translated), explanation, source, user_id))
        return cur.lastrowid

def get_analysis(aid):
    with connect() as db:
        row = db.execute("SELECT * FROM analyses WHERE id=?", (aid,)).fetchone()
        return dict(row) if row else None

def list_analyses(limit=200):
    with connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()]

def list_user_analyses(user_id, limit=200):
    with connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT ?", (int(user_id), int(limit))).fetchall()]

def delete_analysis(aid):
    with connect() as db:
        db.execute("DELETE FROM feedback WHERE analysis_id=?", (aid,))
        db.execute("DELETE FROM analyses WHERE id=?", (aid,))

def add_feedback(aid, kind, details):
    with connect() as db:
        db.execute("INSERT INTO feedback(analysis_id,feedback_type,details) VALUES(?,?,?)", (aid,kind,details))

def dashboard_stats():
    with connect() as db:
        users = db.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
        analyses = db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        fake = db.execute("SELECT COUNT(*) FROM analyses WHERE prediction='Likely Fake'").fetchone()[0]
        real = db.execute("SELECT COUNT(*) FROM analyses WHERE prediction='Likely Real'").fetchone()[0]
        feedback = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        return {"users": users, "analyses": analyses, "fake": fake, "real": real, "feedback": feedback}
