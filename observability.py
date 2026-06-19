import os
import time
import json
from functools import wraps

# ddtrace for auto + custom instrumentation
try:
    from ddtrace import tracer, patch
    from ddtrace.llmobs import LLMObs

    # Auto-patch boto3 (captures Bedrock calls automatically)
    patch(botocore=True)

    # Initialize LLM Observability
    LLMObs.enable(
        ml_app=os.getenv("DD_LLMOBS_APP_NAME", "incident-agent"),
        api_key=os.getenv("DD_API_KEY", ""),
        site=os.getenv("DD_SITE", "datadoghq.com"),
        agentless_enabled=True,
    )
    DDTRACE_ENABLED = True
except ImportError:
    DDTRACE_ENABLED = False
    tracer = None


def trace_llm_call(func):
    """Decorator to trace LLM calls with custom metadata."""
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
            LLMObs.annotate(
                span=span,
                output_data=[{"role": "assistant", "content": result[:500]}],
                metadata={
                    "duration_ms": round(duration_ms, 2),
                },
            )

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
