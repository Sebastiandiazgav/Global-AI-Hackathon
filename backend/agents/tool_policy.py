import re

from database.reference_data import get_reference_dataset
from agents.product_resolver import resolve_support_product


_PURCHASE_HINTS = (
    "activa", "activar", "genera", "generar", "comprar", "compra", "vende",
    "vender", "dame", "damelo", "dámelo", "quiero comprar", "quiero activar",
    "sacame", "sácame", "emitir", "emitelo", "emítelo",
)

_CATALOG_QUERY_HINTS = (
    "tenemos", "hay", "que planes", "qué planes", "que productos", "qué productos",
    "disponibles", "disponible", "catalogo", "catálogo", "opciones", "cuales",
    "cuáles", "valores", "info", "informacion", "información",
)

_FOLLOWUP_SELECTION_PATTERNS = (
    r"\buna de\b",
    r"\buno de\b",
    r"\bla de\b",
    r"\bel de\b",
    r"\besa\b",
    r"\bese\b",
    r"\best[aá]\b",
    r"\beste\b",
    r"\bme llevo\b",
)

_DEICTIC_SELECTION_HINTS = (
    "esa", "ese", "esta", "este", "la de", "el de", "una de", "uno de", "ese de",
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _message_text(msg) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def build_support_conversation_context(messages, max_messages: int = 4) -> str:
    if not messages:
        return ""
    trimmed = messages[-max_messages:]
    parts = []
    for msg in trimmed:
        role = getattr(msg, "type", "message")
        parts.append(f"{role}: {_message_text(msg)}")
    return "\n".join(parts)


def _extract_platform_products(platform: str) -> list[str]:
    pines = get_reference_dataset("soporte_catalogo_pines")
    data = (pines or {}).get((platform or "").lower(), {})
    return [str(product) for product in data.get("productos", [])]


def _extract_offered_products(conversation_context: str) -> list[str]:
    context = conversation_context or ""
    products: list[str] = []
    for line in context.splitlines():
        text = line.strip().lstrip("- ").strip()
        if not text:
            continue

        # Handles patterns like "Steam - Tarjeta 50€" or "Playstation - PS Plus 1 mes"
        if " - " in text:
            parts = [part.strip() for part in text.split(" - ") if part.strip()]
            if len(parts) >= 2:
                products.append(parts[-1])
                continue

        # Fallback if only product text is listed in bullet points.
        if len(text) > 3 and not text.lower().startswith(("user:", "ai:", "human:")):
            products.append(text)

    # Deduplicate preserving order.
    unique: list[str] = []
    seen = set()
    for product in products:
        norm = _normalize_text(product)
        if norm and norm not in seen:
            seen.add(norm)
            unique.append(product)
    return unique


def _looks_like_catalog_query(user_text: str) -> bool:
    text = _normalize_text(user_text)
    if not text:
        return False
    if any(hint in text for hint in _CATALOG_QUERY_HINTS):
        return True
    return "?" in (user_text or "")


def _has_explicit_purchase_intent(user_text: str, conversation_context: str = "") -> bool:
    text = _normalize_text(user_text)
    if not text:
        return False

    if any(hint in text for hint in _PURCHASE_HINTS):
        return True

    selection_like = any(re.search(pattern, text) for pattern in _FOLLOWUP_SELECTION_PATTERNS)
    mentions_amount = bool(re.search(r"\b\d+(?:[\.,]\d+)?\s*(?:€|euros?)\b", text))
    context = _normalize_text(conversation_context)
    prior_offer = any(token in context for token in ("opciones", "planes disponibles", "tarjetas", "productos", "disponibles"))

    if selection_like and prior_offer:
        return True

    return selection_like and mentions_amount and prior_offer


def _has_explicit_product_reference(user_text: str, resolved_product: str, conversation_context: str = "") -> bool:
    text = _normalize_text(user_text)
    product_text = _normalize_text(resolved_product)
    if not text or not product_text:
        return False

    product_tokens = [token for token in product_text.split() if token not in {"tarjeta", "gift", "card", "wallet"}]
    if any(token in text for token in product_tokens if len(token) > 2):
        return True

    if re.search(r"\b\d+(?:[\.,]\d+)?\s*(?:€|euros?)\b", text) and re.search(r"\b\d+(?:[\.,]\d+)?\s*(?:€|euros?)\b", product_text):
        return True

    context = _normalize_text(conversation_context)
    offered_products = _extract_offered_products(conversation_context)

    # If user picks deictically ("esa", "la de 50") and context has offered options,
    # accept when we can anchor it to offered products.
    if any(hint in text for hint in _DEICTIC_SELECTION_HINTS) and offered_products:
        if len(offered_products) == 1:
            return True

        amount_match = re.search(r"\b\d+(?:[\.,]\d+)?\s*(?:€|euros?)\b", text)
        if amount_match:
            amount_norm = _normalize_text(amount_match.group(0)).replace("euros", "€").replace(" ", "")
            for offered in offered_products:
                offered_norm = _normalize_text(offered).replace("euros", "€").replace(" ", "")
                if amount_norm and amount_norm in offered_norm:
                    return True

        for offered in offered_products:
            offered_tokens = [tok for tok in _normalize_text(offered).split() if len(tok) > 2]
            if any(token in text for token in offered_tokens):
                return True

    return bool(context and product_text and product_text in context)


def _build_catalog_guidance(platform: str, resolved_product: str = "") -> str:
    options = _extract_platform_products(platform)
    if resolved_product and resolved_product not in options:
        options = [resolved_product, *options]
    options = options[:4]
    if not options:
        return ""
    return "\n".join(f"- {platform.title()} - {option}" for option in options)


def normalize_support_tool_args(tool_name: str, tool_args: dict, user_text: str) -> dict:
    normalized = dict(tool_args or {})

    if tool_name == "activar_pin_digital":
        resolved = resolve_support_product(
            user_text=user_text,
            platform_hint=str(normalized.get("plataforma", "")),
            product_hint=str(normalized.get("producto", "")),
        )
        if resolved.get("resolved"):
            normalized["plataforma"] = resolved.get("platform", normalized.get("plataforma", ""))
            normalized["producto"] = resolved.get("product", normalized.get("producto", ""))

    return normalized


def validate_support_tool_call(
    tool_name: str,
    tool_args: dict,
    user_text: str,
    conversation_context: str = "",
) -> tuple[bool, str]:
    """Apply hard business constraints before executing support tools."""
    text = (user_text or "").lower()

    if tool_name == "activar_pin_digital":
        platform = str(tool_args.get("plataforma", "")).strip()
        product = str(tool_args.get("producto", "")).strip()
        resolved_from_user = resolve_support_product(user_text=user_text)
        resolved = resolve_support_product(user_text=user_text, platform_hint=platform, product_hint=product)

        if not _has_explicit_purchase_intent(user_text, conversation_context):
            guidance = _build_catalog_guidance(resolved.get("platform", platform), resolved.get("product", product))
            message = (
                "Puedo ayudarte a consultar disponibilidad sin activar nada. "
                "Para activar un PIN necesito que me lo pidas de forma explícita indicando el producto exacto."
            )
            if guidance:
                message += f"\nOpciones disponibles:\n{guidance}"
            return False, message

        if not resolved_from_user.get("resolved"):
            if conversation_context and resolved.get("resolved"):
                resolved_from_user = resolved
            else:
                options = resolved.get("options", [])
                options_text = "\n".join(f"- {opt}" for opt in options[:3])
                if options_text:
                    return False, (
                        "Para evitar errores necesito que confirmes explícitamente plataforma y producto en tu mensaje.\n"
                        f"Opciones sugeridas:\n{options_text}"
                    )
                return False, "Para evitar errores necesito que confirmes explícitamente plataforma y producto en tu mensaje."

        if not resolved.get("resolved"):
            options = resolved.get("options", [])
            options_text = "\n".join(f"- {opt}" for opt in options[:3])
            if options_text:
                return False, (
                    "Necesito confirmar plataforma y producto exactos antes de activarlo. "
                    "Puedes responder con uno de estos formatos:\n"
                    f"{options_text}"
                )
            return False, "Necesito confirmar plataforma y producto exactos antes de activarlo."

        if not _has_explicit_product_reference(user_text, resolved.get("product", product), conversation_context):
            guidance = _build_catalog_guidance(resolved.get("platform", platform), resolved.get("product", product))
            message = "Necesito que confirmes el producto exacto antes de activarlo."
            if guidance:
                message += f"\nOpciones disponibles:\n{guidance}"
            return False, message

    if tool_name == "procesar_recarga":
        country = str(tool_args.get("pais", "")).strip().lower()
        phone = str(tool_args.get("numero_telefono", "")).strip()
        amount = tool_args.get("monto")
        if not country or not phone or amount in (None, ""):
            return False, (
                "Para procesar la recarga necesito los 3 datos: país, número y monto. "
                "Ejemplo: recarga 10 euros a Colombia +57..."
            )

    return True, ""
