"""Helpers to persist tool_result events as analytics transactions."""

from __future__ import annotations

from typing import Any, Dict

from database.db import save_transaction


def _parse_euro_amount(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        cleaned = str(value).replace("EUR", "").replace("€", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return default


def save_tool_transaction_event(event_data: Dict[str, Any], session_id: str) -> bool:
    """Persist a tool_result payload into transaction storage.

    Returns True when a transaction record was created.
    """
    tool = event_data.get("tool", "")
    result = event_data.get("result", {})

    if not isinstance(result, dict):
        return False

    commission = 0.0
    tx_type = ""
    description = ""

    if tool == "procesar_recarga" and result.get("estado") == "recarga_exitosa":
        commission = _parse_euro_amount(result.get("comision_generada", "0"), default=0.0)
        tx_type = "recarga"
        description = f"Recarga {result.get('detalles', {}).get('pais', '')}"

    elif tool == "registrar_paquetes" and result.get("estado") == "registrados":
        tx_type = "paqueteria_recepcion"
        description = f"{result.get('transportista', '')} x {result.get('paquetes_registrados', '')}"

    elif tool == "confirmar_entrega_paquete" and result.get("estado") == "entregado":
        commission = _parse_euro_amount(result.get("comision_generada", "0.30"), default=0.30)
        tx_type = "paqueteria_entrega"
        description = f"Entrega {result.get('codigo_tracking', '')}"

    elif tool == "activar_pin_digital" and result.get("estado") == "pin_activado":
        commission = _parse_euro_amount(result.get("comision_generada", "0"), default=0.0)
        tx_type = "pin_digital"
        description = f"{result.get('plataforma', '')} {result.get('producto', '')}"

    elif tool == "preparar_contrato_energia" and result.get("estado") == "borrador_preparado":
        commission = _parse_euro_amount(result.get("contrato", {}).get("comision_punto_venta", 25), default=25.0)
        tx_type = "energia_contrato"
        description = f"Contrato {result.get('contrato', {}).get('tarifa_destino', '')}"

    elif tool == "calcular_ahorro_energetico":
        tx_type = "energia_analisis"
        description = f"Analisis ahorro {result.get('ahorro_mensual', 0)} EUR/mes"

    if not tx_type:
        estado = str(result.get("estado", "")).strip().lower()
        is_success = any(token in estado for token in (
            "activado", "exitosa", "exitoso", "completada", "completado", "entregado", "registrados"
        ))

        if is_success:
            commission = _parse_euro_amount(
                result.get("comision_generada", result.get("comision", 0)),
                default=0.0,
            )
            tx_type = "venta_digital"

            platform = str(result.get("plataforma", "")).strip()
            product = str(result.get("producto", result.get("nombre", ""))).strip()
            ticket = str(result.get("ticket", result.get("codigo_tracking", ""))).strip()

            parts = [part for part in [platform, product, ticket] if part]
            description = " ".join(parts).strip() or f"{tool} {estado}".strip()

    if not tx_type:
        return False

    save_transaction(
        type=tx_type,
        tool_name=tool,
        description=description,
        commission=commission,
        agent=event_data.get("agent", ""),
        session_id=session_id,
        transport=event_data.get("transport", ""),
        metadata={
            "result": result,
            "transport": event_data.get("transport", ""),
            "server": event_data.get("server", ""),
        },
    )
    return True
