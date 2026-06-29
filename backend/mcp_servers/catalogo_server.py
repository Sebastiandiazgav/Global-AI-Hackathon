"""
MyAgent - MCP Server: Catálogo y Soporte
Real MCP server that exposes catalog/support tools via Model Context Protocol.

Can be run as a standalone process:
    python -m mcp_servers.catalogo_server
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("MyAgent-catalogo")


@server.list_tools()
async def list_tools():
    """MCP Protocol: tools/list - List available catalog/support tools."""
    return [
        Tool(
            name="procesar_recarga",
            description="Procesa una recarga telefónica nacional o internacional",
            inputSchema={
                "type": "object",
                "properties": {
                    "monto": {"type": "number", "description": "Cantidad en euros a recargar"},
                    "pais": {"type": "string", "description": "País destino"},
                    "numero_telefono": {"type": "string", "description": "Número de teléfono destino"},
                    "operador": {"type": "string", "description": "Operador telefónico (opcional)"},
                },
                "required": ["monto", "pais", "numero_telefono"],
            },
        ),
        Tool(
            name="activar_pin_digital",
            description="Activa un PIN digital para plataformas de entretenimiento o servicios",
            inputSchema={
                "type": "object",
                "properties": {
                    "plataforma": {"type": "string", "description": "Plataforma (netflix, playstation, spotify, etc.)"},
                    "producto": {"type": "string", "description": "Tipo de producto"},
                    "valor": {"type": "number", "description": "Valor en euros (si aplica)"},
                },
                "required": ["plataforma", "producto"],
            },
        ),
        Tool(
            name="buscar_en_manuales",
            description="Busca información en la base de conocimiento de manuales operativos (RAG vector store)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pregunta": {"type": "string", "description": "Pregunta sobre procedimientos, productos o incidencias"},
                },
                "required": ["pregunta"],
            },
        ),
        Tool(
            name="consultar_catalogo_productos",
            description="Consulta el catálogo de productos digitales disponibles",
            inputSchema={
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Filtrar por categoría (recargas, pines, entretenimiento, gaming)"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP Protocol: tools/call - Execute a catalog/support tool."""
    from agents.soporte_agent import (
        procesar_recarga,
        activar_pin_digital,
        buscar_en_manuales,
        consultar_catalogo_productos,
    )

    tool_map = {
        "procesar_recarga": procesar_recarga,
        "activar_pin_digital": activar_pin_digital,
        "buscar_en_manuales": buscar_en_manuales,
        "consultar_catalogo_productos": consultar_catalogo_productos,
    }

    if name not in tool_map:
        return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' not found"}))]

    try:
        result = tool_map[name].invoke(arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
