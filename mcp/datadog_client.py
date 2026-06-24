import os
import json
import requests
from datetime import datetime, timedelta

DD_API_KEY = os.getenv("DD_API_KEY", "")
DD_APP_KEY = os.getenv("DD_APP_KEY", "")
DD_SITE = os.getenv("DD_SITE", "datadoghq.com")

HEADERS = {
    "DD-API-KEY": DD_API_KEY,
    "DD-APPLICATION-KEY": DD_APP_KEY,
    "Content-Type": "application/json",
}

BASE_URL = f"https://api.{DD_SITE}/api"


def get_active_monitors(service_name=None):
    """Get active/triggered monitors from Datadog, optionally filtered by service."""
    url = f"{BASE_URL}/v1/monitor"
    params = {}

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        monitors = response.json()

        # Filter only triggered/alert/warn monitors
        active = []
        for m in monitors:
            if m.get("overall_state") in ["Alert", "Warn"]:
                active.append({
                    "name": m.get("name"),
                    "state": m.get("overall_state"),
                    "message": m.get("message", "")[:200],
                    "type": m.get("type"),
                    "created": m.get("created"),
                })
        return active
    except Exception as e:
        print(f"Datadog monitors error: {e}")
        return []


def get_recent_metrics(service_name, metric="aws.ec2.cpuutilization", minutes=30):
    """Get recent metric data from Datadog."""
    url = f"{BASE_URL}/v1/query"
    now = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(minutes=minutes)).timestamp())

    params = {
        "from": start,
        "to": now,
        "query": f"avg:{metric}{{*}}",
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        series = data.get("series", [])
        if not series:
            return None

        pointlist = series[0].get("pointlist", [])
        if not pointlist:
            return None

        values = [p[1] for p in pointlist if p[1] is not None]
        if not values:
            return None

        return {
            "metric": metric,
            "service": service_name,
            "period_minutes": minutes,
            "avg": round(sum(values) / len(values), 2),
            "max": round(max(values), 2),
            "min": round(min(values), 2),
            "latest": round(values[-1], 2),
        }
    except Exception as e:
        print(f"Datadog metrics error: {e}")
        return None


def get_recent_logs(service_name, minutes=30, limit=5):
    """Get recent error logs from Datadog for a service."""
    url = f"https://api.{DD_SITE}/api/v2/logs/events/search"
    now = datetime.utcnow()
    start = now - timedelta(minutes=minutes)

    body = {
        "filter": {
            "query": f"service:{service_name} status:error",
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "indexes": ["*"],
        },
        "sort": "timestamp",
        "page": {"limit": limit},
    }

    try:
        response = requests.post(url, headers=HEADERS, json=body)
        response.raise_for_status()
        data = response.json()

        logs = []
        for event in data.get("data", []):
            attrs = event.get("attributes", {})
            logs.append({
                "timestamp": attrs.get("timestamp", ""),
                "message": attrs.get("message", "")[:300],
                "status": attrs.get("status", ""),
            })
        return logs
    except Exception as e:
        # Logs API not available in this DD plan - silently skip
        pass
        return []


def build_datadog_context(service_name):
    """Build observability context from Datadog for AI enrichment."""
    context_parts = []

    # Active monitors/alerts
    monitors = get_active_monitors(service_name)
    if monitors:
        context_parts.append("## 🚨 Active Alerts (Datadog Monitors)")
        for m in monitors:
            context_parts.append(f"- **[{m['state']}]** {m['name']}")
            if m['message']:
                context_parts.append(f"  Message: {m['message']}")

    # Recent metrics (host-level from DD Agent)
    cpu_metrics = get_recent_metrics(service_name, "system.cpu.user")
    mem_metrics = get_recent_metrics(service_name, "system.mem.pct_usable")
    disk_metrics = get_recent_metrics(service_name, "system.disk.in_use")

    if cpu_metrics or mem_metrics or disk_metrics:
        context_parts.append("\n## 📊 Recent Metrics (last 30 min)")
        if cpu_metrics:
            context_parts.append(f"- CPU: avg={cpu_metrics['avg']}%, max={cpu_metrics['max']}%, latest={cpu_metrics['latest']}%")
        if mem_metrics:
            context_parts.append(f"- Memory Available: avg={cpu_metrics['avg']}%, latest={mem_metrics['latest']}%")
        if disk_metrics:
            context_parts.append(f"- Disk In Use: avg={disk_metrics['avg']}%, max={disk_metrics['max']}%, latest={disk_metrics['latest']}%")

    # Recent error logs
    logs = get_recent_logs(service_name)
    if logs:
        context_parts.append("\n## 📝 Recent Error Logs")
        for log in logs:
            context_parts.append(f"- [{log['timestamp']}] {log['message']}")

    if not context_parts:
        return ""

    return "\n".join(context_parts)
