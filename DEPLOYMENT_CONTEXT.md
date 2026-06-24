# Incident Intelligence Agent - Deployment Checkpoint

## Project Overview
- **Project Path:** ~/Documents/hackaton
- **App:** Incident Intelligence Agent (Streamlit + AWS Bedrock + Datadog LLM Observability)
- **AWS Account:** 058914805579, user: participant
- **Region:** ap-southeast-1

## Permissions
- EC2 ✅, S3 ✅, VPC ✅, Bedrock ✅, IAM ❌

## Infrastructure (Terraform - infra/)
- **EC2 IP:** 54.179.171.169
- **Instance:** t3.small, Ubuntu 24.04
- **S3 Bucket:** incident-agent-knowledge-base-6ca579d6
- **Key Pair:** incident-agent-key (PEM di ~/.ssh/incident-agent-key.pem)
- **SSH User:** ubuntu
- **VPC:** 10.0.0.0/16, Public Subnet 10.0.1.0/24
- **EC2 Instance ID:** i-0cff32b8ab809025a

## Access URLs
- **App:** https://54.179.171.169 (port 443, self-signed cert)
- **Doc Preview:** https://54.179.171.169/?doc=docs/FILENAME.md
- **Dashboard:** https://app.datadoghq.com/dashboard/k8i-7tt-mcc/
- **LLM Obs Traces:** https://app.datadoghq.com/llm/traces (filter: ml_app:incident-agent)
- **Monitors:** https://app.datadoghq.com/monitors/manage (filter: service:incident-agent)

## Environment Variables (set saat launch Streamlit)
```
AWS_REGION=ap-southeast-1
BEDROCK_MODEL_ID=apac.amazon.nova-pro-v1:0
DD_API_KEY=62290c5f5f42b43bbe4c57f967fdf89b
DD_APP_KEY=ddapp_cRdtB6dsBxExrkdxjpUvNqPbI7fF0fpOpR
DD_SITE=datadoghq.com
DD_SERVICE=incident-agent
DD_LLMOBS_ML_APP=incident-agent
DD_LLMOBS_AGENTLESS_ENABLED=1
```

## How to Start Streamlit (if need restart)
```bash
ssh -i ~/.ssh/incident-agent-key.pem ubuntu@54.179.171.169

sudo fuser -k 443/tcp 2>/dev/null; sleep 2
cd /home/ubuntu && source ~/venv/bin/activate
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=apac.amazon.nova-pro-v1:0
export DD_API_KEY=62290c5f5f42b43bbe4c57f967fdf89b
export DD_APP_KEY=ddapp_cRdtB6dsBxExrkdxjpUvNqPbI7fF0fpOpR
export DD_SITE=datadoghq.com
export DD_SERVICE=incident-agent
export DD_LLMOBS_ML_APP=incident-agent
export DD_LLMOBS_AGENTLESS_ENABLED=1

nohup sudo -E ~/venv/bin/streamlit run app.py \
  --server.port 443 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.sslCertFile /home/ubuntu/cert.pem \
  --server.sslKeyFile /home/ubuntu/key.pem \
  > /home/ubuntu/streamlit.log 2>&1 &
```

## App Files di EC2 (/home/ubuntu/) — SYNCED WITH LOCAL ✅
- app.py — Streamlit UI + doc preview via query param (?doc=docs/xxx.md)
- bedrock_agent.py — Bedrock Nova Pro + token tracking + _last_context for hallucination
- knowledge_base.py — RAG retrieval (S3 docs with readable names + known issues)
- known_issues_db.py — Local known issues patterns
- database.py — SQLite ticket storage (tickets.db)
- observability.py — LLMObs + hallucination evaluation + DogStatsD metrics + flush
- mcp/datadog_client.py — Datadog MCP client (monitors Alert/Warn, metrics host-based, logs silenced)
- mcp/__init__.py — exports build_datadog_context

## End-to-End Flow (VERIFIED ✅)
```
User submit ticket → Streamlit UI
  → bedrock_agent.analyze_incident()
    → _retrieve_rag_context() → S3 knowledge base + known issues DB
    → _retrieve_datadog_context() → MCP client → Datadog API
      → get_active_monitors() ✅ (Alert/Warn only)
      → get_recent_metrics() ✅ (CPU, memory, disk — host-based)
    → Store context_section → analyze_incident._last_context
    → Bedrock Nova Pro InvokeModel (with RAG + DD context)
    → AI Response with clickable runbook links
  → Hallucination check: _check_hallucination(output, context)
  → LLMObs: submit_evaluation(faithfulness + hallucination_risk)
  → DogStatsD: llm.hallucination.faithfulness gauge
  → DogStatsD: bedrock.tokens.input/output/total
  → LLMObs.flush()
```

## Datadog Integration Status
| Component | Status |
|-----------|--------|
| DD Agent 7 (infra) | ✅ Running, systemd enabled |
| LLM Observability (agentless) | ✅ Traces on every Bedrock call |
| LLMObs evaluations | ✅ faithfulness + hallucination_risk per span |
| Token Usage (DogStatsD) | ✅ bedrock.tokens.input/output/total |
| Hallucination (DogStatsD) | ✅ llm.hallucination.faithfulness |
| MCP Client → Monitors | ✅ Alert/Warn only |
| MCP Client → Metrics | ✅ CPU/memory/disk (host-based) |
| MCP Client → Logs | ⛔ DD plan doesn't include Logs |
| Custom Dashboard | ✅ id: k8i-7tt-mcc (3 sections) |
| Monitors (3) | ✅ Disk >85%, CPU >80%, Memory >85% |

## Dashboard Panels (k8i-7tt-mcc) — 3 Sections

### 🤖 LLM Performance (12 panels)
1. Total LLM Requests (Bedrock)
2. Avg LLM Latency
3. LLM Errors
4. Total Spans
5. 🪙 Avg Input Tokens
6. 🪙 Avg Output Tokens
7. 🪙 Total Tokens Used
8. 🪙 Token Usage Over Time
9. ⏱️ Bedrock Latency Over Time
10. 📈 Request Volume by Operation
11. 🧠 Top Operations
12. 🔍 Latency by Operation

### 🧠 Hallucination Monitoring (3 panels)
1. Legend/Guide (note widget — score meaning table)
2. Faithfulness Score (latest) — query_value
3. 📈 Faithfulness Over Time — line chart

### 🖥️ Infra Compute (4 panels)
1. CPU Utilization (%)
2. Memory Usage
3. Disk Usage (%)
4. Network In/Out (bytes)

## Hallucination Monitoring Details

### Metrics
- `llm.hallucination.faithfulness` — gauge: 1.0 (safe) / 0.5 (medium) / 0.0 (hallucinated)
- `llm.hallucination.risk.low/medium/high` — gauge: 1 or 0 (new metrics, may take time to appear)

### Custom Checks (observability._check_hallucination)
1. **Fake percentages** — AI claims specific % not in context or common thresholds
2. **Phantom alerts** — AI says "active alert" when none in DD context
3. **Non-existent docs** — AI references runbook filename that doesn't exist

### Where to see in Datadog
- **Dashboard:** Hallucination Monitoring section → faithfulness score + trend
- **LLM Obs Traces:** click span → Evaluations tab → faithfulness + hallucination_risk
- **Span metadata:** hallucination_risk, hallucination_reason

## AI Analysis Output Format
1. 🏷️ Classification
2. 🔍 Root Cause Analysis
3. ✅ Recommendations
4. 📊 Datadog - Observability Insights
5. 📖 Referenced Runbooks (clickable links → new tab doc preview)

## Monitors Created (via API)
- Disk Usage High on EC2 incident-agent (warn 75%, critical 85%)
- CPU Usage High on EC2 incident-agent (warn 60%, critical 80%)
- Memory Usage High on EC2 incident-agent (warn 70%, critical 85%)

## Network Notes
- SSH port 22 works dari network kantor (IPv4: 125.161.118.94)
- Port 443 untuk HTTPS app access
- Hotspot HP → SSH sering ke-block (too many connections / IPv6)
- Kalau SSH blocked, switch ke network kantor

## TODO / Next Steps
- [ ] Setup systemd service (auto-restart on reboot)
- [ ] Optional: proper domain + Let's Encrypt cert
- [ ] Optional: add more runbooks/docs to S3
- [ ] Optional: Slack integration for alerts
