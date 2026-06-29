"""
MyAgent - MCP Server: Logística
Real MCP server that exposes logistics tools via Model Context Protocol.

Can be run as a standalone process:
    python -m mcp_servers.logistica_server
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("MyAgent-logistica")


@server.list_tools()
async def list_tools():
    """MCP Protocol: tools/list - List available logistics tools."""
    return [
        Tool(
            name="registrar_paquetes",
            description="Registra la recepción de paquetes de un transportista en el punto de venta",
            inputSchema={
                "type": "object",
                "properties": {
                    "transportista": {"type": "string", "description": "Nombre del transportista (Amazon, GLS, SEUR)"},
                    "cantidad": {"type": "integer", "description": "Número de paquetes a registrar"},
                    "codigos_tracking": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Lista de códigos de seguimiento (opcional)",
                    },
                },
                "required": ["transportista", "cantidad"],
            },
        ),
        Tool(
            name="confirmar_entrega_paquete",
            description="Confirma la entrega de un paquete al cliente final con verificación",
            inputSchema={
                "type": "object",
                "properties": {
                    "codigo_tracking": {"type": "string", "description": "Código de seguimiento del paquete"},
                    "metodo_verificacion": {"type": "string", "enum": ["pin", "dni", "dni_digital"]},
                    "codigo_verificacion": {"type": "string", "description": "PIN o últimos 4 dígitos del DNI"},
                },
                "required": ["codigo_tracking"],
            },
        ),
        Tool(
            name="consultar_estado_paquete",
            description="Consulta el estado actual de un paquete en el sistema",
            inputSchema={
                "type": "object",
                "properties": {
                    "codigo_tracking": {"type": "string", "description": "Código de seguimiento"},
                },
                "required": ["codigo_tracking"],
            },
        ),
        Tool(
            name="gestionar_devolucion",
            description="Gestiona la devolución de un paquete al transportista",
            inputSchema={
                "type": "object",
                "properties": {
                    "codigo_tracking": {"type": "string", "description": "Código de seguimiento"},
                    "motivo": {"type": "string", "enum": ["no_recogido", "rechazado", "dañado"]},
                },
                "required": ["codigo_tracking"],
            },
        ),
        Tool(
            name="listar_paquetes_pendientes",
            description="Lista todos los paquetes pendientes de recogida en el punto de venta",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP Protocol: tools/call - Execute a logistics tool."""
    from agents.logistica_agent import (
        registrar_paquetes,
        confirmar_entrega_paquete,
        consultar_estado_paquete,
        gestionar_devolucion,
        listar_paquetes_pendientes,
    )

    tool_map = {
        "registrar_paquetes": registrar_paquetes,
        "confirmar_entrega_paquete": confirmar_entrega_paquete,
        "consultar_estado_paquete": consultar_estado_paquete,
        "gestionar_devolucion": gestionar_devolucion,
        "listar_paquetes_pendientes": listar_paquetes_pendientes,
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
