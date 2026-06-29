"""
MyAgent - Agent State Definition
Defines the shared state that flows through the LangGraph.
"""

from typing import TypedDict, Annotated, List, Optional, NotRequired
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Shared state for the multi-agent graph.

    This state flows through all nodes in the LangGraph,
    accumulating messages and tracking execution metadata.
    """

    # Conversation messages (accumulated via add_messages reducer)
    messages: Annotated[List[BaseMessage], add_messages]

    # Routing metadata
    current_agent: str
    intent: str

    # Session tracking
    session_id: str

    # Trace correlation for observability
    trace_id: str

    # Workflow visualization events
    workflow_events: List[dict]

    # Tool execution tracking
    tools_called: List[str]

    # Final response
    final_response: Optional[str]

    # Confidence score
    confidence: float

    # Detected language (ISO 639-1 code)
    language: NotRequired[str]

    # Optional session-level context (e.g. pending product selections)
    session_context: NotRequired[dict]
