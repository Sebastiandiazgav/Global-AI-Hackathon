"""
MyAgent - Persistence Layer
Uses PostgreSQL (ApsaraDB RDS) when available, falls back to in-memory store.
Dual-mode: detects DB availability at startup and routes accordingly.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List
from uuid import uuid4

from database.connection import is_database_available, get_db_session

try:
    from sqlalchemy import text
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False


def _utcnow_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


# ============================================
# IN-MEMORY STORE (Fallback)
# ============================================

class _InMemoryStore:
    """In-memory store for development and when DB is unavailable."""

    def __init__(self):
        self._lock = Lock()
        self._transactions: List[Dict[str, Any]] = []
        self._agent_calls: List[Dict[str, Any]] = []
        self._guardrail_events: List[Dict[str, Any]] = []

    def save_transaction(self, **kwargs) -> None:
        with self._lock:
            self._transactions.append({"id": uuid4().hex, "created_at": _utcnow_iso(), **kwargs})

    def get_transactions(self, limit: int = 50, days: int = 7, session_id: str = "") -> List[Dict]:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
        with self._lock:
            txns = [t for t in self._transactions if t["created_at"] >= since]
            if session_id:
                txns = [t for t in txns if t.get("session_id", "") == session_id]
        txns.sort(key=lambda x: x["created_at"], reverse=True)
        return txns[:limit]

    def save_agent_call(self, **kwargs) -> None:
        with self._lock:
            self._agent_calls.append({"id": uuid4().hex, "created_at": _utcnow_iso(), **kwargs})

    def save_guardrail_event(self, **kwargs) -> None:
        with self._lock:
            self._guardrail_events.append({"id": uuid4().hex, "created_at": _utcnow_iso(), **kwargs})

    def get_analytics_summary(self, days: int = 7) -> Dict:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
        with self._lock:
            transactions = [t for t in self._transactions if t["created_at"] >= since]
            agent_calls = [a for a in self._agent_calls if a["created_at"] >= since]
            guardrail_blocks = [g for g in self._guardrail_events if g["created_at"] >= since and g.get("action") == "blocked"]

        total_commission = round(sum(float(t.get("commission", 0) or 0) for t in transactions), 2)

        by_type: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "commission": 0.0})
        top_tools: Counter = Counter()
        daily: Dict[str, Dict] = defaultdict(lambda: {"commission": 0.0, "transactions": 0})
        mcp_calls = sum(1 for t in transactions if t.get("transport") == "mcp")
        fallback_calls = sum(1 for t in transactions if t.get("transport") == "fallback_direct")

        for t in transactions:
            bucket = by_type[t.get("type", "other")]
            bucket["count"] += 1
            bucket["commission"] += float(t.get("commission", 0) or 0)
            if t.get("tool_name"):
                top_tools[t["tool_name"]] += 1
            day = t["created_at"][:10]
            daily[day]["commission"] += float(t.get("commission", 0) or 0)
            daily[day]["transactions"] += 1

        agent_usage = Counter(a.get("agent", "") for a in agent_calls if a.get("agent"))

        return {
            "period_days": days,
            "total_transactions": len(transactions),
            "total_commission": total_commission,
            "by_type": [{"type": k, "count": v["count"], "commission": round(v["commission"], 2)} for k, v in sorted(by_type.items())],
            "agent_usage": [{"agent": a, "calls": c} for a, c in agent_usage.most_common()],
            "guardrail_blocks": len(guardrail_blocks),
            "mcp_calls": mcp_calls,
            "fallback_calls": fallback_calls,
            "daily_trend": [{"day": k, **v} for k, v in sorted(daily.items())],
            "top_tools": [{"tool_name": n, "uses": c} for n, c in top_tools.most_common(5)],
        }


# ============================================
# POSTGRESQL STORE
# ============================================

class _PostgreSQLStore:
    """PostgreSQL-backed persistence using SQLAlchemy."""

    def __init__(self):
        self._fallback = _InMemoryStore()

    def save_transaction(self, **kwargs) -> None:
        self._fallback.save_transaction(**kwargs)  # Always keep in-memory copy
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO transactions (type, tool_name, description, commission, amount, agent, session_id, transport, metadata)
                    VALUES (:type, :tool_name, :description, :commission, :amount, :agent, :session_id, :transport, :metadata::jsonb)
                """), {
                    "type": kwargs.get("type", ""),
                    "tool_name": kwargs.get("tool_name", ""),
                    "description": kwargs.get("description", ""),
                    "commission": kwargs.get("commission", 0),
                    "amount": kwargs.get("amount", 0),
                    "agent": kwargs.get("agent", ""),
                    "session_id": kwargs.get("session_id", ""),
                    "transport": kwargs.get("transport", ""),
                    "metadata": json.dumps(kwargs.get("metadata") or {}),
                })
        except Exception:
            pass  # Fallback already saved

    def get_transactions(self, limit: int = 50, days: int = 7, session_id: str = "") -> List[Dict]:
        if not _HAS_SQLALCHEMY or not is_database_available():
            return self._fallback.get_transactions(limit, days, session_id)
        try:
            with get_db_session() as session:
                query = f"""
                    SELECT id, created_at, type, tool_name, description, commission, amount, agent, session_id, transport, metadata
                    FROM transactions
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                """
                params = {}
                if session_id:
                    query += " AND session_id = :session_id"
                    params["session_id"] = session_id
                query += f" ORDER BY created_at DESC LIMIT {limit}"

                result = session.execute(text(query), params)
                rows = result.fetchall()
                return [
                    {
                        "id": str(row[0]),
                        "created_at": row[1].isoformat() if row[1] else "",
                        "type": row[2],
                        "tool_name": row[3],
                        "description": row[4],
                        "commission": float(row[5] or 0),
                        "amount": float(row[6] or 0),
                        "agent": row[7],
                        "session_id": row[8],
                        "transport": row[9],
                        "metadata": row[10] or {},
                    }
                    for row in rows
                ]
        except Exception:
            return self._fallback.get_transactions(limit, days, session_id)

    def save_agent_call(self, **kwargs) -> None:
        self._fallback.save_agent_call(**kwargs)
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO agent_calls (session_id, trace_id, agent, intent, tools_used, confidence, response_time_ms, language)
                    VALUES (:session_id, :trace_id, :agent, :intent, :tools_used::jsonb, :confidence, :response_time_ms, :language)
                """), {
                    "session_id": kwargs.get("session_id", ""),
                    "trace_id": kwargs.get("trace_id", ""),
                    "agent": kwargs.get("agent", ""),
                    "intent": kwargs.get("intent", ""),
                    "tools_used": json.dumps(kwargs.get("tools_used") or []),
                    "confidence": kwargs.get("confidence", 0),
                    "response_time_ms": kwargs.get("response_time_ms", 0),
                    "language": kwargs.get("language", "es"),
                })
        except Exception:
            pass

    def save_guardrail_event(self, **kwargs) -> None:
        self._fallback.save_guardrail_event(**kwargs)
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO guardrail_events (event_type, stage, action, message_preview, session_id, category)
                    VALUES (:event_type, :stage, :action, :message_preview, :session_id, :category)
                """), {
                    "event_type": kwargs.get("event_type", ""),
                    "stage": kwargs.get("stage", ""),
                    "action": kwargs.get("action", ""),
                    "message_preview": str(kwargs.get("message_preview", ""))[:200],
                    "session_id": kwargs.get("session_id", ""),
                    "category": kwargs.get("category", ""),
                })
        except Exception:
            pass

    def get_analytics_summary(self, days: int = 7) -> Dict:
        # Use in-memory for now (always has data)
        # TODO: Query PostgreSQL when production data accumulates
        return self._fallback.get_analytics_summary(days)


# ============================================
# STORE INITIALIZATION
# ============================================

def _build_store():
    """Build the appropriate store based on configuration."""
    if _HAS_SQLALCHEMY and is_database_available():
        print("📦 Database: PostgreSQL (connected)")
        return _PostgreSQLStore()
    else:
        print("📦 Database: In-memory (development mode)")
        return _InMemoryStore()


_STORE = None


def _get_store():
    global _STORE
    if _STORE is None:
        _STORE = _build_store()
    return _STORE


# ============================================
# PUBLIC API
# ============================================

def save_transaction(
    type: str = "",
    tool_name: str = "",
    description: str = "",
    commission: float = 0,
    amount: float = 0,
    agent: str = "",
    session_id: str = "",
    transport: str = "",
    metadata: dict = None,
):
    """Save a transaction."""
    _get_store().save_transaction(
        type=type, tool_name=tool_name, description=description,
        commission=commission, amount=amount, agent=agent,
        session_id=session_id, transport=transport, metadata=metadata or {},
    )


def get_transactions(limit: int = 50, days: int = 7, session_id: str = "") -> List[Dict]:
    """Get recent transactions."""
    return _get_store().get_transactions(limit=limit, days=days, session_id=session_id)


def save_agent_call(
    session_id: str = "",
    agent: str = "",
    trace_id: str = "",
    intent: str = "",
    tools_used: list = None,
    confidence: float = 0,
    response_time_ms: int = 0,
    language: str = "es",
):
    """Save an agent call for analytics."""
    _get_store().save_agent_call(
        session_id=session_id, agent=agent, trace_id=trace_id,
        intent=intent, tools_used=list(tools_used or []),
        confidence=confidence, response_time_ms=response_time_ms,
        language=language,
    )


def save_guardrail_event(
    event_type: str = "",
    stage: str = "",
    action: str = "",
    message_preview: str = "",
    session_id: str = "",
    category: str = "",
):
    """Save a guardrail event."""
    _get_store().save_guardrail_event(
        event_type=event_type, stage=stage, action=action,
        message_preview=message_preview[:200], session_id=session_id,
        category=category,
    )


def get_analytics_summary(days: int = 7) -> Dict:
    """Get analytics summary."""
    return _get_store().get_analytics_summary(days=days)
