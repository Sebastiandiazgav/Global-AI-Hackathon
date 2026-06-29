"""
MyAgent - Analytics API
Provides analytics data and AI-generated insights using Qwen Cloud.
"""

import json
import re

from fastapi import APIRouter
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from database.db import get_analytics_summary, get_transactions
from database.mcp_ops import get_mcp_audit_summary
from config import get_settings

router = APIRouter()


@router.get("/summary")
async def analytics_summary(days: int = 7):
    """Get analytics summary for the dashboard."""
    return get_analytics_summary(days)


@router.get("/transactions")
async def analytics_transactions(limit: int = 50, days: int = 7, session_id: str = ""):
    """Get transaction history for analytics."""
    return {"transactions": get_transactions(limit, days, session_id=session_id)}


@router.get("/mcp/summary")
async def analytics_mcp_summary(days: int = 7):
    """Get aggregated MCP operational metrics."""
    return get_mcp_audit_summary(days)


@router.get("/mcp/client/{client_id}")
async def analytics_mcp_client_summary(client_id: str, days: int = 7):
    """Get MCP operational metrics for a specific client."""
    return get_mcp_audit_summary(days, client_id=client_id)


@router.get("/insights")
async def analytics_insights(days: int = 7):
    """
    Generate AI-powered insights using Qwen Cloud.
    Analyzes transaction data and generates:
    - Trends and patterns
    - Opportunities for the business
    - Recommendations to increase commissions
    """
    summary = get_analytics_summary(days)
    settings = get_settings()

    llm = ChatOpenAI(
        model=settings.agent_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=0.4,
        max_tokens=1500,
    )

    analysis_prompt = f"""You are a business analyst for an enterprise point of sale. Analyze these data from the last {days} days and generate an executive report.

DATA:
- Total transactions: {summary['total_transactions']}
- Total commission: {summary['total_commission']}€
- By type: {json.dumps(summary['by_type'], ensure_ascii=False)}
- Agent usage: {json.dumps(summary['agent_usage'], ensure_ascii=False)}
- Guardrail blocks: {summary['guardrail_blocks']}
- Daily trend: {json.dumps(summary['daily_trend'], ensure_ascii=False)}
- Top tools: {json.dumps(summary['top_tools'], ensure_ascii=False)}

Generate an analysis with these sections (respond in the language of the data context, no <think> tags):
1. EXECUTIVE SUMMARY (2-3 lines)
2. DETECTED TRENDS (what's growing/decreasing)
3. OPPORTUNITIES (how to earn more commissions)
4. RECOMMENDATIONS (concrete actions for next week)
5. ALERTS (if anything concerning)

Be concise, practical and action-oriented. Use specific data from the report."""

    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are an expert business analyst. You generate actionable insights."),
            HumanMessage(content=analysis_prompt),
        ])

        content = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()

        return {
            "insights": content,
            "data": summary,
            "generated_by": "myagent_analytics",
            "period_days": days,
        }
    except Exception as e:
        return {
            "insights": f"Could not generate analysis: {str(e)}",
            "data": summary,
            "generated_by": "error",
            "period_days": days,
        }
