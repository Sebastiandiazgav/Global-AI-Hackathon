"""Tests for token utilities."""
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agents.token_utils import compact_messages, compact_tool_result_for_llm


class TestCompactMessages:
    def test_trims_to_max_messages(self):
        messages = [HumanMessage(content=f"msg {i}") for i in range(10)]
        result = compact_messages(messages, max_messages=3, max_chars_per_message=500)
        assert len(result) <= 3

    def test_truncates_long_content(self):
        messages = [HumanMessage(content="x" * 1000)]
        result = compact_messages(messages, max_messages=5, max_chars_per_message=100)
        assert len(result[0].content) <= 103  # 100 + "..."

    def test_ensures_first_message_is_human(self):
        messages = [AIMessage(content="response"), HumanMessage(content="query")]
        result = compact_messages(messages, max_messages=5, max_chars_per_message=500)
        assert isinstance(result[0], HumanMessage)

    def test_empty_messages(self):
        result = compact_messages([], max_messages=5, max_chars_per_message=500)
        assert result == []

    def test_preserves_order(self):
        messages = [
            HumanMessage(content="first"),
            AIMessage(content="second"),
            HumanMessage(content="third"),
        ]
        result = compact_messages(messages, max_messages=5, max_chars_per_message=500)
        assert result[0].content == "first"
        assert result[-1].content == "third"


class TestCompactToolResult:
    def test_dict_result(self):
        result = {"estado": "ok", "data": "value"}
        output = compact_tool_result_for_llm(result, max_chars=100)
        assert "ok" in output
        assert len(output) <= 103

    def test_truncates_large_result(self):
        result = {"large": "x" * 2000}
        output = compact_tool_result_for_llm(result, max_chars=200)
        assert len(output) <= 203
        assert output.endswith("...")

    def test_handles_non_serializable(self):
        result = object()
        output = compact_tool_result_for_llm(result, max_chars=100)
        assert isinstance(output, str)
