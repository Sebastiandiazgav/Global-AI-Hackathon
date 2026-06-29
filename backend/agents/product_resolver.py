from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List

from database.reference_data import get_reference_dataset


def _normalize_text(value: str) -> str:
    text = value or ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Apply common synonyms/translations for better matching
    synonyms = {
        "estandar": "standard",
        "basico": "standard",
        "mensual": "monthly",
        "anual": "annual",
        "premium": "premium",
        "familia": "family",
        "individual": "individual",
        "tarjeta regalo": "gift card",
        "tarjeta": "gift card",
        "regalo": "gift card",
        "suscripcion": "monthly",
        "mes": "monthly",
        "ano": "annual",
        "juego": "game",
        "juegos": "game",
        "activar": "",
        "activame": "",
        "quiero": "",
        "dame": "",
        "por favor": "",
    }
    for es, en in synonyms.items():
        text = text.replace(es, en)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _token_overlap(a: str, b: str) -> float:
    tokens_a = set(_normalize_text(a).split())
    tokens_b = set(_normalize_text(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return inter / union if union else 0.0


def _similarity(a: str, b: str) -> float:
    norm_a = _normalize_text(a)
    norm_b = _normalize_text(b)
    if not norm_a or not norm_b:
        return 0.0
    ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    overlap = _token_overlap(norm_a, norm_b)
    return (ratio * 0.7) + (overlap * 0.3)


def _flatten_catalog_products() -> List[Dict[str, str]]:
    pines = get_reference_dataset("soporte_catalogo_pines")
    catalog = get_reference_dataset("soporte_catalogo_productos")

    entries: List[Dict[str, str]] = []

    for platform, data in (pines or {}).items():
        for product in data.get("productos", []):
            label = f"{platform} {product}"
            entries.append(
                {
                    "platform": str(platform),
                    "product": str(product),
                    "label": label,
                    "source": "pines",
                }
            )

    for category, category_data in (catalog or {}).items():
        for product_data in category_data.get("productos", []):
            name = str(product_data.get("nombre", "")).strip()
            if not name:
                continue

            # Try infer platform by known platform keywords.
            platform = ""
            for candidate in (pines or {}).keys():
                if _normalize_text(candidate) in _normalize_text(name):
                    platform = str(candidate)
                    break

            if not platform:
                platform = str(category)

            entries.append(
                {
                    "platform": platform,
                    "product": name,
                    "label": f"{platform} {name}",
                    "source": "catalogo",
                }
            )

    # Deduplicate by normalized label.
    dedup: Dict[str, Dict[str, str]] = {}
    for entry in entries:
        dedup[_normalize_text(entry["label"])] = entry
    return list(dedup.values())


def _derive_platform_aliases() -> Dict[str, List[str]]:
    """Build aliases from reference data instead of hardcoded brand lists."""
    pines = get_reference_dataset("soporte_catalogo_pines") or {}
    catalog = get_reference_dataset("soporte_catalogo_productos") or {}

    aliases: Dict[str, List[str]] = {}

    for platform in pines.keys():
        key = str(platform)
        base = _normalize_text(key)
        variants = {
            key,
            base,
            base.replace(" ", ""),
            base.replace("+", " plus "),
            base.replace("+", ""),
            base.replace(" ", " "),
        }
        aliases[key] = [variant for variant in variants if variant]

    # Include catalog categories as fallback platform-like anchors.
    for category in catalog.keys():
        key = str(category)
        if key not in aliases:
            base = _normalize_text(key)
            aliases[key] = [key, base, base.replace(" ", "")]

    return aliases


def _detect_platform(text: str) -> str:
    norm = _normalize_text(text)
    if not norm:
        return ""
    aliases = _derive_platform_aliases()

    for platform, candidates in aliases.items():
        if any(_normalize_text(candidate) and _normalize_text(candidate) in norm for candidate in candidates):
            return platform

    # Fuzzy fallback for typos and split words (e.g. "play stattion").
    tokens = norm.split()
    windows: List[str] = []
    for size in (1, 2, 3):
        for i in range(0, max(len(tokens) - size + 1, 0)):
            windows.append(" ".join(tokens[i:i + size]))

    best_platform = ""
    best_score = 0.0
    for platform in aliases.keys():
        platform_norm = _normalize_text(platform)
        for window in windows:
            score = SequenceMatcher(None, window, platform_norm).ratio()
            if score > best_score:
                best_score = score
                best_platform = platform

    if best_score >= 0.78:
        return best_platform
    return ""


def resolve_support_product(user_text: str, platform_hint: str = "", product_hint: str = "") -> Dict[str, Any]:
    """Resolve platform/product from noisy user text using full support catalog."""
    request_text = " ".join(part for part in [user_text, platform_hint, product_hint] if part).strip()
    request_norm = _normalize_text(request_text)
    if not request_norm:
        return {
            "resolved": False,
            "ambiguous": False,
            "platform": "",
            "product": "",
            "confidence": 0.0,
            "options": [],
            "reason": "empty_request",
        }

    candidates = _flatten_catalog_products()
    if not candidates:
        return {
            "resolved": False,
            "ambiguous": False,
            "platform": "",
            "product": "",
            "confidence": 0.0,
            "options": [],
            "reason": "empty_catalog",
        }

    platform_locked = _detect_platform(" ".join([platform_hint, user_text])) or _detect_platform(platform_hint)
    filtered_candidates = candidates
    if platform_locked:
        narrowed = [c for c in candidates if _normalize_text(c["platform"]) == _normalize_text(platform_locked)]
        if narrowed:
            filtered_candidates = narrowed

    scored: List[Dict[str, Any]] = []
    for c in filtered_candidates:
        joined = c["label"]
        product_only = c["product"]
        score_joined = _similarity(request_text, joined)
        score_product = _similarity(request_text, product_only)
        score_platform = _similarity(request_text, c["platform"])
        final_score = max(score_joined, (score_product * 0.9) + (score_platform * 0.1))

        # Boost explicit platform mention.
        if _normalize_text(c["platform"]) in request_norm:
            final_score += 0.08

        if platform_locked and _normalize_text(c["platform"]) == _normalize_text(platform_locked):
            final_score += 0.18

        norm_product = _normalize_text(c["product"])
        if "mensual" in request_norm and ("1 mes" in norm_product or "mensual" in norm_product):
            final_score += 0.08
        if "basico" in request_norm and ("estandar" in norm_product or "standard" in norm_product):
            final_score += 0.08
        if "gold" in request_norm and ("game pass" in norm_product or "xbox" in norm_product):
            final_score += 0.06

        scored.append({
            "platform": c["platform"],
            "product": c["product"],
            "score": min(final_score, 1.0),
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    best = scored[0]
    second = scored[1] if len(scored) > 1 else None
    options = [f"{item['platform'].title()} - {item['product']}" for item in scored[:5]]

    confidence = float(best["score"])
    ambiguous = bool(second and abs(best["score"] - second["score"]) < 0.06 and best["score"] < 0.90 and not platform_locked)
    threshold = 0.40 if platform_locked else 0.55
    resolved = confidence >= threshold and not ambiguous

    return {
        "resolved": resolved,
        "ambiguous": ambiguous,
        "platform": best["platform"] if resolved else "",
        "product": best["product"] if resolved else "",
        "confidence": round(confidence, 4),
        "options": options,
        "reason": "ok" if resolved else ("ambiguous" if ambiguous else "low_confidence"),
    }
