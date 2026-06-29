from agents.tool_policy import validate_support_tool_call, normalize_support_tool_args
from agents.product_resolver import resolve_support_product


def test_pin_activation_rejected_without_explicit_platform_in_user_text():
    ok, message = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "netflix", "producto": "suscripción mensual"},
        "deseo comprar un pino",
    )

    assert ok is False
    assert "confirmes" in message.lower() or "confirmar" in message.lower()


def test_pin_activation_rejected_without_explicit_product_confirmation():
    ok, message = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "netflix", "producto": "Premium 1 mes"},
        "quiero un pin de netflix",
    )

    assert ok is False
    assert "producto exacto" in message.lower() or "opciones disponibles" in message.lower()


def test_pin_activation_allowed_when_platform_and_product_are_explicit():
    ok, _ = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "netflix", "producto": "Premium 1 mes"},
        "quiero activar netflix premium 1 mes",
    )

    assert ok is True


def test_pin_activation_rejected_for_catalog_question_even_if_model_resolves_product():
    ok, message = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "steam", "producto": "Tarjeta 20€"},
        "tenemos pines de steam?",
    )

    assert ok is False
    assert "consultar disponibilidad" in message.lower() or "opciones disponibles" in message.lower()


def test_pin_activation_allows_followup_selection_with_recent_catalog_context():
    ok, _ = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "steam", "producto": "Tarjeta 50€"},
        "la de 50 euros",
        conversation_context="ai: Opciones disponibles:\n- Steam - Tarjeta 20€\n- Steam - Tarjeta 50€",
    )

    assert ok is True


def test_pin_activation_allows_deictic_followup_with_recent_catalog_context():
    ok, _ = validate_support_tool_call(
        "activar_pin_digital",
        {"plataforma": "playstation", "producto": "PS Plus 1 mes"},
        "dame esa",
        conversation_context="ai: Opciones disponibles:\n- Playstation - PS Plus 1 mes\n- Playstation - Tarjeta 25€",
    )

    assert ok is True


def test_catalog_resolver_supports_typo_for_netflix():
    resolved = resolve_support_product("1 pin para netflx basico por favor")
    assert resolved["resolved"] is True
    assert "netflix" in resolved["platform"].lower()


def test_catalog_resolver_supports_xbox_product_variants():
    resolved = resolve_support_product("1 xbox game pass gold por favor")
    assert resolved["resolved"] is True
    assert "xbox" in resolved["platform"].lower()


def test_normalize_support_tool_args_canonicalizes_typo_input():
    normalized = normalize_support_tool_args(
        "activar_pin_digital",
        {"plataforma": "netflx", "producto": "basico 1 mes"},
        "quiero un pin de netflx basico",
    )
    assert normalized.get("plataforma", "").lower() == "netflix"
    assert normalized.get("producto", "")
