"""
MyAgent - Database Seed Script
Initializes the database with reference data, MCP clients, and tool policies.
Run: python -m database.seed
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from database.connection import init_database, is_database_available
from database.mcp_ops import register_mcp_client, register_tool_policy


def seed_mcp_clients():
    """Register default MCP clients for testing and external integrations."""
    clients = [
        {
            "client_id": "internal-system",
            "api_key": "internal-no-auth-required",
            "allowed_tools": ["*"],
            "rate_limit": 120,
        },
        {
            "client_id": "demo-partner",
            "api_key": "demo-key-2026-hackaton",
            "allowed_tools": ["consultar_tarifas_disponibles", "consultar_catalogo_productos", "listar_paquetes_pendientes"],
            "rate_limit": 30,
        },
        {
            "client_id": "energy-partner",
            "api_key": "energy-partner-key-2026",
            "allowed_tools": ["calcular_ahorro_energetico", "consultar_tarifas_disponibles"],
            "rate_limit": 60,
        },
        {
            "client_id": "logistics-partner",
            "api_key": "logistics-partner-key-2026",
            "allowed_tools": ["registrar_paquetes", "consultar_estado_paquete", "listar_paquetes_pendientes"],
            "rate_limit": 60,
        },
    ]

    for client in clients:
        register_mcp_client(
            client_id=client["client_id"],
            api_key=client["api_key"],
            allowed_tools=client["allowed_tools"],
            rate_limit=client["rate_limit"],
        )
        print(f"  ✓ Client: {client['client_id']}")


def seed_tool_policies():
    """Register tool execution policies."""
    policies = [
        {"tool_name": "calcular_ahorro_energetico", "timeout_ms": 5000, "max_retries": 2},
        {"tool_name": "preparar_contrato_energia", "timeout_ms": 8000, "max_retries": 1},
        {"tool_name": "consultar_tarifas_disponibles", "timeout_ms": 3000, "max_retries": 3},
        {"tool_name": "registrar_paquetes", "timeout_ms": 5000, "max_retries": 2},
        {"tool_name": "confirmar_entrega_paquete", "timeout_ms": 5000, "max_retries": 1},
        {"tool_name": "consultar_estado_paquete", "timeout_ms": 3000, "max_retries": 3},
        {"tool_name": "gestionar_devolucion", "timeout_ms": 5000, "max_retries": 2},
        {"tool_name": "listar_paquetes_pendientes", "timeout_ms": 3000, "max_retries": 3},
        {"tool_name": "procesar_recarga", "timeout_ms": 8000, "max_retries": 1},
        {"tool_name": "activar_pin_digital", "timeout_ms": 8000, "max_retries": 1},
        {"tool_name": "buscar_en_manuales", "timeout_ms": 10000, "max_retries": 2},
        {"tool_name": "consultar_catalogo_productos", "timeout_ms": 3000, "max_retries": 3},
    ]

    for policy in policies:
        register_tool_policy(**policy)
        print(f"  ✓ Policy: {policy['tool_name']} ({policy['timeout_ms']}ms)")


def main():
    print("=" * 50)
    print("🌱 MyAgent - Database Seed")
    print("=" * 50)

    # Initialize schema
    print("\n📋 Initializing database schema...")
    db_ok = init_database()

    if db_ok:
        print("✅ PostgreSQL connected and schema ready")
    else:
        print("⚠️  Using in-memory fallback (no PostgreSQL)")

    # Seed MCP clients
    print("\n👥 Seeding MCP clients...")
    seed_mcp_clients()

    # Seed tool policies
    print("\n📜 Seeding tool policies...")
    seed_tool_policies()

    print("\n" + "=" * 50)
    print("✅ Seed complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
