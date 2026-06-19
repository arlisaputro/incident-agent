# 🚨 Incident Intelligence Agent

**AWS x Datadog – AI-powered Incident Copilot**

RAG-powered operational intelligence system dengan full LLM observability (production-grade AI).

---

## 🏗️ Architecture

```
User (Streamlit) → SQLite → Amazon Bedrock (AI Agent)
                                    ↕
                        S3 (Runbooks/SOP) + DynamoDB (Known Issues)
                                    ↓
                        Datadog LLM Observability
```

### Layers:
1. **User Layer** – Streamlit Web UI (incident form + ticket list)
2. **Ticket Storage** – SQLite (lightweight incident DB)
3. **AI Layer** – Amazon Bedrock (classification, RCA, recommendation)
4. **RAG Layer** – S3 + DynamoDB + Knowledge Base Retrieval
5. **Observability** – Datadog (latency, token usage, cost, prompt trace)

---

## 📁 Project Structure

```
.
├── app.py                       # Streamlit UI
├── database.py                  # SQLite helper
├── requirements.txt             # Python dependencies
├── detailsolution.txt           # Architecture detail (Mermaid)
└── infra/
    ├── main.tf                  # Terraform IaC (VPC, EC2, S3, DynamoDB, IAM)
    ├── variables.tf             # Input variables
    ├── outputs.tf               # Outputs (IP, URL, bucket name)
    └── terraform.tfvars.example # Config template
```

---

## 🚀 Deployment Guide (Step-by-Step)

### Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5.0 installed
- EC2 Key Pair sudah dibuat di AWS Console (region ap-southeast-1)
- Public IP kamu (jalankan: `curl ifconfig.me`)

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
key_pair_name = "your-key-pair-name" # key pair yang sudah ada di AWS
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
- `streamlit_url` – URL akses Streamlit

---

### Step 4: SSH ke EC2

```bash
ssh -i ~/path/to/your-key.pem ec2-user@<EC2_PUBLIC_IP>
```

---

### Step 5: Deploy Application di EC2

```bash
# Clone repo di EC2
git clone https://github.com/arlisaputro/incident-agent.git
cd incident-agent

# Install dependencies
pip3 install -r requirements.txt

# Run Streamlit (background)
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

---

### Step 6: Akses Aplikasi

Buka browser:
```
http://<EC2_PUBLIC_IP>:8501
```

---

### Step 7: Upload Knowledge Base ke S3 (Optional)

```bash
# Dari local machine
aws s3 cp ./docs/runbook-payment.md s3://<S3_BUCKET_NAME>/runbooks/
aws s3 cp ./docs/sop-incident.md s3://<S3_BUCKET_NAME>/sop/
```

---

### Step 8: Seed DynamoDB Known Issues (Optional)

```bash
aws dynamodb put-item --table-name incident-agent-known-issues --item '{
  "issue_id": {"S": "KI-001"},
  "service_name": {"S": "payment-service"},
  "title": {"S": "Payment timeout during peak hours"},
  "root_cause": {"S": "Connection pool exhaustion on DB"},
  "resolution": {"S": "Increase max pool size to 50 and add circuit breaker"}
}'
```

---

### 🧹 Cleanup (Destroy Infrastructure)

```bash
cd infra
terraform destroy
```

---

## 💻 Local Development (tanpa AWS)

Kalau mau test UI saja tanpa deploy ke AWS:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Akses di `http://localhost:8501`

---

## 🔧 Infrastructure (Terraform)

| Resource | Purpose |
|----------|---------|
| VPC + Public Subnet | Networking |
| Security Group | SSH (22) + Streamlit (8501) restricted to your IP |
| EC2 (t3.small) | App server |
| IAM Role | Bedrock + S3 + DynamoDB access |
| S3 Bucket | Knowledge base (runbooks, SOP, RCA docs) |
| DynamoDB | Known issues / problem history |

---

## 📌 TODO

- [ ] Integrate Amazon Bedrock (AI analysis)
- [ ] Setup Bedrock Knowledge Base (RAG)
- [ ] Upload sample runbooks to S3
- [ ] Seed DynamoDB with known issues
- [ ] Integrate Datadog LLM Observability
- [ ] Demo script (3 min pitch)

---

## 👥 Team

Hackathon 2025 – AWS x Datadog
