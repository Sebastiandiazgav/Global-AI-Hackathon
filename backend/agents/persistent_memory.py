"""
MyAgent - Persistent Memory Engine
Manages cross-session memory: preferences, patterns, client info, and insights.
Implements intelligent forgetting (TTL + relevance decay) and selective recall.

Memory Types:
- preference: User habits and preferences ("always sells Netflix", "prefers morning shifts")
- pattern: Detected behavioral patterns ("sells more on weekends", "high recharge volume Fridays")
- client_info: Anonymized frequent client data ("client ***4521 picks up packages Mondays")
- service_history: Summary of past services performed
- insight: AI-generated observations about the business

Storage: PostgreSQL when available, in-memory fallback for development.
"""

from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from database.connection import is_database_available, get_db_session

try:
    from sqlalchemy import text
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False


# Memory type constants
MEMORY_PREFERENCE = "preference"
MEMORY_PATTERN = "pattern"
MEMORY_CLIENT_INFO = "client_info"
MEMORY_SERVICE_HISTORY = "service_history"
MEMORY_INSIGHT = "insight"

# TTL by type (days)
MEMORY_TTL = {
    MEMORY_PREFERENCE: 180,
    MEMORY_PATTERN: 90,
    MEMORY_CLIENT_INFO: 60,
    MEMORY_SERVICE_HISTORY: 30,
    MEMORY_INSIGHT: 14,
}

# Max memories per session per type
MAX_MEMORIES_PER_TYPE = {
    MEMORY_PREFERENCE: 20,
    MEMORY_PATTERN: 15,
    MEMORY_CLIENT_INFO: 30,
    MEMORY_SERVICE_HISTORY: 50,
    MEMORY_INSIGHT: 10,
}


class PersistentMemoryStore:
    """
    Cross-session persistent memory store.
    
    Features:
    - Store memories with type, relevance, and TTL
    - Recall memories by session, type, or keyword relevance
    - Intelligent forgetting: expired memories are pruned, low-relevance decays
    - Access tracking: frequently accessed memories get relevance boost
    """

    def __init__(self):
        self._lock = Lock()
        self._memories: Dict[str, List[Dict]] = {}  # session_id -> memories

    def store(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        relevance: float = 0.7,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Store a new memory.
        
        Args:
            session_id: Session/user identifier
            memory_type: One of preference, pattern, client_info, service_history, insight
            content: The memory content (natural language)
            relevance: Initial relevance score (0.0 - 1.0)
            metadata: Additional structured data
            
        Returns:
            Memory ID
        """
        memory_id = uuid4().hex
        ttl_days = MEMORY_TTL.get(memory_type, 30)
        now = datetime.utcnow()

        memory = {
            "id": memory_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "content": content,
            "relevance": min(max(relevance, 0.0), 1.0),
            "access_count": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_accessed": now.isoformat(),
            "expires_at": (now + timedelta(days=ttl_days)).isoformat(),
            "metadata": metadata or {},
        }

        # Store in-memory
        with self._lock:
            if session_id not in self._memories:
                self._memories[session_id] = []
            self._memories[session_id].append(memory)
            self._enforce_limits(session_id, memory_type)

        # Store in PostgreSQL
        self._persist_to_db(memory)

        return memory_id

    def recall(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
        min_relevance: float = 0.3,
    ) -> List[Dict]:
        """
        Recall memories for a session.
        
        Args:
            session_id: Session to recall from
            memory_type: Filter by type (optional)
            query: Keyword search in content (optional)
            limit: Max results
            min_relevance: Minimum relevance threshold
            
        Returns:
            List of memories sorted by relevance (descending)
        """
        # Prune expired memories first
        self._prune_expired(session_id)

        with self._lock:
            memories = self._memories.get(session_id, [])

        # Filter
        filtered = []
        for m in memories:
            if m["relevance"] < min_relevance:
                continue
            if memory_type and m["memory_type"] != memory_type:
                continue
            if query:
                query_lower = query.lower()
                if query_lower not in m["content"].lower():
                    # Simple keyword matching; skip if no match
                    continue
            filtered.append(m)

        # Sort by relevance descending, then by recency
        filtered.sort(key=lambda x: (x["relevance"], x["last_accessed"]), reverse=True)

        # Update access counts for returned memories
        results = filtered[:limit]
        for m in results:
            self._touch_memory(session_id, m["id"])

        return results

    def recall_for_context(self, session_id: str, current_query: str = "", limit: int = 5) -> str:
        """
        Recall memories formatted as context for an agent prompt.
        Returns a natural language summary of relevant memories.
        """
        memories = self.recall(session_id, query=current_query, limit=limit, min_relevance=0.4)

        if not memories:
            return ""

        lines = ["[Persistent Memory Context]"]
        for m in memories:
            type_label = {
                MEMORY_PREFERENCE: "📌 Preference",
                MEMORY_PATTERN: "📊 Pattern",
                MEMORY_CLIENT_INFO: "👤 Client",
                MEMORY_SERVICE_HISTORY: "📋 History",
                MEMORY_INSIGHT: "💡 Insight",
            }.get(m["memory_type"], "📝 Note")
            lines.append(f"- {type_label}: {m['content']}")

        return "\n".join(lines)

    def forget(self, session_id: str, memory_id: str) -> bool:
        """Explicitly forget (delete) a specific memory."""
        with self._lock:
            memories = self._memories.get(session_id, [])
            before = len(memories)
            self._memories[session_id] = [m for m in memories if m["id"] != memory_id]
            removed = len(self._memories[session_id]) < before

        if removed:
            self._delete_from_db(memory_id)

        return removed

    def forget_by_type(self, session_id: str, memory_type: str) -> int:
        """Forget all memories of a specific type for a session."""
        with self._lock:
            memories = self._memories.get(session_id, [])
            before = len(memories)
            self._memories[session_id] = [m for m in memories if m["memory_type"] != memory_type]
            count = before - len(self._memories[session_id])
        return count

    def get_session_summary(self, session_id: str) -> Dict:
        """Get a summary of stored memories for a session."""
        with self._lock:
            memories = self._memories.get(session_id, [])

        by_type = {}
        for m in memories:
            t = m["memory_type"]
            if t not in by_type:
                by_type[t] = {"count": 0, "avg_relevance": 0.0}
            by_type[t]["count"] += 1
            by_type[t]["avg_relevance"] += m["relevance"]

        for t in by_type:
            if by_type[t]["count"] > 0:
                by_type[t]["avg_relevance"] = round(by_type[t]["avg_relevance"] / by_type[t]["count"], 3)

        return {
            "session_id": session_id,
            "total_memories": len(memories),
            "by_type": by_type,
            "oldest": memories[0]["created_at"] if memories else None,
            "newest": memories[-1]["created_at"] if memories else None,
        }

    def list_all_sessions(self) -> List[str]:
        """List all sessions that have stored memories."""
        with self._lock:
            return list(self._memories.keys())

    # ============================================
    # INTERNAL METHODS
    # ============================================

    def _touch_memory(self, session_id: str, memory_id: str):
        """Update access count and last_accessed for a memory."""
        with self._lock:
            memories = self._memories.get(session_id, [])
            for m in memories:
                if m["id"] == memory_id:
                    m["access_count"] += 1
                    m["last_accessed"] = datetime.utcnow().isoformat()
                    # Relevance boost for frequently accessed memories
                    if m["access_count"] % 5 == 0 and m["relevance"] < 0.95:
                        m["relevance"] = min(m["relevance"] + 0.05, 1.0)
                    break

    def _prune_expired(self, session_id: str):
        """Remove expired memories and apply relevance decay."""
        now = datetime.utcnow()
        now_iso = now.isoformat()

        with self._lock:
            memories = self._memories.get(session_id, [])
            active = []
            for m in memories:
                if m["expires_at"] < now_iso:
                    continue  # Expired, remove
                # Relevance decay: memories not accessed in 7+ days lose relevance
                last_accessed = datetime.fromisoformat(m["last_accessed"])
                days_since_access = (now - last_accessed).days
                if days_since_access > 7:
                    decay = 0.01 * (days_since_access - 7)
                    m["relevance"] = max(m["relevance"] - decay, 0.1)
                active.append(m)
            self._memories[session_id] = active

    def _enforce_limits(self, session_id: str, memory_type: str):
        """Enforce max memories per type, removing lowest relevance first."""
        max_count = MAX_MEMORIES_PER_TYPE.get(memory_type, 20)
        memories = self._memories.get(session_id, [])
        typed = [m for m in memories if m["memory_type"] == memory_type]

        if len(typed) <= max_count:
            return

        # Sort by relevance ascending (lowest first) and remove excess
        typed.sort(key=lambda x: x["relevance"])
        to_remove = set(m["id"] for m in typed[: len(typed) - max_count])
        self._memories[session_id] = [m for m in memories if m["id"] not in to_remove]

    def _persist_to_db(self, memory: Dict):
        """Persist a memory to PostgreSQL."""
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            import json
            with get_db_session() as session:
                session.execute(text("""
                    INSERT INTO persistent_memories 
                    (id, session_id, memory_type, content, relevance, access_count, last_accessed, expires_at, metadata)
                    VALUES (:id::uuid, :session_id, :memory_type, :content, :relevance, :access_count, :last_accessed::timestamptz, :expires_at::timestamptz, :metadata::jsonb)
                """), {
                    "id": memory["id"],
                    "session_id": memory["session_id"],
                    "memory_type": memory["memory_type"],
                    "content": memory["content"],
                    "relevance": memory["relevance"],
                    "access_count": memory["access_count"],
                    "last_accessed": memory["last_accessed"],
                    "expires_at": memory["expires_at"],
                    "metadata": json.dumps(memory.get("metadata") or {}),
                })
        except Exception:
            pass

    def _delete_from_db(self, memory_id: str):
        """Delete a memory from PostgreSQL."""
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            with get_db_session() as session:
                session.execute(
                    text("DELETE FROM persistent_memories WHERE id = :id::uuid"),
                    {"id": memory_id},
                )
        except Exception:
            pass

    def load_from_db(self, session_id: str):
        """Load memories from PostgreSQL for a session (called on first access)."""
        if not _HAS_SQLALCHEMY or not is_database_available():
            return
        try:
            with get_db_session() as db_session:
                result = db_session.execute(text("""
                    SELECT id, session_id, memory_type, content, relevance, access_count, 
                           last_accessed, expires_at, metadata, created_at, updated_at
                    FROM persistent_memories
                    WHERE session_id = :session_id AND expires_at > NOW()
                    ORDER BY relevance DESC
                """), {"session_id": session_id})
                rows = result.fetchall()

            with self._lock:
                if session_id not in self._memories:
                    self._memories[session_id] = []
                existing_ids = {m["id"] for m in self._memories[session_id]}

                for row in rows:
                    mid = str(row[0])
                    if mid in existing_ids:
                        continue
                    self._memories[session_id].append({
                        "id": mid,
                        "session_id": row[1],
                        "memory_type": row[2],
                        "content": row[3],
                        "relevance": float(row[4] or 0.5),
                        "access_count": int(row[5] or 0),
                        "last_accessed": row[6].isoformat() if row[6] else datetime.utcnow().isoformat(),
                        "expires_at": row[7].isoformat() if row[7] else (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "metadata": row[8] or {},
                        "created_at": row[9].isoformat() if row[9] else datetime.utcnow().isoformat(),
                        "updated_at": row[10].isoformat() if row[10] else datetime.utcnow().isoformat(),
                    })
        except Exception:
            pass


# ============================================
# SINGLETON + AUTO-MEMORY EXTRACTION
# ============================================

_persistent_memory_store: Optional[PersistentMemoryStore] = None


def get_persistent_memory() -> PersistentMemoryStore:
    """Get the singleton persistent memory store."""
    global _persistent_memory_store
    if _persistent_memory_store is None:
        _persistent_memory_store = PersistentMemoryStore()
    return _persistent_memory_store


def extract_and_store_memories(session_id: str, agent: str, tools_called: List[str], tool_results: List[Dict]):
    """
    Automatically extract and store relevant memories after a successful interaction.
    Called after each completed agent execution.
    """
    store = get_persistent_memory()

    for tool_name in tools_called:
        if tool_name == "calcular_ahorro_energetico":
            store.store(
                session_id=session_id,
                memory_type=MEMORY_SERVICE_HISTORY,
                content=f"Performed energy savings analysis (agent: {agent})",
                relevance=0.6,
                metadata={"tool": tool_name, "agent": agent},
            )
        elif tool_name == "preparar_contrato_energia":
            store.store(
                session_id=session_id,
                memory_type=MEMORY_SERVICE_HISTORY,
                content=f"Prepared energy contract (high-value transaction, commission: 25€)",
                relevance=0.9,
                metadata={"tool": tool_name, "agent": agent, "commission": 25.0},
            )
        elif tool_name == "procesar_recarga":
            store.store(
                session_id=session_id,
                memory_type=MEMORY_PATTERN,
                content=f"Processed phone recharge (agent: {agent})",
                relevance=0.5,
                metadata={"tool": tool_name, "agent": agent},
            )
        elif tool_name == "activar_pin_digital":
            store.store(
                session_id=session_id,
                memory_type=MEMORY_PATTERN,
                content=f"Activated digital PIN (agent: {agent})",
                relevance=0.5,
                metadata={"tool": tool_name, "agent": agent},
            )
        elif tool_name == "registrar_paquetes":
            store.store(
                session_id=session_id,
                memory_type=MEMORY_SERVICE_HISTORY,
                content=f"Registered incoming packages (agent: {agent})",
                relevance=0.5,
                metadata={"tool": tool_name, "agent": agent},
            )

    # Track agent usage pattern
    if agent in ("energia", "logistica", "soporte"):
        store.store(
            session_id=session_id,
            memory_type=MEMORY_PATTERN,
            content=f"Used {agent} agent",
            relevance=0.3,
            metadata={"agent": agent, "timestamp": datetime.utcnow().isoformat()},
        )
