# 🚨 Incident Intelligence Agent

**AWS x Datadog – AI-powered Incident Copilot**

RAG-powered operational intelligence system dengan full LLM observability (production-grade AI).

---

## 🏗️ Architecture

```
User (Streamlit) → SQLite (tickets.db) → Amazon Bedrock (Amazon Nova Pro)
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
3. **AI Layer** – Amazon Bedrock Amazon Nova Pro (classification, RCA, recommendation)
4. **RAG Layer** – Bedrock Knowledge Base (S3) + SQLite `data/known_issues.db` (known issues)
5. **Observability Layer** – Datadog MCP (real-time context) + LLM Obs (tracing)

---

## 📁 Project Structure

```
.
├── app.py                          # Streamlit UI + AI analyze button
├── database.py                     # SQLite helper (tickets.db)
├── known_issues_db.py              # SQLite helper (data/known_issues.db)
├── bedrock_agent.py                # Bedrock Claude 3 + RAG + Datadog MCP context
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

## 🚀 Deployment Guide (Step-by-Step)

### Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5.0 installed
- EC2 Key Pair sudah dibuat di AWS Console (region ap-southeast-1)
- Public IP kamu (jalankan: `curl ifconfig.me`)
- Bedrock model access enabled (Amazon Nova Pro) di AWS Console
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

### Step 6: Setup Datadog

#### 6a. Get API Keys
1. Buka **Datadog Console → Organization Settings → API Keys**
2. Create/copy **API Key**
3. Buka **Organization Settings → Application Keys**
4. Create/copy **Application Key**

#### 6b. (Optional) Install Datadog Agent di EC2
```bash
DD_API_KEY=<your-api-key> DD_SITE="datadoghq.com" bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)"
```

#### 6c. Configure service tags di Datadog
Pastikan services yang di-monitor di Datadog punya tag `service:<service_name>` yang match dengan nama service di incident ticket (e.g. `service:payment-service`, `service:api-gateway`).

---

### Step 7: SSH ke EC2 & Deploy Application

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
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=anthropic.nova-pro-20240229-v1:0
export KNOWLEDGE_BASE_ID=<YOUR_KB_ID>
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

### Step 8: Akses Aplikasi

Buka browser:
```
http://<EC2_PUBLIC_IP>:8501
```

> Known issues database (`data/known_issues.db`) otomatis dibuat dan di-seed dengan sample data pada first run.

---

### Step 9: Verify Datadog LLM Observability

1. Buka **Datadog Console → LLM Observability**
2. Filter by app: `incident-agent`
3. Verify traces muncul setiap kali klik "Analyze with AI"
4. Check: latency, token usage, prompt/response content, RAG spans

---

## 🧪 How It Works (Demo Flow)

1. **Create Ticket** – Isi form incident (title, severity, service, description)
2. **Klik "🧠 Analyze with AI"** – Trigger full analysis pipeline
3. **RAG Retrieval** – Query Bedrock KB (S3 runbooks) + SQLite (known issues)
4. **Datadog MCP** – Query real-time: active alerts, CPU/error metrics, recent error logs
5. **AI Analysis** – Amazon Nova Pro menganalisis dengan ALL context:
   - 🏷️ Classification (incident type + severity validation)
   - 🔍 Root Cause Analysis (correlate with known issues + Datadog alerts)
   - ✅ Recommendations (reference runbook steps)
   - 📊 Observability Insights (signal summary + monitoring suggestions)
6. **Trace** – Full pipeline trace dikirim ke Datadog LLM Observability

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
| `BEDROCK_MODEL_ID` | ✅ | Bedrock model ID |
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
> - `data/known_issues.db` auto-created & seeded dengan sample data
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
- [x] Amazon Bedrock integration (Amazon Nova Pro)
- [x] RAG Layer (Bedrock Knowledge Base from S3)
- [x] Sample knowledge base documents
- [x] Terraform IaC (VPC, EC2, S3, IAM)
- [x] Datadog LLM Observability (ddtrace)
- [x] Datadog MCP (real-time monitors/metrics/logs context)
- [x] Demo script (3 min pitch)

---

## 👥 Team

Hackathon 2025 – AWS x Datadog
