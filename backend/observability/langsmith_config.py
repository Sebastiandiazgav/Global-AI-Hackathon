"""
MyAgent - LangSmith Observability Configuration
Configures tracing, monitoring, and evaluation with LangSmith.
"""

import os
from config import get_settings


def configure_langsmith():
    """
    Configure LangSmith tracing environment variables.
    
    When LANGCHAIN_API_KEY is set, all LangChain/LangGraph operations
    are automatically traced and sent to LangSmith.
    
    Returns:
        dict with configuration status
    """
    settings = get_settings()

    # Set environment variables that LangChain SDK reads
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        tracing_active = True
    else:
        # Disable tracing if no API key (graceful degradation)
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        tracing_active = False

    return {
        "tracing_active": tracing_active,
        "project": settings.langchain_project,
        "endpoint": settings.langchain_endpoint,
        "has_api_key": bool(settings.langchain_api_key),
    }


def get_langsmith_status() -> dict:
    """
    Get current LangSmith configuration status.
    Useful for health checks and debugging.
    """
    settings = get_settings()

    status = {
        "enabled": settings.langchain_tracing_v2,
        "has_api_key": bool(settings.langchain_api_key),
        "project": settings.langchain_project,
        "endpoint": settings.langchain_endpoint,
        "status": "active" if settings.langchain_api_key else "inactive (no API key)",
        "setup_instructions": None,
    }

    if not settings.langchain_api_key:
        status["setup_instructions"] = (
            "Para activar LangSmith:\n"
            "1. Regístrate en https://smith.langchain.com (gratis)\n"
            "2. Crea una API key en Settings > API Keys\n"
            "3. Añade LANGCHAIN_API_KEY=lsv2_... a tu .env\n"
            "4. Reinicia el backend"
        )

    return status


def get_trace_url(run_id: str) -> str:
    """Generate a LangSmith trace URL for a specific run."""
    settings = get_settings()
    return f"https://smith.langchain.com/o/default/projects/p/{settings.langchain_project}/r/{run_id}"
