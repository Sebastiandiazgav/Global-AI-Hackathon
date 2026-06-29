from api import transaction_persistence


def test_save_tool_transaction_event_persists_pin_activation(monkeypatch):
    captured = {}

    def _save_transaction(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(transaction_persistence, "save_transaction", _save_transaction)

    created = transaction_persistence.save_tool_transaction_event(
        {
            "tool": "activar_pin_digital",
            "result": {
                "estado": "pin_activado",
                "plataforma": "Playstation",
                "producto": "PS Plus 1 mes",
                "comision_generada": "2€",
                "ticket": "PIN-PLA-12345",
            },
            "transport": "mcp",
            "server": "MyAgent-catalogo",
        },
        "session-test-1",
    )

    assert created is True
    assert captured["type"] == "pin_digital"
    assert captured["tool_name"] == "activar_pin_digital"
    assert captured["session_id"] == "session-test-1"


def test_save_tool_transaction_event_generic_success_fallback(monkeypatch):
    captured = {}

    def _save_transaction(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(transaction_persistence, "save_transaction", _save_transaction)

    created = transaction_persistence.save_tool_transaction_event(
        {
            "tool": "emitir_producto_digital",
            "result": {
                "estado": "compra_exitosa",
                "plataforma": "Amazon",
                "producto": "Gift Card 50€",
                "comision_generada": "1.5€",
                "ticket": "ORD-123",
            },
            "transport": "mcp",
            "server": "MyAgent-catalogo",
        },
        "session-test-2",
    )

    assert created is True
    assert captured["type"] == "venta_digital"
    assert "Amazon" in captured["description"]
    assert captured["session_id"] == "session-test-2"
