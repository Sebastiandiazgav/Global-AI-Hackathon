"""
MyAgent - LangGraph Multi-Agent Orchestration
Defines the agent graph with supervisor routing and specialized agents.
Includes Agent Society for strategic consulting.
"""

from typing import AsyncGenerator
import asyncio
import uuid

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.supervisor import supervisor_node, route_to_agent
from agents.energia_agent import energia_node
from agents.logistica_agent import logistica_node
from agents.soporte_agent import soporte_node
from agents.analytics_agent import analytics_node
from agents.visual_agent import visual_node
from agents.society.society_node import society_node
from agents.memory import get_memory_store
from agents.persistent_memory import extract_and_store_memories, get_persistent_memory

# Track last agent per session for continuation mode
_session_last_agent: dict = {}


def _detect_language_simple(text: str) -> str:
    """Simple language detection based on common words. Used in continuation mode."""
    text_lower = text.lower()
    # Check for language indicators
    if any(w in text_lower for w in ["the", "i need", "can you", "please", "want", "how", "what"]):
        return "en"
    if any(w in text_lower for w in ["je", "vous", "merci", "bonjour", "comment"]):
        return "fr"
    if any(w in text_lower for w in ["eu", "você", "obrigado", "como", "preciso"]):
        return "pt"
    if any(w in text_lower for w in ["ich", "bitte", "danke", "wie", "können"]):
        return "de"
    if any(w in text_lower for w in ["io", "vorrei", "grazie", "come", "posso"]):
        return "it"
    if any(w in text_lower for w in ["我", "你", "请", "需要", "怎么"]):
        return "zh"
    # Default to Spanish (most common for this app)
    return "es"

# Short messages that indicate continuation (not a new topic)
CONTINUATION_PATTERNS = {
    "si", "sí", "ok", "vale", "claro", "perfecto", "adelante", "procede",
    "gracias", "genial", "listo", "hecho", "confirmo",
    "yes", "no thanks", "sure", "done", "perdon", "perdón", "quise decir",
    "oui", "ja", "sim", "certo", "d'accord", "genau",
}


def is_continuation_message(message: str) -> bool:
    """Detect if a message is a simple continuation/confirmation."""
    cleaned = message.strip().lower().rstrip(".,!?")
    if cleaned in {"no", "cancelar", "stop", "parar", "cancel"}:
        return False

    keywords = [
        "energ", "kwh", "tarifa", "paquete", "amazon", "gls", "recarga", "pin",
        "netflix", "strategy", "estrategia", "how to", "cómo", "analytics", "report",
    ]
    if any(token in cleaned for token in keywords):
        return False

    if cleaned.startswith("es ") or "quise decir" in cleaned or "perdon" in cleaned:
        return True

    if len(cleaned) < 50:
        if cleaned in CONTINUATION_PATTERNS:
            return True
        stripped = cleaned.replace(" ", "").replace("+", "").replace("€", "").replace("euros", "").replace("-", "")
        if stripped.replace(".", "").isdigit():
            return True
        if len(stripped) >= 8 and stripped[:-1].isdigit() and stripped[-1].isalpha():
            return True
        if len(cleaned) < 25 and not any(word in cleaned for word in ["quiero", "necesito", "hazme", "analiza", "dame", "want", "need", "give"]):
            return True

    return False


def build_agent_graph() -> StateGraph:
    """
    Builds the multi-agent LangGraph.

    Graph Structure:

        [START]
           │
           ▼
      ┌──────────┐
      │Supervisor │  ← Classifies intent, decides routing
      └─────┬────┘
            │
            ├── "energia"   ──▶ [Energy Agent]     ──▶ [END]
            ├── "logistica" ──▶ [Logistics Agent]  ──▶ [END]
            ├── "soporte"   ──▶ [Support Agent]    ──▶ [END]
            ├── "visual"    ──▶ [Visual Agent]     ──▶ [END]
            ├── "analytics" ──▶ [Analytics Agent]  ──▶ [END]
            └── "society"   ──▶ [Society Debate]   ──▶ [END]
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("energia", energia_node)
    graph.add_node("logistica", logistica_node)
    graph.add_node("soporte", soporte_node)
    graph.add_node("visual", visual_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("society", society_node)

    # Set entry point
    graph.set_entry_point("supervisor")

    # Add conditional edges from supervisor to specialized agents
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "energia": "energia",
            "logistica": "logistica",
            "soporte": "soporte",
            "visual": "visual",
            "analytics": "analytics",
            "society": "society",
        },
    )

    # All specialized agents go to END
    graph.add_edge("energia", END)
    graph.add_edge("logistica", END)
    graph.add_edge("soporte", END)
    graph.add_edge("visual", END)
    graph.add_edge("analytics", END)
    graph.add_edge("society", END)

    return graph


# Compile the graph (singleton)
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_agent_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


async def run_agent_graph(
    message: str,
    session_id: str = "default",
    context: dict = None,
) -> dict:
    """
    Execute the agent graph with a user message.
    Includes conversational memory and continuation mode.
    """
    compiled_graph = get_compiled_graph()
    memory_store = get_memory_store()
    trace_id = str(uuid.uuid4())

    history = memory_store.get_history(session_id)
    session_metadata = memory_store.get_session_metadata(session_id)
    session_context = session_metadata.get("support_context", {})
    memory_store.add_user_message(session_id, message)

    messages = history + [HumanMessage(content=message)]

    # CONTINUATION MODE: Skip supervisor for simple follow-up messages
    last_agent = _session_last_agent.get(session_id)
    if last_agent and is_continuation_message(message):
        agent_nodes = {
            "energia": energia_node,
            "logistica": logistica_node,
            "soporte": soporte_node,
            "analytics": analytics_node,
        }
        if last_agent in agent_nodes:
            detected_lang = _detect_language_simple(message)
            state = AgentState(
                messages=messages, current_agent=last_agent, intent="continuation",
                session_id=session_id, trace_id=trace_id, workflow_events=[], tools_called=[],
                final_response=None, confidence=1.0, session_context=session_context,
                language=detected_lang,
            )
            result = await agent_nodes[last_agent](state)
            final_response = result.get("final_response", "")
            memory_store.add_ai_message(session_id, final_response)
            if isinstance(result.get("session_context"), dict):
                memory_store.update_session_metadata(session_id, {"support_context": result.get("session_context", {})})
            return {
                "response": final_response,
                "agent_used": last_agent,
                "tools_called": result.get("tools_called", []),
                "workflow_steps": result.get("workflow_events", []),
                "intent": "continuation",
                "trace_id": trace_id,
                "confidence": 1.0,
            }

    # NORMAL MODE: Full pipeline with supervisor routing
    # Load persistent memory context for this session
    persistent_store = get_persistent_memory()
    persistent_store.load_from_db(session_id)
    memory_context = persistent_store.recall_for_context(session_id, current_query=message, limit=5)

    initial_state: AgentState = {
        "messages": messages,
        "current_agent": "",
        "intent": "",
        "session_id": session_id,
        "trace_id": trace_id,
        "workflow_events": [],
        "tools_called": [],
        "final_response": None,
        "confidence": 0.0,
        "session_context": {**session_context, "persistent_memory": memory_context},
    }

    result = await compiled_graph.ainvoke(initial_state)

    final_response = result.get("final_response", "Could not process your request.")
    agent_used = result.get("current_agent", "unknown")
    memory_store.add_ai_message(session_id, final_response)
    if isinstance(result.get("session_context"), dict):
        memory_store.update_session_metadata(session_id, {"support_context": result.get("session_context", {})})

    _session_last_agent[session_id] = agent_used

    # Extract and store persistent memories from this interaction
    tools_called = result.get("tools_called", [])
    if tools_called:
        extract_and_store_memories(
            session_id=session_id,
            agent=agent_used,
            tools_called=tools_called,
            tool_results=result.get("workflow_events", []),
        )

    return {
        "response": final_response,
        "agent_used": agent_used,
        "tools_called": tools_called,
        "workflow_steps": result.get("workflow_events", []),
        "intent": result.get("intent", ""),
        "trace_id": trace_id,
        "confidence": result.get("confidence", 0.0),
    }


async def run_agent_graph_streaming(
    message: str,
    session_id: str = "default",
) -> AsyncGenerator[dict, None]:
    """
    Execute the agent graph with streaming events.
    Includes continuation mode for efficiency.
    """
    compiled_graph = get_compiled_graph()
    memory_store = get_memory_store()
    trace_id = str(uuid.uuid4())

    history = memory_store.get_history(session_id)
    session_metadata = memory_store.get_session_metadata(session_id)
    session_context = session_metadata.get("support_context", {})
    memory_store.add_user_message(session_id, message)
    messages = history + [HumanMessage(content=message)]

    # CONTINUATION MODE
    last_agent = _session_last_agent.get(session_id)
    if last_agent and is_continuation_message(message):
        yield {"type": "thinking", "data": {"message": "Continuing...", "step": "continuation"}}

        agent_nodes = {"energia": energia_node, "logistica": logistica_node, "soporte": soporte_node, "analytics": analytics_node}
        if last_agent in agent_nodes:
            # Detect language from the current message for proper response
            detected_lang = _detect_language_simple(message)
            
            state = AgentState(
                messages=messages, current_agent=last_agent, intent="continuation",
                session_id=session_id, trace_id=trace_id, workflow_events=[], tools_called=[],
                final_response=None, confidence=1.0, session_context=session_context,
                language=detected_lang,
            )
            result = await agent_nodes[last_agent](state)

            for event in result.get("workflow_events", []):
                yield event
                await asyncio.sleep(0.05)

            final_response = result.get("final_response", "")
            memory_store.add_ai_message(session_id, final_response)
            if isinstance(result.get("session_context"), dict):
                memory_store.update_session_metadata(session_id, {"support_context": result.get("session_context", {})})

            agent_events = result.get("workflow_events", [])
            tool_results = [e for e in agent_events if e.get("type") == "tool_result"]

            yield {
                "type": "complete",
                "data": {
                    "message": final_response,
                    "agent_used": last_agent,
                    "tools_called": result.get("tools_called", []),
                    "tool_results": tool_results,
                    "intent": "continuation",
                    "trace_id": trace_id,
                    "confidence": 1.0,
                },
            }
            return

    # NORMAL MODE: Full pipeline
    initial_state: AgentState = {
        "messages": messages,
        "current_agent": "",
        "intent": "",
        "session_id": session_id,
        "trace_id": trace_id,
        "workflow_events": [],
        "tools_called": [],
        "final_response": None,
        "confidence": 0.0,
        "session_context": session_context,
    }

    yield {"type": "thinking", "data": {"message": "Analyzing your message...", "step": "start"}}

    final_state = None
    async for state_update in compiled_graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_output in state_update.items():
            if node_name == "supervisor":
                agent = node_output.get("current_agent", "")
                intent = node_output.get("intent", "")
                confidence = node_output.get("confidence", 0.0)
                language = node_output.get("language", "es")
                _session_last_agent[session_id] = agent
                yield {
                    "type": "routing",
                    "data": {
                        "agent_selected": agent,
                        "intent": intent,
                        "confidence": confidence,
                        "language": language,
                    },
                }
                await asyncio.sleep(0.1)

            elif node_name in ("energia", "logistica", "soporte", "visual", "analytics", "society"):
                events = node_output.get("workflow_events", [])
                for event in events:
                    if event.get("type") != "routing":
                        yield event
                        await asyncio.sleep(0.05)
                final_state = node_output

    if final_state:
        final_response = final_state.get("final_response", "")
        memory_store.add_ai_message(session_id, final_response)
        if isinstance(final_state.get("session_context"), dict):
            memory_store.update_session_metadata(session_id, {"support_context": final_state.get("session_context", {})})

        agent_events = final_state.get("workflow_events", [])
        tool_results = [e for e in agent_events if e.get("type") == "tool_result"]

        yield {
            "type": "complete",
            "data": {
                "message": final_response,
                "agent_used": final_state.get("current_agent", ""),
                "tools_called": final_state.get("tools_called", []),
                "tool_results": tool_results,
                "intent": final_state.get("intent", ""),
                "trace_id": trace_id,
                "confidence": final_state.get("confidence", 0.0),
            },
        }
    else:
        yield {"type": "error", "data": {"message": "Could not process the request."}}
