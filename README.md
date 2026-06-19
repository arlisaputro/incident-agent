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
                                              ↓
                                  Datadog LLM Observability
```

### Layers:
1. **User Layer** – Streamlit Web UI (incident form + ticket list + AI analysis)
2. **Ticket Storage** – Amazon RDS PostgreSQL (production-grade DB)
3. **AI Layer** – Amazon Bedrock Claude 3 Sonnet (classification, RCA, recommendation)
4. **RAG Layer** – Bedrock Knowledge Base (S3) + DynamoDB (known issues)
5. **Observability** – Datadog (latency, token usage, cost, prompt trace)

---

## 📁 Project Structure

```
.
├── app.py                          # Streamlit UI + AI analyze button
├── database.py                     # PostgreSQL helper (psycopg2)
├── bedrock_agent.py                # Bedrock Claude 3 invocation + RAG context
├── knowledge_base.py               # RAG retrieval (Bedrock KB + DynamoDB)
├── requirements.txt                # Python dependencies
├── architecture-diagram.drawio     # Draw.io architecture diagram
├── detailsolution.txt              # Architecture detail (Mermaid)
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
# Dari local machine
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
export DB_HOST=<RDS_ENDPOINT>        # e.g. incident-agent-db.xxxxx.ap-southeast-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=incident_agent
export DB_USER=incident_admin
export DB_PASSWORD=YourSecurePassword123!
export AWS_REGION=ap-southeast-1
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export KNOWLEDGE_BASE_ID=<YOUR_KB_ID>
export DYNAMODB_TABLE=incident-agent-known-issues

# Run Streamlit
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

---

### Step 8: Akses Aplikasi

Buka browser:
```
http://<EC2_PUBLIC_IP>:8501
```

---

## 🧪 How It Works (Demo Flow)

1. **Create Ticket** – Isi form incident (title, severity, service, description)
2. **Klik "🧠 Analyze with AI"** – Trigger Bedrock analysis
3. **RAG Retrieval** – System query Knowledge Base (S3 runbooks) + DynamoDB (known issues)
4. **AI Analysis** – Claude 3 Sonnet menganalisis dengan context dari RAG:
   - 🏷️ Classification (incident type + severity validation)
   - 🔍 Root Cause Analysis (dengan referensi known issues)
   - ✅ Recommendations (dengan referensi runbook steps)

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

## 💻 Local Development (tanpa AWS)

Kalau mau test UI saja tanpa full AWS integration:

```bash
pip install -r requirements.txt

# Set minimal env (akan fallback gracefully kalau Bedrock/KB tidak available)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=incident_agent
export DB_USER=postgres
export DB_PASSWORD=password

streamlit run app.py
```

---

## 🧹 Cleanup (Destroy Infrastructure)

```bash
cd infra
terraform destroy
```

---

## 📌 TODO

- [x] Streamlit UI (incident form + ticket list)
- [x] PostgreSQL database (RDS)
- [x] Amazon Bedrock integration (Claude 3 Sonnet)
- [x] RAG Layer (Bedrock Knowledge Base + DynamoDB)
- [x] Sample knowledge base documents
- [x] Terraform IaC (all infrastructure)
- [ ] Integrate Datadog LLM Observability
- [ ] Demo script (3 min pitch)

---

## 👥 Team

Hackathon 2025 – AWS x Datadog
