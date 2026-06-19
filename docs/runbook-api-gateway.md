# Runbook: API Gateway Incident Response

## Service Overview
API Gateway is the main entry point for all microservices. It handles routing, rate limiting, authentication, and request transformation.

## Common Issues

### 1. 5xx Spike (Internal Server Error)
**Symptoms:** Sudden increase in 500/502/503 errors, elevated latency
**Root Cause:** Backend service crash, memory leak, or deployment rollback needed
**Resolution:**
- Check which backend is returning errors: review access logs
- Verify recent deployments: `kubectl rollout history deployment/api-gateway`
- Rollback if recent deploy: `kubectl rollout undo deployment/api-gateway`
- Check memory/CPU usage on backend pods
- Increase replica count if load-related

### 2. Rate Limiting Triggered (429 Too Many Requests)
**Symptoms:** Customers receiving 429 responses, API calls blocked
**Root Cause:** Traffic spike, misconfigured rate limits, or DDoS attempt
**Resolution:**
- Check rate limit dashboard for spike source (IP/API key)
- If legitimate traffic: temporarily increase rate limit threshold
- If DDoS: enable WAF rules, block offending IPs
- Notify affected customers if false positive

### 3. Authentication Failures (401/403)
**Symptoms:** Valid users getting unauthorized errors
**Root Cause:** Token service down, JWT secret rotation issue, CORS misconfiguration
**Resolution:**
- Verify token service health: `curl -s http://auth-service/health`
- Check if JWT secrets were recently rotated
- Verify CORS allowed origins in gateway config
- Clear CDN cache if stale auth responses cached

## SLA Requirements
- Availability: 99.95%
- P99 latency: < 200ms
- Max error rate: < 0.1%
