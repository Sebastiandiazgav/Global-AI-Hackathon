"""
MyAgent - Agent Society Graph
Orchestrates a multi-agent strategic debate with 2 rounds + consensus.

Flow:
1. Gather real business data (analytics + memory)
2. Round 1: Each agent proposes independently based on data
3. Moderator identifies conflicts and agreements
4. Round 2: Agents refine positions with counter-arguments
5. Moderator synthesizes consensus into actionable plan

All turns are emitted as SSE events for real-time frontend visualization.
"""

import json
import re
from typing import Dict, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config import get_settings
from agents.society.participants import (
    ALL_PARTICIPANTS,
    SALES_AGENT,
    MARKETING_AGENT,
    OPERATIONS_AGENT,
    FINANCE_AGENT,
    MODERATOR,
)
from database.db import get_analytics_summary, get_transactions
from agents.persistent_memory import get_persistent_memory


def _get_society_llm():
    """Get LLM for society debate agents."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.society_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=0.6,
        max_tokens=800,
    )


def _get_moderator_llm():
    """Get LLM for moderator (lower temperature for synthesis)."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.society_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=0.3,
        max_tokens=1500,
    )


def _gather_business_context(session_id: str) -> str:
    """Gather real business data for the debate context."""
    # Get analytics
    summary_7d = get_analytics_summary(days=7)
    summary_1d = get_analytics_summary(days=1)
    transactions = get_transactions(limit=20, days=7)

    # Get persistent memory insights
    store = get_persistent_memory()
    memories = store.recall(session_id, limit=10, min_relevance=0.3)
    memory_lines = [f"- {m['content']}" for m in memories] if memories else ["- No previous patterns recorded"]

    context = f"""REAL BUSINESS DATA (last 7 days):
- Total transactions: {summary_7d.get('total_transactions', 0)}
- Total commission earned: {summary_7d.get('total_commission', 0)}€
- Today's transactions: {summary_1d.get('total_transactions', 0)}
- Today's commission: {summary_1d.get('total_commission', 0)}€
- By type: {json.dumps(summary_7d.get('by_type', []), ensure_ascii=False)}
- Agent usage: {json.dumps(summary_7d.get('agent_usage', []), ensure_ascii=False)}
- Top tools: {json.dumps(summary_7d.get('top_tools', []), ensure_ascii=False)}
- Daily trend: {json.dumps(summary_7d.get('daily_trend', []), ensure_ascii=False)}
- MCP protocol calls: {summary_7d.get('mcp_calls', 0)}
- Guardrail blocks: {summary_7d.get('guardrail_blocks', 0)}

COMMISSION RATES (reference):
- Energy contract: 15-35€ per signed contract
- Package delivery: 0.25-0.35€ per package
- Phone recharge: 5% (national), 8% (international)
- Digital PINs: 1-5€ per activation
- Gift cards: 2-3% of value

RECENT PATTERNS & MEMORY:
{chr(10).join(memory_lines)}

RECENT TRANSACTIONS (sample):
{json.dumps([{"type": t.get("type",""), "tool": t.get("tool_name",""), "commission": t.get("commission",0)} for t in transactions[:10]], ensure_ascii=False)}"""

    return context


async def _agent_turn(
    agent_config: Dict,
    business_context: str,
    user_query: str,
    debate_history: str,
    language: str,
) -> str:
    """Execute a single agent's turn in the debate."""
    llm = _get_society_llm()

    language_instruction = f"Respond in '{language}' language."

    messages = [
        SystemMessage(content=agent_config["system_prompt"] + f"\n\n{language_instruction}"),
        HumanMessage(content=(
            f"BUSINESS DATA:\n{business_context}\n\n"
            f"USER QUESTION: {user_query}\n\n"
            f"{debate_history}"
            f"\nYour proposal:"
        )),
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()
    # Clean think tags
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content


async def _moderator_turn(
    business_context: str,
    user_query: str,
    all_proposals: Dict[str, str],
    round_number: int,
    language: str,
) -> str:
    """Execute the moderator's analysis/synthesis turn."""
    llm = _get_moderator_llm()

    language_instruction = f"Respond in '{language}' language."

    proposals_text = "\n\n".join([
        f"{ALL_PARTICIPANTS[agent]['emoji']} {ALL_PARTICIPANTS[agent]['name']}:\n{proposal}"
        for agent, proposal in all_proposals.items()
    ])

    if round_number == 1:
        task = (
            "ANALYZE the proposals above. Identify:\n"
            "1. AGREEMENTS: What do agents agree on? (at least 2 points)\n"
            "2. CONFLICTS: Where do they disagree? Be specific about the disagreement.\n"
            "3. CHALLENGE: Ask each disagreeing agent ONE question to refine their position.\n"
            "Be thorough in your analysis (minimum 150 words)."
        )
    else:
        task = (
            "SYNTHESIZE the final consensus from all refined proposals.\n"
            "You MUST create a DETAILED PRIORITIZED ACTION PLAN using this exact format:\n\n"
            "📋 ACTION PLAN:\n"
            "1. [Quick Win - This Week]: specific action + expected €/impact + who does it\n"
            "2. [Short Term - This Month]: specific action + expected €/impact + metrics\n"
            "3. [Medium Term - This Quarter]: specific action + expected €/impact + timeline\n"
            "4. [Long Term - Next Quarter]: strategic initiative + projected growth\n\n"
            "💰 PROJECTED MONTHLY IMPACT: estimated commission increase in € (with calculation)\n"
            "📈 GROWTH PROJECTION: current monthly vs projected monthly after implementation\n"
            "⚠️ TOP 3 RISKS: three things that could go wrong and mitigation\n"
            "📊 SUCCESS METRICS: three specific numbers to track weekly\n"
            "🎯 FIRST ACTION TOMORROW: one concrete thing to do immediately\n\n"
            "The plan MUST include ideas from ALL agents. Be specific with numbers and dates.\n"
            "MINIMUM 300 words for the consensus. This is a comprehensive strategic plan."
        )

    messages = [
        SystemMessage(content=MODERATOR["system_prompt"] + f"\n\n{language_instruction}"),
        HumanMessage(content=(
            f"BUSINESS DATA:\n{business_context}\n\n"
            f"USER QUESTION: {user_query}\n\n"
            f"AGENT PROPOSALS:\n{proposals_text}\n\n"
            f"YOUR TASK (Round {round_number}):\n{task}"
        )),
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content


async def run_society_debate(
    query: str,
    session_id: str,
    language: str = "es",
) -> Dict:
    """
    Run a full Agent Society debate.
    
    Returns dict with:
    - rounds: list of debate rounds with all turns
    - consensus: final synthesized plan
    - participants: who participated
    - workflow_events: SSE events for frontend
    """
    workflow_events = []
    debate_agents = ["sales", "marketing", "operations", "finance"]

    # Step 1: Gather real business data
    business_context = _gather_business_context(session_id)

    workflow_events.append({
        "type": "society_start",
        "data": {
            "message": "🏛️ Agent Society convened. Gathering business data...",
            "participants": [ALL_PARTICIPANTS[a]["name"] for a in debate_agents],
        },
    })

    # ============================================
    # ROUND 1: Independent proposals
    # ============================================
    round1_proposals = {}

    for agent_key in debate_agents:
        agent_config = ALL_PARTICIPANTS[agent_key]
        workflow_events.append({
            "type": "society_turn",
            "data": {
                "round": 1,
                "agent": agent_config["name"],
                "emoji": agent_config["emoji"],
                "role": agent_config["role"],
                "status": "thinking",
            },
        })

        proposal = await _agent_turn(
            agent_config=agent_config,
            business_context=business_context,
            user_query=query,
            debate_history="",
            language=language,
        )

        round1_proposals[agent_key] = proposal

        workflow_events.append({
            "type": "society_proposal",
            "data": {
                "round": 1,
                "agent": agent_config["name"],
                "emoji": agent_config["emoji"],
                "proposal": proposal,
            },
        })

    # Moderator analysis (Round 1)
    workflow_events.append({
        "type": "society_turn",
        "data": {
            "round": 1,
            "agent": MODERATOR["name"],
            "emoji": MODERATOR["emoji"],
            "role": "Analyzing conflicts and agreements",
            "status": "thinking",
        },
    })

    moderator_r1 = await _moderator_turn(
        business_context=business_context,
        user_query=query,
        all_proposals=round1_proposals,
        round_number=1,
        language=language,
    )

    workflow_events.append({
        "type": "society_moderator",
        "data": {
            "round": 1,
            "analysis": moderator_r1,
            "emoji": MODERATOR["emoji"],
        },
    })

    # ============================================
    # ROUND 2: Refined positions with counter-arguments
    # ============================================
    debate_history = (
        "ROUND 1 PROPOSALS:\n"
        + "\n".join([
            f"{ALL_PARTICIPANTS[a]['emoji']} {ALL_PARTICIPANTS[a]['name']}: {p}"
            for a, p in round1_proposals.items()
        ])
        + f"\n\nMODERATOR ANALYSIS:\n{moderator_r1}\n\n"
        + "Now REFINE your position considering the moderator's feedback and other agents' proposals. "
        "Address conflicts, defend or modify your stance."
    )

    round2_proposals = {}

    for agent_key in debate_agents:
        agent_config = ALL_PARTICIPANTS[agent_key]
        workflow_events.append({
            "type": "society_turn",
            "data": {
                "round": 2,
                "agent": agent_config["name"],
                "emoji": agent_config["emoji"],
                "role": agent_config["role"],
                "status": "refining",
            },
        })

        proposal = await _agent_turn(
            agent_config=agent_config,
            business_context=business_context,
            user_query=query,
            debate_history=debate_history,
            language=language,
        )

        round2_proposals[agent_key] = proposal

        workflow_events.append({
            "type": "society_proposal",
            "data": {
                "round": 2,
                "agent": agent_config["name"],
                "emoji": agent_config["emoji"],
                "proposal": proposal,
            },
        })

    # ============================================
    # FINAL CONSENSUS
    # ============================================
    workflow_events.append({
        "type": "society_turn",
        "data": {
            "round": 2,
            "agent": MODERATOR["name"],
            "emoji": MODERATOR["emoji"],
            "role": "Building final consensus",
            "status": "synthesizing",
        },
    })

    consensus = await _moderator_turn(
        business_context=business_context,
        user_query=query,
        all_proposals=round2_proposals,
        round_number=2,
        language=language,
    )

    workflow_events.append({
        "type": "society_consensus",
        "data": {
            "consensus": consensus,
            "emoji": "🎯",
        },
    })

    return {
        "rounds": [
            {"round": 1, "proposals": round1_proposals, "moderator": moderator_r1},
            {"round": 2, "proposals": round2_proposals, "consensus": consensus},
        ],
        "consensus": consensus,
        "participants": [ALL_PARTICIPANTS[a]["name"] for a in debate_agents] + [MODERATOR["name"]],
        "workflow_events": workflow_events,
        "total_llm_calls": len(debate_agents) * 2 + 2,  # 4 agents × 2 rounds + 2 moderator
    }
