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

## 🚀 Quick Start

### 1. Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 2. Deploy Infrastructure (AWS)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars (isi my_ip, key_pair_name)

terraform init
terraform plan
terraform apply
```

### 3. Deploy App to EC2

```bash
# SSH ke EC2
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>

# Clone & run
git clone <repo-url>
cd hackaton
pip3 install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

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
