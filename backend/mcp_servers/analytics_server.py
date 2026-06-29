"""
MyAgent - MCP Server: Analytics
Exposes analytics and reporting tools via Model Context Protocol.

Can be run as a standalone process:
    python -m mcp_servers.analytics_server

Tools:
- get_daily_summary: Performance overview for a period
- get_top_products: Best performing products/services
- get_commission_trend: Commission data over time
- compare_periods: Period-over-period comparison
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("myagent-analytics")


@server.list_tools()
async def list_tools():
    """MCP Protocol: tools/list - List available analytics tools."""
    return [
        Tool(
            name="get_daily_summary",
            description="Get a summary of transactions and commissions for the specified period (1=today, 7=week, 30=month)",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to analyze (default 1)"},
                },
            },
        ),
        Tool(
            name="get_top_products",
            description="Get the top performing products/services ranked by volume",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Period to analyze (default 7)"},
                    "limit": {"type": "integer", "description": "Max products to return (default 10)"},
                },
            },
        ),
        Tool(
            name="get_commission_trend",
            description="Get commission trend data over time for visualizing growth",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days for trend (default 7)"},
                },
            },
        ),
        Tool(
            name="compare_periods",
            description="Compare current performance vs previous period to show growth or decline",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_days": {"type": "integer", "description": "Days for current period (default 7)"},
                    "previous_days": {"type": "integer", "description": "Days for previous period (default 7)"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP Protocol: tools/call - Execute an analytics tool."""
    from agents.analytics_agent import (
        get_daily_summary,
        get_top_products,
        get_commission_trend,
        compare_periods,
    )

    tool_map = {
        "get_daily_summary": get_daily_summary,
        "get_top_products": get_top_products,
        "get_commission_trend": get_commission_trend,
        "compare_periods": compare_periods,
    }

    if name not in tool_map:
        return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' not found"}))]

    try:
        result = tool_map[name].invoke(arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
