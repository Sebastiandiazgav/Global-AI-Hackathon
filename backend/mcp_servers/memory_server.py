"""
MyAgent - MCP Server: Memory
Exposes persistent memory tools via Model Context Protocol.

Can be run as a standalone process:
    python -m mcp_servers.memory_server

Tools:
- store_memory: Save a new memory (preference, pattern, insight)
- recall_memories: Retrieve relevant memories for context
- forget_memory: Explicitly forget a specific memory
- get_memory_summary: Get overview of stored memories
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("myagent-memory")


@server.list_tools()
async def list_tools():
    """MCP Protocol: tools/list - List available memory tools."""
    return [
        Tool(
            name="store_memory",
            description="Store a persistent memory that will be remembered across sessions. Use for preferences, patterns, and important observations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session/user identifier"},
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory to store",
                        "enum": ["preference", "pattern", "client_info", "service_history", "insight"],
                    },
                    "content": {"type": "string", "description": "The memory content in natural language"},
                    "relevance": {"type": "number", "description": "Importance score 0.0-1.0 (default 0.7)"},
                },
                "required": ["session_id", "memory_type", "content"],
            },
        ),
        Tool(
            name="recall_memories",
            description="Recall stored memories for a session. Use to get context about user preferences, patterns, and history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session/user identifier"},
                    "memory_type": {
                        "type": "string",
                        "description": "Filter by type (optional)",
                        "enum": ["preference", "pattern", "client_info", "service_history", "insight"],
                    },
                    "query": {"type": "string", "description": "Keyword to search in memories (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="forget_memory",
            description="Explicitly forget (delete) a specific memory by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session/user identifier"},
                    "memory_id": {"type": "string", "description": "ID of the memory to forget"},
                },
                "required": ["session_id", "memory_id"],
            },
        ),
        Tool(
            name="get_memory_summary",
            description="Get an overview of all stored memories for a session (counts by type, relevance stats).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session/user identifier"},
                },
                "required": ["session_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP Protocol: tools/call - Execute a memory tool."""
    from agents.persistent_memory import get_persistent_memory

    store = get_persistent_memory()

    if name == "store_memory":
        memory_id = store.store(
            session_id=arguments["session_id"],
            memory_type=arguments["memory_type"],
            content=arguments["content"],
            relevance=arguments.get("relevance", 0.7),
        )
        result = {"stored": True, "memory_id": memory_id, "type": arguments["memory_type"]}

    elif name == "recall_memories":
        memories = store.recall(
            session_id=arguments["session_id"],
            memory_type=arguments.get("memory_type"),
            query=arguments.get("query"),
            limit=arguments.get("limit", 10),
        )
        result = {
            "count": len(memories),
            "memories": [
                {
                    "id": m["id"],
                    "type": m["memory_type"],
                    "content": m["content"],
                    "relevance": m["relevance"],
                    "created_at": m["created_at"],
                    "access_count": m["access_count"],
                }
                for m in memories
            ],
        }

    elif name == "forget_memory":
        success = store.forget(
            session_id=arguments["session_id"],
            memory_id=arguments["memory_id"],
        )
        result = {"forgotten": success, "memory_id": arguments["memory_id"]}

    elif name == "get_memory_summary":
        result = store.get_session_summary(arguments["session_id"])

    else:
        result = {"error": f"Tool '{name}' not found"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
