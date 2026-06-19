import os
import json
import boto3
from knowledge_base import build_rag_context
from mcp import build_datadog_context
from observability import trace_llm_call, trace_rag_retrieval, trace_datadog_mcp

BEDROCK_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and Incident Response specialist.
Your job is to analyze incident tickets and provide:
1. Classification - categorize the incident type and validate/suggest severity
2. Root Cause Analysis (RCA) - identify likely root causes based on the description
3. Recommendations - provide actionable steps to resolve and prevent recurrence

You have access to:
- Organizational knowledge base (runbooks, SOPs)
- Known issues database
- Real-time observability data from Datadog (monitors, metrics, logs)

Use ALL provided context to give accurate and specific recommendations.
If Datadog shows active alerts or anomalies, factor them into your RCA.
If context is available, reference specific runbook steps.

Be concise, structured, and actionable. Use bullet points."""


@trace_rag_retrieval
def _retrieve_rag_context(title, service_affected, description):
    return build_rag_context(title, service_affected, description)


@trace_datadog_mcp
def _retrieve_datadog_context(service_name):
    return build_datadog_context(service_name)


@trace_llm_call
def analyze_incident(title, severity, service_affected, description):
    # Build RAG context (Knowledge Base + DynamoDB)
    rag_context = _retrieve_rag_context(title, service_affected, description)

    # Build Datadog MCP context (monitors, metrics, logs)
    datadog_context = _retrieve_datadog_context(service_affected)

    # Assemble context sections
    context_section = ""

    if rag_context:
        context_section += f"""
---
## 📚 Retrieved Context (Knowledge Base & Known Issues)

{rag_context}
"""

    if datadog_context:
        context_section += f"""
---
## 📡 Real-time Observability (Datadog)

{datadog_context}
"""

    if context_section:
        context_section += "\n---\n"

    user_prompt = f"""Analyze this incident ticket:

**Title:** {title}
**Severity:** {severity}
**Service Affected:** {service_affected}
**Description:** {description}

{context_section}

Provide your analysis in the following format:

## 🏷️ Classification
- Incident Type: (e.g. Performance, Availability, Security, Data, Network)
- Suggested Severity: (Low/Medium/High/Critical) with brief justification

## 🔍 Root Cause Analysis
- List 2-3 most likely root causes
- Reference any relevant known issues if found in context
- Correlate with Datadog metrics/alerts if available

## ✅ Recommendations
- Immediate actions (to resolve now)
- Preventive actions (to avoid recurrence)
- Reference specific runbook steps if available from context

## 📊 Observability Insights
- Summarize relevant signals from Datadog (if available)
- Suggest additional monitoring/alerting to add
"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
    })

    response = bedrock_client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]
