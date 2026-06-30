"""
MyAgent - Supervisor Agent (Router)
Routes incoming messages to the appropriate specialized agent.
Supports multilingual input/output detection.
Powered by Qwen Cloud.
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import get_settings
from agents.state import AgentState
from agents.prompts import get_supervisor_prompt


def get_supervisor_llm():
    """Initialize Qwen Cloud LLM for supervisor routing with automatic fallback."""
    from agents.model_router import get_llm
    settings = get_settings()
    return get_llm(role="supervisor", temperature=0.1, max_tokens=settings.supervisor_max_tokens)


async def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node - analyzes intent and routes to specialized agent.
    Uses conversation history for contextual routing.
    Detects language and instructs agents to respond in the same language.
    """
    llm = get_supervisor_llm()
    settings = get_settings()

    # Get the last user message
    last_message = state["messages"][-1]

    # Build context from recent history for better routing
    history_context = ""
    if len(state["messages"]) > 1:
        window = max(1, settings.supervisor_history_max_messages + 1)
        recent = state["messages"][-window:]
        history_lines = []
        for msg in recent[:-1]:
            role = "Usuario" if msg.type == "human" else "Agente"
            history_lines.append(f"{role}: {str(msg.content)[:settings.supervisor_history_max_chars]}")
        if history_lines:
            history_context = "Historial reciente:\n" + "\n".join(history_lines) + "\n\n"

    routing_prompt = (
        "You are the router of MyAgent, an enterprise AI copilot. "
        "Classify the user message and respond ONLY with valid JSON.\n\n"
        "Available agents:\n"
        "- energia: Everything about electricity, utility bills, kWh, energy tariffs, savings, contracts\n"
        "- logistica: Packages, Amazon Hub, GLS, SEUR, deliveries, returns, tracking\n"
        "- soporte: Phone recharges, digital PINs (Netflix/PlayStation/Spotify/Steam), "
        "operational procedures, product catalog, general questions, greetings, help requests, technical errors\n"
        "- visual: When the message mentions an image, photo, screenshot, or contains image data\n"
        "- analytics: Performance questions, commissions earned, sales metrics, reports, trends\n"
        "- society: Strategic questions about growth, business improvement, sales strategy, "
        "marketing ideas, how to sell more, optimization suggestions\n\n"
        "RULES:\n"
        "- Greetings ('hola', 'hello', 'hi', 'buenos días'), general help requests, "
        "or 'what can you do' → ALWAYS 'soporte'\n"
        "- If the message mentions 'bill', 'kWh', 'tariff', 'electricity', 'energy', 'light' → ALWAYS 'energia'\n"
        "- If asking about performance, commissions, metrics, 'how much did I earn' → 'analytics'\n"
        "- If asking about strategy, growth, improvement, 'how to sell more' → 'society'\n"
        "- If message includes image reference or mentions photo/picture → 'visual'\n"
        "- CONTEXT RULE: If recent history shows a conversation about a topic, "
        "and the new message is a continuation (provides data, says 'yes', gives a number), keep SAME agent.\n\n"
        "Detect the language of the user message and include it in the response.\n"
        "IMPORTANT: The 'language' field MUST match the language the user is writing in.\n\n"
        "Respond ONLY with valid JSON (no extra text, no <think> tags):\n"
        '{"agent": "energia|logistica|soporte|visual|analytics|society", '
        '"intent": "brief description in the user\'s language", '
        '"confidence": 0.0-1.0, '
        '"language": "detected ISO 639-1 code (es, en, fr, pt, de, it, zh)"}'
    )

    messages = [
        SystemMessage(content=routing_prompt),
        HumanMessage(content=f"{history_context}Current message: {last_message.content}"),
    ]

    # Get routing decision with automatic fallback
    from agents.model_router import get_available_model, mark_model_exhausted, MODEL_CHAINS
    
    response = None
    for attempt in range(len(MODEL_CHAINS.get("supervisor", []))):
        try:
            llm = get_supervisor_llm()
            response = await llm.ainvoke(
                messages,
                config={
                    "tags": ["myagent", "supervisor", "routing"],
                    "metadata": {
                        "trace_id": state.get("trace_id", ""),
                        "session_id": state.get("session_id", ""),
                        "node": "supervisor",
                    },
                },
            )
            break  # Success
        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "exhausted", "freetieronly"]):
                current_model = get_available_model("supervisor")
                mark_model_exhausted(current_model)
                continue
            raise

    if response is None:
        # All models exhausted - return default routing
        return {
            **state,
            "current_agent": "soporte",
            "intent": "fallback - all models exhausted",
            "confidence": 0.5,
            "language": settings.default_language,
            "workflow_events": state.get("workflow_events", []),
        }

    # Parse the routing decision
    try:
        raw_content = response.content.strip()
        # Remove <think>...</think> blocks if present
        raw_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
        # Extract JSON from response
        json_match = re.search(r"\{[^}]+\}", raw_content)
        if json_match:
            decision = json.loads(json_match.group())
        else:
            decision = json.loads(raw_content)
        agent = decision.get("agent", "soporte")
        intent = decision.get("intent", "general query")
        confidence = decision.get("confidence", 0.8)
        language = decision.get("language", settings.default_language)
    except (json.JSONDecodeError, AttributeError):
        agent = "soporte"
        intent = "general query (fallback)"
        confidence = 0.6
        language = settings.default_language

    # Validate agent name
    valid_agents = {"energia", "logistica", "soporte", "visual", "analytics", "society"}
    if agent not in valid_agents:
        agent = "soporte"

    # Update state with routing decision
    workflow_events = state.get("workflow_events", [])
    workflow_events.append({
        "type": "routing",
        "data": {
            "agent_selected": agent,
            "intent": intent,
            "confidence": confidence,
            "language": language,
        },
    })

    return {
        **state,
        "current_agent": agent,
        "intent": intent,
        "confidence": confidence,
        "language": language,
        "workflow_events": workflow_events,
    }


def route_to_agent(state: AgentState) -> str:
    """Conditional edge function - routes to the selected agent node."""
    return state["current_agent"]
