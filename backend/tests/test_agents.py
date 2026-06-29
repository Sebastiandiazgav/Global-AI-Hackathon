"""
MyAgent - Agent Integration Tests
Tests the multi-agent system routing and execution.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from agents.supervisor import supervisor_node, route_to_agent
from agents.energia_agent import calcular_ahorro_energetico, consultar_tarifas_disponibles
from agents.logistica_agent import registrar_paquetes, listar_paquetes_pendientes
from agents.soporte_agent import procesar_recarga, activar_pin_digital, buscar_en_manuales


class TestEnergyTools:
    """Test energy agent tools."""

    def test_calcular_ahorro_basico(self):
        """Test basic savings calculation."""
        result = calcular_ahorro_energetico.invoke({
            "consumo_kwh": 350,
            "tarifa_actual": "plana",
        })

        assert "ahorro_mensual" in result
        assert "mejor_tarifa" in result
        assert "coste_actual_mensual" in result
        assert result["consumo_kwh"] == 350
        assert result["ahorro_mensual"] >= 0

    def test_calcular_ahorro_indexada(self):
        """Test savings calculation for indexed tariff."""
        result = calcular_ahorro_energetico.invoke({
            "consumo_kwh": 200,
            "tarifa_actual": "indexada",
        })

        assert result["tarifa_actual"] == "indexada"
        assert "ahorro_porcentaje" in result

    def test_consultar_tarifas(self):
        """Test tariff listing."""
        result = consultar_tarifas_disponibles.invoke({})

        assert "tarifas" in result
        assert len(result["tarifas"]) > 0
        assert all("nombre" in t for t in result["tarifas"])
        assert all("comision_vendedor" in t for t in result["tarifas"])


class TestLogisticsTools:
    """Test logistics agent tools."""

    def test_registrar_paquetes_amazon(self):
        """Test package registration for Amazon."""
        result = registrar_paquetes.invoke({
            "transportista": "Amazon",
            "cantidad": 5,
        })

        assert result["estado"] == "registrados"
        assert result["paquetes_registrados"] == 5
        assert "comision_total" in result
        assert result["transportista"] == "Amazon"

    def test_registrar_paquetes_gls(self):
        """Test package registration for GLS."""
        result = registrar_paquetes.invoke({
            "transportista": "GLS",
            "cantidad": 3,
        })

        assert result["paquetes_registrados"] == 3
        assert "0.25" in result["comision_por_paquete"]

    def test_listar_pendientes(self):
        """Test listing pending packages."""
        result = listar_paquetes_pendientes.invoke({})

        assert "total_pendientes" in result
        assert "por_transportista" in result
        assert "alertas" in result


class TestSupportTools:
    """Test support agent tools."""

    def test_procesar_recarga_internacional(self):
        """Test international recharge processing."""
        result = procesar_recarga.invoke({
            "monto": 15.0,
            "pais": "Ecuador",
            "numero_telefono": "+593 99 123 4567",
        })

        assert result["estado"] == "recarga_exitosa"
        assert result["detalles"]["pais"] == "Ecuador"
        assert result["detalles"]["tipo"] == "internacional"
        assert "comision_generada" in result

    def test_procesar_recarga_nacional(self):
        """Test national recharge processing."""
        result = procesar_recarga.invoke({
            "monto": 10.0,
            "pais": "España",
            "numero_telefono": "+34 612 345 678",
        })

        assert result["detalles"]["tipo"] == "nacional"

    def test_activar_pin_netflix(self):
        """Test Netflix PIN activation."""
        result = activar_pin_digital.invoke({
            "plataforma": "netflix",
            "producto": "Premium 1 mes",
        })

        assert result["estado"] == "pin_activado"
        assert "pin" in result
        assert result["plataforma"] == "Netflix"
        assert "-" in result["pin"]  # PIN should be formatted

    def test_buscar_manuales_recarga(self):
        """Test knowledge base search for recharges."""
        result = buscar_en_manuales.invoke({
            "pregunta": "¿Cómo hago una recarga internacional?",
        })

        assert result["encontrado"] == True
        assert "recarga" in result["respuesta"].lower()
        assert "fuente" in result

    def test_buscar_manuales_amazon(self):
        """Test knowledge base search for Amazon Hub."""
        result = buscar_en_manuales.invoke({
            "pregunta": "Procedimiento Amazon Hub Counter",
        })

        assert result["encontrado"] == True
        assert "amazon" in result["respuesta"].lower()


class TestRouting:
    """Test supervisor routing logic."""

    def test_route_to_agent_energia(self):
        """Test routing returns correct agent name."""
        state = {"current_agent": "energia"}
        assert route_to_agent(state) == "energia"

    def test_route_to_agent_logistica(self):
        """Test routing returns correct agent name."""
        state = {"current_agent": "logistica"}
        assert route_to_agent(state) == "logistica"

    def test_route_to_agent_soporte(self):
        """Test routing returns correct agent name."""
        state = {"current_agent": "soporte"}
        assert route_to_agent(state) == "soporte"
