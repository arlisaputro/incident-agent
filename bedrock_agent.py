import os
import json
import boto3

BEDROCK_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and Incident Response specialist.
Your job is to analyze incident tickets and provide:
1. Classification - categorize the incident type and validate/suggest severity
2. Root Cause Analysis (RCA) - identify likely root causes based on the description
3. Recommendations - provide actionable steps to resolve and prevent recurrence

Be concise, structured, and actionable. Use bullet points."""


def analyze_incident(title, severity, service_affected, description):
    user_prompt = f"""Analyze this incident ticket:

**Title:** {title}
**Severity:** {severity}
**Service Affected:** {service_affected}
**Description:** {description}

Provide your analysis in the following format:

## 🏷️ Classification
- Incident Type: (e.g. Performance, Availability, Security, Data, Network)
- Suggested Severity: (Low/Medium/High/Critical) with brief justification

## 🔍 Root Cause Analysis
- List 2-3 most likely root causes

## ✅ Recommendations
- Immediate actions (to resolve now)
- Preventive actions (to avoid recurrence)
"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
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
