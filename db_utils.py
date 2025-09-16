from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("logs.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    time_utc TEXT NOT NULL,
    action TEXT NOT NULL
);
"""

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db() -> None:
    conn = _get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()

def log_user_action(user_id: int, username: str | None, action: str) -> None:
    """
    Пишем в таблицу logs. Время — UTC в ISO 8601.
    """
    iso_utc = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO logs (user_id, username, time_utc, action) VALUES (?,?,?,?)",
            (user_id, username, iso_utc, action),
        )
        conn.commit()
    finally:
        conn.close()