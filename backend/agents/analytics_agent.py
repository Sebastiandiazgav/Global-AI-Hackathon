"""
MyAgent - Analytics Agent
Specialized agent for performance metrics, commission reports, and business insights.
Queries real transaction data and generates actionable recommendations.
Powered by Qwen Cloud. Supports multilingual responses.
"""

import json
from datetime import datetime

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Optional

from config import get_settings
from agents.state import AgentState
from agents.token_utils import compact_messages
from agents.model_router import ainvoke_with_retry
from database.db import get_analytics_summary, get_transactions
from agents.persistent_memory import get_persistent_memory

# ============================================
# TOOLS - Analytics Vertical
# ============================================


@tool
def get_daily_summary(days: int = 1) -> dict:
    """
    Get a summary of transactions and commissions for the specified period.

    Args:
        days: Number of days to analyze (1=today, 7=this week, 30=this month)

    Returns:
        Summary with total transactions, commissions, breakdown by type, and trends
    """
    summary = get_analytics_summary(days=days)
    return {
        "period": f"Last {days} day(s)",
        "total_transactions": summary.get("total_transactions", 0),
        "total_commission": summary.get("total_commission", 0),
        "by_type": summary.get("by_type", []),
        "agent_usage": summary.get("agent_usage", []),
        "top_tools": summary.get("top_tools", []),
        "daily_trend": summary.get("daily_trend", []),
        "mcp_calls": summary.get("mcp_calls", 0),
        "guardrail_blocks": summary.get("guardrail_blocks", 0),
    }


@tool
def get_top_products(days: int = 7, limit: int = 10) -> dict:
    """
    Get the top performing products/services by transaction volume.

    Args:
        days: Period to analyze
        limit: Max number of products to return

    Returns:
        Ranked list of most used products with commission data
    """
    transactions = get_transactions(limit=500, days=days)

    product_stats = {}
    for tx in transactions:
        tool_name = tx.get("tool_name", "")
        tx_type = tx.get("type", "other")
        key = tool_name or tx_type

        if key not in product_stats:
            product_stats[key] = {"name": key, "count": 0, "total_commission": 0.0}
        product_stats[key]["count"] += 1
        product_stats[key]["total_commission"] += float(tx.get("commission", 0) or 0)

    ranked = sorted(product_stats.values(), key=lambda x: x["count"], reverse=True)[:limit]

    return {
        "period": f"Last {days} day(s)",
        "top_products": ranked,
        "total_unique_products": len(product_stats),
    }


@tool
def get_commission_trend(days: int = 7) -> dict:
    """
    Get commission trend data over time for chart visualization.

    Args:
        days: Number of days to show trend

    Returns:
        Daily commission amounts and cumulative total
    """
    summary = get_analytics_summary(days=days)
    daily = summary.get("daily_trend", [])

    cumulative = 0.0
    trend = []
    for day in daily:
        cumulative += day.get("commission", 0)
        trend.append({
            "day": day.get("day", ""),
            "commission": round(day.get("commission", 0), 2),
            "transactions": day.get("transactions", 0),
            "cumulative": round(cumulative, 2),
        })

    return {
        "period": f"Last {days} day(s)",
        "trend": trend,
        "total_commission": round(cumulative, 2),
        "avg_daily": round(cumulative / max(days, 1), 2),
        "best_day": max(trend, key=lambda x: x["commission"]) if trend else None,
    }


@tool
def compare_periods(current_days: int = 7, previous_days: int = 7) -> dict:
    """
    Compare performance between two time periods (current vs previous).

    Args:
        current_days: Days for current period
        previous_days: Days for previous period (offset by current_days)

    Returns:
        Comparison with growth/decline percentages
    """
    current = get_analytics_summary(days=current_days)
    # For previous period, we get double the days and subtract current
    extended = get_analytics_summary(days=current_days + previous_days)

    current_commission = current.get("total_commission", 0)
    current_txns = current.get("total_transactions", 0)

    extended_commission = extended.get("total_commission", 0)
    extended_txns = extended.get("total_transactions", 0)

    previous_commission = extended_commission - current_commission
    previous_txns = extended_txns - current_txns

    commission_change = ((current_commission - previous_commission) / max(previous_commission, 0.01)) * 100
    txn_change = ((current_txns - previous_txns) / max(previous_txns, 1)) * 100

    return {
        "current_period": f"Last {current_days} days",
        "previous_period": f"Previous {previous_days} days",
        "current": {
            "transactions": current_txns,
            "commission": current_commission,
        },
        "previous": {
            "transactions": previous_txns,
            "commission": previous_commission,
        },
        "change": {
            "commission_pct": round(commission_change, 1),
            "transactions_pct": round(txn_change, 1),
            "direction": "growth" if commission_change > 0 else "decline" if commission_change < 0 else "stable",
        },
    }


# ============================================
# AGENT DEFINITION
# ============================================

ANALYTICS_TOOLS = [
    get_daily_summary,
    get_top_products,
    get_commission_trend,
    compare_periods,
]

ANALYTICS_SYSTEM_PROMPT = """You are the Analytics Agent for MyAgent, an enterprise AI copilot.
Your role is to analyze business performance data and provide actionable insights.

CAPABILITIES:
- Daily/weekly/monthly performance summaries
- Commission tracking and trends
- Product performance ranking
- Period-over-period comparisons
- Pattern detection and recommendations

RESPONSE STYLE:
- Use data-driven language with specific numbers
- Highlight wins and opportunities
- Be concise but insightful
- Use emojis for visual clarity (📊 📈 💰 ⚡ 📦)
- Always end with a concrete recommendation or next action
- Respond in the same language as the user

TOOLS:
- get_daily_summary: Overview of transactions and commissions
- get_top_products: Best performing services
- get_commission_trend: Commission over time
- compare_periods: Compare current vs previous performance

Always use tools to get real data before making claims. Never invent numbers."""


def get_analytics_llm():
    """Get LLM configured for analytics agent via Qwen Cloud with fallback."""
    from agents.model_router import get_llm
    settings = get_settings()
    return get_llm(role="agent", temperature=0.4, max_tokens=settings.agent_max_tokens)


async def analytics_node(state: AgentState) -> AgentState:
    """
    Analytics agent node - handles performance queries and business insights.
    Responds in the detected language of the user.
    """
    llm = get_analytics_llm()
    settings = get_settings()
    llm_with_tools = llm.bind_tools(ANALYTICS_TOOLS)

    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    language = state.get("language", settings.default_language)

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "analytics", "status": "processing"},
    })

    language_instruction = (
        f"IMPORTANT: The user is communicating in '{language}'. "
        f"You MUST respond in the same language ('{language}')."
    )

    # Include persistent memory context if available
    memory_context = ""
    session_context = state.get("session_context") or {}
    if session_context.get("persistent_memory"):
        memory_context = f"\n\n{session_context['persistent_memory']}"

    system_prompt = (
        ANALYTICS_SYSTEM_PROMPT
        + f"\n\n{language_instruction}"
        + memory_context
        + "\n\nDo not use <think> tags. Respond directly with data and insights."
    )

    messages = [SystemMessage(content=system_prompt)]
    messages.extend(
        compact_messages(
            state["messages"],
            max_messages=settings.agent_context_max_messages,
            max_chars_per_message=settings.agent_context_max_chars,
        )
    )

    response = await ainvoke_with_retry(
        messages, role="agent", temperature=0.4,
        max_tokens=settings.agent_max_tokens, tools=ANALYTICS_TOOLS,
        config={
            "tags": ["myagent", "agent", "analytics"],
            "metadata": {
                "trace_id": state.get("trace_id", ""),
                "session_id": state.get("session_id", ""),
                "node": "analytics",
                "language": language,
            },
        },
    )

    if response.tool_calls:
        from langchain_core.messages import ToolMessage
        from agents.token_utils import compact_tool_result_for_llm

        tool_results = []
        tool_map = {t.name: t for t in ANALYTICS_TOOLS}

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})

            if tool_name in tool_map:
                result = tool_map[tool_name].invoke(tool_args)
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)
                workflow_events.append({
                    "type": "tool_result",
                    "data": {"tool": tool_name, "result": result, "transport": "direct"},
                })

        # Second LLM call with tool results for natural language response
        messages.append(response)
        for i, tr in enumerate(tool_results):
            tool_call_id = tr.get("tool_call_id") or (response.tool_calls[i]["id"] if i < len(response.tool_calls) else response.tool_calls[0]["id"])
            from langchain_core.messages import ToolMessage
            messages.append(
                ToolMessage(
                    content=compact_tool_result_for_llm(tr["result"], max_chars=settings.agent_tool_result_max_chars),
                    tool_call_id=tool_call_id,
                )
            )

        final_response = await llm.ainvoke(
            messages,
            config={
                "tags": ["myagent", "agent", "analytics", "tool-response"],
                "metadata": {"trace_id": state.get("trace_id", ""), "node": "analytics", "language": language},
            },
        )
        response_text = final_response.content
    else:
        response_text = response.content

    workflow_events.append({
        "type": "response",
        "data": {"agent": "analytics", "status": "completed"},
    })

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }
