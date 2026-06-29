"""Tests for MCP operations: client auth, rate limiting, audit."""
import pytest
from database.mcp_ops import (
    validate_mcp_client,
    is_tool_allowed_for_client,
    check_mcp_rate_limit,
    save_mcp_tool_audit,
    get_mcp_audit_summary,
    register_mcp_client,
    register_tool_policy,
    get_tool_policy,
)


class TestMCPClientValidation:
    def setup_method(self):
        register_mcp_client("test-client", "test-key-123", ["*"], 60)
        register_mcp_client("limited-client", "limited-key", ["consultar_tarifas_disponibles"], 10)

    def test_valid_client(self):
        valid, reason, data = validate_mcp_client("test-client", "test-key-123")
        assert valid is True
        assert reason == "ok"
        assert data["client_id"] == "test-client"

    def test_invalid_key(self):
        valid, reason, _ = validate_mcp_client("test-client", "wrong-key")
        assert valid is False
        assert reason == "invalid_api_key"

    def test_nonexistent_client(self):
        valid, reason, _ = validate_mcp_client("nonexistent", "any-key")
        assert valid is False
        assert reason == "client_not_found"

    def test_tool_allowed_wildcard(self):
        _, _, data = validate_mcp_client("test-client", "test-key-123")
        assert is_tool_allowed_for_client(data, "any_tool") is True

    def test_tool_not_allowed(self):
        _, _, data = validate_mcp_client("limited-client", "limited-key")
        assert is_tool_allowed_for_client(data, "procesar_recarga") is False

    def test_tool_allowed_specific(self):
        _, _, data = validate_mcp_client("limited-client", "limited-key")
        assert is_tool_allowed_for_client(data, "consultar_tarifas_disponibles") is True


class TestRateLimiting:
    def test_allows_within_limit(self):
        allowed, retry, current = check_mcp_rate_limit("rate-test-1", 100)
        assert allowed is True
        assert retry == 0

    def test_blocks_at_limit(self):
        client_id = "rate-test-exhausted"
        # Exhaust the limit
        for _ in range(5):
            check_mcp_rate_limit(client_id, 5)
        # Next call should be blocked
        allowed, retry, current = check_mcp_rate_limit(client_id, 5)
        assert allowed is False
        assert retry > 0


class TestToolPolicies:
    def setup_method(self):
        register_tool_policy("test_tool", timeout_ms=5000, max_retries=3)

    def test_get_policy(self):
        policy = get_tool_policy("test_tool")
        assert policy is not None
        assert policy["timeout_ms"] == 5000
        assert policy["max_retries"] == 3

    def test_get_nonexistent_policy(self):
        policy = get_tool_policy("nonexistent_tool")
        assert policy is None


class TestAuditLogging:
    def test_save_and_retrieve_audit(self):
        save_mcp_tool_audit(
            client_id="audit-test",
            tool_name="calcular_ahorro_energetico",
            status="ok",
            latency_ms=150,
            transport="mcp_stdio",
            server="myagent-energia",
        )

        summary = get_mcp_audit_summary(days=1, client_id="audit-test")
        assert summary["total_calls"] >= 1
        assert "ok" in summary["by_status"]
