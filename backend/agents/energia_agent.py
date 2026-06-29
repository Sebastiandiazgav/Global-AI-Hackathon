"""
MyAgent - Energy Agent
Specialized agent for energy services: tariff comparison, savings calculation, contracts.
Powered by Qwen Cloud. Supports multilingual responses.
"""

import re
from typing import Optional

from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from config import get_settings
from agents.state import AgentState
from agents.token_utils import compact_messages, compact_tool_result_for_llm
from mcp_servers.client import get_mcp_client
from database.reference_data import get_reference_dataset

# ============================================
# TOOLS - Energy Vertical
# ============================================


@tool
def calcular_ahorro_energetico(consumo_kwh: float, tarifa_actual: str) -> dict:
    """
    Calculates potential savings by comparing the client's current tariff
    with the best available offers in the market.

    Args:
        consumo_kwh: Monthly consumption in kWh
        tarifa_actual: Current tariff type (plana, indexada, discriminacion_horaria)

    Returns:
        Savings analysis with optimal tariff recommendation
    """
    tarifas_mercado = get_reference_dataset("energia_tarifas_mercado")
    precios_actuales = get_reference_dataset("energia_precios_actuales")

    precio_actual = precios_actuales.get(tarifa_actual.lower(), 0.19)
    coste_actual = consumo_kwh * precio_actual + 4.00

    mejor_tarifa = None
    mejor_coste = coste_actual
    for nombre, datos in tarifas_mercado.items():
        if "precio_kwh_punta" in datos:
            coste = (
                consumo_kwh * 0.6 * datos["precio_kwh_punta"]
                + consumo_kwh * 0.4 * datos["precio_kwh_valle"]
                + datos["fijo_mensual"]
            )
        else:
            coste = consumo_kwh * datos["precio_kwh"] + datos["fijo_mensual"]

        if coste < mejor_coste:
            mejor_coste = coste
            mejor_tarifa = nombre

    ahorro_mensual = coste_actual - mejor_coste
    ahorro_porcentaje = (ahorro_mensual / coste_actual) * 100 if coste_actual > 0 else 0

    return {
        "consumo_kwh": consumo_kwh,
        "tarifa_actual": tarifa_actual,
        "coste_actual_mensual": round(coste_actual, 2),
        "mejor_tarifa": mejor_tarifa or "Current tariff is already optimal",
        "coste_nuevo_mensual": round(mejor_coste, 2),
        "ahorro_mensual": round(ahorro_mensual, 2),
        "ahorro_porcentaje": round(ahorro_porcentaje, 1),
        "ahorro_anual": round(ahorro_mensual * 12, 2),
        "recomendacion": f"Switch to {mejor_tarifa}" if mejor_tarifa else "Keep current tariff",
    }


@tool
def preparar_contrato_energia(
    dni_cliente: str,
    nueva_tarifa: str,
    consumo_kwh: float,
    nombre_cliente: Optional[str] = None,
    telefono_cliente: Optional[str] = None,
    email_cliente: Optional[str] = None,
) -> dict:
    """
    Prepares a draft contract for energy tariff change.
    REQUIRES real client data: DNI, name and phone are MANDATORY.

    Args:
        dni_cliente: Client's ID number (format: 8 digits + letter)
        nueva_tarifa: Target tariff name
        consumo_kwh: Estimated monthly consumption in kWh
        nombre_cliente: Full name of the account holder (MANDATORY)
        telefono_cliente: Client contact phone (MANDATORY)
        email_cliente: Email for confirmation (optional)

    Returns:
        Contract draft or error if mandatory data is missing
    """
    errores = []
    if not dni_cliente or len(dni_cliente) < 7:
        errores.append("Client ID/DNI (format: 12345678A)")
    if not nombre_cliente or len(nombre_cliente) < 3:
        errores.append("Full name of the account holder")
    if not telefono_cliente or len(telefono_cliente) < 9:
        errores.append("Client contact phone number")

    if errores:
        return {
            "estado": "datos_incompletos",
            "error": "Cannot prepare contract without client data.",
            "datos_faltantes": errores,
            "mensaje": f"Please request these from the client: {', '.join(errores)}",
        }

    dni_limpio = dni_cliente.strip().upper()
    if not (len(dni_limpio) >= 8 and any(c.isdigit() for c in dni_limpio)):
        return {
            "estado": "datos_invalidos",
            "error": "Invalid ID format.",
            "mensaje": "ID must have 8 digits and a letter (e.g. 12345678A).",
        }

    return {
        "estado": "borrador_preparado",
        "contrato": {
            "titular": nombre_cliente,
            "dni": f"***{dni_limpio[-4:]}",
            "telefono": f"***{telefono_cliente[-4:]}",
            "email": email_cliente or "Not provided",
            "tarifa_destino": nueva_tarifa,
            "consumo_estimado_kwh": consumo_kwh,
            "fecha_efectiva": "Next billing cycle",
            "comision_punto_venta": 25.00,
        },
        "siguiente_paso": "Client must sign on the Smart POS screen to confirm the change.",
        "nota": "Change will take effect in the next billing cycle (max 21 days)",
    }


@tool
def consultar_tarifas_disponibles() -> dict:
    """
    Queries the currently available energy tariffs in the system.

    Returns:
        List of tariffs with their main characteristics
    """
    return get_reference_dataset("energia_tarifas_catalogo")


from agents.prompts import get_energia_prompt

# ============================================
# AGENT DEFINITION
# ============================================

ENERGIA_TOOLS = [
    calcular_ahorro_energetico,
    preparar_contrato_energia,
    consultar_tarifas_disponibles,
]


def _is_contract_intent(user_text: str) -> bool:
    text = (user_text or "").lower()
    hints = ("contrato", "contract", "cambio de tarifa", "cambiar tarifa", "alta luz", "tarifa", "switch tariff")
    return any(h in text for h in hints)


def _extract_contract_fields(user_text: str) -> dict:
    text = user_text or ""
    lower = text.lower()

    dni_match = re.search(r"\b([0-9]{7,8}[a-zA-Z])\b", text)
    phone_match = re.search(r"\b(6\d{8}|7\d{8}|9\d{8}|\+34\s?\d{9})\b", lower)
    consumo_match = re.search(r"(\d+[\.,]?\d*)\s*kwh", lower)

    tarifa = ""
    for t in ["plana", "indexada", "discriminacion_horaria", "discriminación horaria"]:
        if t in lower:
            tarifa = "discriminacion_horaria" if "discrimin" in t else t
            break

    name_match = re.search(
        r"(?:me llamo|nombre(?: es)?|soy|my name is|i am)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,40})",
        text,
        flags=re.IGNORECASE,
    )

    consumo_value = 0.0
    if consumo_match:
        consumo_value = float(consumo_match.group(1).replace(",", "."))

    return {
        "dni_cliente": dni_match.group(1).upper() if dni_match else "",
        "telefono_cliente": phone_match.group(1).replace(" ", "") if phone_match else "",
        "nombre_cliente": name_match.group(1).strip() if name_match else "",
        "nueva_tarifa": tarifa,
        "consumo_kwh": consumo_value,
    }


def get_energia_llm():
    """Get LLM configured for energy agent via Qwen Cloud."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.agent_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=0.3,
        max_tokens=settings.agent_max_tokens,
    )


async def energia_node(state: AgentState) -> AgentState:
    """
    Energy agent node - handles all energy-related queries.
    Responds in the detected language of the user.
    """
    llm = get_energia_llm()
    settings = get_settings()
    llm_with_tools = llm.bind_tools(ENERGIA_TOOLS)

    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    language = state.get("language", settings.default_language)

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "energia", "status": "processing"},
    })

    language_instruction = (
        f"IMPORTANT: The user is communicating in '{language}'. "
        f"You MUST respond in the same language ('{language}'). "
        "Adapt your response naturally to that language."
    )

    system_rules = (
        "IMPORTANT: Do not use <think> tags. Respond directly. "
        "When there is kWh consumption data, execute calcular_ahorro_energetico. "
        "For contracts, request and validate name, DNI and phone before calling preparar_contrato_energia.\n\n"
        f"{language_instruction}"
    )

    messages = [SystemMessage(content=get_energia_prompt() + "\n\n" + system_rules)]
    messages.extend(
        compact_messages(
            state["messages"],
            max_messages=settings.agent_context_max_messages,
            max_chars_per_message=settings.agent_context_max_chars,
        )
    )

    response = await llm_with_tools.ainvoke(
        messages,
        config={
            "tags": ["myagent", "agent", "energia"],
            "metadata": {
                "trace_id": state.get("trace_id", ""),
                "session_id": state.get("session_id", ""),
                "node": "energia",
                "intent": state.get("intent", ""),
                "language": language,
            },
        },
    )

    if response.tool_calls:
        tool_results = []
        tool_map = {t.name: t for t in ENERGIA_TOOLS}
        mcp_client = get_mcp_client()
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            workflow_events.append({
                "type": "tool_call",
                "data": {"tool": tool_name, "args": tool_args},
            })

            mcp_result = await mcp_client.call_tool(tool_name, tool_args)
            if not mcp_result.get("is_error", False):
                result = mcp_result.get("content", {})
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)
                workflow_events.append({
                    "type": "tool_result",
                    "data": {"tool": tool_name, "result": result, "transport": "mcp", "server": mcp_result.get("server", "")},
                })
            elif tool_name in tool_map:
                result = tool_map[tool_name].invoke(tool_args)
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)
                workflow_events.append({
                    "type": "tool_result",
                    "data": {"tool": tool_name, "result": result, "transport": "fallback_direct"},
                })

        messages.append(response)
        for tr in tool_results:
            messages.append(
                ToolMessage(
                    content=compact_tool_result_for_llm(tr["result"], max_chars=settings.agent_tool_result_max_chars),
                    tool_call_id=tr.get("tool_call_id") or response.tool_calls[0]["id"],
                )
            )

        final_response = await llm.ainvoke(
            messages,
            config={
                "tags": ["myagent", "agent", "energia", "tool-response"],
                "metadata": {"trace_id": state.get("trace_id", ""), "node": "energia", "language": language},
            },
        )
        response_text = final_response.content
    else:
        user_text = state["messages"][-1].content if state.get("messages") else ""
        if _is_contract_intent(user_text):
            extracted = _extract_contract_fields(user_text)
            missing = []
            if not extracted["nombre_cliente"]:
                missing.append("full name")
            if not extracted["dni_cliente"]:
                missing.append("ID/DNI")
            if not extracted["telefono_cliente"]:
                missing.append("phone number")
            if not extracted["nueva_tarifa"]:
                missing.append("target tariff")
            if extracted["consumo_kwh"] <= 0:
                missing.append("estimated consumption in kWh")

            if missing:
                response_text = f"To prepare the contract I need: {', '.join(missing)}."
            else:
                tool_name = "preparar_contrato_energia"
                mcp_client = get_mcp_client()
                mcp_result = await mcp_client.call_tool(tool_name, extracted)
                result = mcp_result.get("content", {}) if not mcp_result.get("is_error", False) else {}

                workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": extracted}})
                workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "mcp"}})
                tools_called.append(tool_name)

                if result.get("estado") == "borrador_preparado":
                    contrato = result.get("contrato", {})
                    response_text = (
                        f"Energy contract prepared. "
                        f"Holder: {contrato.get('titular', '')}. "
                        f"Tariff: {contrato.get('tarifa_destino', '')}. "
                        f"Commission: {contrato.get('comision_punto_venta', 0)} EUR. "
                        "Request signature on Smart POS to confirm."
                    )
                elif result.get("mensaje"):
                    response_text = str(result.get("mensaje"))
                else:
                    response_text = "Could not prepare the contract. Please try again with client data."
        else:
            response_text = response.content

    workflow_events.append({
        "type": "response",
        "data": {"agent": "energia", "status": "completed"},
    })

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }
