"""
MyAgent - Configuration Management
Loads environment variables and provides typed settings for Qwen Cloud + Alibaba infrastructure.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Qwen Cloud (LLMs + Embeddings)
    qwen_cloud_api_key: str = Field(..., env="QWEN_CLOUD_API_KEY")
    qwen_cloud_base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        env="QWEN_CLOUD_BASE_URL",
    )

    # Model Configuration
    supervisor_model: str = Field(default="qwen3.5-omni-plus", env="SUPERVISOR_MODEL")
    agent_model: str = Field(default="qwen3.5-omni-flash", env="AGENT_MODEL")
    society_model: str = Field(default="qwen3.5-omni-plus", env="SOCIETY_MODEL")
    vision_model: str = Field(default="qwen-vl-max", env="VISION_MODEL")
    embedding_model: str = Field(default="text-embedding-v4", env="EMBEDDING_MODEL")

    # Alibaba Cloud
    alibaba_access_key_id: str = Field(default="", env="ALIBABA_ACCESS_KEY_ID")
    alibaba_access_key_secret: str = Field(default="", env="ALIBABA_ACCESS_KEY_SECRET")
    alibaba_region: str = Field(default="ap-southeast-1", env="ALIBABA_REGION")

    # Database (PostgreSQL)
    database_url: str = Field(
        default="postgresql://myagent:myagent_pass@db:5432/myagent_db",
        env="DATABASE_URL",
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")

    # Vector Store
    vector_store_type: str = Field(default="pgvector", env="VECTOR_STORE_TYPE")
    vector_store_collection: str = Field(default="myagent_knowledge", env="VECTOR_STORE_COLLECTION")

    # LangSmith (Observability)
    langchain_tracing_v2: bool = Field(default=True, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="hackaton-enterprise", env="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT"
    )

    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    app_debug: bool = Field(default=True, env="APP_DEBUG")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    frontend_port: int = Field(default=3000, env="FRONTEND_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Security
    guardrails_enabled: bool = Field(default=True, env="GUARDRAILS_ENABLED")
    max_transaction_amount: float = Field(default=500.0, env="MAX_TRANSACTION_AMOUNT")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # Token/Context optimization
    supervisor_max_tokens: int = Field(default=256, env="SUPERVISOR_MAX_TOKENS")
    supervisor_history_max_messages: int = Field(default=3, env="SUPERVISOR_HISTORY_MAX_MESSAGES")
    supervisor_history_max_chars: int = Field(default=120, env="SUPERVISOR_HISTORY_MAX_CHARS")
    agent_max_tokens: int = Field(default=1024, env="AGENT_MAX_TOKENS")
    agent_context_max_messages: int = Field(default=10, env="AGENT_CONTEXT_MAX_MESSAGES")
    agent_context_max_chars: int = Field(default=600, env="AGENT_CONTEXT_MAX_CHARS")
    agent_tool_result_max_chars: int = Field(default=1500, env="AGENT_TOOL_RESULT_MAX_CHARS")

    # MCP transport strategy: auto, stdio, inprocess
    mcp_transport_mode: str = Field(default="auto", env="MCP_TRANSPORT_MODE")
    mcp_clients_table: str = Field(default="myagent_mcp_clients", env="MCP_CLIENTS_TABLE")
    mcp_tool_policies_table: str = Field(default="myagent_mcp_tool_policies", env="MCP_TOOL_POLICIES_TABLE")
    mcp_tool_audit_table: str = Field(default="myagent_tool_audit", env="MCP_TOOL_AUDIT_TABLE")

    # Memory
    memory_max_messages_per_session: int = Field(default=30, env="MEMORY_MAX_MESSAGES_PER_SESSION")
    memory_session_ttl_minutes: int = Field(default=120, env="MEMORY_SESSION_TTL_MINUTES")
    memory_persistent_enabled: bool = Field(default=True, env="MEMORY_PERSISTENT_ENABLED")

    # Multilingual
    default_language: str = Field(default="es", env="DEFAULT_LANGUAGE")
    supported_languages: str = Field(default="es,en,fr,pt,de,it,zh", env="SUPPORTED_LANGUAGES")

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
