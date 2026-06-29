"""
MyAgent - Output Sanitization Guardrails
Validates agent responses before sending to the user.
"""

import re
from typing import Tuple


class OutputSanitizer:
    """
    Sanitizes and validates agent output before delivery.
    
    Ensures:
    - No internal system information leaks
    - No hallucinated transaction confirmations
    - Responses stay within domain scope
    - Sensitive data is masked
    """

    # Patterns that should never appear in output
    FORBIDDEN_PATTERNS = [
        r"api[_\s]?key",
        r"secret[_\s]?key",
        r"password\s*[:=]",
        r"token\s*[:=]",
        r"QWEN_CLOUD_API",
        r"ALIBABA_ACCESS",
    ]

    # Thinking tags to remove (LLM internal reasoning)
    THINKING_PATTERNS = [
        r"<think>.*?</think>",
        r"<thinking>.*?</thinking>",
    ]

    # DNI pattern to mask
    DNI_PATTERN = r'\b\d{8}[A-Z]\b'
    TRANSACTIONAL_TOOLS = {
        "procesar_recarga",
        "activar_pin_digital",
        "registrar_paquetes",
        "confirmar_entrega_paquete",
        "preparar_contrato_energia",
    }
    SUCCESS_STATES = {
        "recarga_exitosa",
        "pin_activado",
        "registrados",
        "entregado",
        "borrador_preparado",
    }

    def __init__(self):
        self._compiled_forbidden = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.FORBIDDEN_PATTERNS
        ]

    def sanitize(self, response: str) -> str:
        """
        Sanitize agent response.
        
        Args:
            response: Raw agent response
            
        Returns:
            Sanitized response safe for display
        """
        # Remove thinking/reasoning tags (LLM internal)
        for pattern in self.THINKING_PATTERNS:
            response = re.sub(pattern, '', response, flags=re.DOTALL)

        # Clean up extra whitespace from removed blocks
        response = re.sub(r'\n{3,}', '\n\n', response).strip()

        # Mask DNI numbers (show only last 4)
        response = re.sub(
            self.DNI_PATTERN,
            lambda m: f"***{m.group()[-4:]}",
            response,
        )

        # Mask full phone numbers (show only last 4 digits)
        response = re.sub(
            r'\+?\d{2,3}\s?\d{6,}',
            lambda m: f"***{m.group()[-4:]}",
            response,
        )

        # Remove any accidentally leaked system info
        for pattern in self._compiled_forbidden:
            response = pattern.sub("[REDACTED]", response)

        return response

    def validate(self, response: str) -> Tuple[bool, str]:
        """
        Validate that the response is appropriate.
        
        Args:
            response: Agent response to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for empty response
        if not response or len(response.strip()) < 5:
            return False, "Respuesta vacía o demasiado corta"

        # Check for model content filter blocks
        if "blocked by our content filters" in response.lower():
            return False, "Respuesta bloqueada por filtros del modelo"

        # Check for forbidden content
        for pattern in self._compiled_forbidden:
            if pattern.search(response):
                return False, "Respuesta contiene información sensible"

        # Check response length (too long might indicate hallucination)
        if len(response) > 5000:
            return False, "Respuesta excesivamente larga"

        return True, ""

    def validate_transaction_evidence(self, tools_called: list, tool_results: list) -> Tuple[bool, str]:
        """Ensure transactional confirmations have concrete successful tool evidence."""
        called = set(tools_called or [])
        required = called & self.TRANSACTIONAL_TOOLS
        if not required:
            return True, ""

        successful = set()
        for tr in tool_results or []:
            item = tr.get("data", tr) if isinstance(tr, dict) else {}
            tool_name = item.get("tool", "") if isinstance(item, dict) else ""
            result = item.get("result", {}) if isinstance(item, dict) else {}
            if tool_name in self.TRANSACTIONAL_TOOLS and isinstance(result, dict):
                state = str(result.get("estado", "")).strip().lower()
                if state in self.SUCCESS_STATES:
                    successful.add(tool_name)

        missing = sorted(required - successful)
        if missing:
            return False, f"Falta evidencia transaccional para: {', '.join(missing)}"
        return True, ""


# Singleton
_output_sanitizer = None


def get_output_sanitizer() -> OutputSanitizer:
    """Get singleton OutputSanitizer instance."""
    global _output_sanitizer
    if _output_sanitizer is None:
        _output_sanitizer = OutputSanitizer()
    return _output_sanitizer
