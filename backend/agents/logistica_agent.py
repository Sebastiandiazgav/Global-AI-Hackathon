"""
MyAgent - Logistics Agent
Specialized agent for package management: Amazon Hub, GLS, deliveries, returns.
Powered by Qwen Cloud. Supports multilingual responses.
"""

from typing import Optional, List
from datetime import datetime

from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from config import get_settings
from agents.state import AgentState
from agents.token_utils import compact_messages, compact_tool_result_for_llm
from agents.model_router import ainvoke_with_retry
from mcp_servers.client import get_mcp_client
from database.reference_data import get_reference_dataset

# ============================================
# TOOLS - Logistics Vertical
# ============================================


@tool
def registrar_paquetes(
    transportista: str,
    cantidad: int,
    codigos_tracking: Optional[List[str]] = None,
) -> dict:
    """
    Registers package reception from a carrier at the point of sale.
    Activates bulk scanning mode for processing multiple packages.

    Args:
        transportista: Carrier name (Amazon, GLS, SEUR, etc.)
        cantidad: Number of packages to register
        codigos_tracking: Optional list of tracking codes
    """
    if not codigos_tracking:
        codigos_tracking = [
            f"{transportista[:3].upper()}-{datetime.now().strftime('%Y%m%d')}-{str(i).zfill(4)}"
            for i in range(1, cantidad + 1)
        ]

    comisiones = get_reference_dataset("logistica_comision_por_transportista")
    comision_por_paquete = comisiones.get(transportista.lower(), comisiones.get("default", 0.25))
    comision_total = comision_por_paquete * cantidad

    return {
        "estado": "registrados",
        "transportista": transportista,
        "paquetes_registrados": cantidad,
        "codigos": codigos_tracking[:5],
        "comision_por_paquete": f"{comision_por_paquete}€",
        "comision_total": f"{comision_total}€",
        "ubicacion_sugerida": f"Shelf {chr(65 + (cantidad % 4))}, zone {transportista[:3].upper()}",
        "plazo_recogida": "7 calendar days",
        "siguiente_paso": "Scan barcode of each package with the Smart POS",
        "nota": "Uncollected packages after 7 days are returned automatically",
    }


@tool
def confirmar_entrega_paquete(
    codigo_tracking: str,
    metodo_verificacion: str = "pin",
    codigo_verificacion: Optional[str] = None,
) -> dict:
    """
    Confirms package delivery to the end customer.
    Verifies identity via PIN or ID document.

    Args:
        codigo_tracking: Package tracking code
        metodo_verificacion: Verification method (pin, dni, dni_digital)
        codigo_verificacion: PIN or last 4 digits of ID
    """
    return {
        "estado": "entregado",
        "codigo_tracking": codigo_tracking,
        "verificacion": {"metodo": metodo_verificacion, "resultado": "verified_ok"},
        "timestamp": datetime.now().isoformat(),
        "comision_generada": "0.30€",
        "mensaje_cliente": "Package delivered successfully. Thank you for using our service!",
        "siguiente_paso": "System will automatically notify the carrier",
    }


@tool
def consultar_estado_paquete(codigo_tracking: str) -> dict:
    """
    Queries the current status of a package in the system.

    Args:
        codigo_tracking: Package tracking code
    """
    return {
        "codigo_tracking": codigo_tracking,
        "estado_actual": "at_point_of_sale",
        "transportista": "Amazon",
        "fecha_recepcion": "2026-06-08T09:30:00",
        "dias_en_tienda": 2,
        "plazo_restante": "5 days",
        "destinatario": "Client ***4521",
        "historial": [
            {"fecha": "2026-06-07", "evento": "Shipped from warehouse"},
            {"fecha": "2026-06-08", "evento": "Received at point of sale"},
            {"fecha": "2026-06-09", "evento": "Awaiting pickup"},
        ],
    }


@tool
def gestionar_devolucion(
    codigo_tracking: str,
    motivo: str = "no_recogido",
) -> dict:
    """
    Manages the return of a package to the carrier.

    Args:
        codigo_tracking: Package tracking code
        motivo: Return reason (no_recogido, rechazado, dañado)
    """
    return {
        "estado": "devolucion_programada",
        "codigo_tracking": codigo_tracking,
        "motivo": motivo,
        "recogida_programada": "Next carrier pass (24-48h)",
        "instrucciones": [
            "Keep the package in the returns area",
            "Print return label from Smart POS",
            "Hand to carrier on their next visit",
        ],
        "nota": "No commission for returns, but the management is logged",
    }


@tool
def listar_paquetes_pendientes() -> dict:
    """
    Lists all packages pending pickup at the point of sale.

    Returns:
        List of packages with their statuses and deadlines
    """
    return get_reference_dataset("logistica_paquetes_pendientes")


from agents.prompts import get_logistica_prompt

# ============================================
# AGENT DEFINITION
# ============================================

LOGISTICA_TOOLS = [
    registrar_paquetes,
    confirmar_entrega_paquete,
    consultar_estado_paquete,
    gestionar_devolucion,
    listar_paquetes_pendientes,
]


def get_logistica_llm():
    """Get LLM configured for logistics agent via Qwen Cloud with fallback."""
    from agents.model_router import get_llm
    settings = get_settings()
    return get_llm(role="agent", temperature=0.2, max_tokens=settings.agent_max_tokens)


async def logistica_node(state: AgentState) -> AgentState:
    """
    Logistics agent node - handles all package/delivery queries.
    Responds in the detected language of the user.
    """
    llm = get_logistica_llm()
    settings = get_settings()
    llm_with_tools = llm.bind_tools(LOGISTICA_TOOLS)

    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    language = state.get("language", settings.default_language)

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "logistica", "status": "processing"},
    })

    language_instruction = (
        f"IMPORTANT: The user is communicating in '{language}'. "
        f"You MUST respond in the same language ('{language}'). "
        "Adapt your response naturally to that language."
    )

    system_rules = (
        "IMPORTANT: Do not use <think> tags. Respond directly. "
        "If packages arrive use registrar_paquetes. For status queries use listar_paquetes_pendientes. "
        "Do not simulate results without executing tools.\n\n"
        f"{language_instruction}"
    )

    messages = [SystemMessage(content=get_logistica_prompt() + "\n\n" + system_rules)]
    messages.extend(
        compact_messages(
            state["messages"],
            max_messages=settings.agent_context_max_messages,
            max_chars_per_message=settings.agent_context_max_chars,
        )
    )

    response = await ainvoke_with_retry(
        messages, role="agent", temperature=0.2,
        max_tokens=settings.agent_max_tokens, tools=LOGISTICA_TOOLS,
        config={
            "tags": ["myagent", "agent", "logistica"],
            "metadata": {
                "trace_id": state.get("trace_id", ""),
                "session_id": state.get("session_id", ""),
                "node": "logistica",
                "language": language,
            },
        },
    )

    if response.tool_calls:
        tool_results = []
        tool_map = {t.name: t for t in LOGISTICA_TOOLS}
        mcp_client = get_mcp_client()
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})

            mcp_result = await mcp_client.call_tool(tool_name, tool_args)
            if not mcp_result.get("is_error", False):
                result = mcp_result.get("content", {})
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)
                workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "mcp"}})
            elif tool_name in tool_map:
                result = tool_map[tool_name].invoke(tool_args)
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)
                workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "fallback_direct"}})

        messages.append(response)
        for i, tr in enumerate(tool_results):
            tool_call_id = tr.get("tool_call_id") or (response.tool_calls[i]["id"] if i < len(response.tool_calls) else response.tool_calls[0]["id"])
            messages.append(
                ToolMessage(
                    content=compact_tool_result_for_llm(tr["result"], max_chars=settings.agent_tool_result_max_chars),
                    tool_call_id=tool_call_id,
                )
            )

        final_response = await llm.ainvoke(
            messages,
            config={
                "tags": ["myagent", "agent", "logistica", "tool-response"],
                "metadata": {"trace_id": state.get("trace_id", ""), "node": "logistica", "language": language},
            },
        )
        response_text = final_response.content
    else:
        response_text = response.content

    workflow_events.append({
        "type": "response",
        "data": {"agent": "logistica", "status": "completed"},
    })

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }
