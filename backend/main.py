"""
MyAgent - Main FastAPI Application
Enterprise AI Copilot - Multi-Agent System powered by Qwen Cloud
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from config import get_settings
from api.routes import router as api_router
from api.sse import router as sse_router
from api.analytics import router as analytics_router
from observability.langsmith_config import configure_langsmith


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    settings = get_settings()

    # Initialize database schema
    from database.connection import init_database, is_database_available, reset_availability_cache
    reset_availability_cache()  # Reset so it re-checks after DB is ready
    db_ok = init_database()
    if db_ok:
        reset_availability_cache()  # Reset again so the store picks up the connection

    # Configure LangSmith observability
    langsmith_status = configure_langsmith()

    print(f"🚀 MyAgent Backend starting...")
    print(f"   Environment: {settings.app_env}")
    print(f"   LLM Provider: Qwen Cloud")
    print(f"   Supervisor Model: {settings.supervisor_model}")
    print(f"   Agent Model: {settings.agent_model}")
    print(f"   Vision Model: {settings.vision_model}")
    print(f"   Embedding Model: {settings.embedding_model}")
    print(f"   Guardrails: {'enabled' if settings.guardrails_enabled else 'disabled'}")
    print(f"   LangSmith: {'active ✓' if langsmith_status['tracing_active'] else 'inactive'}")
    print(f"   Database: PostgreSQL")
    print(f"   Languages: {settings.supported_languages}")
    print(f"")
    print(f"   🤖 Multi-Agent System: LangGraph")
    print(f"   🏛️  Agent Society: Enabled")
    print(f"   📡 Protocol: MCP (Model Context Protocol)")
    print(f"   🧠 Memory: Persistent cross-session")
    print(f"   👁️  Vision: Enabled (VL model)")
    print(f"")
    print(f"✅ MyAgent ready on port {settings.backend_port}")

    yield

    print("👋 MyAgent shutting down...")


app = FastAPI(
    title="MyAgent - Enterprise AI Copilot",
    description=(
        "Multi-agent AI system for enterprise operations. "
        "Unifies energy, logistics, catalog/support, analytics, and strategic consulting "
        "through a single intelligent copilot powered by Qwen Cloud."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://43.98.164.203:3000",
        "http://43.98.164.203",
    ],
    allow_origin_regex=r"https?://43\.98\.164\.203(:\d+)?|https://.*\.alicontainer\.com|https://.*\.aliyuncs\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router, prefix="/api")
app.include_router(sse_router, prefix="/api/stream")
app.include_router(analytics_router, prefix="/api/analytics")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "myagent-backend",
        "version": "2.0.0",
        "llm_provider": "qwen_cloud",
        "models": {
            "supervisor": settings.supervisor_model,
            "agent": settings.agent_model,
            "vision": settings.vision_model,
        },
        "agents": [
            "supervisor",
            "energia",
            "logistica",
            "soporte",
            "visual",
            "analytics",
            "society",
        ],
        "infrastructure": "alibaba_cloud",
    }
