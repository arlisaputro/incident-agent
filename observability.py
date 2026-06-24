import os
import time
import json
import re
from functools import wraps

# ddtrace for auto + custom instrumentation
try:
    from ddtrace import tracer, patch
    from ddtrace.llmobs import LLMObs

    # Auto-patch boto3 (captures Bedrock calls automatically)
    patch(botocore=True)

    # Initialize LLM Observability (only if DD_API_KEY is set)
    if os.getenv("DD_API_KEY"):
        LLMObs.enable(
            ml_app=os.getenv("DD_LLMOBS_APP_NAME", "incident-agent"),
            api_key=os.getenv("DD_API_KEY"),
            site=os.getenv("DD_SITE", "datadoghq.com"),
            agentless_enabled=True,
        )
        DDTRACE_ENABLED = True
    else:
        DDTRACE_ENABLED = False
        tracer = None
except (ImportError, ValueError):
    DDTRACE_ENABLED = False
    tracer = None


def _check_hallucination(output, context):
    """Simple hallucination check: verify AI claims against provided context."""
    if not context or not output:
        return {"score": "unknown", "reason": "No context to verify against"}

    issues = []
    context_lower = context.lower()

    # Check 1: AI mentions specific percentages - verify they exist in context or input
    percentages_in_output = re.findall(r'(\d+(?:\.\d+)?)\s*%', output)
    # Common thresholds AI might suggest (not hallucination)
    common_thresholds = [10, 12, 15, 20, 25, 30, 50, 75, 80, 85, 90, 95, 99, 100]
    for pct in percentages_in_output:
        pct_float = float(pct)
        if pct not in context and pct_float not in common_thresholds:
            if pct not in context_lower:
                issues.append(f"Percentage {pct}% claimed but not in provided data")

    # Check 2: AI says "active alert" but no alerts in context
    if "active alert" in output.lower() and "active alerts" not in context_lower and "🚨" not in context:
        issues.append("Claims active alert but none in context")

    # Check 3: AI references runbook that wasn't in context
    valid_docs = ["sop-incident-management", "runbook-api-gateway", "runbook-payment-service", "runbook-database-infrastructure"]
    doc_refs = re.findall(r'docs/([\w-]+)\.md', output)
    for doc in doc_refs:
        if doc not in valid_docs:
            issues.append(f"References non-existent doc: {doc}")

    # Score
    if not issues:
        return {"score": "low", "reason": "No hallucination detected"}
    elif len(issues) <= 2:
        return {"score": "medium", "reason": "; ".join(issues[:3])}
    else:
        return {"score": "high", "reason": "; ".join(issues[:5])}


def trace_llm_call(func):
    """Decorator to trace LLM calls with hallucination evaluation."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DDTRACE_ENABLED:
            return func(*args, **kwargs)

        with LLMObs.llm(
            model_name=os.getenv("BEDROCK_MODEL_ID", "claude-3-sonnet"),
            name="incident_analysis",
            model_provider="aws_bedrock",
        ) as span:
            start_time = time.time()

            # Annotate input
            if args:
                LLMObs.annotate(
                    span=span,
                    input_data=[{"role": "user", "content": f"Incident: {args[0]}"}],
                    metadata={
                        "severity": args[1] if len(args) > 1 else "unknown",
                        "service": args[2] if len(args) > 2 else "unknown",
                    },
                )

            result = func(*args, **kwargs)

            # Annotate output
            duration_ms = (time.time() - start_time) * 1000

            # Get context stored by analyze_incident
            context = getattr(func, '_last_context', '')

            # Run hallucination check
            hallucination = _check_hallucination(result, context)

            LLMObs.annotate(
                span=span,
                output_data=[{"role": "assistant", "content": result[:500]}],
                metadata={
                    "duration_ms": round(duration_ms, 2),
                    "hallucination_risk": hallucination["score"],
                    "hallucination_reason": hallucination["reason"],
                },
                tags={
                    "hallucination_risk": hallucination["score"],
                },
            )

            # Submit evaluation to LLM Obs
            try:
                LLMObs.submit_evaluation(
                    span_context=span,
                    label="faithfulness",
                    metric_type="score",
                    value=1.0 if hallucination["score"] == "low" else 0.5 if hallucination["score"] == "medium" else 0.0,
                )
                LLMObs.submit_evaluation(
                    span_context=span,
                    label="hallucination_risk",
                    metric_type="categorical",
                    value=hallucination["score"],
                )
            except Exception:
                pass

            # Also send as DogStatsD metric for dashboard
            try:
                from datadog import statsd
                score_val = 1.0 if hallucination["score"] == "low" else 0.5 if hallucination["score"] == "medium" else 0.0
                statsd.gauge("llm.hallucination.faithfulness", score_val, tags=["service:incident-agent"])
                # Count per risk level (use gauge with 1 so dashboard shows cumulative)
                statsd.gauge("llm.hallucination.risk.low", 1 if hallucination["score"] == "low" else 0, tags=["service:incident-agent"])
                statsd.gauge("llm.hallucination.risk.medium", 1 if hallucination["score"] == "medium" else 0, tags=["service:incident-agent"])
                statsd.gauge("llm.hallucination.risk.high", 1 if hallucination["score"] == "high" else 0, tags=["service:incident-agent"])
            except Exception:
                pass

            LLMObs.flush()
            return result

    return wrapper


def trace_rag_retrieval(func):
    """Decorator to trace RAG retrieval operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DDTRACE_ENABLED:
            return func(*args, **kwargs)

        with LLMObs.retrieval(
            name="rag_retrieval",
        ) as span:
            start_time = time.time()

            result = func(*args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            LLMObs.annotate(
                span=span,
                input_data=args[0] if args else "unknown query",
                output_data=result[:1000] if isinstance(result, str) else str(result)[:1000],
                metadata={
                    "duration_ms": round(duration_ms, 2),
                    "source": "bedrock_kb+dynamodb",
                },
            )

            return result

    return wrapper


def trace_datadog_mcp(func):
    """Decorator to trace Datadog MCP context retrieval."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DDTRACE_ENABLED:
            return func(*args, **kwargs)

        with LLMObs.retrieval(
            name="datadog_mcp_context",
        ) as span:
            start_time = time.time()

            result = func(*args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            LLMObs.annotate(
                span=span,
                input_data=args[0] if args else "unknown service",
                output_data=result[:1000] if isinstance(result, str) else "",
                metadata={
                    "duration_ms": round(duration_ms, 2),
                    "source": "datadog_api",
                },
            )

            return result

    return wrapper
