"""
MyAgent - Alibaba Cloud Log Service (SLS) Integration
Sends structured logs to centralized logging for monitoring and alerting.
"""

import time
from typing import Optional
from config import get_settings

try:
    from aliyun.log import LogClient, PutLogsRequest, LogItem
    _HAS_SLS = True
except ImportError:
    _HAS_SLS = False

_client = None
_sls_available = None

SLS_PROJECT = "myagent-logs"
SLS_LOGSTORE = "app-logs"
SLS_ENDPOINT = "ap-southeast-1.log.aliyuncs.com"


def _get_client():
    """Get or create SLS client."""
    global _client, _sls_available

    if _sls_available is False:
        return None
    if _client is not None:
        return _client
    if not _HAS_SLS:
        _sls_available = False
        return None

    settings = get_settings()
    if not settings.alibaba_access_key_id or not settings.alibaba_access_key_secret:
        _sls_available = False
        return None

    try:
        _client = LogClient(SLS_ENDPOINT, settings.alibaba_access_key_id, settings.alibaba_access_key_secret)
        _sls_available = True
        print(f"✅ Log Service: Connected (project: {SLS_PROJECT})")
        return _client
    except Exception as e:
        print(f"⚠️ Log Service: Not available ({str(e)[:50]})")
        _sls_available = False
        return None


def is_sls_available() -> bool:
    """Check if SLS is connected."""
    _get_client()
    return _sls_available is True


def log_event(
    level: str = "INFO",
    event: str = "",
    agent: str = "",
    session_id: str = "",
    trace_id: str = "",
    tool: str = "",
    latency_ms: int = 0,
    details: str = "",
):
    """
    Send a structured log event to Alibaba Cloud Log Service.
    Non-blocking: fails silently if SLS is unavailable.
    """
    client = _get_client()
    if not client:
        return

    try:
        log_item = LogItem()
        log_item.set_time(int(time.time()))
        log_item.set_contents([
            ("level", level),
            ("event", event),
            ("agent", agent),
            ("session_id", session_id),
            ("trace_id", trace_id),
            ("tool", tool),
            ("latency_ms", str(latency_ms)),
            ("details", details[:500]),
            ("service", "myagent-backend"),
        ])

        request = PutLogsRequest(SLS_PROJECT, SLS_LOGSTORE, "", "", [log_item])
        client.put_logs(request)
    except Exception:
        pass  # Non-blocking


def log_agent_call(agent: str, session_id: str, trace_id: str, intent: str, latency_ms: int = 0):
    """Log an agent routing/execution event."""
    log_event(level="INFO", event="agent_call", agent=agent, session_id=session_id, trace_id=trace_id, latency_ms=latency_ms, details=intent)


def log_error(error: str, agent: str = "", session_id: str = ""):
    """Log an error event."""
    log_event(level="ERROR", event="error", agent=agent, session_id=session_id, details=error)


def log_guardrail(action: str, stage: str, session_id: str = ""):
    """Log a guardrail event."""
    log_event(level="WARN", event="guardrail", details=f"{stage}:{action}", session_id=session_id)


def log_model_fallback(exhausted_model: str, next_model: str, role: str):
    """Log a model fallback event."""
    log_event(level="WARN", event="model_fallback", details=f"{exhausted_model} -> {next_model} (role: {role})")
