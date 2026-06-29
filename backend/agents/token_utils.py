"""MyAgent - Helpers to reduce prompt/context token usage without changing behavior."""

from __future__ import annotations

import json
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


_MAX_RESULT_CHARS = 1200


def _truncate_text(value: str, max_chars: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def compact_messages(
    messages: List[BaseMessage],
    max_messages: int,
    max_chars_per_message: int,
) -> List[BaseMessage]:
    """Keep only the latest N messages and trim overly long content."""
    recent = messages[-max_messages:] if max_messages > 0 else messages
    compacted: List[BaseMessage] = []

    for msg in recent:
        content = getattr(msg, "content", "")
        if not isinstance(content, str):
            compacted.append(msg)
            continue

        trimmed = _truncate_text(content, max_chars_per_message)
        if isinstance(msg, HumanMessage):
            compacted.append(HumanMessage(content=trimmed))
        elif isinstance(msg, AIMessage):
            compacted.append(AIMessage(content=trimmed))
        else:
            compacted.append(msg)

    # Qwen API requires the first conversation message to be from user.
    # After trimming to the latest N messages, we may start on an AI turn.
    while compacted and isinstance(compacted[0], AIMessage):
        compacted.pop(0)

    # If all retained messages were AI turns, recover the latest user turn
    # from the original history so the conversation always starts correctly.
    if not compacted:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = getattr(msg, "content", "")
                if isinstance(content, str):
                    compacted.append(HumanMessage(content=_truncate_text(content, max_chars_per_message)))
                else:
                    compacted.append(msg)
                break

    return compacted


def compact_tool_result_for_llm(result: object, max_chars: int = _MAX_RESULT_CHARS) -> str:
    """Serialize tool outputs in a bounded way before passing them back to the LLM."""
    try:
        text = json.dumps(result, ensure_ascii=False)
    except TypeError:
        text = str(result)
    return _truncate_text(text, max_chars)
