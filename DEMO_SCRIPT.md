# 🎤 Demo Script – Incident Intelligence Agent (3 Minutes)

## Pitch Structure

| Time | Section | Duration |
|------|---------|----------|
| 0:00 | Problem Statement | 30 sec |
| 0:30 | Solution Overview | 30 sec |
| 1:00 | Live Demo | 90 sec |
| 2:30 | Architecture & Tech Stack | 20 sec |
| 2:50 | Closing & Impact | 10 sec |

---

## 🎬 Script

### [0:00 – 0:30] Problem Statement

> "Bayangkan jam 2 pagi, alert masuk: payment service down. On-call engineer bangun, buka laptop, tapi bingung harus mulai dari mana.
>
> Dia harus cek 5 dashboard, baca runbook yang panjang, cari tahu apakah ini known issue atau bukan — semua manual, semua lambat.
>
> Rata-rata MTTR (Mean Time To Resolve) bisa 45 menit sampai 2 jam, padahal setiap menit downtime = revenue loss."

---

### [0:30 – 1:00] Solution Overview

> "Kami membangun **Incident Intelligence Agent** — AI copilot yang otomatis menganalisis incident dalam hitungan detik.
>
> Cara kerjanya: engineer tinggal submit ticket, AI langsung:
> 1. **Classify** — tentukan tipe dan severity
> 2. **Analyze** — generate Root Cause Analysis berdasarkan runbook + known issues
> 3. **Recommend** — kasih action steps spesifik
>
> Yang bikin beda: AI kami punya akses ke **real-time Datadog data** — jadi dia tahu ada alert apa, CPU berapa, error log terakhir apa. Bukan cuma analisis berdasarkan teks, tapi correlate dengan observability data."

---

### [1:00 – 2:30] Live Demo

#### Demo 1: Create Incident (15 sec)
> "Ini UI-nya. Saya buat ticket: **'Payment timeout spike'**, severity **High**, service **payment-service**, description: 'HTTP 504 responses increasing, customers unable to complete checkout.'"
>
> *[Submit ticket]*

#### Demo 2: AI Analysis (45 sec)
> "Sekarang saya klik **Analyze with AI**..."
>
> *[Klik tombol, tunggu loading]*
>
> "Dalam 3 detik, AI sudah kasih:
> - **Classification**: Performance issue, severity validated as High
> - **RCA**: kemungkinan besar connection pool exhaustion — dan ini match dengan known issue KI-001 dari database kami
> - **Recommendations**: immediate action — increase pool size, enable circuit breaker. Ini langsung reference dari runbook payment service halaman specific
> - **Observability Insights**: Datadog menunjukkan CPU spike 87% dan ada 3 active alerts di service ini"

#### Demo 3: Datadog LLM Observability (30 sec)
> "Di balik layar, setiap AI call di-trace oleh Datadog LLM Observability."
>
> *[Buka Datadog dashboard]*
>
> "Kita bisa lihat:
> - Latency: 2.8 detik end-to-end
> - Token usage: 450 input, 380 output
> - Full trace: RAG retrieval → Datadog MCP query → LLM inference
> - Ini production-grade monitoring — kita tahu persis berapa cost per request dan kalau ada degradation"

---

### [2:30 – 2:50] Architecture & Tech Stack

> "Tech stack-nya:
> - **Amazon Bedrock** (Amazon Nova Pro) — reasoning engine
> - **Bedrock Knowledge Base** — RAG dari S3 runbooks
> - **DynamoDB** — known issues database
> - **Datadog MCP** — real-time observability context
> - **Datadog LLM Obs** — full AI pipeline tracing
> - Semua infra as code pakai **Terraform**, deploy ke **EC2 + RDS**"

---

### [2:50 – 3:00] Closing & Impact

> "Dengan Incident Intelligence Agent, kita bisa compress MTTR dari 45 menit jadi **under 5 menit** — karena engineer langsung dapat RCA + action steps + context dari day one.
>
> It's not replacing engineers, it's **giving them superpowers at 2 AM**.
>
> Terima kasih."

---

## 💡 Demo Tips

1. **Pre-seed data** — Pastikan sudah ada 1-2 ticket + DynamoDB known issues sebelum demo
2. **Warm up Bedrock** — Invoke sekali sebelum presentasi supaya tidak cold start
3. **Buka Datadog dashboard** di tab terpisah, siap switch
4. **Backup plan** — Kalau Bedrock lambat, siapkan screenshot hasil analisis
5. **Eye contact** — Jangan terlalu fokus ke layar, jelaskan sambil lihat juri

---

## 🏆 Key Messages untuk Juri

- **Business value** → MTTR reduction (45 min → <5 min)
- **Technical depth** → RAG + MCP + LLM Observability (bukan cuma wrapper ChatGPT)
- **Production-ready** → Full tracing, cost monitoring, IaC, proper security (IAM roles, SG, private subnets)
- **Differentiation** → Real-time Datadog correlation (bukan AI yang kerja di vacuum)
