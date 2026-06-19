# SOP: Incident Management Process

## Severity Definitions

| Severity | Impact | Response Time | Resolution Target |
|----------|--------|---------------|-------------------|
| Critical | Full service outage, data loss | 5 min | 1 hour |
| High | Major feature degraded, >10% users affected | 15 min | 4 hours |
| Medium | Minor feature impacted, workaround available | 30 min | 24 hours |
| Low | Cosmetic issue, no user impact | 4 hours | 1 week |

## Incident Response Steps

### 1. Detection & Triage
- Alert received from monitoring (Datadog/CloudWatch)
- On-call engineer acknowledges within response time SLA
- Initial severity assessment based on impact scope

### 2. Communication
- Critical/High: Notify stakeholders via Slack #incidents channel
- Create incident ticket with title, severity, affected service
- Post status update every 30 minutes for Critical, 1 hour for High

### 3. Investigation
- Check recent deployments (last 2 hours)
- Review dashboards: error rate, latency, CPU/memory
- Check dependent services health
- Review application logs for exceptions

### 4. Mitigation
- If deploy-related: immediate rollback
- If traffic-related: scale up / enable rate limiting
- If dependency-related: enable circuit breaker / failover
- If data-related: stop writes, assess damage scope

### 5. Resolution & Recovery
- Confirm metrics back to normal
- Run smoke tests on affected features
- Remove any temporary mitigations
- Update incident ticket status to Resolved

### 6. Post-Mortem (within 48 hours)
- Timeline of events
- Root cause analysis
- What went well / what went wrong
- Action items to prevent recurrence
- Share with team for learning
