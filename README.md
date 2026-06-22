# 🚨 Incident Intelligence Agent

**AWS x Datadog – AI-powered Incident Copilot**

RAG-powered operational intelligence system dengan full LLM observability (production-grade AI).

---

## 🏗️ Architecture

```
User (Streamlit) → PostgreSQL (RDS) → Amazon Bedrock (Claude 3 Sonnet)
                                              ↕
                              S3 (Runbooks/SOP) + DynamoDB (Known Issues)
                                              ↕
                                  Bedrock Knowledge Base (RAG)
                                              ↕
                                  Datadog MCP (Monitors/Metrics/Logs)
                                              ↓
                                  Datadog LLM Observability (Trace)
```

### Layers:
1. **User Layer** – Streamlit Web UI (incident form + ticket list + AI analysis)
2. **Ticket Storage** – Amazon RDS PostgreSQL (production-grade DB)
3. **AI Layer** – Amazon Bedrock Claude 3 Sonnet (classification, RCA, recommendation)
4. **RAG Layer** – Bedrock Knowledge Base (S3) + DynamoDB (known issues)
5. **Observability Layer** – Datadog MCP (real-time context) + LLM Obs (tracing)

---

## 📁 Project Structure

```
.
├── app.py                          # Streamlit UI + AI analyze button
├── database.py                     # PostgreSQL helper (psycopg2)
├── bedrock_agent.py                # Bedrock Claude 3 + RAG + Datadog MCP context
├── knowledge_base.py               # RAG retrieval (Bedrock KB + DynamoDB)
├── observability.py                # ddtrace LLM Observability (traces, spans)
├── requirements.txt                # Python dependencies
├── architecture-diagram.drawio     # Draw.io architecture diagram
├── detailsolution.txt              # Architecture detail (Mermaid)
├── mcp/                            # Datadog MCP integration
│   ├── __init__.py
│   └── datadog_client.py           # Query Datadog API (monitors, metrics, logs)
├── docs/                           # Knowledge Base documents (upload to S3)
│   ├── runbook-api-gateway.md
│   ├── runbook-payment-service.md
│   └── sop-incident-management.md
└── infra/                          # Terraform IaC
    ├── main.tf                     # All AWS resources
    ├── variables.tf                # Input variables
    ├── outputs.tf                  # Outputs (IPs, endpoints, ARNs)
    └── terraform.tfvars.example    # Config template
```

---

## 🚀 Deployment Guide (Step-by-Step)

### Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5.0 installed
- EC2 Key Pair sudah dibuat di AWS Console (region ap-southeast-1)
- Public IP kamu (jalankan: `curl ifconfig.me`)
- Bedrock model access enabled (Claude 3 Sonnet) di AWS Console
- Datadog account + API Key + Application Key

---

### Step 1: Clone Repository

```bash
git clone https://github.com/arlisaputro/incident-agent.git
cd incident-agent
```

---

### Step 2: Configure Terraform Variables

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region    = "ap-southeast-1"
project_name  = "incident-agent"
my_ip         = "103.x.x.x/32"      # hasil dari curl ifconfig.me
ami_id        = "ami-0672fd5b9210aa093"
instance_type = "t3.small"
key_pair_name = "your-key-pair-name"
db_username   = "incident_admin"
db_password   = "YourSecurePassword123!"
```

---

### Step 3: Provision Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

Setelah selesai, catat output:
- `ec2_public_ip` – IP untuk SSH & akses app
- `s3_bucket_name` – bucket untuk upload runbooks
- `dynamodb_table_name` – table known issues
- `rds_endpoint` – PostgreSQL endpoint
- `streamlit_url` – URL akses Streamlit
- `bedrock_kb_role_arn` – IAM role untuk Bedrock Knowledge Base

---

### Step 4: Upload Knowledge Base Documents ke S3

```bash
aws s3 cp docs/runbook-api-gateway.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp docs/runbook-payment-service.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp docs/sop-incident-management.md s3://<S3_BUCKET_NAME>/sop/
```

---

### Step 5: Create Bedrock Knowledge Base (AWS Console)

1. Buka **Bedrock Console → Knowledge Bases → Create**
2. Name: `incident-agent-kb`
3. IAM Role: pilih `incident-agent-bedrock-kb-role` (dari terraform)
4. Data source: S3 bucket (dari output `s3_bucket_name`)
5. Embedding model: **Titan Embedding V2**
6. Vector store: pilih **Quick create** (managed OpenSearch Serverless)
7. Create → Sync data source
8. Catat **Knowledge Base ID**

---

### Step 6: Seed DynamoDB Known Issues

```bash
aws dynamodb put-item --table-name incident-agent-known-issues --item '{
  "issue_id": {"S": "KI-001"},
  "service_name": {"S": "payment-service"},
  "title": {"S": "Payment timeout during peak hours"},
  "root_cause": {"S": "Connection pool exhaustion on DB"},
  "resolution": {"S": "Increase max pool size to 50 and add circuit breaker"}
}'

aws dynamodb put-item --table-name incident-agent-known-issues --item '{
  "issue_id": {"S": "KI-002"},
  "service_name": {"S": "api-gateway"},
  "title": {"S": "5xx spike after deployment"},
  "root_cause": {"S": "Memory leak in new release v2.3.1"},
  "resolution": {"S": "Rollback to v2.3.0 and fix memory allocation in handler"}
}'
```

---

### Step 7: Setup Datadog

#### 7a. Get API Keys
1. Buka **Datadog Console → Organization Settings → API Keys**
2. Create/copy **API Key**
3. Buka **Organization Settings → Application Keys**
4. Create/copy **Application Key**

#### 7b. (Optional) Install Datadog Agent di EC2
```bash
DD_API_KEY=<your-api-key> DD_SITE="datadoghq.com" bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)"
```

#### 7c. Configure service tags di Datadog
Pastikan services yang di-monitor di Datadog punya tag `service:<service_name>` yang match dengan nama service di incident ticket (e.g. `service:payment-service`, `service:api-gateway`).

---

### Step 8: SSH ke EC2 & Deploy Application

```bash
ssh -i ~/path/to/your-key.pem ec2-user@<EC2_PUBLIC_IP>
```

```bash
# Clone repo
git clone https://github.com/arlisaputro/incident-agent.git
cd incident-agent

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export DB_HOST=<RDS_ENDPOINT>
export DB_PORT=5432
export DB_NAME=incident_agent
export DB_USER=incident_admin
export DB_PASSWORD=YourSecurePassword123!
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export KNOWLEDGE_BASE_ID=<YOUR_KB_ID>
export DYNAMODB_TABLE=incident-agent-known-issues
export DD_API_KEY=<YOUR_DD_API_KEY>
export DD_APP_KEY=<YOUR_DD_APP_KEY>
export DD_SITE=datadoghq.com
export DD_LLMOBS_APP_NAME=incident-agent

# Run with Datadog tracing
ddtrace-run streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

> **Note:** Kalau mau run tanpa Datadog tracing (development), cukup:
> ```bash
> streamlit run app.py --server.port 8501 --server.address 0.0.0.0
> ```

---

### Step 9: Akses Aplikasi

Buka browser:
```
http://<EC2_PUBLIC_IP>:8501
```

---

### Step 10: Verify Datadog LLM Observability

1. Buka **Datadog Console → LLM Observability**
2. Filter by app: `incident-agent`
3. Verify traces muncul setiap kali klik "Analyze with AI"
4. Check: latency, token usage, prompt/response content, RAG spans

---

## 🧪 How It Works (Demo Flow)

1. **Create Ticket** – Isi form incident (title, severity, service, description)
2. **Klik "🧠 Analyze with AI"** – Trigger full analysis pipeline
3. **RAG Retrieval** – Query Bedrock KB (S3 runbooks) + DynamoDB (known issues)
4. **Datadog MCP** – Query real-time: active alerts, CPU/error metrics, recent error logs
5. **AI Analysis** – Claude 3 Sonnet menganalisis dengan ALL context:
   - 🏷️ Classification (incident type + severity validation)
   - 🔍 Root Cause Analysis (correlate with known issues + Datadog alerts)
   - ✅ Recommendations (reference runbook steps)
   - 📊 Observability Insights (signal summary + monitoring suggestions)
6. **Trace** – Full pipeline trace dikirim ke Datadog LLM Observability

---

## 🔧 Infrastructure (Terraform)

| Resource | Purpose |
|----------|---------|
| VPC + Public/Private Subnets | Networking (multi-AZ) |
| Security Group (App) | SSH (22) + Streamlit (8501) restricted to your IP |
| Security Group (RDS) | PostgreSQL (5432) only from app SG |
| EC2 (t3.small) | App server |
| RDS PostgreSQL (db.t3.micro) | Ticket database |
| IAM Role (EC2) | Bedrock + S3 + DynamoDB access |
| IAM Role (Bedrock KB) | S3 read access for knowledge base |
| S3 Bucket | Knowledge base documents (runbooks, SOP, RCA) |
| DynamoDB + GSI | Known issues / problem history (service-index) |

---

## 📡 Datadog Integration

### LLM Observability (ddtrace)
| What's Traced | Detail |
|---------------|--------|
| LLM Call | Model, latency, input/output tokens, prompt/response |
| RAG Retrieval | Duration, source (KB + DynamoDB), retrieved context |
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
| `DB_HOST` | ✅ | RDS PostgreSQL endpoint |
| `DB_PORT` | ✅ | PostgreSQL port (default: 5432) |
| `DB_NAME` | ✅ | Database name (default: incident_agent) |
| `DB_USER` | ✅ | Database username |
| `DB_PASSWORD` | ✅ | Database password |
| `AWS_REGION` | ✅ | AWS region (default: ap-southeast-1) |
| `BEDROCK_MODEL_ID` | ✅ | Bedrock model ID |
| `KNOWLEDGE_BASE_ID` | ⚡ | Bedrock KB ID (RAG won't work without this) |
| `DYNAMODB_TABLE` | ⚡ | DynamoDB table name |
| `DD_API_KEY` | ⚡ | Datadog API key |
| `DD_APP_KEY` | ⚡ | Datadog Application key |
| `DD_SITE` | ⚡ | Datadog site (default: datadoghq.com) |
| `DD_LLMOBS_APP_NAME` | ⚡ | App name in LLM Obs (default: incident-agent) |

> ✅ = required, ⚡ = required for full functionality (graceful fallback if missing)

---

## 💻 Local Development (tanpa AWS)

```bash
pip install -r requirements.txt

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=incident_agent
export DB_USER=postgres
export DB_PASSWORD=password

streamlit run app.py
```

> AI analysis dan Datadog features akan fallback gracefully kalau credentials tidak ada.

---

## 🧹 Cleanup (Destroy Infrastructure)

```bash
cd infra
terraform destroy
```

---

## 📌 Feature Checklist

- [x] Streamlit UI (incident form + ticket list)
- [x] PostgreSQL database (RDS)
- [x] Amazon Bedrock integration (Claude 3 Sonnet)
- [x] RAG Layer (Bedrock Knowledge Base + DynamoDB)
- [x] Sample knowledge base documents
- [x] Terraform IaC (all infrastructure)
- [x] Datadog LLM Observability (ddtrace)
- [x] Datadog MCP (real-time monitors/metrics/logs context)
- [ ] Demo script (3 min pitch)

---

## 👥 Team

IpCoE
