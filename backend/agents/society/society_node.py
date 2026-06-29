"""
MyAgent - Society Node
LangGraph node that integrates Agent Society debate into the main agent graph.
"""

from langchain_core.messages import AIMessage

from agents.state import AgentState
from agents.society.society_graph import run_society_debate
from config import get_settings


async def society_node(state: AgentState) -> AgentState:
    """
    Society agent node — triggers a multi-agent strategic debate.
    Called when the supervisor detects a strategic/growth question.
    
    The debate runs through 2 rounds:
    - Round 1: Sales, Marketing, Operations, Finance propose independently
    - Moderator identifies conflicts
    - Round 2: Agents refine positions
    - Moderator synthesizes consensus into action plan
    
    All turns are emitted as workflow events for SSE streaming.
    """
    settings = get_settings()
    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    language = state.get("language", settings.default_language)
    session_id = state.get("session_id", "default")

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "society", "status": "processing"},
    })

    # Extract the user's strategic question
    user_query = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content
            break

    if not user_query:
        user_query = state.get("intent", "How can I grow my business?")

    # Run the full debate
    debate_result = await run_society_debate(
        query=user_query,
        session_id=session_id,
        language=language,
    )

    # Collect all debate workflow events
    debate_events = debate_result.get("workflow_events", [])
    workflow_events.extend(debate_events)
    tools_called.append("society_debate")

    # Build the final response with the consensus
    consensus = debate_result.get("consensus", "")
    participants = debate_result.get("participants", [])
    total_calls = debate_result.get("total_llm_calls", 0)

    response_header = (
        f"🏛️ **Agent Society — Strategic Consulting**\n"
        f"*{len(participants)} agents debated your question in 2 rounds*\n\n"
    )

    response_text = response_header + consensus

    response_footer = (
        f"\n\n---\n"
        f"*Participants: {', '.join(participants)}*\n"
        f"*Debate rounds: 2 | LLM calls: {total_calls}*"
    )

    response_text += response_footer

    workflow_events.append({
        "type": "response",
        "data": {"agent": "society", "status": "completed"},
    })

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }
