# Runbook: Payment Service Incident Response

## Service Overview
Payment service handles all transaction processing including credit card, bank transfer, and e-wallet payments.

## Common Issues

### 1. Payment Timeout (5xx errors)
**Symptoms:** High latency > 5s, HTTP 504 responses, transaction failures
**Root Cause:** Database connection pool exhaustion during peak traffic
**Resolution:**
- Check DB connection pool usage: `SELECT count(*) FROM pg_stat_activity;`
- Increase max pool size from 25 to 50 in config
- Enable circuit breaker if DB is unresponsive > 10s
- Scale read replicas if query load is high

### 2. Payment Gateway Integration Failure
**Symptoms:** HTTP 502 from upstream, payment provider errors
**Root Cause:** Third-party payment gateway downtime or certificate expiry
**Resolution:**
- Check payment gateway status page
- Verify SSL certificates: `openssl s_client -connect gateway.example.com:443`
- Failover to backup payment provider
- Enable retry with exponential backoff (max 3 retries)

### 3. Duplicate Transaction
**Symptoms:** Customer charged multiple times, duplicate records in DB
**Root Cause:** Missing idempotency key, retry without dedup check
**Resolution:**
- Verify idempotency_key is set on all API calls
- Check for race conditions in concurrent requests
- Run dedup query and refund duplicates
- Add distributed lock (Redis) for critical payment operations

## Escalation Path
1. L1: On-call SRE → restart service, check dashboards
2. L2: Payment team lead → investigate code/config
3. L3: VP Engineering → customer communication, major incident
