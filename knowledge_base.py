import os
import boto3
from known_issues_db import get_known_issues_by_service

BEDROCK_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")

bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name=BEDROCK_REGION)


def retrieve_from_knowledge_base(query, max_results=3):
    """Retrieve relevant documents from Bedrock Knowledge Base (S3 runbooks/SOP)."""
    if not KNOWLEDGE_BASE_ID:
        return []

    try:
        response = bedrock_agent_client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results
                }
            },
        )

        results = []
        for item in response.get("retrievalResults", []):
            results.append({
                "content": item["content"]["text"],
                "source": item.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
                "score": item.get("score", 0),
            })
        return results

    except Exception as e:
        print(f"Knowledge Base retrieval error: {e}")
        return []


def retrieve_known_issues(service_name):
    """Retrieve known issues from local SQLite database."""
    try:
        return get_known_issues_by_service(service_name)
    except Exception as e:
        print(f"Known issues retrieval error: {e}")
        return []


def build_rag_context(title, service_affected, description):
    """Build RAG context by combining KB retrieval + known issues (SQLite)."""
    query = f"{title} {service_affected} {description}"

    # Retrieve from Bedrock Knowledge Base (S3 docs)
    kb_results = retrieve_from_knowledge_base(query)

    # Retrieve known issues from SQLite
    known_issues = retrieve_known_issues(service_affected)

    # Build context string
    context_parts = []

    if kb_results:
        context_parts.append("## Relevant Documentation (from Knowledge Base)")
        for i, doc in enumerate(kb_results, 1):
            context_parts.append(f"\n### Document {i} (Source: {doc['source']})")
            context_parts.append(doc["content"][:1500])

    if known_issues:
        context_parts.append("\n## Known Issues (from Problem Database)")
        for issue in known_issues:
            context_parts.append(f"- **{issue.get('title', 'N/A')}**")
            context_parts.append(f"  Root Cause: {issue.get('root_cause', 'N/A')}")
            context_parts.append(f"  Resolution: {issue.get('resolution', 'N/A')}")

    if not context_parts:
        return ""

    return "\n".join(context_parts)
