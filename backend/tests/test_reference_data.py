"""Tests for reference data module."""
import pytest
from database.reference_data import get_reference_dataset, validate_required_reference_data


def test_get_energia_tarifas_mercado():
    data = get_reference_dataset("energia_tarifas_mercado")
    assert isinstance(data, dict)
    assert len(data) >= 5
    assert "EnergíaVerde Hogar" in data
    assert "precio_kwh" in data["EnergíaVerde Hogar"]


def test_get_energia_precios_actuales():
    data = get_reference_dataset("energia_precios_actuales")
    assert "plana" in data
    assert "indexada" in data
    assert data["plana"] > 0


def test_get_logistica_comisiones():
    data = get_reference_dataset("logistica_comision_por_transportista")
    assert "amazon" in data
    assert "gls" in data
    assert "dhl" in data
    assert data["amazon"] >= 0.25


def test_get_logistica_paquetes_pendientes():
    data = get_reference_dataset("logistica_paquetes_pendientes")
    assert "paquetes" in data
    assert len(data["paquetes"]) >= 5


def test_get_soporte_operadores():
    data = get_reference_dataset("soporte_operadores_por_pais")
    assert "españa" in data
    assert "colombia" in data
    assert "usa" in data
    assert len(data["españa"]) >= 3


def test_get_soporte_catalogo_pines():
    data = get_reference_dataset("soporte_catalogo_pines")
    assert "netflix" in data
    assert "spotify" in data
    assert "playstation" in data
    assert "xbox" in data
    assert "steam" in data
    assert len(data) >= 15  # 15+ platforms


def test_get_soporte_catalogo_productos():
    data = get_reference_dataset("soporte_catalogo_productos")
    assert "streaming" in data
    assert "gaming" in data
    assert "gift_cards" in data
    assert "education" in data
    assert "food_delivery" in data
    # Check expanded catalog
    total = sum(len(v.get("productos", [])) for v in data.values())
    assert total >= 50  # 50+ products


def test_validate_required_reference_data():
    # Should not raise
    validate_required_reference_data()


def test_get_nonexistent_dataset():
    with pytest.raises(KeyError):
        get_reference_dataset("nonexistent_dataset")
