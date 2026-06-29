"""
MyAgent - Conversational Memory
Manages session-based conversation history for multi-turn interactions.
Supports multilingual conversations with context preservation.
"""

from typing import Dict, List
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dataclasses import dataclass, field
import threading


@dataclass
class SessionMemory:
    """Memory for a single conversation session."""
    messages: List[BaseMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)


class ConversationMemoryStore:
    """
    In-memory store for conversation sessions.
    
    Features:
    - Session-based isolation (each tendero/terminal has its own history)
    - Configurable max history length (sliding window)
    - Auto-cleanup of stale sessions
    - Thread-safe operations
    """

    def __init__(self, max_messages_per_session: int = 20, session_ttl_minutes: int = 60):
        self._sessions: Dict[str, SessionMemory] = {}
        self._lock = threading.Lock()
        self._max_messages = max_messages_per_session
        self._session_ttl = timedelta(minutes=session_ttl_minutes)

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """Get conversation history for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            session.last_active = datetime.now()
            return session.messages.copy()

    def add_user_message(self, session_id: str, content: str):
        """Add a user message to the session history."""
        with self._lock:
            session = self._get_or_create_session(session_id)
            session.messages.append(HumanMessage(content=content))
            session.last_active = datetime.now()
            self._trim_history(session)

    def add_ai_message(self, session_id: str, content: str):
        """Add an AI response to the session history."""
        with self._lock:
            session = self._get_or_create_session(session_id)
            session.messages.append(AIMessage(content=content))
            session.last_active = datetime.now()
            self._trim_history(session)

    def clear_session(self, session_id: str):
        """Clear all history for a session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def get_session_info(self, session_id: str) -> Dict:
        """Get metadata about a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {"exists": False}
            return {
                "exists": True,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat(),
            }

    def get_session_metadata(self, session_id: str) -> Dict:
        """Get custom metadata for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {}
            session.last_active = datetime.now()
            return dict(session.metadata or {})

    def update_session_metadata(self, session_id: str, metadata: Dict):
        """Merge custom metadata into a session."""
        if not isinstance(metadata, dict):
            return
        with self._lock:
            session = self._get_or_create_session(session_id)
            session.metadata.update(metadata)
            session.last_active = datetime.now()

    def list_active_sessions(self) -> List[Dict]:
        """List all active sessions."""
        with self._lock:
            self._cleanup_stale_sessions()
            return [
                {
                    "session_id": sid,
                    "message_count": session.message_count,
                    "last_active": session.last_active.isoformat(),
                }
                for sid, session in self._sessions.items()
            ]

    def _get_or_create_session(self, session_id: str) -> SessionMemory:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory()
        return self._sessions[session_id]

    def _trim_history(self, session: SessionMemory):
        """Keep only the last N messages (sliding window)."""
        if len(session.messages) > self._max_messages:
            session.messages = session.messages[-self._max_messages:]

    def _cleanup_stale_sessions(self):
        """Remove sessions that haven't been active within TTL."""
        now = datetime.now()
        stale = [
            sid for sid, session in self._sessions.items()
            if now - session.last_active > self._session_ttl
        ]
        for sid in stale:
            del self._sessions[sid]


# Singleton memory store
_memory_store = None


def get_memory_store() -> ConversationMemoryStore:
    """Get the singleton memory store."""
    global _memory_store
    if _memory_store is None:
        _memory_store = ConversationMemoryStore(
            max_messages_per_session=20,
            session_ttl_minutes=60,
        )
    return _memory_store
