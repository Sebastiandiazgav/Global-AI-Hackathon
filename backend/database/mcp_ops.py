"""
MyAgent - MCP Operations Database
Manages MCP client authentication, tool policies, rate limiting, and audit logging.
Supports PostgreSQL with in-memory fallback.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from database.connection import is_database_available, get_db_session

try:
    from sqlalchemy import text
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False


_lock = Lock()
_clients: Dict[str, Dict] = {}
_tool_policies: Dict[str, Dict] = {}
_audit_log: List[Dict] = []
_rate_limit_windows: Dict[str, List[datetime]] = defaultdict(list)


# ============================================
# CLIENT MANAGEMENT
# ============================================

def validate_mcp_client(client_id: str, api_key: str) -> Tuple[bool, str, Optional[Dict]]:
    """Validate an MCP client by ID and API key."""
    # Try PostgreSQL first
    if _HAS_SQLALCHEMY and is_database_available():
        try:
            with get_db_session() as session:
                result = session.execute(
                    text("SELECT client_id, api_key, active, allowed_tools, rate_limit_per_minute FROM mcp_clients WHERE client_id = :id"),
                    {"id": client_id},
                )
                row = result.fetchone()
                if not row:
                    return False, "client_not_found", None
                if row[1] != api_key:
                    return False, "invalid_api_key", None
                if not row[2]:
                    return False, "client_disabled", None
                return True, "ok", {
                    "client_id": row[0],
                    "api_key": row[1],
                    "active": row[2],
                    "allowed_tools": row[3] or ["*"],
                    "rate_limit_per_minute": row[4] or 60,
                }
        except Exception:
            pass

    # Fallback to in-memory
    with _lock:
        client = _clients.get(client_id)
        if not client:
            return False, "client_not_found", None
        if client.get("api_key") != api_key:
            return False, "invalid_api_key", None
        if not client.get("active", True):
            return False, "client_disabled", None
        return True, "ok", client


def is_tool_allowed_for_client(client_data: Dict, tool_name: str) -> bool:
    """Check if a tool is allowed for a specific client."""
    allowed_tools = client_data.get("allowed_tools", [])
    if not allowed_tools or "*" in allowed_tools:
        return True
    return tool_name in allowed_tools


# ============================================
# TOOL POLICIES
# ============================================

def get_tool_policy(tool_name: str) -> Optional[Dict]:
    """Get the policy for a specific tool."""
    if _HAS_SQLALCHEMY and is_database_available():
        try:
            with get_db_session() as session:
                result = session.execute(
                    text("SELECT tool_name, timeout_ms, max_retries FROM mcp_tool_policies WHERE tool_name = :name"),
                    {"name": tool_name},
                )
                row = result.fetchone()
                if row:
                    return {"tool_name": row[0], "timeout_ms": row[1], "max_retries": row[2]}
        except Exception:
            pass

    with _lock:
        return _tool_policies.get(tool_name)


# ============================================
# RATE LIMITING
# ============================================

def check_mcp_rate_limit(client_id: str, limit_per_minute: int) -> Tuple[bool, int, int]:
    """
    Check rate limit for a client.
    Returns (allowed, retry_after_seconds, current_count).
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)

    with _lock:
        _rate_limit_windows[client_id] = [
            ts for ts in _rate_limit_windows[client_id] if ts > window_start
        ]
        current = len(_rate_limit_windows[client_id])

        if current >= limit_per_minute:
            oldest = min(_rate_limit_windows[client_id])
            retry_after = int((oldest + timedelta(minutes=1) - now).total_seconds()) + 1
            return False, max(retry_after, 1), current

        _rate_limit_windows[client_id].append(now)
        return True, 0, current + 1


# ============================================
# AUDIT LOGGING
# ============================================

def save_mcp_tool_audit(
    client_id: str = "",
    tool_name: str = "",
    status: str = "",
    latency_ms: int = 0,
    transport: str = "",
    server: str = "",
    trace_id: str = "",
    error: str = "",
) -> None:
    """Save an MCP tool invocation audit record."""
    record = {
        "id": uuid4().hex,
        "created_at": datetime.utcnow().isoformat(),
        "client_id": client_id,
        "tool_name": tool_name,
        "status": status,
        "latency_ms": latency_ms,
        "transport": transport,
        "server": server,
        "trace_id": trace_id,
        "error": error[:200] if error else "",
    }

    with _lock:
        _audit_log.append(record)

    if _HAS_SQLALCHEMY and is_database_available():
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO mcp_tool_audit (client_id, tool_name, status, latency_ms, transport, server, trace_id, error)
                    VALUES (:client_id, :tool_name, :status, :latency_ms, :transport, :server, :trace_id, :error)
                """), record)
        except Exception:
            pass


def get_mcp_audit_summary(days: int = 7, client_id: str = "") -> Dict:
    """Get MCP audit summary for analytics."""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with _lock:
        records = [r for r in _audit_log if r["created_at"] >= since]
        if client_id:
            records = [r for r in records if r["client_id"] == client_id]

    total = len(records)
    by_status = defaultdict(int)
    by_tool = defaultdict(int)
    latencies = []

    for r in records:
        by_status[r.get("status", "unknown")] += 1
        by_tool[r.get("tool_name", "")] += 1
        if r.get("latency_ms", 0) > 0:
            latencies.append(r["latency_ms"])

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    return {
        "period_days": days,
        "total_calls": total,
        "by_status": dict(by_status),
        "top_tools": dict(sorted(by_tool.items(), key=lambda x: x[1], reverse=True)[:5]),
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "client_id": client_id or "all",
    }


# ============================================
# SEEDING (for initial setup)
# ============================================

def register_mcp_client(client_id: str, api_key: str, allowed_tools: List[str] = None, rate_limit: int = 60) -> None:
    """Register a new MCP client."""
    client_data = {
        "client_id": client_id,
        "api_key": api_key,
        "active": True,
        "allowed_tools": allowed_tools or ["*"],
        "rate_limit_per_minute": rate_limit,
        "created_at": datetime.utcnow().isoformat(),
    }

    with _lock:
        _clients[client_id] = client_data

    if _HAS_SQLALCHEMY and is_database_available():
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO mcp_clients (client_id, api_key, active, allowed_tools, rate_limit_per_minute)
                    VALUES (:client_id, :api_key, :active, :allowed_tools::jsonb, :rate_limit)
                    ON CONFLICT (client_id) DO UPDATE SET api_key = :api_key, allowed_tools = :allowed_tools::jsonb
                """), {
                    "client_id": client_id,
                    "api_key": api_key,
                    "active": True,
                    "allowed_tools": json.dumps(allowed_tools or ["*"]),
                    "rate_limit": rate_limit,
                })
        except Exception:
            pass


def register_tool_policy(tool_name: str, timeout_ms: int = 8000, max_retries: int = 2) -> None:
    """Register a tool policy."""
    with _lock:
        _tool_policies[tool_name] = {
            "tool_name": tool_name,
            "timeout_ms": timeout_ms,
            "max_retries": max_retries,
        }

    if _HAS_SQLALCHEMY and is_database_available():
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO mcp_tool_policies (tool_name, timeout_ms, max_retries)
                    VALUES (:tool_name, :timeout_ms, :max_retries)
                    ON CONFLICT (tool_name) DO UPDATE SET timeout_ms = :timeout_ms, max_retries = :max_retries
                """), {"tool_name": tool_name, "timeout_ms": timeout_ms, "max_retries": max_retries})
        except Exception:
            pass
