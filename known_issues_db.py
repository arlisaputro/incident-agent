import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "known_issues.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS known_issues (
            issue_id TEXT PRIMARY KEY,
            service_name TEXT NOT NULL,
            title TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            resolution TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_service ON known_issues(service_name)")
    conn.commit()
    conn.close()


def seed_known_issues():
    """Seed sample known issues if table is empty."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM known_issues").fetchone()[0]
    if count == 0:
        sample_data = [
            (
                "KI-001",
                "payment-service",
                "Payment timeout during peak hours",
                "Connection pool exhaustion on DB",
                "Increase max pool size to 50 and add circuit breaker",
            ),
            (
                "KI-002",
                "api-gateway",
                "5xx spike after deployment",
                "Memory leak in new release v2.3.1",
                "Rollback to v2.3.0 and fix memory allocation in handler",
            ),
            (
                "KI-003",
                "payment-service",
                "Duplicate transactions during retry",
                "Missing idempotency key in payment flow",
                "Add idempotency_key check + Redis distributed lock",
            ),
            (
                "KI-004",
                "api-gateway",
                "Authentication failures (401/403)",
                "JWT secret rotation broke token validation",
                "Sync new secret to all gateway instances, clear CDN cache",
            ),
        ]
        conn.executemany(
            "INSERT INTO known_issues (issue_id, service_name, title, root_cause, resolution) VALUES (?, ?, ?, ?, ?)",
            sample_data,
        )
        conn.commit()
    conn.close()


def get_known_issues_by_service(service_name):
    """Retrieve known issues for a specific service."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM known_issues WHERE service_name = ?", (service_name,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_known_issues():
    """Retrieve all known issues."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM known_issues ORDER BY service_name").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_known_issue(issue_id, service_name, title, root_cause, resolution):
    """Add a new known issue."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO known_issues (issue_id, service_name, title, root_cause, resolution) VALUES (?, ?, ?, ?, ?)",
        (issue_id, service_name, title, root_cause, resolution),
    )
    conn.commit()
    conn.close()


# Initialize on import
init_db()
seed_known_issues()
