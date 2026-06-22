# 🚨 Incident Intelligence Agent

**AWS x Datadog – AI-powered Incident Copilot**

RAG-powered operational intelligence system dengan full LLM observability (production-grade AI).

---

## 🏗️ Architecture

```
User (Streamlit) → SQLite (tickets.db) → Amazon Bedrock (Nova Pro)
                                                ↕
                                S3 (Runbooks/SOP) via Bedrock Knowledge Base
                                                ↕
                                SQLite (data/known_issues.db) - Known Issues
                                                ↕
                                Datadog MCP (Monitors/Metrics/Logs)
                                                ↓
                                Datadog LLM Observability (Trace)
```

### Layers:
1. **User Layer** – Streamlit Web UI (incident form + ticket list + AI analysis)
2. **Ticket Storage** – SQLite `tickets.db` (incident tickets)
3. **AI Layer** – Amazon Bedrock Nova Pro (classification, RCA, recommendation)
4. **RAG Layer** – Bedrock Knowledge Base (S3) + SQLite `data/known_issues.db`
5. **Observability Layer** – Datadog MCP (real-time context) + LLM Obs (tracing)

---

## 📁 Project Structure

```
.
├── app.py                          # Streamlit UI + AI analyze button
├── database.py                     # SQLite helper (tickets.db)
├── known_issues_db.py              # SQLite helper (data/known_issues.db)
├── bedrock_agent.py                # Bedrock Nova Pro + RAG + Datadog MCP context
├── knowledge_base.py               # RAG retrieval (Bedrock KB + known issues SQLite)
├── observability.py                # ddtrace LLM Observability (traces, spans)
├── requirements.txt                # Python dependencies
├── architecture-diagram.drawio     # Draw.io architecture diagram
├── detailsolution.txt              # Architecture detail (Mermaid)
├── DEMO_SCRIPT.md                  # 3-minute pitch script
├── data/                           # Knowledge base data (SQLite)
│   └── known_issues.db             # Auto-created & seeded on first run
├── mcp/                            # Datadog MCP integration
│   ├── __init__.py
│   └── datadog_client.py           # Query Datadog API (monitors, metrics, logs)
├── docs/                           # Knowledge Base documents (upload to S3)
│   ├── runbook-api-gateway.md
│   ├── runbook-payment-service.md
│   └── sop-incident-management.md
└── infra/                          # Terraform IaC
    ├── main.tf                     # AWS resources (VPC, EC2, S3, IAM)
    ├── variables.tf                # Input variables
    ├── outputs.tf                  # Outputs (IPs, bucket, ARNs)
    └── terraform.tfvars.example    # Config template
```

---

## 🚀 How to Deploy

### Prerequisites

| Tool | Cara Install |
|------|-------------|
| AWS CLI | `brew install awscli` lalu `aws configure` |
| Terraform | `brew install terraform` |
| EC2 Key Pair | Buat di AWS Console → EC2 → Key Pairs |
| Bedrock Access | AWS Console → Bedrock → Model Access → Enable **Amazon Nova Pro** |
| Datadog Account | https://www.datadoghq.com (free trial available) |

---

### Phase 1: Provision AWS Infrastructure

```bash
# 1. Clone repo
git clone https://github.com/arlisaputro/incident-agent.git
cd incident-agent/infra

# 2. Copy & edit config
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region    = "ap-southeast-1"
project_name  = "incident-agent"
my_ip         = "YOUR_IP/32"         # jalankan: curl ifconfig.me
ami_id        = "ami-0672fd5b9210aa093"
instance_type = "t3.small"
key_pair_name = "YOUR_KEY_PAIR"      # nama key pair di AWS
```

```bash
# 3. Deploy
terraform init
terraform plan
terraform apply
```

✅ **Output yang perlu dicatat:**
```
ec2_public_ip     = "x.x.x.x"
s3_bucket_name    = "incident-agent-knowledge-base-xxxxxxxx"
streamlit_url     = "http://x.x.x.x:8501"
bedrock_kb_role_arn = "arn:aws:iam::xxxx:role/incident-agent-bedrock-kb-role"
```

---

### Phase 2: Setup Bedrock Knowledge Base

```bash
# 1. Upload docs ke S3 (dari local machine)
cd ../  # kembali ke root project
aws s3 cp docs/runbook-api-gateway.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp docs/runbook-payment-service.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp docs/runbook-database-infrastructure.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp docs/sop-incident-management.md s3://<S3_BUCKET_NAME>/sop/
```

```
# 2. Buat Knowledge Base di AWS Console:
#    - Buka: Bedrock Console → Knowledge Bases → Create
#    - Name: incident-agent-kb
#    - IAM Role: incident-agent-bedrock-kb-role
#    - Data Source: S3 → pilih bucket dari output terraform
#    - Embedding Model: Titan Embedding V2
#    - Vector Store: Quick create (OpenSearch Serverless)
#    - Klik Create → Sync data source
#    - Catat KNOWLEDGE_BASE_ID
```

---

### Phase 3: Setup Datadog

```
# 1. Get API Keys dari Datadog Console:
#    - Organization Settings → API Keys → Create/Copy
#    - Organization Settings → Application Keys → Create/Copy

# 2. (Optional) Pastikan services di Datadog punya tag:
#    service:payment-service, service:api-gateway, etc.
```

---

### Phase 4: Deploy Application ke EC2

```bash
# 1. SSH ke EC2
ssh -i ~/path/to/your-key.pem ec2-user@<EC2_PUBLIC_IP>

# 2. Clone repo
git clone https://github.com/arlisaputro/incident-agent.git
cd incident-agent

# 3. Install dependencies
pip3 install -r requirements.txt

# 4. Set environment variables
cat <<'EOF' >> ~/.bashrc
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
export KNOWLEDGE_BASE_ID=<YOUR_KB_ID>
export DD_API_KEY=<YOUR_DD_API_KEY>
export DD_APP_KEY=<YOUR_DD_APP_KEY>
export DD_SITE=datadoghq.com
export DD_LLMOBS_APP_NAME=incident-agent
EOF
source ~/.bashrc

# 5. (Optional) Install Datadog Agent
DD_API_KEY=$DD_API_KEY DD_SITE="datadoghq.com" bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)"

# 6. Run application
ddtrace-run streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Atau tanpa Datadog tracing:
# streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Untuk run di background:
# nohup ddtrace-run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

---

### Phase 5: Verify & Test

```
# 1. Buka browser
http://<EC2_PUBLIC_IP>:8501

# 2. Buat test ticket:
#    - Title: "API Gateway 5xx spike"
#    - Severity: High
#    - Service: api-gateway
#    - Description: "Sudden increase in 500 errors, customers affected"

# 3. Klik "🧠 Analyze with AI" → verify AI response muncul

# 4. Check Datadog:
#    - Buka Datadog Console → LLM Observability
#    - Filter app: incident-agent
#    - Verify trace: latency, tokens, prompt/response
```

---

## 🧪 How It Works (Demo Flow)

1. **Create Ticket** – Isi form incident (title, severity, service, description)
2. **Klik "🧠 Analyze with AI"** – Trigger full analysis pipeline
3. **RAG Retrieval** – Query Bedrock KB (S3 runbooks) + SQLite (known issues)
4. **Datadog MCP** – Query real-time: active alerts, CPU/error metrics, recent error logs
5. **AI Analysis** – Nova Pro menganalisis dengan ALL context:
   - 🏷️ Classification (incident type + severity validation)
   - 🔍 Root Cause Analysis (correlate with known issues + Datadog alerts)
   - ✅ Recommendations (reference runbook steps)
   - 📊 Observability Insights (signal summary + monitoring suggestions)
6. **Trace** – Full pipeline trace dikirim ke Datadog LLM Observability

### Sample Test Cases

Gunakan contoh input berikut untuk testing/demo:

#### Test Case 1: Payment Timeout
| Field | Value |
|-------|-------|
| Title | Payment service timeout during checkout |
| Severity | Critical |
| Service | payment-service |
| Description | Multiple customers reporting HTTP 504 timeout when completing payment. Transaction success rate dropped from 99.5% to 72% in the last 15 minutes. Error logs show "connection pool exhausted" messages. Peak traffic period (lunch hour). |

#### Test Case 2: API Gateway 5xx Spike
| Field | Value |
|-------|-------|
| Title | API Gateway returning 502 Bad Gateway |
| Severity | High |
| Service | api-gateway |
| Description | 502 errors spiked to 15% after deployment v2.4.0 rolled out 30 minutes ago. Latency P99 increased from 180ms to 2.5s. Backend health checks intermittently failing. Memory usage on gateway pods showing steady increase. |

#### Test Case 3: Redis Cache Failure
| Field | Value |
|-------|-------|
| Title | Redis OOM causing high latency across services |
| Severity | High |
| Service | redis-cache |
| Description | Redis cluster reporting OOM errors. Cache hit rate dropped from 95% to 20%. All downstream services experiencing 3-5x latency increase. Memory usage at 100%, eviction policy not configured. Last restart was 3 weeks ago. |

#### Test Case 4: Database Slow Queries
| Field | Value |
|-------|-------|
| Title | Database queries timing out on order history |
| Severity | Medium |
| Service | database |
| Description | Order history page taking 30+ seconds to load. PostgreSQL showing queries on orders table doing sequential scan. Table has 50M rows. Query: SELECT * FROM orders WHERE created_at > now() - interval '30 days' ORDER BY created_at DESC. No index on created_at column. |

#### Test Case 5: Login Failures
| Field | Value |
|-------|-------|
| Title | Mass login failures reported by customers |
| Severity | Critical |
| Service | user-service |
| Description | 500+ customers unable to login in the last 10 minutes. Auth0 returning 429 rate limit errors. Security team detected brute force attempts from 50+ IPs targeting multiple accounts. Legitimate users blocked due to shared rate limit bucket. |

---

## 🔧 Infrastructure (Terraform)

| Resource | Purpose |
|----------|---------|
| VPC + Public Subnet | Networking |
| Security Group | SSH (22) + Streamlit (8501) restricted to your IP |
| EC2 (t3.small) | App server (SQLite DBs run locally) |
| IAM Role (EC2) | Bedrock + S3 access |
| IAM Role (Bedrock KB) | S3 read access for knowledge base |
| S3 Bucket | Knowledge base documents (runbooks, SOP, RCA) |

---

## 📡 Datadog Integration

### LLM Observability (ddtrace)
| What's Traced | Detail |
|---------------|--------|
| LLM Call | Model, latency, input/output tokens, prompt/response |
| RAG Retrieval | Duration, source (KB + SQLite), retrieved context |
| MCP Query | Duration, Datadog API calls, returned context |

### MCP (Real-time Context)
| Data Source | What AI Gets |
|-------------|-------------|
| Monitors | Active alerts/warnings for the affected service |
| Metrics | CPU utilization, error rate (last 30 min) |
| Logs | Recent error logs from the service |

---

## 🌍 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_REGION` | ✅ | AWS region (default: ap-southeast-1) |
| `BEDROCK_MODEL_ID` | ✅ | Bedrock model ID (default: amazon.nova-pro-v1:0) |
| `KNOWLEDGE_BASE_ID` | ⚡ | Bedrock KB ID (RAG from S3 won't work without this) |
| `DD_API_KEY` | ⚡ | Datadog API key |
| `DD_APP_KEY` | ⚡ | Datadog Application key |
| `DD_SITE` | ⚡ | Datadog site (default: datadoghq.com) |
| `DD_LLMOBS_APP_NAME` | ⚡ | App name in LLM Obs (default: incident-agent) |

> ✅ = required, ⚡ = required for full functionality (graceful fallback if missing)

---

## 💻 Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

Akses di `http://localhost:8501`

> - `tickets.db` auto-created di root directory
> - `data/known_issues.db` auto-created & seeded dengan 15 sample known issues
>   - Services: `payment-service`, `api-gateway`, `database`, `redis-cache`, `user-service`, `notification-service`, `infrastructure`, `order-service`
> - AI analysis dan Datadog features akan fallback gracefully kalau credentials tidak ada

---

## 🧹 Cleanup (Destroy Infrastructure)

```bash
cd infra
terraform destroy
```

---

## 📌 Feature Checklist

- [x] Streamlit UI (incident form + ticket list)
- [x] SQLite ticket database
- [x] SQLite known issues database (auto-seeded)
- [x] Amazon Bedrock integration (Nova Pro)
- [x] RAG Layer (Bedrock Knowledge Base from S3)
- [x] Sample knowledge base documents
- [x] Terraform IaC (VPC, EC2, S3, IAM)
- [x] Datadog LLM Observability (ddtrace)
- [x] Datadog MCP (real-time monitors/metrics/logs context)
- [x] Demo script (3 min pitch)

---

## 👥 Team

Hackathon 2025 – AWS x Datadog
