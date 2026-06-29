"""Tests for persistent memory engine."""
import pytest
from agents.persistent_memory import (
    PersistentMemoryStore,
    MEMORY_PREFERENCE,
    MEMORY_PATTERN,
    MEMORY_INSIGHT,
)


class TestPersistentMemory:
    def setup_method(self):
        self.store = PersistentMemoryStore()

    def test_store_and_recall(self):
        memory_id = self.store.store(
            session_id="test-session",
            memory_type=MEMORY_PREFERENCE,
            content="User prefers Netflix products",
            relevance=0.8,
        )
        assert memory_id is not None

        memories = self.store.recall("test-session")
        assert len(memories) >= 1
        assert any("Netflix" in m["content"] for m in memories)

    def test_recall_by_type(self):
        self.store.store("s1", MEMORY_PREFERENCE, "Likes energy contracts", 0.8)
        self.store.store("s1", MEMORY_PATTERN, "Sells more on weekends", 0.7)

        prefs = self.store.recall("s1", memory_type=MEMORY_PREFERENCE)
        patterns = self.store.recall("s1", memory_type=MEMORY_PATTERN)

        assert all(m["memory_type"] == MEMORY_PREFERENCE for m in prefs)
        assert all(m["memory_type"] == MEMORY_PATTERN for m in patterns)

    def test_recall_with_query(self):
        self.store.store("s2", MEMORY_PREFERENCE, "Always recommends solar tariffs", 0.8)
        self.store.store("s2", MEMORY_PREFERENCE, "Prefers Netflix over Disney", 0.7)

        results = self.store.recall("s2", query="solar")
        assert len(results) >= 1
        assert "solar" in results[0]["content"].lower()

    def test_forget_specific(self):
        mid = self.store.store("s3", MEMORY_INSIGHT, "Test memory to forget", 0.5)
        assert len(self.store.recall("s3")) >= 1

        self.store.forget("s3", mid)
        remaining = [m for m in self.store.recall("s3") if m["id"] == mid]
        assert len(remaining) == 0

    def test_forget_by_type(self):
        self.store.store("s4", MEMORY_PATTERN, "Pattern 1", 0.5)
        self.store.store("s4", MEMORY_PATTERN, "Pattern 2", 0.5)
        self.store.store("s4", MEMORY_PREFERENCE, "Preference 1", 0.8)

        count = self.store.forget_by_type("s4", MEMORY_PATTERN)
        assert count == 2

        remaining = self.store.recall("s4")
        assert all(m["memory_type"] != MEMORY_PATTERN for m in remaining)

    def test_relevance_filtering(self):
        self.store.store("s5", MEMORY_INSIGHT, "Low relevance", 0.2)
        self.store.store("s5", MEMORY_INSIGHT, "High relevance", 0.9)

        results = self.store.recall("s5", min_relevance=0.5)
        assert all(m["relevance"] >= 0.5 for m in results)

    def test_session_summary(self):
        self.store.store("s6", MEMORY_PREFERENCE, "Pref 1", 0.8)
        self.store.store("s6", MEMORY_PATTERN, "Pattern 1", 0.7)

        summary = self.store.get_session_summary("s6")
        assert summary["total_memories"] >= 2
        assert MEMORY_PREFERENCE in summary["by_type"]

    def test_recall_for_context(self):
        self.store.store("s7", MEMORY_PREFERENCE, "Prefers energy contracts", 0.9)
        self.store.store("s7", MEMORY_PATTERN, "High recharge volume on Fridays", 0.7)

        context = self.store.recall_for_context("s7", current_query="energy")
        assert "[Persistent Memory Context]" in context
        assert "energy" in context.lower()

    def test_access_count_increments(self):
        self.store.store("s8", MEMORY_PREFERENCE, "Test access tracking", 0.7)
        # Recall multiple times
        self.store.recall("s8")
        self.store.recall("s8")
        memories = self.store.recall("s8")
        assert memories[0]["access_count"] >= 2

    def test_isolation_between_sessions(self):
        self.store.store("session-a", MEMORY_PREFERENCE, "Session A memory", 0.8)
        self.store.store("session-b", MEMORY_PREFERENCE, "Session B memory", 0.8)

        a_memories = self.store.recall("session-a")
        b_memories = self.store.recall("session-b")

        assert not any("Session B" in m["content"] for m in a_memories)
        assert not any("Session A" in m["content"] for m in b_memories)
