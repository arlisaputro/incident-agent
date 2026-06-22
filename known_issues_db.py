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
            # Payment Service
            (
                "KI-001",
                "payment-service",
                "Payment timeout during peak hours",
                "Connection pool exhaustion on DB due to long-running queries and high concurrent requests",
                "Increase max pool size from 25 to 50, enable circuit breaker with 10s timeout, add PgBouncer as connection pooler",
            ),
            (
                "KI-002",
                "payment-service",
                "Duplicate transactions during retry",
                "Missing idempotency key in payment flow causing double-charge on network timeout retry",
                "Add idempotency_key check on all payment endpoints, implement Redis distributed lock for critical operations",
            ),
            (
                "KI-003",
                "payment-service",
                "Payment gateway integration failure",
                "Third-party payment gateway SSL certificate expired causing TLS handshake failure",
                "Failover to backup payment provider, monitor cert expiry with alert 30 days before, enable retry with exponential backoff",
            ),
            # API Gateway
            (
                "KI-004",
                "api-gateway",
                "5xx spike after deployment",
                "Memory leak in new release v2.3.1 causing OOM after 2 hours under load",
                "Rollback to v2.3.0, fix memory allocation in request handler, add memory-based auto-scaling",
            ),
            (
                "KI-005",
                "api-gateway",
                "Authentication failures (401/403)",
                "JWT secret rotation broke token validation on 2 of 5 gateway instances due to stale config",
                "Sync new JWT secret to all instances via config reload, clear CDN cache, verify with rolling restart",
            ),
            (
                "KI-006",
                "api-gateway",
                "Rate limiting false positives",
                "Rate limit counter not resetting due to Redis cluster failover, all requests counted against stale bucket",
                "Restart rate limit service, flush stale counters, switch to sliding window algorithm",
            ),
            # Database
            (
                "KI-007",
                "database",
                "PostgreSQL connection pool exhausted",
                "Application code not releasing connections after transaction timeout, causing pool drain under load",
                "Set statement_timeout=30s, add connection leak detection, implement PgBouncer with max_client_conn=200",
            ),
            (
                "KI-008",
                "database",
                "Slow queries causing cascade failure",
                "Missing index on orders.created_at column causing full table scan on reporting queries",
                "Add index: CREATE INDEX idx_orders_created ON orders(created_at), separate OLTP and OLAP workloads",
            ),
            # Redis / Cache
            (
                "KI-009",
                "redis-cache",
                "Redis OOM causing cache miss spike",
                "Large session objects stored without TTL, memory grew to 100% over 2 weeks",
                "Set maxmemory-policy allkeys-lru, add TTL (1h) to all cached objects, alert on memory > 75%",
            ),
            (
                "KI-010",
                "redis-cache",
                "Cache stampede after Redis restart",
                "All cache expired simultaneously after restart, causing thundering herd to database",
                "Implement cache warming on startup, add jitter to TTL values, use lock-based cache rebuild",
            ),
            # User Service
            (
                "KI-011",
                "user-service",
                "Login failures spike",
                "Auth0 rate limit hit due to brute force attack on multiple accounts",
                "Enable IP-based rate limiting on login endpoint, add CAPTCHA after 3 failed attempts, block offending IPs via WAF",
            ),
            # Notification Service
            (
                "KI-012",
                "notification-service",
                "Email delivery delays > 30 minutes",
                "SQS queue backlog due to SES throttling (sending rate exceeded)",
                "Increase SES sending quota, scale consumers, implement priority queue for critical notifications",
            ),
            # Infrastructure
            (
                "KI-013",
                "infrastructure",
                "ECS tasks OOMKilled in production",
                "Java application memory leak in HTTP client connection pool not closing idle connections",
                "Increase task memory to 1024MB, fix connection pool config (maxIdleTime=60s), add -XX:MaxRAMPercentage=75",
            ),
            (
                "KI-014",
                "infrastructure",
                "Disk space full on application server",
                "Log rotation not configured, application.log grew to 50GB in 2 weeks",
                "Configure logrotate (7 days, compress, 500MB max), clean old logs, alert on disk > 80%",
            ),
            # Order Service
            (
                "KI-015",
                "order-service",
                "Order processing stuck in pending state",
                "Dead letter queue filling up due to schema mismatch after payment-service API change",
                "Fix message schema to match new API, replay DLQ messages, add schema validation on producer side",
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
