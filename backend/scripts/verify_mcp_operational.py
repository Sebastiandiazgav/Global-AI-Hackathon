"""
MyAgent - MCP Operational Verification Script
Verifies that MCP servers and tools are functioning correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.client import get_mcp_client
from mcp_servers.registry import get_mcp_registry


async def verify():
    """Run verification checks on MCP infrastructure."""
    print("🔍 MyAgent MCP Operational Verification")
    print("=" * 50)

    # 1. Registry check
    registry = get_mcp_registry()
    servers = registry.list_servers()
    print(f"\n✅ Registry: {len(servers)} servers registered")
    for s in servers:
        print(f"   - {s['name']} ({s['tools_count']} tools) [{s['status']}]")

    # 2. Tools listing
    tools = registry.list_tools()
    print(f"\n✅ Total tools: {len(tools)}")
    for t in tools:
        print(f"   - {t['name']} [{t['server']}]")

    # 3. Tool invocation test
    print("\n🧪 Testing tool invocations...")
    client = get_mcp_client()

    test_cases = [
        ("consultar_tarifas_disponibles", {}),
        ("listar_paquetes_pendientes", {}),
        ("consultar_catalogo_productos", {"categoria": "streaming"}),
    ]

    for tool_name, args in test_cases:
        result = await client.call_tool(tool_name, args)
        status = "✅" if not result.get("is_error") else "❌"
        transport = result.get("transport", "unknown")
        print(f"   {status} {tool_name} [{transport}]")

    print("\n" + "=" * 50)
    print("✅ Verification complete!")


if __name__ == "__main__":
    asyncio.run(verify())
