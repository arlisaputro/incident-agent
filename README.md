# 🚨 Incident Intelligence Agent

AI-powered Incident Copilot built with **AWS Bedrock** and **Datadog LLM Observability**.

An intelligent agent that automatically analyzes incident tickets by combining real-time observability data from Datadog with organizational knowledge bases, providing evidence-based Root Cause Analysis and actionable recommendations.

## 🎯 What It Does

1. **User submits incident ticket** via web UI
2. **Agent retrieves context** from:
   - 📚 Knowledge Base (S3) — runbooks, SOPs, known issues
   - 📡 Datadog API (MCP) — active monitors, CPU/memory/disk metrics
3. **AI analyzes** using AWS Bedrock (Nova Pro) with enriched context
4. **Output includes:**
   - 🏷️ Classification & severity assessment
   - 🔍 Root Cause Analysis (correlated with real Datadog data)
   - ✅ Immediate & preventive recommendations
   - 📊 Observability insights from Datadog
   - 📖 Clickable runbook references
5. **Hallucination monitoring** validates AI output accuracy
6. **Full observability** — traces, token usage, latency in Datadog dashboard

## 🏗️ Architecture

```
User (Browser) ──HTTPS:443──▶ Streamlit App (EC2)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Datadog API      S3 Docs         AWS Bedrock
              (MCP Context)    (RAG)           (Nova Pro)
              - monitors       - runbooks      - analyze
              - metrics        - SOPs          - generate RCA
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                          Datadog LLM Observability
                          - traces & spans
                          - token usage
                          - hallucination score
                          - custom dashboard
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit (Python) |
| LLM | AWS Bedrock — `apac.amazon.nova-pro-v1:0` |
| RAG | boto3 → S3 (keyword-matched document retrieval) |
| MCP | Datadog API (monitors, metrics) |
| Observability | ddtrace + LLMObs SDK + DogStatsD |
| Infrastructure | EC2, S3, VPC (Terraform) |
| Monitoring | Datadog Agent 7, Custom Dashboard |

## 📁 Project Structure

```
├── app.py                  # Streamlit UI + doc preview
├── bedrock_agent.py        # LLM agent + token tracking
├── observability.py        # LLMObs + hallucination monitoring
├── knowledge_base.py       # RAG retrieval from S3
├── known_issues_db.py      # Known issues pattern database
├── database.py             # SQLite ticket storage
├── mcp/
│   ├── __init__.py
│   └── datadog_client.py   # Datadog API client (monitors, metrics)
├── docs/
│   ├── runbook-api-gateway.md
│   ├── runbook-database-infrastructure.md
│   ├── runbook-payment-service.md
│   ├── sop-incident-management.md
│   └── DASHBOARD_DOCUMENTATION.md
├── infra/
│   ├── main.tf             # Terraform (EC2, S3, VPC)
│   ├── variables.tf
│   └── outputs.tf
├── PROJECT_DOCUMENT.md     # Full project documentation
├── DEPLOYMENT_CONTEXT.md   # Deployment state & operations guide
├── datadog-dashboard.json  # Dashboard definition (importable)
├── architecture-diagram.drawio  # Architecture diagram (draw.io)
└── requirements.txt
```

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock access (ap-southeast-1)
- Datadog account with API key
- Python 3.10+
- Terraform

### 1. Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init && terraform apply
```

### 2. Deploy Application

```bash
# SSH to EC2
ssh -i ~/.ssh/incident-agent-key.pem ubuntu@<EC2_IP>

# Setup
python3 -m venv ~/venv && source ~/venv/bin/activate
pip install -r requirements.txt

# Configure
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=apac.amazon.nova-pro-v1:0
export DD_API_KEY=<your-dd-api-key>
export DD_APP_KEY=<your-dd-app-key>
export DD_SITE=datadoghq.com
export DD_SERVICE=incident-agent
export DD_LLMOBS_ML_APP=incident-agent
export DD_LLMOBS_AGENTLESS_ENABLED=1

# Run
streamlit run app.py --server.port 443 --server.address 0.0.0.0 --server.headless true
```

### 3. Upload Knowledge Base

```bash
aws s3 cp docs/ s3://<your-bucket>/docs/ --recursive
```

## 📊 Datadog Dashboard

Custom dashboard with 3 sections:

| Section | Panels | What It Shows |
|---------|--------|---------------|
| 🤖 LLM Performance | 12 | Request count, latency, errors, token usage, operations breakdown |
| 🧠 Hallucination Monitoring | 3 | Faithfulness score, trend over time, score guide |
| 🖥️ Infra Compute | 4 | CPU, memory, disk, network |

See [DASHBOARD_DOCUMENTATION.md](docs/DASHBOARD_DOCUMENTATION.md) for detailed panel descriptions.

## 🔍 Hallucination Monitoring

Every AI analysis is automatically checked for:

| Check | Detects |
|-------|---------|
| Fake Percentages | AI claims numbers not in context |
| Phantom Alerts | AI says "active alert" when none exist |
| Non-existent Docs | AI references runbooks that don't exist |

**Faithfulness Score:**
- `1.0` — ✅ Output consistent with context
- `0.5` — ⚠️ Some claims not fully backed
- `0.0` — 🚨 Hallucinated data

## 📖 Documentation

- [PROJECT_DOCUMENT.md](PROJECT_DOCUMENT.md) — Full project documentation (architecture, features, demo walkthrough)
- [DASHBOARD_DOCUMENTATION.md](docs/DASHBOARD_DOCUMENTATION.md) — Detailed dashboard panel documentation
- [DEPLOYMENT_CONTEXT.md](DEPLOYMENT_CONTEXT.md) — Deployment state & operations guide

## 🏆 Hackathon

Built for **AWS x Datadog Hackathon** — demonstrating how LLM Observability and real-time monitoring data can be combined to create an intelligent, trustworthy incident response agent.

**Key Innovation:** AI agent that doesn't just analyze — it validates its own outputs against real data, and every interaction is fully observable.
