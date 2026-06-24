# 🚨 Incident Intelligence Agent

## AI-powered Incident Copilot — AWS Bedrock x Datadog

---

## 1. Executive Summary

**Problem:** Incident response lambat karena SRE harus manual cek runbook, korelasi metrics, dan cari root cause dari berbagai sumber data yang terpisah.

**Solution:** AI agent yang otomatis menganalisis incident ticket dengan meng-enrich context dari real-time observability data (Datadog) dan organizational knowledge base (S3), menghasilkan RCA dan rekomendasi yang evidence-based.

**Tech Stack:** Python · Streamlit · AWS Bedrock (Nova Pro) · Datadog LLM Observability · Terraform

---

## 2. Problem Statement

Saat incident terjadi, SRE/on-call engineer harus:
- ❌ Buka Datadog → cek alerts, metrics, logs secara manual
- ❌ Cari runbook yang relevan dari knowledge base
- ❌ Korelasi data dari multiple sources
- ❌ Tulis RCA berdasarkan pengalaman pribadi (inconsistent)

**Impact:**
- MTTR tinggi karena proses manual & knowledge silo
- Kualitas RCA inconsistent (tergantung siapa yang on-call)
- Knowledge base jarang dipakai karena susah dicari saat panik
- Tidak ada monitoring apakah rekomendasi yang diberikan akurat

---

## 3. Solution Overview

```
┌──────────────┐     ┌──────────────────────────────────┐     ┌────────────────┐
│  User/SRE    │────▶│  Incident Intelligence Agent     │────▶│  AI Analysis   │
│  (Browser)   │     │  - Streamlit UI (HTTPS:443)      │     │  - RCA         │
└──────────────┘     │  - Submit incident ticket        │     │  - Recommend   │
                     └──────────┬───────────────────────┘     │  - Runbook ref │
                                │                             └────────────────┘
                    ┌───────────┼───────────────┐
                    ▼           ▼               ▼
            ┌──────────┐ ┌──────────┐  ┌──────────────┐
            │ Datadog  │ │ S3 Docs  │  │ AWS Bedrock  │
            │ MCP API  │ │ (RAG)    │  │ Nova Pro LLM │
            │ monitors │ │ runbooks │  │              │
            │ metrics  │ │ SOPs     │  │              │
            └──────────┘ └──────────┘  └──────────────┘
```

**Key Differentiator:** AI bukan asal jawab — setiap analysis di-validate menggunakan real-time data dari Datadog dan di-monitor untuk hallucination.

---

## 4. Key Features

| Feature | Description |
|---------|-------------|
| 🧠 AI Incident Analysis | Bedrock Nova Pro menganalisis incident dengan structured output (Classification, RCA, Recommendations) |
| 📚 RAG Knowledge Base | Runbooks & SOP dari S3 di-inject sebagai context ke LLM |
| 📡 MCP Datadog Integration | Real-time monitors, CPU/memory/disk metrics diambil dari Datadog API saat analysis |
| 🔍 Hallucination Monitoring | Otomatis detect jika AI ngarang data (fake alerts, wrong percentages, non-existent docs) |
| 📊 LLM Observability | Full tracing: latency, token usage, faithfulness score — semua di Datadog dashboard |
| 📖 Clickable Runbook References | AI output berisi link yang bisa diklik untuk preview doc langsung di browser |
| 🖥️ Infra Monitoring | DD Agent monitor CPU, memory, disk, network — visible di dashboard |
| 🎫 Ticket Management | Create & track incident tickets via Streamlit UI |

---

## 5. Architecture & Tech Stack

### AWS Services
| Service | Purpose |
|---------|---------|
| EC2 (t3.small) | Application server |
| S3 | Knowledge base storage (runbooks, SOPs) |
| VPC | Network isolation |
| Bedrock | LLM inference (Nova Pro v1) |

### Datadog
| Component | Purpose |
|-----------|---------|
| DD Agent 7 | Infrastructure monitoring (CPU, memory, disk) |
| LLM Observability | Trace every LLM call (latency, tokens, input/output) |
| DogStatsD | Custom metrics (token usage, hallucination scores) |
| Monitors API | Real-time alert status (MCP context) |
| Metrics API | Real-time infra metrics (MCP context) |
| Custom Dashboard | Unified view: LLM perf + hallucination + infra |

### Application Stack
| Component | Technology |
|-----------|-----------|
| UI | Streamlit (Python) |
| LLM | AWS Bedrock (apac.amazon.nova-pro-v1:0) |
| RAG | boto3 → S3 (keyword matching) |
| MCP | requests → Datadog API |
| Tracing | ddtrace + LLMObs SDK |
| Metrics | datadog (DogStatsD) |
| Database | SQLite (tickets) |
| Infra-as-Code | Terraform |
| SSL | Self-signed certificate |

---

## 6. How It Works (Step-by-Step)

### Step 1: User Creates Incident Ticket
User mengisi form di Streamlit UI:
- Title (e.g., "Payment gateway timeout")
- Severity (Low / Medium / High / Critical)
- Service Affected (e.g., "payment-service")
- Description (detail masalah)

### Step 2: Context Enrichment
Saat "Analyze with AI" diklik, app mengambil context dari 2 sumber:

**A. RAG — Knowledge Base (S3)**
- Match service name → relevant runbooks
- Always include SOP Incident Management
- Truncate to 2000 chars per doc

**B. MCP — Datadog API**
- `get_active_monitors()` → alerts yang sedang firing (Alert/Warn)
- `get_recent_metrics()` → CPU, memory, disk usage (last 30 min)

### Step 3: LLM Analysis
Context di-inject ke prompt, lalu Bedrock Nova Pro generate analysis:

```
[System Prompt: SRE expert role]
[User Prompt: Ticket details + RAG context + Datadog context]
[Output Format: Classification → RCA → Recommendations → DD Insights → Runbook refs]
```

### Step 4: Hallucination Check
Setelah AI response, otomatis dijalankan:
1. Cek apakah AI claim "active alert" padahal tidak ada di context
2. Cek apakah AI mention persentase yang tidak ada di data
3. Cek apakah AI reference runbook yang tidak exist

Result: faithfulness score (1.0 = safe, 0.5 = medium risk, 0.0 = hallucinated)

### Step 5: Observability
Semua data dikirim ke Datadog:
- LLM Obs: trace span dengan input/output, evaluations
- DogStatsD: token usage (input/output/total), faithfulness score
- DD Agent: infra metrics (CPU, memory, disk, network)

### Step 6: Output ke User
AI response ditampilkan di UI dengan:
- Structured sections (Classification, RCA, Recommendations, etc.)
- Clickable runbook links (open doc preview di new tab)
- Real Datadog data di-reference oleh AI

---

## 7. Demo Walkthrough

### 7.1 Submit Ticket
1. Buka **https://54.179.171.169**
2. Isi form:
   - Title: "Payment gateway timeout on checkout"
   - Severity: High
   - Service: payment-service
   - Description: "Timeout errors on /api/v1/checkout. 15% error rate."
3. Klik "🚀 Submit Ticket"

### 7.2 AI Analysis
1. Expand ticket di daftar
2. Klik "🧠 Analyze with AI"
3. AI response tampil dengan:
   - 🏷️ Classification: Availability, High severity
   - 🔍 RCA: Connection pool exhaustion (reference known issue dari runbook)
   - ✅ Recommendations: Check DB pool, verify SSL, rollback deploy
   - 📊 Datadog Insights: Current CPU/memory normal, no active alerts
   - 📖 Runbook links: clickable ke Payment Service runbook

### 7.3 Runbook Preview
- Klik link "[Runbook Payment Service](https://54.179.171.169/?doc=docs/runbook-payment-service.md)"
- Doc dari S3 di-render full di browser

### 7.4 Datadog Dashboard
- Buka **https://app.datadoghq.com/dashboard/k8i-7tt-mcc/**
- 3 sections visible:
  - 🤖 LLM Performance (requests, latency, tokens)
  - 🧠 Hallucination Monitoring (faithfulness score + trend)
  - 🖥️ Infra Compute (CPU, memory, disk, network)

### 7.5 LLM Observability Traces
- Buka **https://app.datadoghq.com/llm/traces**
- Filter: `ml_app:incident-agent`
- Klik trace → lihat:
  - Input prompt
  - Output response
  - Evaluations (faithfulness, hallucination_risk)
  - Duration & metadata

---

## 8. Results & Impact

| Metric | Before | After |
|--------|--------|-------|
| Time to initial RCA | 15-30 min (manual) | ~5 seconds (AI) |
| Context sources checked | 1-2 (manual) | 3+ (automated: runbooks + DD monitors + metrics) |
| RCA consistency | Varies by engineer | Structured, evidence-based every time |
| Knowledge base utilization | Low (hard to find) | 100% (auto-retrieved + linked) |
| AI quality monitoring | None | Real-time hallucination scoring |
| Cost visibility | None | Token usage tracked per request |

---

## 9. Future Improvements

| Priority | Improvement |
|----------|-------------|
| High | Auto-trigger dari Datadog alert (tanpa manual submit ticket) |
| High | Slack/Teams integration — AI analysis langsung ke incident channel |
| Medium | Vector search for RAG (replace keyword matching) |
| Medium | More knowledge sources (Confluence, wiki, past incidents) |
| Medium | Auto-remediation — execute runbook steps otomatis |
| Low | Fine-tune hallucination checks dengan human feedback |
| Low | Multi-model support (compare Nova vs Claude vs Titan) |
| Low | Cost estimation per incident analysis |

---

## Appendix

### A. Access Information
| Resource | URL |
|----------|-----|
| App | https://54.179.171.169 |
| Dashboard | https://app.datadoghq.com/dashboard/k8i-7tt-mcc/ |
| LLM Traces | https://app.datadoghq.com/llm/traces |
| Monitors | https://app.datadoghq.com/monitors/manage |

### B. Knowledge Base Documents (S3)
| Document | Purpose |
|----------|---------|
| sop-incident-management.md | Standard incident response process |
| runbook-api-gateway.md | API Gateway troubleshooting |
| runbook-payment-service.md | Payment service incidents |
| runbook-database-infrastructure.md | Database & Redis issues |

### C. Datadog Monitors
| Monitor | Warning | Critical |
|---------|---------|----------|
| Disk Usage | 75% | 85% |
| CPU Usage | 60% | 80% |
| Memory Usage | 70% | 85% |

### D. Hallucination Scoring
| Score | Risk Level | Meaning |
|-------|-----------|---------|
| 1.0 | ✅ Low | AI output consistent with provided context |
| 0.5 | ⚠️ Medium | AI made claims not fully backed by context |
| 0.0 | 🚨 High | AI hallucinated — fabricated data or references |
