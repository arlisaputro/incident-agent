import os
import boto3
from known_issues_db import get_known_issues_by_service

BEDROCK_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_BUCKET = os.getenv("KB_S3_BUCKET", "incident-agent-knowledge-base-6ca579d6")
S3_PREFIX = os.getenv("KB_S3_PREFIX", "docs/")

s3_client = boto3.client("s3", region_name=BEDROCK_REGION)

# Mapping: service name keywords → relevant S3 doc keys
SERVICE_DOC_MAP = {
    "api-gateway": ["docs/runbook-api-gateway.md"],
    "gateway": ["docs/runbook-api-gateway.md"],
    "payment": ["docs/runbook-payment-service.md"],
    "payment-service": ["docs/runbook-payment-service.md"],
    "database": ["docs/runbook-database-infrastructure.md"],
    "postgres": ["docs/runbook-database-infrastructure.md"],
    "redis": ["docs/runbook-database-infrastructure.md"],
    "infrastructure": ["docs/runbook-database-infrastructure.md"],
}


def retrieve_from_s3(service_affected, title="", description=""):
    """Retrieve relevant docs from S3 based on service name keyword matching."""
    try:
        # Find matching docs by service name
        matched_keys = set()
        search_terms = [service_affected.lower(), title.lower()]

        for term in search_terms:
            for keyword, doc_keys in SERVICE_DOC_MAP.items():
                if keyword in term:
                    matched_keys.update(doc_keys)

        # Always include SOP
        matched_keys.add("docs/sop-incident-management.md")

        # Download and return matched docs
        results = []
        for key in matched_keys:
            try:
                response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                content = response["Body"].read().decode("utf-8")
                results.append({
                    "content": content[:2000],
                    "source": f"s3://{S3_BUCKET}/{key}",
                })
            except Exception as e:
                print(f"S3 read error for {key}: {e}")

        return results
    except Exception as e:
        print(f"S3 retrieval error: {e}")
        return []


def retrieve_known_issues(service_name):
    """Retrieve known issues from local SQLite database."""
    try:
        return get_known_issues_by_service(service_name)
    except Exception as e:
        print(f"Known issues retrieval error: {e}")
        return []


def build_rag_context(title, service_affected, description):
    """Build RAG context by combining S3 docs + known issues (SQLite)."""
    # Retrieve from S3 directly
    kb_results = retrieve_from_s3(service_affected, title, description)

    # Retrieve known issues from SQLite
    known_issues = retrieve_known_issues(service_affected)

    # Build context string
    context_parts = []

    if kb_results:
        context_parts.append("## Relevant Documentation (from Knowledge Base)")
        for i, doc in enumerate(kb_results, 1):
            doc_name = doc["source"].split("/")[-1].replace(".md", "").replace("-", " ").title()
            context_parts.append(f"\n### Document {i}: {doc_name}")
            context_parts.append(doc["content"])

    if known_issues:
        context_parts.append("\n## Known Issues (from Problem Database)")
        for issue in known_issues:
            context_parts.append(f"- **{issue.get('title', 'N/A')}**")
            context_parts.append(f"  Root Cause: {issue.get('root_cause', 'N/A')}")
            context_parts.append(f"  Resolution: {issue.get('resolution', 'N/A')}")

    if not context_parts:
        return ""

    return "\n".join(context_parts)
