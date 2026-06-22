import sqlite3
from datetime import datetime

DB_PATH = "tickets.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            service_affected TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_ticket(title, severity, service_affected, description):
    conn = get_connection()
    conn.execute(
        "INSERT INTO incidents (title, severity, service_affected, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, severity, service_affected, description, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_tickets():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_by_id(ticket_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()
