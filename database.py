import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "incident_agent")
DB_USER = os.getenv("DB_USER", "incident_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            service_affected TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def create_ticket(title, severity, service_affected, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO incidents (title, severity, service_affected, description, created_at) VALUES (%s, %s, %s, %s, %s)",
        (title, severity, service_affected, description, datetime.now()),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_all_tickets():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM incidents ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_ticket_by_id(ticket_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM incidents WHERE id = %s", (ticket_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


init_db()
