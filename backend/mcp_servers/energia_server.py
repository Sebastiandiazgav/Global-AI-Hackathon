"""
MyAgent - MCP Server: Energy
Real MCP server that exposes energy tools via Model Context Protocol.

Can be run as a standalone process:
    python -m mcp_servers.energia_server

Or used in-process via the MCPClient.
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create MCP Server instance
server = Server("myagent-energia")


@server.list_tools()
async def list_tools():
    """MCP Protocol: tools/list - List available energy tools."""
    return [
        Tool(
            name="calcular_ahorro_energetico",
            description="Calcula el ahorro potencial comparando la tarifa actual del cliente con las mejores ofertas del mercado",
            inputSchema={
                "type": "object",
                "properties": {
                    "consumo_kwh": {
                        "type": "number",
                        "description": "Consumo mensual en kWh del cliente",
                    },
                    "tarifa_actual": {
                        "type": "string",
                        "description": "Tipo de tarifa actual (plana, indexada, discriminacion_horaria)",
                        "enum": ["plana", "indexada", "discriminacion_horaria"],
                    },
                },
                "required": ["consumo_kwh", "tarifa_actual"],
            },
        ),
        Tool(
            name="preparar_contrato_energia",
            description="Prepara un borrador de contrato para cambio de tarifa energética",
            inputSchema={
                "type": "object",
                "properties": {
                    "dni_cliente": {"type": "string", "description": "DNI del cliente"},
                    "nueva_tarifa": {"type": "string", "description": "Nombre de la tarifa destino"},
                    "consumo_kwh": {"type": "number", "description": "Consumo mensual estimado"},
                    "nombre_cliente": {"type": "string", "description": "Nombre completo del titular"},
                    "telefono_cliente": {"type": "string", "description": "Teléfono de contacto"},
                    "email_cliente": {"type": "string", "description": "Email de contacto (opcional)"},
                },
                "required": ["dni_cliente", "nueva_tarifa", "consumo_kwh", "nombre_cliente", "telefono_cliente"],
            },
        ),
        Tool(
            name="consultar_tarifas_disponibles",
            description="Consulta todas las tarifas energéticas disponibles actualmente en el sistema",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP Protocol: tools/call - Execute an energy tool."""
    from agents.energia_agent import (
        calcular_ahorro_energetico,
        preparar_contrato_energia,
        consultar_tarifas_disponibles,
    )

    tool_map = {
        "calcular_ahorro_energetico": calcular_ahorro_energetico,
        "preparar_contrato_energia": preparar_contrato_energia,
        "consultar_tarifas_disponibles": consultar_tarifas_disponibles,
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
