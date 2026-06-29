"""
MyAgent - Test Configuration
Shared fixtures and configuration for the test suite.
"""

import os
import sys
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables for testing
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")


@pytest.fixture
def sample_messages():
    """Sample messages for testing agent routing (multilingual)."""
    return {
        "energia": [
            "Analyze this bill: 350 kWh consumption on flat rate",
            "Analiza esta factura: consumo de 350 kWh en tarifa plana",
            "A client wants to know if they can save on electricity",
            "What energy tariffs are available?",
        ],
        "logistica": [
            "GLS just arrived with 5 packages",
            "Llegó el repartidor de GLS con 5 paquetes",
            "A client is here to pick up an Amazon package, PIN 123456",
            "How many pending packages do I have?",
        ],
        "soporte": [
            "How do I process an international recharge to Ecuador?",
            "I want to activate a Netflix PIN",
            "Recharge 15€ to +593 99 123 4567",
            "What gaming products do you have?",
        ],
        "analytics": [
            "How much did I earn today?",
            "What are my best selling products?",
            "Show me my commission trend this week",
        ],
        "society": [
            "How can I grow my sales?",
            "What strategy should I follow to increase commissions?",
            "Give me business advice to improve my performance",
        ],
        "visual": [
            "Analyze this image of an energy bill",
            "Read the tracking codes from this package label photo",
        ],
    }


@pytest.fixture
def energia_test_cases():
    """Test cases for energy agent evaluation."""
    return [
        {
            "input": "Client with 350 kWh bill on flat rate, can they save?",
            "expected_tool": "calcular_ahorro_energetico",
            "expected_contains": ["ahorro", "tarifa", "€"],
        },
        {
            "input": "What energy tariffs are available?",
            "expected_tool": "consultar_tarifas_disponibles",
            "expected_contains": ["EnergíaVerde", "LuzDirecta"],
        },
    ]


@pytest.fixture
def logistica_test_cases():
    """Test cases for logistics agent evaluation."""
    return [
        {
            "input": "Amazon just arrived with 3 packages",
            "expected_tool": "registrar_paquetes",
            "expected_contains": ["registr", "comisi"],
        },
        {
            "input": "How many packages are pending pickup?",
            "expected_tool": "listar_paquetes_pendientes",
            "expected_contains": ["pending", "Amazon"],
        },
    ]


@pytest.fixture
def analytics_test_cases():
    """Test cases for analytics agent."""
    return [
        {
            "input": "How much commission did I earn today?",
            "expected_tool": "get_daily_summary",
        },
        {
            "input": "What are my top products this week?",
            "expected_tool": "get_top_products",
        },
    ]
