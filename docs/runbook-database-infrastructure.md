# Runbook: Database & Infrastructure Incident Response

## Service Overview
Core infrastructure services including PostgreSQL databases, Redis cache, message queues (SQS/RabbitMQ), and container orchestration (ECS/EKS).

## Common Issues

### 1. Database Connection Pool Exhaustion
**Symptoms:** Application logs show "too many connections", response time > 10s, new requests failing
**Root Cause:** Long-running queries holding connections, connection leak in application code, sudden traffic spike
**Investigation:**
- Check active connections: `SELECT count(*), state FROM pg_stat_activity GROUP BY state;`
- Find long-running queries: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;`
- Check connection pool metrics in Datadog: `postgresql.connections.active`
**Resolution:**
- Kill long-running queries: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '5 minutes';`
- Increase pool size: update `max_connections` in `postgresql.conf` (default 100 → 200)
- Restart application to release leaked connections
- Add PgBouncer as connection pooler for long-term fix
**Prevention:**
- Set statement_timeout to 30s for application queries
- Implement connection pool monitoring alert (threshold: 80% usage)
- Add health check endpoint that validates DB connectivity

### 2. Redis Cache Failure / High Memory
**Symptoms:** Cache miss rate spike, application latency increase, Redis returning OOM errors
**Root Cause:** Memory limit reached, large key accumulation, missing TTL on cached objects
**Investigation:**
- Check memory: `redis-cli info memory`
- Find large keys: `redis-cli --bigkeys`
- Check eviction policy: `redis-cli config get maxmemory-policy`
**Resolution:**
- Immediate: flush expired keys `redis-cli MEMORY PURGE`
- If OOM: increase `maxmemory` or scale to larger instance
- Identify and remove large unused keys
- Set TTL on all cached objects (default: 1 hour)
**Prevention:**
- Alert on memory usage > 75%
- Implement cache warming strategy
- Use Redis Cluster for horizontal scaling
- Set `maxmemory-policy allkeys-lru` for auto-eviction

### 3. Message Queue Backlog (SQS/RabbitMQ)
**Symptoms:** Message age increasing, consumers lagging, downstream services delayed
**Root Cause:** Consumer crash/restart, processing bottleneck, sudden producer spike
**Investigation:**
- Check queue depth: `aws sqs get-queue-attributes --queue-url <URL> --attribute-names ApproximateNumberOfMessages`
- Check consumer health and processing rate
- Review Dead Letter Queue (DLQ) for failed messages
**Resolution:**
- Scale up consumers (increase ECS task count)
- If consumer crashed: restart and monitor
- If DLQ filling up: investigate poison messages, fix and replay
- Temporarily increase visibility timeout if processing is slow
**Prevention:**
- Auto-scaling policy based on queue depth (target: < 1000 messages)
- Alert on message age > 5 minutes
- Implement circuit breaker between producer and consumer
- DLQ alarm with redrive policy

### 4. Disk Space Full (EC2/EBS)
**Symptoms:** Application write failures, "No space left on device" errors, service crash
**Root Cause:** Log rotation not configured, large dump files, DB WAL accumulation
**Investigation:**
- Check disk usage: `df -h`
- Find large files: `du -sh /* | sort -rh | head -20`
- Check log directory: `du -sh /var/log/*`
**Resolution:**
- Delete old logs: `find /var/log -name "*.gz" -mtime +7 -delete`
- Truncate large log files: `truncate -s 0 /var/log/application.log`
- If DB WAL: run checkpoint `SELECT pg_switch_wal();` and archive
- Extend EBS volume if needed (online resize supported)
**Prevention:**
- Configure logrotate (max 7 days, compress, 500MB max)
- Alert on disk usage > 80%
- Use CloudWatch agent for disk monitoring
- Schedule cron job for cleanup: `0 2 * * * find /tmp -mtime +3 -delete`

### 5. Container OOMKilled (ECS/EKS)
**Symptoms:** Container restart loop, ECS task stopping with "OutOfMemory", application unresponsive
**Root Cause:** Memory leak in application, undersized memory limit, large request payload
**Investigation:**
- Check ECS events: `aws ecs describe-services --cluster <cluster> --services <service>`
- Review container metrics: memory usage over time in Datadog
- Check application heap dump if Java: `-XX:+HeapDumpOnOutOfMemoryError`
**Resolution:**
- Immediate: increase task memory limit (e.g., 512MB → 1024MB)
- Restart task: `aws ecs update-service --force-new-deployment`
- If memory leak: identify and fix in code, deploy hotfix
- Add memory-based auto-scaling
**Prevention:**
- Set memory reservation at 75% of limit (soft limit)
- Alert on memory usage > 85% of limit
- Regular load testing to identify memory growth patterns
- Use `-XX:MaxRAMPercentage=75` for Java containers

## Escalation Path
1. L1: On-call SRE → restart services, scale up, basic troubleshooting
2. L2: Platform Engineering → infrastructure changes, capacity planning
3. L3: Database Admin / Architect → schema changes, major infrastructure decisions

## Key Metrics to Monitor
| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| DB Connection Pool | 70% used | 90% used |
| Redis Memory | 75% of max | 90% of max |
| Queue Depth | > 1000 messages | > 10000 messages |
| Disk Usage | 80% | 95% |
| Container Memory | 85% of limit | 95% of limit |
| DB Query Duration P99 | > 1s | > 5s |
