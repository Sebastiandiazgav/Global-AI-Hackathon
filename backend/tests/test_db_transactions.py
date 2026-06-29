"""Tests for database transaction persistence."""
import pytest
from database.db import save_transaction, get_transactions, save_agent_call, get_analytics_summary


class TestTransactions:
    def test_save_and_retrieve(self):
        save_transaction(
            type="recarga",
            tool_name="procesar_recarga",
            description="Test recharge",
            commission=1.20,
            amount=15.0,
            agent="soporte",
            session_id="test-session",
            transport="mcp",
        )

        txns = get_transactions(limit=10, days=1, session_id="test-session")
        assert len(txns) >= 1
        latest = txns[0]
        assert latest["type"] == "recarga"
        assert latest["commission"] == 1.20

    def test_filter_by_session(self):
        save_transaction(type="pin", tool_name="activar_pin_digital", session_id="session-A", commission=2.0)
        save_transaction(type="pin", tool_name="activar_pin_digital", session_id="session-B", commission=3.0)

        a_txns = get_transactions(limit=50, days=1, session_id="session-A")
        b_txns = get_transactions(limit=50, days=1, session_id="session-B")

        assert all(t["session_id"] == "session-A" for t in a_txns)
        assert all(t["session_id"] == "session-B" for t in b_txns)


class TestAgentCalls:
    def test_save_agent_call(self):
        save_agent_call(
            session_id="test-session",
            agent="energia",
            trace_id="trace-123",
            intent="energy savings analysis",
            tools_used=["calcular_ahorro_energetico"],
            confidence=0.95,
            response_time_ms=850,
        )
        # No exception = success


class TestAnalyticsSummary:
    def test_get_summary(self):
        # Seed some data
        save_transaction(type="energia", tool_name="calcular_ahorro", commission=0, session_id="summary-test")
        save_transaction(type="recarga", tool_name="procesar_recarga", commission=1.5, session_id="summary-test")

        summary = get_analytics_summary(days=1)
        assert "total_transactions" in summary
        assert "total_commission" in summary
        assert "by_type" in summary
        assert "daily_trend" in summary
        assert summary["total_transactions"] >= 2
