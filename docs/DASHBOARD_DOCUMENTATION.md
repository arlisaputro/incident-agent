# Datadog Dashboard Documentation

## Dashboard: Incident Intelligence Agent - LLM Observability
**Dashboard ID:** k8i-7tt-mcc  
**URL:** https://app.datadoghq.com/dashboard/k8i-7tt-mcc/

---

## Section 1: 🤖 LLM Performance

Memantau performa dan usage dari AI agent (Bedrock Nova Pro) setiap kali melakukan incident analysis.

| # | Panel Name | Description & Fungsi | Metric / Query | Cara Dapat Metric |
|---|-----------|---------------------|----------------|-------------------|
| 1 | Total LLM Requests (Bedrock) | Menghitung total berapa kali AI dipanggil untuk analyze incident. Berguna untuk monitor volume usage. | `count` dari spans `service:incident-agent resource_name:InvokeModel` | Auto-captured oleh `ddtrace` library saat `patch(botocore=True)`. Setiap kali `bedrock_client.invoke_model()` dipanggil, otomatis muncul span `InvokeModel`. |
| 2 | Avg LLM Latency | Rata-rata waktu response dari Bedrock (dalam nanoseconds). Untuk detect degradasi performa LLM. | `avg @duration` dari spans `service:incident-agent resource_name:InvokeModel` | Otomatis dari `ddtrace` botocore patch. Duration diukur dari request dikirim sampai response diterima. |
| 3 | LLM Errors | Jumlah request ke Bedrock yang gagal (throttling, timeout, dll). Alert jika terlalu banyak. | `count` dari spans `service:incident-agent resource_name:InvokeModel status:error` | Otomatis dari `ddtrace`. Span di-mark error jika Bedrock return exception (ThrottlingException, ValidationException, dll). |
| 4 | Total Spans | Total semua spans (termasuk InvokeModel + sub-operations). Overview activity keseluruhan. | `count` dari spans `service:incident-agent` | Semua operations yang di-trace oleh `ddtrace` termasuk boto3 calls. |
| 5 | 🪙 Avg Input Tokens | Rata-rata jumlah token yang dikirim ke Bedrock per request. Untuk monitor prompt size / cost. | `avg:bedrock.tokens.input{service:incident-agent}` | Dikirim via DogStatsD dari `bedrock_agent.py`. Setelah `invoke_model()`, extract `result["usage"]["inputTokens"]` lalu `statsd.gauge("bedrock.tokens.input", value)`. |
| 6 | 🪙 Avg Output Tokens | Rata-rata jumlah token yang di-generate oleh Bedrock. Untuk monitor response length / cost. | `avg:bedrock.tokens.output{service:incident-agent}` | Sama seperti input tokens. Extract `result["usage"]["outputTokens"]` lalu kirim via `statsd.gauge()`. |
| 7 | 🪙 Total Tokens Used | Akumulasi total semua token (input + output) yang dipakai. Untuk cost tracking. | `sum:bedrock.tokens.total{service:incident-agent}` | Extract `inputTokens + outputTokens` dari Bedrock response, kirim via `statsd.gauge("bedrock.tokens.total", value)`. |
| 8 | 🪙 Token Usage Over Time | Bar chart perbandingan input vs output tokens over time. Visualisasi trend usage. | `avg:bedrock.tokens.input{...}` vs `avg:bedrock.tokens.output{...}` | Sama — DogStatsD gauge dari `bedrock_agent.py` setiap kali analysis selesai. |
| 9 | ⏱️ Bedrock Latency Over Time | Line chart trend latency Bedrock over time. Detect jika ada degradasi gradual. | `avg @duration` dari spans `resource_name:InvokeModel` (timeseries) | Auto dari `ddtrace` botocore patch. Setiap InvokeModel call punya duration span. |
| 10 | 📈 Request Volume by Operation | Bar chart grouped by operation type. Lihat breakdown: InvokeModel vs S3 GetObject vs lainnya. | `count` dari spans `service:incident-agent` grouped by `@resource_name` | Auto dari `ddtrace`. Semua boto3 calls (Bedrock, S3) otomatis di-trace dengan resource name masing-masing. |
| 11 | 🧠 Top Operations | Ranking operasi mana yang paling sering dipanggil (toplist). | `count` grouped by `resource_name` | Auto dari `ddtrace`. Ranking berdasarkan jumlah calls per operation. |
| 12 | 🔍 Latency by Operation | Ranking operasi mana yang paling lambat (toplist). Identify bottleneck. | `avg @duration` grouped by `resource_name` | Auto dari `ddtrace`. Ranking berdasarkan average duration per operation. |

---

## Section 2: 🧠 Hallucination Monitoring

Memantau apakah AI output akurat dan faithful terhadap context yang diberikan. Detect hallucination (AI ngarang).

| # | Panel Name | Description & Fungsi | Metric / Query | Cara Dapat Metric |
|---|-----------|---------------------|----------------|-------------------|
| 1 | Legend / Guide (Note) | Tabel penjelasan arti score: 1.0 = safe, 0.5 = medium risk, 0.0 = hallucinated. Reference untuk pembaca dashboard. | — (static text) | — |
| 2 | Faithfulness Score (latest) | Nilai terakhir faithfulness. Semakin tinggi (mendekati 1.0) = AI semakin akurat. Jika turun ke 0.0 = AI hallucinate. | `avg:llm.hallucination.faithfulness{service:incident-agent}` | Dihitung di `observability.py` → function `_check_hallucination(output, context)` membandingkan AI output vs context yang diberikan. Score dikirim via `statsd.gauge("llm.hallucination.faithfulness", score)`. |
| 3 | 📈 Faithfulness Over Time | Line chart trend faithfulness score. Monitor apakah AI quality improve atau degrade over time. | `avg:llm.hallucination.faithfulness{service:incident-agent}` (timeseries) | Sama — setiap analysis selesai, score dihitung dan dikirim ke DogStatsD. Chart menunjukkan trend. |

### Hallucination Check Logic

Checks yang dijalankan (di `observability._check_hallucination`):

| Check | Apa yang Dicek | Contoh Hallucination |
|-------|---------------|---------------------|
| Fake Percentages | AI claim angka % yang tidak ada di context maupun common thresholds | AI bilang "CPU at 73%" tapi data DD cuma menunjukkan 0.85% |
| Phantom Alerts | AI claim ada "active alert" tapi tidak ada alert data di context | AI bilang "Based on the active alert..." tapi DD monitors semua OK |
| Non-existent Docs | AI reference runbook filename yang tidak exist di S3 | AI bilang "See runbook-kubernetes.md" tapi file itu tidak ada |

---

## Section 3: 🖥️ Infra Compute (EC2)

Memantau kesehatan infrastructure EC2 instance yang menjalankan aplikasi.

| # | Panel Name | Description & Fungsi | Metric / Query | Cara Dapat Metric |
|---|-----------|---------------------|----------------|-------------------|
| 1 | CPU Utilization (%) | Persentase CPU yang digunakan. Alert jika sustained tinggi (app overloaded). | `avg:system.cpu.user{*}` | Auto-collected oleh Datadog Agent yang terinstall di EC2. Agent report setiap 15 detik. |
| 2 | Memory Usage | Jumlah memory yang digunakan (bytes). Detect memory leaks atau app butuh scale up. | `avg:system.mem.used{*}` | Auto-collected oleh Datadog Agent. Baca dari `/proc/meminfo`. |
| 3 | Disk Usage (%) | Persentase disk terpakai. Critical jika mendekati 100% (app bisa crash). | `avg:system.disk.in_use{*} * 100` | Auto-collected oleh Datadog Agent. Baca dari `df` equivalent. |
| 4 | Network In/Out (bytes) | Traffic network masuk dan keluar. Detect anomali traffic atau DDoS. | `avg:system.net.bytes_rcvd{*}` + `avg:system.net.bytes_sent{*}` | Auto-collected oleh Datadog Agent. Baca dari `/proc/net/dev`. |

---

## Sumber Data Summary

| Source | Metrics yang Dihasilkan | Mechanism |
|--------|------------------------|-----------|
| `ddtrace` (auto-patch botocore) | Span count, duration, errors, resource_name | Otomatis — library intercept semua boto3 API calls |
| `DogStatsD` (dari app code) | bedrock.tokens.*, llm.hallucination.* | Manual — code kirim via `statsd.gauge()` / `statsd.increment()` |
| `Datadog Agent` (system) | system.cpu.*, system.mem.*, system.disk.*, system.net.* | Otomatis — agent collect OS-level metrics setiap 15 detik |
| `LLMObs SDK` (ddtrace.llmobs) | LLM traces, evaluations (faithfulness, hallucination_risk) | Manual — code annotate spans via `LLMObs.annotate()` + `LLMObs.submit_evaluation()` |

---

## How to Access

1. **Dashboard:** https://app.datadoghq.com/dashboard/k8i-7tt-mcc/
2. **LLM Traces (detail per-request):** https://app.datadoghq.com/llm/traces → filter `ml_app:incident-agent`
3. **Monitors:** https://app.datadoghq.com/monitors/manage → filter `service:incident-agent`
