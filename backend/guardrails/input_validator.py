"""
MyAgent - Input Validation Guardrails
Validates and sanitizes user input before it reaches the agent system.
"""

import re
from typing import Tuple
from config import get_settings


class InputValidator:
    """
    Validates user input for security and business rules.
    
    Checks:
    - Prompt injection attempts
    - Input length limits
    - Malicious content patterns
    - Business rule violations
    """

    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+(instructions|prompts|rules)",
        r"you\s+are\s+now\s+a",
        r"forget\s+(everything|all|your)\s+(you|instructions|rules)",
        r"system\s*prompt",
        r"reveal\s+(your|the)\s+(instructions|prompt|system)",
        r"act\s+as\s+(if|a|an)",
        r"pretend\s+(you|to\s+be)",
        r"jailbreak",
        r"DAN\s+mode",
        r"bypass\s+(safety|security|filters|guardrails)",
    ]

    # Explicit requests for illegal offensive actions.
    ILLEGAL_INTENT_PATTERNS = [
        r"\b(quiero|ayudame|ayúdame|ensename|enséñame|como|cómo)\b.{0,25}\b(hackear|hackeo|hack|crackear|phishing|ddos|tumbar\s+un\s+sistema)\b",
        r"\bhackear\s+(el\s+)?sistema\b",
        r"\bhackear\s+(el\s+)?sustema\b",
        r"\b(hackear|hackeo|crackear|phishing|ddos)\b",
    ]

    # Maximum input length (characters)
    MAX_INPUT_LENGTH = 2000

    # Minimum input length
    MIN_INPUT_LENGTH = 2

    def __init__(self):
        self.settings = get_settings()
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.INJECTION_PATTERNS
        ]
        self._compiled_illegal_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.ILLEGAL_INTENT_PATTERNS
        ]

    def validate(self, message: str) -> Tuple[bool, str]:
        """
        Validate user input.
        
        Args:
            message: Raw user input
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check length
        if len(message) < self.MIN_INPUT_LENGTH:
            return False, "El mensaje es demasiado corto."

        if len(message) > self.MAX_INPUT_LENGTH:
            return False, f"El mensaje excede el límite de {self.MAX_INPUT_LENGTH} caracteres."

        # Check for prompt injection
        if self._detect_injection(message):
            return False, "Mensaje no permitido por razones de seguridad."

        # Check explicit illegal/offensive cyber intent
        if self._detect_illegal_intent(message):
            return False, "Mensaje no permitido por razones de seguridad."

        return True, ""

    def _detect_injection(self, message: str) -> bool:
        """Detect prompt injection attempts."""
        for pattern in self._compiled_patterns:
            if pattern.search(message):
                return True
        return False

    def _detect_illegal_intent(self, message: str) -> bool:
        """Detect explicit malicious cyber intent requests."""
        for pattern in self._compiled_illegal_patterns:
            if pattern.search(message):
                return True
        return False

    def sanitize(self, message: str) -> str:
        """
        Sanitize user input (remove potentially harmful content).
        
        Args:
            message: Raw user input
            
        Returns:
            Sanitized message
        """
        # Remove excessive whitespace
        message = re.sub(r'\s+', ' ', message).strip()

        # Remove potential HTML/script tags
        message = re.sub(r'<[^>]+>', '', message)

        # Truncate if too long
        if len(message) > self.MAX_INPUT_LENGTH:
            message = message[:self.MAX_INPUT_LENGTH]

        return message


class TransactionValidator:
    """
    Validates transaction-related inputs for business rules.
    """

    def __init__(self):
        self.settings = get_settings()

    def validate_recharge_amount(self, amount: float) -> Tuple[bool, str]:
        """Validate recharge amount is within acceptable range."""
        if amount <= 0:
            return False, "El monto debe ser mayor a 0€."

        if amount > self.settings.max_transaction_amount:
            return False, (
                f"El monto máximo permitido es {self.settings.max_transaction_amount}€. "
                f"Para montos superiores, contacta con soporte."
            )

        if amount < 5:
            return False, "El monto mínimo de recarga es 5€."

        return True, ""

    def validate_phone_number(self, number: str) -> Tuple[bool, str]:
        """Validate phone number format."""
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-\(\)]', '', number)

        # Must start with + or be a local number
        if not re.match(r'^(\+?\d{9,15})$', cleaned):
            return False, "Formato de número de teléfono no válido."

        return True, ""

    def validate_energy_consumption(self, kwh: float) -> Tuple[bool, str]:
        """Validate energy consumption is realistic."""
        if kwh <= 0:
            return False, "El consumo debe ser mayor a 0 kWh."

        if kwh > 5000:
            return False, (
                "Un consumo de más de 5000 kWh/mes es inusual para un hogar. "
                "¿Estás seguro del dato?"
            )

        return True, ""


# Singleton instances
_input_validator = None
_transaction_validator = None


def get_input_validator() -> InputValidator:
    """Get singleton InputValidator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def get_transaction_validator() -> TransactionValidator:
    """Get singleton TransactionValidator instance."""
    global _transaction_validator
    if _transaction_validator is None:
        _transaction_validator = TransactionValidator()
    return _transaction_validator
