"""
MyAgent - MCP Client
Provides a unified interface for agents to invoke tools via MCP protocol.

This client acts as the bridge between LangChain agents and MCP servers,
translating function calls into MCP tool invocations.
"""

import json
import sys
from time import perf_counter
from importlib import import_module
from pathlib import Path
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from config import get_settings
from database.mcp_ops import get_tool_policy, save_mcp_tool_audit
from mcp_servers.registry import get_mcp_registry


_TOOL_PATHS = {
    # Energy
    "calcular_ahorro_energetico": ("agents.energia_agent", "calcular_ahorro_energetico"),
    "preparar_contrato_energia": ("agents.energia_agent", "preparar_contrato_energia"),
    "consultar_tarifas_disponibles": ("agents.energia_agent", "consultar_tarifas_disponibles"),
    # Logistics
    "registrar_paquetes": ("agents.logistica_agent", "registrar_paquetes"),
    "confirmar_entrega_paquete": ("agents.logistica_agent", "confirmar_entrega_paquete"),
    "consultar_estado_paquete": ("agents.logistica_agent", "consultar_estado_paquete"),
    "gestionar_devolucion": ("agents.logistica_agent", "gestionar_devolucion"),
    "listar_paquetes_pendientes": ("agents.logistica_agent", "listar_paquetes_pendientes"),
    # Support/Catalog
    "procesar_recarga": ("agents.soporte_agent", "procesar_recarga"),
    "activar_pin_digital": ("agents.soporte_agent", "activar_pin_digital"),
    "buscar_en_manuales": ("agents.soporte_agent", "buscar_en_manuales"),
    "consultar_catalogo_productos": ("agents.soporte_agent", "consultar_catalogo_productos"),
    # Memory (handled by memory_server via MCP, no direct tool path needed)
}

_SERVER_MODULES = {
    "myagent-energia": "mcp_servers.energia_server",
    "myagent-logistica": "mcp_servers.logistica_server",
    "myagent-catalogo": "mcp_servers.catalogo_server",
    "myagent-memory": "mcp_servers.memory_server",
    "myagent-analytics": "mcp_servers.analytics_server",
}


def _resolve_tool(tool_name: str):
    """Load tool implementation lazily to avoid circular imports."""
    path = _TOOL_PATHS.get(tool_name)
    if not path:
        return None
    module_name, symbol_name = path
    module = import_module(module_name)
    return getattr(module, symbol_name, None)


class MCPClient:
    """
    MCP Client for MyAgent.
    
    Implements the client side of the Model Context Protocol,
    providing tool discovery and invocation capabilities.
    
    In production, this would communicate with MCP servers via stdio/SSE transport.
    For this MVP, it uses in-process invocation with the same protocol interface.
    """

    def __init__(self):
        self.registry = get_mcp_registry()
        self.settings = get_settings()
        self._cwd = str(Path(__file__).resolve().parents[1])

    async def list_tools(self, server_name: str = None) -> list:
        """
        MCP Protocol: tools/list
        Discover available tools from MCP servers.
        """
        return self.registry.list_tools(server_name)

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        client_id: str = "internal-system",
        trace_id: str = "",
    ) -> Dict[str, Any]:
        """
        MCP Protocol: tools/call
        Invoke a tool on the appropriate MCP server.
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments matching the input schema
            
        Returns:
            Tool execution result
        """
        # Verify tool exists in registry
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            return {
                "error": f"Tool '{tool_name}' not found in MCP registry",
                "available_tools": [t["name"] for t in self.registry.list_tools()],
                "is_error": True,
            }

        mode = (self.settings.mcp_transport_mode or "auto").strip().lower()
        policy = get_tool_policy(tool_name) or {}

        # First try real MCP transport through stdio.
        started = perf_counter()
        if mode in ("auto", "stdio"):
            stdio_result = await self._call_tool_stdio(tool_def.server_name, tool_name, arguments)
            latency_ms = int((perf_counter() - started) * 1000)
            save_mcp_tool_audit(
                client_id=client_id,
                tool_name=tool_name,
                status="error" if stdio_result.get("is_error") else "ok",
                latency_ms=latency_ms,
                transport=stdio_result.get("transport", ""),
                server=stdio_result.get("server", ""),
                trace_id=trace_id,
                error=str((stdio_result.get("content") or {}).get("error", "")) if isinstance(stdio_result.get("content"), dict) else "",
            )
            if not stdio_result.get("is_error", False):
                stdio_result["policy"] = policy
                return stdio_result
            if mode == "stdio":
                stdio_result["policy"] = policy
                return stdio_result

        # Fallback path keeps service availability while stdio is not available.
        fallback_started = perf_counter()
        fallback_result = self._call_tool_inprocess(tool_def.server_name, tool_name, arguments)
        fallback_latency_ms = int((perf_counter() - fallback_started) * 1000)
        save_mcp_tool_audit(
            client_id=client_id,
            tool_name=tool_name,
            status="error" if fallback_result.get("is_error") else "ok",
            latency_ms=fallback_latency_ms,
            transport=fallback_result.get("transport", ""),
            server=fallback_result.get("server", ""),
            trace_id=trace_id,
            error=str((fallback_result.get("content") or {}).get("error", "")) if isinstance(fallback_result.get("content"), dict) else "",
        )
        fallback_result["policy"] = policy
        return fallback_result

    async def _call_tool_stdio(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        module_name = _SERVER_MODULES.get(server_name)
        if not module_name:
            return {
                "content": {"error": f"No MCP server module configured for '{server_name}'"},
                "tool_name": tool_name,
                "server": server_name,
                "transport": "mcp_stdio",
                "is_error": True,
            }

        try:
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", module_name],
                cwd=self._cwd,
            )
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    call_result = await session.call_tool(tool_name, arguments or {})

            if getattr(call_result, "isError", False):
                return {
                    "content": self._extract_mcp_content(call_result.content),
                    "tool_name": tool_name,
                    "server": server_name,
                    "transport": "mcp_stdio",
                    "is_error": True,
                }

            return {
                "content": self._extract_mcp_content(call_result.content),
                "tool_name": tool_name,
                "server": server_name,
                "transport": "mcp_stdio",
                "is_error": False,
            }
        except Exception as exc:
            return {
                "content": {"error": str(exc)},
                "tool_name": tool_name,
                "server": server_name,
                "transport": "mcp_stdio",
                "is_error": True,
            }

    def _call_tool_inprocess(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        implementation = _resolve_tool(tool_name)
        if not implementation:
            return {
                "error": f"No implementation found for tool '{tool_name}'",
                "server": server_name,
                "transport": "inprocess",
                "is_error": True,
            }

        try:
            result = implementation.invoke(arguments)
            return {
                "content": result,
                "tool_name": tool_name,
                "server": server_name,
                "transport": "inprocess",
                "is_error": False,
            }
        except Exception as exc:
            return {
                "content": {"error": str(exc)},
                "tool_name": tool_name,
                "server": server_name,
                "transport": "inprocess",
                "is_error": True,
            }

    @staticmethod
    def _extract_mcp_content(content: Any) -> Any:
        if isinstance(content, dict):
            return content
        if isinstance(content, list):
            texts = []
            for item in content:
                text = getattr(item, "text", None)
                if isinstance(text, str) and text.strip():
                    texts.append(text)
            if not texts:
                return {"raw": str(content)}
            if len(texts) == 1:
                text = texts[0]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw": text}
            return {"raw": texts}
        return {"raw": str(content)}

    async def get_server_info(self, server_name: str) -> Dict[str, Any] | None:
        """
        MCP Protocol: server/info
        Get information about a specific MCP server.
        """
        server = self.registry.get_server(server_name)
        if not server:
            return None
        return {
            "name": server.name,
            "description": server.description,
            "domain": server.domain,
            "status": server.status,
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
            },
        }


# Singleton client
_client = None


def get_mcp_client() -> MCPClient:
    """Get the singleton MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
