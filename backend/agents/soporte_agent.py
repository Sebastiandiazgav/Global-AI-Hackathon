"""
MyAgent - Support Agent
Specialized agent for support, recharges, catalog queries, and RAG-based knowledge retrieval.
Powered by Qwen Cloud. Supports multilingual responses.
"""

import re
import random
import string

from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Optional

from config import get_settings
from agents.state import AgentState
from agents.token_utils import compact_messages, compact_tool_result_for_llm
from mcp_servers.client import get_mcp_client
from guardrails.input_validator import get_transaction_validator
from database.reference_data import get_reference_dataset
from agents.tool_policy import (
    validate_support_tool_call,
    normalize_support_tool_args,
    build_support_conversation_context,
)
from agents.product_resolver import resolve_support_product

# ============================================
# TOOLS - Support & Catalog Vertical
# ============================================


@tool
def procesar_recarga(
    monto: float,
    pais: str,
    numero_telefono: str,
    operador: Optional[str] = None,
) -> dict:
    """
    Processes a national or international phone recharge.

    Args:
        monto: Amount in euros to recharge
        pais: Destination country (españa, ecuador, peru, colombia, rep_dominicana, usa, uk, france, germany)
        numero_telefono: Destination phone number
        operador: Phone operator (optional, auto-detected)
    """
    validator = get_transaction_validator()
    is_amount_valid, amount_error = validator.validate_recharge_amount(monto)
    if not is_amount_valid:
        return {"estado": "datos_invalidos", "error": amount_error, "mensaje": "Verify the amount and try again."}

    is_phone_valid, phone_error = validator.validate_phone_number(numero_telefono)
    if not is_phone_valid:
        return {"estado": "datos_invalidos", "error": phone_error, "mensaje": "Number must have valid international or national format."}

    operadores = get_reference_dataset("soporte_operadores_por_pais")
    pais_lower = pais.lower().replace("república ", "rep_")
    operador_detectado = operador or (operadores.get(pais_lower, ["Operator"])[0])

    es_internacional = pais_lower not in ("españa", "spain")
    comision = monto * 0.08 if es_internacional else monto * 0.05

    return {
        "estado": "recarga_exitosa",
        "detalles": {
            "numero": numero_telefono,
            "pais": pais,
            "operador": operador_detectado,
            "monto": f"{monto}€",
            "tipo": "international" if es_internacional else "national",
        },
        "comision_generada": f"{round(comision, 2)}€",
        "saldo_aplicado": "Immediate (max 5 minutes)",
        "ticket": f"REC-{pais[:3].upper()}-{random.randint(10000, 99999)}",
        "nota": "Recharge processed successfully. Client will receive SMS confirmation.",
    }


@tool
def activar_pin_digital(
    plataforma: str,
    producto: str,
    valor: Optional[float] = None,
) -> dict:
    """
    Activates a digital PIN for entertainment or service platforms.

    Args:
        plataforma: Platform name as listed in the product catalog
        producto: Product type or name from the platform's available products
        valor: Value in euros (if applicable)
    """
    catalogo = get_reference_dataset("soporte_catalogo_pines")
    info = catalogo.get(plataforma.lower(), {"productos": [producto], "comision": 1.00})

    pin_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    pin_formatted = "-".join([pin_code[i : i + 4] for i in range(0, 16, 4)])

    return {
        "estado": "pin_activado",
        "plataforma": plataforma.capitalize(),
        "producto": producto,
        "pin": pin_formatted,
        "valor": f"{valor}€" if valor else "As per product",
        "comision_generada": f"{info['comision']}€",
        "instrucciones_cliente": f"Redeem at {plataforma}.com/redeem or in the app",
        "validez": "12 months from activation",
        "ticket": f"PIN-{plataforma[:3].upper()}-{random.randint(10000, 99999)}",
    }


@tool
def buscar_en_manuales(pregunta: str) -> dict:
    """
    Searches the operational manuals knowledge base using RAG.

    Args:
        pregunta: Question about procedures, products, or incidents
    """
    from rag.retriever import get_vectorstore

    try:
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search_with_score(query=pregunta, k=3)

        if not results:
            return {
                "encontrado": False,
                "respuesta": "No specific information found. Contact support: support@enterprise.com",
                "fuente": "General support system",
                "relevancia": 0.3,
            }

        best_doc, best_score = results[0]
        snippets = [doc.page_content[:800] for doc, score in results]
        all_content = "\n\n---\n\n".join(snippets)[:1800]

        return {
            "encontrado": True,
            "respuesta": all_content,
            "fuente": best_doc.metadata.get("source", "Enterprise Manuals"),
            "relevancia": round(float(best_score), 4) if best_score <= 1 else round(1.0 / (1.0 + best_score), 4),
            "num_resultados": len(results),
        }
    except Exception as e:
        return {
            "encontrado": False,
            "respuesta": "Knowledge base temporarily unavailable. Contact support: support@enterprise.com",
            "fuente": "General support (fallback)",
            "relevancia": 0.0,
            "error": str(e)[:100],
        }


@tool
def consultar_catalogo_productos(categoria: Optional[str] = None) -> dict:
    """
    Queries the digital products catalog.

    Args:
        categoria: Filter by category (recargas, pines, entretenimiento, gaming, streaming, servicios)
    """
    catalogo = get_reference_dataset("soporte_catalogo_productos")

    if categoria and categoria.lower() in catalogo:
        return {"categoria": categoria, **catalogo[categoria.lower()]}

    return {
        "categorias_disponibles": list(catalogo.keys()),
        "total_productos": sum(len(v.get("productos", [])) for v in catalogo.values()),
        "catalogo": catalogo,
        "nota": "500+ products available. Use category to filter.",
    }


from agents.prompts import get_soporte_prompt

# ============================================
# AGENT DEFINITION
# ============================================

SOPORTE_TOOLS = [
    procesar_recarga,
    activar_pin_digital,
    buscar_en_manuales,
    consultar_catalogo_productos,
]


def get_soporte_llm():
    """Get LLM configured for support agent via Qwen Cloud."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.agent_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=0.3,
        max_tokens=settings.agent_max_tokens,
    )


def _extract_last_user_text(messages) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and isinstance(msg.content, str):
            return msg.content
    return ""


def _normalize_country_from_text(user_text: str) -> str:
    text = user_text.lower()
    aliases = {
        "españa": ["españa", "espana", "spain"],
        "colombia": ["colombia", "col"],
        "ecuador": ["ecuador"],
        "peru": ["peru", "perú"],
        "rep_dominicana": ["rep dominicana", "república dominicana", "republica dominicana", "dominicana", "dominican"],
        "usa": ["usa", "united states", "estados unidos", "eeuu"],
        "uk": ["uk", "united kingdom", "reino unido", "england", "inglaterra"],
        "france": ["france", "francia"],
        "germany": ["germany", "alemania"],
        "italy": ["italy", "italia"],
        "portugal": ["portugal"],
        "brazil": ["brazil", "brasil"],
        "mexico": ["mexico", "méxico"],
    }
    for canonical, variants in aliases.items():
        if any(v in text for v in variants):
            return canonical
    return ""


def _country_from_phone(number: str) -> str:
    digits = re.sub(r"\s+", "", number)
    prefixes = {
        "+34": "españa", "+57": "colombia", "+593": "ecuador", "+51": "peru",
        "+1": "usa", "+44": "uk", "+33": "france", "+49": "germany",
        "+39": "italy", "+351": "portugal", "+55": "brazil", "+52": "mexico",
    }
    for prefix, country in prefixes.items():
        if digits.startswith(prefix):
            return country
    return ""


def _parse_recharge_request(user_text: str) -> dict:
    text = user_text or ""
    if not any(word in text.lower() for word in ["recarga", "recharge", "top up", "topup"]):
        return {}

    amount_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:€|euros?|eur)", text, flags=re.IGNORECASE)
    phone_match = re.search(r"(\+\d{2,4}[\s\d]{6,}|\b\d{9,15}\b)", text)

    if not amount_match or not phone_match:
        return {}

    amount = float(amount_match.group(1).replace(",", "."))
    phone = re.sub(r"\s+", "", phone_match.group(1))
    country = _normalize_country_from_text(text) or _country_from_phone(phone)

    return {"monto": amount, "numero_telefono": phone, "pais": country}


def _format_recharge_response(result: dict) -> str:
    detalles = result.get("detalles", {}) if isinstance(result, dict) else {}
    return (
        "📱 Recharge Processed\n\n"
        f"Number: {detalles.get('numero', '')}\n"
        f"Country: {detalles.get('pais', '')} | Operator: {detalles.get('operador', '')}\n"
        f"Amount: {detalles.get('monto', '')} | 💰 Commission: {result.get('comision_generada', '')}\n"
        "⏱️ Application: Immediate (max 5 min)\n"
        f"Ticket: {result.get('ticket', '')}\n\n"
        "Client will receive SMS confirmation."
    )


def _format_pin_response(result: dict) -> str:
    return (
        "🎬 PIN Activated\n\n"
        f"Platform: {result.get('plataforma', '')} | Product: {result.get('producto', '')}\n"
        f"🔑 PIN: {result.get('pin', 'XXXX-XXXX-XXXX-XXXX')}\n"
        f"💰 Commission: {result.get('comision_generada', '')}\n"
        f"📋 Redeem at: {result.get('instrucciones_cliente', '')}\n"
        f"Validity: {result.get('validez', '')}\n"
        "Need anything else?"
    )


def _is_pin_intent(user_text: str) -> bool:
    """Detect if the user is asking about a digital product activation.
    Uses the catalog dynamically instead of hardcoded names."""
    text = (user_text or "").lower()
    
    # Check for activation verbs
    activation_verbs = ("pin", "activa", "activate", "dame", "give me", "quiero", "i want", "gift card", "tarjeta regalo")
    has_activation_verb = any(verb in text for verb in activation_verbs)
    
    # Check if any platform from the catalog is mentioned
    try:
        catalogo_pines = get_reference_dataset("soporte_catalogo_pines")
        platform_names = list(catalogo_pines.keys())
        has_platform = any(platform in text for platform in platform_names)
    except Exception:
        has_platform = False
    
    return has_activation_verb or has_platform


def _has_activation_verb(user_text: str) -> bool:
    """Check if user explicitly uses an activation/purchase verb."""
    text = (user_text or "").lower()
    verbs = ("activa", "activame", "activate", "dame", "give me", "quiero", "i want", "je veux", "ich will", "voglio")
    return any(verb in text for verb in verbs)


def _detect_platform_from_text(user_text: str) -> str:
    """Detect which platform is mentioned in the text using the catalog."""
    text = (user_text or "").lower()
    try:
        catalogo = get_reference_dataset("soporte_catalogo_pines")
        for platform in catalogo.keys():
            if platform.lower() in text:
                return platform
    except Exception:
        pass
    return ""


async def soporte_node(state: AgentState) -> AgentState:
    """
    Support agent node - handles recharges, PINs, catalog queries, and RAG-based support.
    Responds in the detected language of the user.
    """
    llm = get_soporte_llm()
    settings = get_settings()
    llm_with_tools = llm.bind_tools(SOPORTE_TOOLS)

    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    session_context = dict(state.get("session_context") or {})
    support_offer = dict(session_context.get("support_offer") or {})
    language = state.get("language", settings.default_language)

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "soporte", "status": "processing"},
    })

    language_instruction = (
        f"IMPORTANT: The user is communicating in '{language}'. "
        f"You MUST respond in the same language ('{language}'). "
        "Adapt your response naturally to that language."
    )

    system_rules = (
        "IMPORTANT: Do not use <think> tags. Respond directly. "
        "For recharges use procesar_recarga; for digital products/PINs use activar_pin_digital; "
        "for procedures use buscar_en_manuales; do not simulate results.\n\n"
        "RECHARGE RULE: When the user provides a phone number with international prefix, "
        "AUTOMATICALLY detect the country from the prefix:\n"
        "+34=España, +57=Colombia, +593=Ecuador, +51=Peru, +1=USA, +44=UK, "
        "+33=France, +49=Germany, +39=Italy, +351=Portugal, +55=Brazil, +52=Mexico\n"
        "If the user provides number + amount → call procesar_recarga IMMEDIATELY (do NOT ask for country).\n"
        "If only number without amount → ask ONLY for the amount.\n"
        "If only amount without number → ask ONLY for the number.\n\n"
        "CRITICAL ACTIVATION RULE:\n"
        "When the user says 'activa', 'activame', 'dame', 'quiero', 'activate', 'give me', 'I want' "
        "followed by ANY platform + product reference, you MUST call activar_pin_digital RIGHT NOW.\n"
        "- For 'plataforma': use the platform name (netflix, spotify, xbox, steam, disney, etc.)\n"
        "- For 'producto': map the user's words to the closest match:\n"
        "  estandar/standard/basico → 'Standard Monthly'\n"
        "  premium → 'Premium Monthly'\n"
        "  mensual/monthly/mes → 'Standard Monthly' (if no tier specified)\n"
        "  game pass/ultimate → 'Game Pass Ultimate'\n"
        "  wallet + amount → 'Steam Wallet [amount]€'\n"
        "  plus/mensual → 'Monthly' or the default subscription\n"
        "DO NOT ask 'which one do you want' if the user already specified. Just call the tool.\n"
        "DO NOT show options if the user used an activation verb. Execute immediately.\n\n"
        "ONLY show options when: the user asks 'what do you have?', 'show me', 'list', 'que tienes'\n\n"
        f"{language_instruction}"
    )

    messages = [SystemMessage(content=get_soporte_prompt() + "\n\n" + system_rules)]
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
            "tags": ["myagent", "agent", "soporte"],
            "metadata": {
                "trace_id": state.get("trace_id", ""),
                "session_id": state.get("session_id", ""),
                "node": "soporte",
                "language": language,
            },
        },
    )

    user_text = _extract_last_user_text(state["messages"])
    conversation_context = build_support_conversation_context(state["messages"][:-1])

    if response.tool_calls:
        tool_results = []
        tool_map = {t.name: t for t in SOPORTE_TOOLS}
        mcp_client = get_mcp_client()
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = normalize_support_tool_args(tool_name, tool_call["args"], user_text)

            is_allowed, reject_message = validate_support_tool_call(
                tool_name, tool_args, user_text, conversation_context=conversation_context,
            )
            if not is_allowed:
                response_text = reject_message
                workflow_events.append({"type": "response", "data": {"agent": "soporte", "status": "completed"}})
                return {
                    **state,
                    "final_response": response_text,
                    "tools_called": tools_called,
                    "workflow_events": workflow_events,
                    "messages": state["messages"] + [AIMessage(content=response_text)],
                    "session_context": {**session_context, "support_offer": support_offer},
                }

            workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})

            mcp_result = await mcp_client.call_tool(tool_name, tool_args)
            if not mcp_result.get("is_error", False):
                result = mcp_result.get("content", {})
                tool_results.append({"tool": tool_name, "result": result, "tool_call_id": tool_call.get("id", "")})
                tools_called.append(tool_name)

                if tool_name == "activar_pin_digital" and result.get("estado") == "pin_activado":
                    support_offer = {}

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
                "tags": ["myagent", "agent", "soporte", "tool-response"],
                "metadata": {"trace_id": state.get("trace_id", ""), "node": "soporte", "language": language},
            },
        )
        response_text = final_response.content
    else:
        response_text = response.content

        # Deterministic fallback for PIN intents when LLM doesn't call the tool
        if _is_pin_intent(user_text) and _has_activation_verb(user_text):
            resolved = resolve_support_product(user_text=user_text, product_hint=conversation_context)
            if resolved.get("resolved"):
                # Product fully resolved — activate it
                tool_name = "activar_pin_digital"
                tool_args = normalize_support_tool_args(
                    tool_name,
                    {"plataforma": resolved.get("platform", ""), "producto": resolved.get("product", "")},
                    user_text,
                )
                is_allowed, reject_message = validate_support_tool_call(tool_name, tool_args, user_text, conversation_context=conversation_context)
                if not is_allowed:
                    response_text = reject_message
                else:
                    workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})
                    mcp_client = get_mcp_client()
                    mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                    if not mcp_result.get("is_error", False):
                        result = mcp_result.get("content", {})
                        tools_called.append(tool_name)
                        support_offer = {}
                        workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "mcp"}})
                        response_text = _format_pin_response(result)
            else:
                # Platform detected but product not fully resolved — if user has activation verb,
                # try to activate with the best guess (first matching product)
                platform_detected = resolved.get("platform", "") or _detect_platform_from_text(user_text)
                if platform_detected and _has_activation_verb(user_text):
                    # Force activation with the first product of that platform
                    try:
                        catalogo = get_reference_dataset("soporte_catalogo_pines")
                        platform_products = catalogo.get(platform_detected.lower(), {}).get("productos", [])
                        if platform_products:
                            # Pick the best match from user text or default to first
                            best_product = platform_products[0]
                            user_lower = user_text.lower()
                            for p in platform_products:
                                p_lower = p.lower()
                                if "premium" in user_lower and "premium" in p_lower:
                                    best_product = p; break
                                elif ("estandar" in user_lower or "standard" in user_lower) and ("standard" in p_lower or "monthly" in p_lower):
                                    best_product = p; break
                                elif "mensual" in user_lower and "monthly" in p_lower:
                                    best_product = p; break

                            tool_name = "activar_pin_digital"
                            tool_args = {"plataforma": platform_detected, "producto": best_product}
                            workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})
                            mcp_client = get_mcp_client()
                            mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                            if not mcp_result.get("is_error", False):
                                result = mcp_result.get("content", {})
                                tools_called.append(tool_name)
                                support_offer = {}
                                workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "mcp"}})
                                response_text = _format_pin_response(result)
                            else:
                                response_text = f"Could not activate {platform_detected} product. Please try again."
                    except Exception:
                        pass
                else:
                    options = resolved.get("options", [])
                    if options:
                        support_offer = {"platform": resolved.get("platform", ""), "options": options}
                        options_text = "\n".join(f"- {opt}" for opt in options[:4])
                        response_text = f"Available options:\n{options_text}\nWhich one would you like?"

        # Deterministic fallback for recharge intents
        parsed = _parse_recharge_request(user_text)
        if parsed and parsed.get("pais") and not _is_pin_intent(user_text):
            tool_name = "procesar_recarga"
            tool_args = {"monto": parsed["monto"], "pais": parsed["pais"], "numero_telefono": parsed["numero_telefono"]}
            workflow_events.append({"type": "tool_call", "data": {"tool": tool_name, "args": tool_args}})
            mcp_client = get_mcp_client()
            mcp_result = await mcp_client.call_tool(tool_name, tool_args)
            if not mcp_result.get("is_error", False):
                result = mcp_result.get("content", {})
                tools_called.append(tool_name)
                workflow_events.append({"type": "tool_result", "data": {"tool": tool_name, "result": result, "transport": "mcp"}})
                response_text = _format_recharge_response(result)
        elif parsed and not parsed.get("pais") and not _is_pin_intent(user_text):
            response_text = "To process the recharge I need the destination country. Example: recharge 10€ to Colombia +57..."

    workflow_events.append({"type": "response", "data": {"agent": "soporte", "status": "completed"}})

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "session_context": {**session_context, "support_offer": support_offer},
    }
