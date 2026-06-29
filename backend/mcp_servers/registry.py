"""
MyAgent - MCP Server Registry
Manages MCP server configurations and provides a unified interface
for discovering and invoking tools across all MCP servers.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
import json


@dataclass
class MCPToolDefinition:
    """Definition of a tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict
    server_name: str


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    description: str
    domain: str
    tools: List[MCPToolDefinition] = field(default_factory=list)
    status: str = "active"


class MCPRegistry:
    """
    Registry of all MCP servers in the MyAgent system.
    
    Provides:
    - Server discovery
    - Tool listing across all servers
    - Tool invocation routing
    - Health monitoring
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._tool_map: Dict[str, MCPToolDefinition] = {}
        self._initialize_servers()

    def _initialize_servers(self):
        """Register all MCP servers."""
        # Energy Server
        self.register_server(MCPServerConfig(
            name="myagent-energia",
            description="Servicios de energía: comparación de tarifas, contratos, ahorro",
            domain="energia",
            tools=[
                MCPToolDefinition(
                    name="calcular_ahorro_energetico",
                    description="Calcula el ahorro potencial comparando tarifas eléctricas del mercado",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "consumo_kwh": {"type": "number", "description": "Consumo mensual en kWh"},
                            "tarifa_actual": {
                                "type": "string",
                                "description": "Tipo de tarifa actual",
                                "enum": ["plana", "indexada", "discriminacion_horaria"],
                            },
                        },
                        "required": ["consumo_kwh", "tarifa_actual"],
                    },
                    server_name="myagent-energia",
                ),
                MCPToolDefinition(
                    name="preparar_contrato_energia",
                    description="Prepara borrador de contrato para cambio de tarifa energética",
                    input_schema={
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
                    server_name="myagent-energia",
                ),
                MCPToolDefinition(
                    name="consultar_tarifas_disponibles",
                    description="Consulta todas las tarifas energéticas disponibles en el sistema",
                    input_schema={"type": "object", "properties": {}},
                    server_name="myagent-energia",
                ),
            ],
        ))

        # Logistics Server
        self.register_server(MCPServerConfig(
            name="myagent-logistica",
            description="Servicios de logística: paquetería, Amazon Hub, GLS, devoluciones",
            domain="logistica",
            tools=[
                MCPToolDefinition(
                    name="registrar_paquetes",
                    description="Registra recepción de paquetes de un transportista",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "transportista": {"type": "string", "description": "Nombre del transportista"},
                            "cantidad": {"type": "integer", "description": "Número de paquetes"},
                            "codigos_tracking": {
                                "type": "array", "items": {"type": "string"},
                                "description": "Códigos de seguimiento (opcional)",
                            },
                        },
                        "required": ["transportista", "cantidad"],
                    },
                    server_name="myagent-logistica",
                ),
                MCPToolDefinition(
                    name="confirmar_entrega_paquete",
                    description="Confirma entrega de paquete al cliente final",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "codigo_tracking": {"type": "string", "description": "Código de seguimiento"},
                            "metodo_verificacion": {
                                "type": "string", "enum": ["pin", "dni", "dni_digital"],
                            },
                            "codigo_verificacion": {"type": "string"},
                        },
                        "required": ["codigo_tracking"],
                    },
                    server_name="myagent-logistica",
                ),
                MCPToolDefinition(
                    name="consultar_estado_paquete",
                    description="Consulta estado actual de un paquete",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "codigo_tracking": {"type": "string", "description": "Código de seguimiento"},
                        },
                        "required": ["codigo_tracking"],
                    },
                    server_name="myagent-logistica",
                ),
                MCPToolDefinition(
                    name="gestionar_devolucion",
                    description="Gestiona devolución de un paquete",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "codigo_tracking": {"type": "string"},
                            "motivo": {"type": "string", "enum": ["no_recogido", "rechazado", "dañado"]},
                        },
                        "required": ["codigo_tracking"],
                    },
                    server_name="myagent-logistica",
                ),
                MCPToolDefinition(
                    name="listar_paquetes_pendientes",
                    description="Lista todos los paquetes pendientes de recogida",
                    input_schema={"type": "object", "properties": {}},
                    server_name="myagent-logistica",
                ),
            ],
        ))

        # Catalog/Support Server
        self.register_server(MCPServerConfig(
            name="myagent-catalogo",
            description="Servicios de catálogo y soporte: recargas, PINs, RAG, productos",
            domain="soporte",
            tools=[
                MCPToolDefinition(
                    name="procesar_recarga",
                    description="Procesa recarga telefónica nacional o internacional",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "monto": {"type": "number", "description": "Cantidad en euros"},
                            "pais": {"type": "string", "description": "País destino"},
                            "numero_telefono": {"type": "string", "description": "Número destino"},
                            "operador": {"type": "string", "description": "Operador (opcional)"},
                        },
                        "required": ["monto", "pais", "numero_telefono"],
                    },
                    server_name="myagent-catalogo",
                ),
                MCPToolDefinition(
                    name="activar_pin_digital",
                    description="Activa PIN digital para plataformas de entretenimiento",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "plataforma": {"type": "string", "description": "Plataforma (netflix, playstation, etc.)"},
                            "producto": {"type": "string", "description": "Tipo de producto"},
                            "valor": {"type": "number", "description": "Valor en euros (si aplica)"},
                        },
                        "required": ["plataforma", "producto"],
                    },
                    server_name="myagent-catalogo",
                ),
                MCPToolDefinition(
                    name="buscar_en_manuales",
                    description="Busca información en manuales operativos via RAG (vector store)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "pregunta": {"type": "string", "description": "Pregunta sobre procedimientos"},
                        },
                        "required": ["pregunta"],
                    },
                    server_name="myagent-catalogo",
                ),
                MCPToolDefinition(
                    name="consultar_catalogo_productos",
                    description="Consulta catálogo de productos digitales disponibles",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "categoria": {"type": "string", "description": "Categoría a filtrar"},
                        },
                    },
                    server_name="myagent-catalogo",
                ),
            ],
        ))

        # Memory Server
        self.register_server(MCPServerConfig(
            name="myagent-memory",
            description="Persistent memory management: store, recall, and forget cross-session memories",
            domain="memory",
            tools=[
                MCPToolDefinition(
                    name="store_memory",
                    description="Store a persistent memory across sessions (preferences, patterns, insights)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session/user identifier"},
                            "memory_type": {"type": "string", "enum": ["preference", "pattern", "client_info", "service_history", "insight"]},
                            "content": {"type": "string", "description": "Memory content in natural language"},
                            "relevance": {"type": "number", "description": "Importance 0.0-1.0"},
                        },
                        "required": ["session_id", "memory_type", "content"],
                    },
                    server_name="myagent-memory",
                ),
                MCPToolDefinition(
                    name="recall_memories",
                    description="Recall stored memories for context (preferences, patterns, history)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session/user identifier"},
                            "memory_type": {"type": "string", "enum": ["preference", "pattern", "client_info", "service_history", "insight"]},
                            "query": {"type": "string", "description": "Keyword search"},
                            "limit": {"type": "integer", "description": "Max results"},
                        },
                        "required": ["session_id"],
                    },
                    server_name="myagent-memory",
                ),
                MCPToolDefinition(
                    name="forget_memory",
                    description="Explicitly forget a specific memory by ID",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session/user identifier"},
                            "memory_id": {"type": "string", "description": "Memory ID to forget"},
                        },
                        "required": ["session_id", "memory_id"],
                    },
                    server_name="myagent-memory",
                ),
                MCPToolDefinition(
                    name="get_memory_summary",
                    description="Get overview of all stored memories for a session",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session/user identifier"},
                        },
                        "required": ["session_id"],
                    },
                    server_name="myagent-memory",
                ),
            ],
        ))

        # Analytics Server
        self.register_server(MCPServerConfig(
            name="myagent-analytics",
            description="Business analytics: performance metrics, commission trends, product ranking, period comparison",
            domain="analytics",
            tools=[
                MCPToolDefinition(
                    name="get_daily_summary",
                    description="Get transaction and commission summary for a period",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "Days to analyze"},
                        },
                    },
                    server_name="myagent-analytics",
                ),
                MCPToolDefinition(
                    name="get_top_products",
                    description="Get top performing products/services by volume",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer"},
                            "limit": {"type": "integer"},
                        },
                    },
                    server_name="myagent-analytics",
                ),
                MCPToolDefinition(
                    name="get_commission_trend",
                    description="Get commission trend data over time",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer"},
                        },
                    },
                    server_name="myagent-analytics",
                ),
                MCPToolDefinition(
                    name="compare_periods",
                    description="Compare current vs previous period performance",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "current_days": {"type": "integer"},
                            "previous_days": {"type": "integer"},
                        },
                    },
                    server_name="myagent-analytics",
                ),
            ],
        ))

    def register_server(self, config: MCPServerConfig):
        """Register an MCP server and index its tools."""
        self._servers[config.name] = config
        for tool in config.tools:
            self._tool_map[tool.name] = tool

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered MCP servers."""
        return [
            {
                "name": server.name,
                "description": server.description,
                "domain": server.domain,
                "status": server.status,
                "tools_count": len(server.tools),
                "tools": [t.name for t in server.tools],
            }
            for server in self._servers.values()
        ]

    def list_tools(self, server_name: str = None) -> List[Dict[str, Any]]:
        """List all tools, optionally filtered by server."""
        tools = []
        for tool in self._tool_map.values():
            if server_name and tool.server_name != server_name:
                continue
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "server": tool.server_name,
                "input_schema": tool.input_schema,
            })
        return tools

    def get_tool(self, tool_name: str) -> MCPToolDefinition | None:
        """Get a specific tool definition."""
        return self._tool_map.get(tool_name)

    def get_server(self, server_name: str) -> MCPServerConfig | None:
        """Get a specific server configuration."""
        return self._servers.get(server_name)

    def get_tools_for_domain(self, domain: str) -> List[MCPToolDefinition]:
        """Get all tools for a specific domain."""
        server = next(
            (s for s in self._servers.values() if s.domain == domain),
            None,
        )
        return server.tools if server else []


# Singleton registry
_registry = None


def get_mcp_registry() -> MCPRegistry:
    """Get the singleton MCP registry."""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
    return _registry
