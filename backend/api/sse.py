"""
MyAgent - Server-Sent Events (SSE) for Workflow Visualization
Streams agent execution steps in real-time to the frontend.
"""

import json
import time
from typing import AsyncGenerator, Optional
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field

from agents.graph import run_agent_graph_streaming
from guardrails.input_validator import get_input_validator
from guardrails.output_sanitizer import get_output_sanitizer
from guardrails.content_filter import classify_content
from config import get_settings
from database.db import save_agent_call, save_guardrail_event
from api.transaction_persistence import save_tool_transaction_event

router = APIRouter()


class StreamChatRequest(BaseModel):
    """Streaming chat request."""
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default")
    image: Optional[str] = Field(default=None, description="Base64 encoded image data")


@router.post("/chat")
async def stream_chat(request: StreamChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    
    Emits workflow events as the agent graph executes:
    - guardrails: Input/output validation applied
    - thinking: Agent is starting to process
    - routing: Supervisor is deciding which agent to use
    - agent_selected: A specialized agent has been chosen
    - tool_call: A tool is being invoked
    - tool_result: Tool execution completed
    - complete: Final response ready
    - error: Something went wrong
    """

    async def event_generator() -> AsyncGenerator[dict, None]:
        settings = get_settings()

        # ── INPUT GUARDRAILS ──
        if settings.guardrails_enabled:
            input_validator = get_input_validator()
            is_valid, error_msg = input_validator.validate(request.message)

            if not is_valid:
                save_guardrail_event(
                    event_type="input_validation",
                    stage="input",
                    action="blocked",
                    message_preview=request.message,
                    session_id=request.session_id,
                )
                yield {
                    "event": "guardrails",
                    "data": json.dumps({
                        "action": "blocked",
                        "reason": error_msg,
                        "stage": "input",
                    }, ensure_ascii=False),
                }
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "message": f"⚠️ {error_msg}",
                        "agent_used": "guardrails",
                        "tools_called": [],
                        "confidence": 0.0,
                    }, ensure_ascii=False),
                }
                return

            # Sanitize
            sanitized_message = input_validator.sanitize(request.message)

            content_result = await classify_content(sanitized_message)
            if content_result.get("action") == "BLOCKED":
                save_guardrail_event(
                    event_type="content_filter",
                    stage="input",
                    action="blocked",
                    message_preview=sanitized_message,
                    session_id=request.session_id,
                )
                replacement = content_result.get("replacement_text", "Message not allowed.")
                yield {
                    "event": "guardrails",
                    "data": json.dumps({
                        "action": "blocked",
                        "reason": content_result.get("category", ""),
                        "stage": "input",
                    }, ensure_ascii=False),
                }
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "message": f"🛡️ {replacement}",
                        "agent_used": "guardrails",
                        "tools_called": [],
                        "confidence": 0.0,
                    }, ensure_ascii=False),
                }
                return

            yield {
                "event": "guardrails",
                "data": json.dumps({
                    "action": "passed",
                    "stage": "input",
                    "checks": ["prompt_injection", "length", "sanitization"],
                }, ensure_ascii=False),
            }
        else:
            sanitized_message = request.message

        # ── AGENT EXECUTION (STREAMING) ──
        try:
            final_message = ""
            start_time = time.time()
            saved_tool_events = set()
            # Append image data to message if provided
            stream_message = sanitized_message
            if request.image:
                stream_message = f"{sanitized_message}\n{request.image}"
            async for event in run_agent_graph_streaming(
                message=stream_message,
                session_id=request.session_id,
            ):
                event_type = event["type"]
                event_data = event["data"]

                # Save tool_result transactions to database
                if event_type == "tool_result":
                    fingerprint = json.dumps(event_data, sort_keys=True, ensure_ascii=True, default=str)
                    if fingerprint not in saved_tool_events:
                        save_tool_transaction_event(event_data, request.session_id)
                        saved_tool_events.add(fingerprint)

                # Capture final message for output guardrails
                if event_type == "complete":
                    final_message = event_data.get("message", "")
                    elapsed_ms = int((time.time() - start_time) * 1000)

                    # Save agent call to database
                    save_agent_call(
                        session_id=request.session_id,
                        trace_id=event_data.get("trace_id", ""),
                        agent=event_data.get("agent_used", ""),
                        intent=event_data.get("intent", ""),
                        tools_used=event_data.get("tools_called", []),
                        confidence=event_data.get("confidence", 0),
                        response_time_ms=elapsed_ms,
                    )

                    # ALWAYS re-emit tool_results as separate events before complete
                    # This ensures the frontend transaction log captures all transactions
                    complete_tool_results = event_data.get("tool_results", [])
                    if complete_tool_results:
                        for tr in complete_tool_results:
                            tr_data = tr.get("data", tr) if isinstance(tr, dict) else tr
                            fingerprint = json.dumps(tr_data, sort_keys=True, ensure_ascii=True, default=str)
                            if fingerprint not in saved_tool_events:
                                save_tool_transaction_event(tr_data, request.session_id)
                                saved_tool_events.add(fingerprint)
                            yield {
                                "event": "tool_result",
                                "data": json.dumps(tr_data, ensure_ascii=True, default=str),
                            }

                    # ── OUTPUT GUARDRAILS ──
                    if settings.guardrails_enabled:
                        output_sanitizer = get_output_sanitizer()
                        is_valid, reason = output_sanitizer.validate(final_message)
                        evidence_ok, evidence_reason = output_sanitizer.validate_transaction_evidence(
                            event_data.get("tools_called", []),
                            event_data.get("tool_results", []),
                        )

                        if not is_valid or not evidence_ok:
                            save_guardrail_event(
                                event_type="output_validation",
                                stage="output",
                                action="regenerated",
                                message_preview=final_message if is_valid else f"{final_message} | {reason}",
                                session_id=request.session_id,
                            )
                            # Build response from tool results if available
                            tool_results = event_data.get("tool_results", [])
                            tools_called = event_data.get("tools_called", [])

                            if tool_results:
                                # Construct a useful response from tool data
                                parts = []
                                for tr in tool_results:
                                    tr_data = tr.get("data", tr) if isinstance(tr, dict) else {}
                                    result = tr_data.get("result", {})
                                    if isinstance(result, dict):
                                        # Handle validation errors from tools
                                        if result.get("estado") == "datos_incompletos":
                                            parts.append(f"⚠️ {result.get('error', 'Faltan datos')}")
                                            datos = result.get("datos_faltantes", [])
                                            if datos:
                                                parts.append("Necesito del cliente:")
                                                for d in datos:
                                                    parts.append(f"- {d}")
                                        elif result.get("estado") == "datos_invalidos":
                                            parts.append(f"⚠️ {result.get('mensaje', result.get('error', 'Datos inválidos'))}")
                                        elif result.get("estado") == "pin_activado":
                                            parts.append(f"🎮 **PIN activado**")
                                            parts.append(f"- Plataforma: {result.get('plataforma', '')}")
                                            parts.append(f"- Producto: {result.get('producto', '')}")
                                            parts.append(f"- 🔑 PIN: {result.get('pin', 'Generado')}")
                                            parts.append(f"- 💰 Comisión: {result.get('comision_generada', '')}")
                                            parts.append(f"- Canjear en: {result.get('instrucciones_cliente', '')}")
                                        elif result.get("estado") == "recarga_exitosa":
                                            detalles = result.get("detalles", {})
                                            parts.append(f"📱 **Recarga procesada**")
                                            parts.append(f"- Número: {detalles.get('numero', '')}")
                                            parts.append(f"- Monto: {detalles.get('monto', '')}")
                                            parts.append(f"- 💰 Comisión: {result.get('comision_generada', '')}")
                                        elif result.get("estado") == "registrados":
                                            parts.append(f"📦 **{result.get('paquetes_registrados', '')} paquetes registrados**")
                                            parts.append(f"- Transportista: {result.get('transportista', '')}")
                                            parts.append(f"- Ubicación: {result.get('ubicacion_sugerida', '')}")
                                        elif result.get("estado") == "borrador_preparado":
                                            contrato = result.get("contrato", {})
                                            parts.append(f"📋 **Contrato preparado**")
                                            parts.append(f"- Titular: {contrato.get('titular', '')}")
                                            parts.append(f"- Tarifa: {contrato.get('tarifa_destino', '')}")
                                            parts.append(f"- 🏪 Comisión: {contrato.get('comision_punto_venta', 25)}€")
                                            parts.append(f"- ➡️ {result.get('siguiente_paso', '')}")
                                        elif "tarifas" in result:
                                            parts.append("⚡ **Tarifas disponibles:**")
                                            for t in result.get("tarifas", []):
                                                parts.append(f"- {t.get('nombre', '')}: {t.get('precio_kwh', '')} | Comisión: {t.get('comision_vendedor', '')}")
                                        elif "productos" in result or "catalogo" in result:
                                            catalogo = result.get("catalogo", result)
                                            if isinstance(catalogo, dict):
                                                for cat, info in catalogo.items():
                                                    if isinstance(info, dict) and "productos" in info:
                                                        parts.append(f"\n**{cat.capitalize()}:**")
                                                        for p in info["productos"][:5]:
                                                            parts.append(f"- {p.get('nombre', '')}: {p.get('precio', p.get('rango', ''))} | Comisión: {p.get('comision', '')}")
                                        else:
                                            parts.append(f"✅ {result.get('estado', 'Completado')}")
                                final_message = "\n".join(parts) if parts else (
                                    "⚠️ No pude confirmar el resultado de la operación. "
                                    "Vamos a intentarlo de nuevo con país, número y monto."
                                )
                            elif tools_called and evidence_ok:
                                final_message = f"✅ Operación completada ({', '.join(tools_called)}). ¿Puedo ayudarte con algo más?"
                            elif tools_called and not evidence_ok:
                                final_message = (
                                    "⚠️ No pude confirmar evidencia transaccional de la operación. "
                                    "Repite la solicitud para ejecutarla de nuevo y validar el resultado."
                                )
                            else:
                                if "content filters" in final_message.lower():
                                    final_message = (
                                        "⚠️ No pude completar la solicitud por una restricción de seguridad del modelo. "
                                        "¿Puedes reformularla con más detalle?"
                                    )
                                else:
                                    final_message = (
                                        "⚠️ No pude completar la operación correctamente. "
                                        "Intenta de nuevo indicando país, número y monto (ej: recarga 10€ a Colombia +57...)."
                                    )
                        else:
                            final_message = output_sanitizer.sanitize(final_message)

                        event_data["message"] = final_message

                        # Re-emit tool_results as separate events so frontend can track transactions
                        complete_tool_results = event_data.get("tool_results", [])
                        if complete_tool_results:
                            for tr in complete_tool_results:
                                yield {
                                    "event": "tool_result",
                                    "data": json.dumps(tr.get("data", tr) if isinstance(tr, dict) else tr, ensure_ascii=True, default=str),
                                }

                        yield {
                            "event": "guardrails",
                            "data": json.dumps({
                                "action": "passed",
                                "stage": "output",
                                "checks": ["content_validation", "data_masking"],
                            }, ensure_ascii=False),
                        }

                yield {
                    "event": event_type,
                    "data": json.dumps(event_data, ensure_ascii=True, default=str),
                }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
