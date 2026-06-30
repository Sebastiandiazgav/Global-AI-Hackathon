"""
MyAgent - Intelligent Model Router with Automatic Fallback
Routes LLM calls to available models with automatic failover when quota is exhausted.
Ensures zero downtime regardless of individual model quota limits.
"""

import structlog
from typing import Optional
from langchain_openai import ChatOpenAI
from config import get_settings

logger = structlog.get_logger()

# Model fallback chains by role
# Each role has a primary model + ordered fallbacks with similar capabilities
MODEL_CHAINS = {
    "agent": [
        "qwen3-omni-flash",
        "qwen3.5-omni-flash-2026-03-15",
        "qwen3-omni-flash-2025-09-15",
        "qwen3.6-flash",
        "qwen3.5-flash",
        "qwen-flash",
        "qwen-turbo",
        "deepseek-v4-flash",
        "glm-5.2",
        "qwen3.6-plus",
        "qwen3.5-plus",
        "qwen-plus",
        "deepseek-v4-flash",
        "qwen3.7-plus",
        "qwen-max",
    ],
    "supervisor": [
        "qwen3-omni-flash",
        "qwen3.6-flash",
        "qwen3.5-omni-flash-2026-03-15",
        "qwen3-omni-flash-2025-09-15",
        "qwen3.5-flash",
        "qwen-flash",
        "qwen3.6-plus",
        "qwen3.5-plus",
        "qwen-plus",
        "deepseek-v4-flash",
        "qwen3.7-plus",
    ],
    "society": [
        "qwen3.6-plus",
        "qwen3-omni-flash",
        "qwen3.5-omni-flash-2026-03-15",
        "qwen3.6-flash",
        "qwen3.5-flash",
        "qwen-plus",
        "qwen3.5-plus",
        "qwen3.7-plus",
        "deepseek-v4-flash",
        "qwen-max",
    ],
    "vision": [
        "qwen-vl-max",
        "qwen-vl-plus",
        "qwen3-vl-plus",
        "qwen3-vl-flash",
        ],
    "embedding": [
        "text-embedding-v4",
    ],
}

# Track which models have exhausted quota (avoid retrying them)
_exhausted_models: set = set()


def get_available_model(role: str) -> str:
    """
    Get the first available model for a given role.
    Skips models that have been marked as exhausted.
    """
    chain = MODEL_CHAINS.get(role, MODEL_CHAINS["agent"])
    for model in chain:
        if model not in _exhausted_models:
            return model
    # If all exhausted, reset and try the primary again
    _exhausted_models.clear()
    return chain[0]


def mark_model_exhausted(model: str):
    """Mark a model as having exhausted quota."""
    _exhausted_models.add(model)
    logger.warning("model_quota_exhausted", model=model, exhausted_count=len(_exhausted_models))


def get_llm(
    role: str = "agent",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    model_override: Optional[str] = None,
) -> ChatOpenAI:
    """
    Get a ChatOpenAI instance with the best available model for the role.
    
    Args:
        role: One of 'agent', 'supervisor', 'society', 'vision'
        temperature: LLM temperature
        max_tokens: Maximum output tokens
        model_override: Force a specific model (bypasses router)
    
    Returns:
        ChatOpenAI instance configured with Qwen Cloud
    """
    settings = get_settings()
    model = model_override or get_available_model(role)

    return ChatOpenAI(
        model=model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def invoke_with_fallback(llm_call_func, role: str = "agent", max_retries: int = 3):
    """
    Execute an LLM call with automatic model fallback on quota errors.
    
    Args:
        llm_call_func: Async function that takes a model name and returns the LLM response.
                       Signature: async def func(model: str) -> response
        role: The role for model selection
        max_retries: Maximum number of fallback attempts
    
    Returns:
        The LLM response from whichever model succeeds
    
    Raises:
        Exception: If all models fail
    """
    chain = MODEL_CHAINS.get(role, MODEL_CHAINS["agent"])
    last_error = None

    for attempt in range(min(max_retries, len(chain))):
        model = get_available_model(role)
        try:
            result = await llm_call_func(model)
            return result
        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "exhausted", "freetieronly", "internalerror", "400"]):
                mark_model_exhausted(model)
                logger.info("model_fallback", exhausted_model=model, attempt=attempt + 1, role=role)
                last_error = e
                continue
            else:
                # Non-quota error — don't retry with different model
                raise

    # All models exhausted
    raise last_error or Exception(f"All models exhausted for role '{role}'")


def get_model_status() -> dict:
    """Get current status of model availability."""
    status = {}
    for role, chain in MODEL_CHAINS.items():
        available = [m for m in chain if m not in _exhausted_models]
        exhausted = [m for m in chain if m in _exhausted_models]
        status[role] = {
            "active_model": available[0] if available else "none",
            "available_count": len(available),
            "exhausted": exhausted,
            "total_in_chain": len(chain),
        }
    return status


async def ainvoke_with_retry(messages, role: str = "agent", temperature: float = 0.3, max_tokens: int = 1024, tools=None, config=None):
    """
    Invoke LLM with automatic model fallback. Drop-in replacement for llm.ainvoke().
    If a model returns quota error, automatically tries the next available model.
    
    Args:
        messages: List of messages to send
        role: Model role for fallback chain selection
        temperature: LLM temperature
        max_tokens: Max output tokens
        tools: Optional tools to bind (for function calling)
        config: Optional LangChain config (tags, metadata)
    
    Returns:
        LLM response
    """
    chain = MODEL_CHAINS.get(role, MODEL_CHAINS["agent"])
    last_error = None

    for attempt in range(len(chain)):
        model = get_available_model(role)
        settings = get_settings()
        
        llm = ChatOpenAI(
            model=model,
            base_url=settings.qwen_cloud_base_url,
            api_key=settings.qwen_cloud_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        if tools:
            llm = llm.bind_tools(tools)

        try:
            result = await llm.ainvoke(messages, config=config or {})
            return result
        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "exhausted", "freetieronly", "403"]):
                mark_model_exhausted(model)
                logger.info("model_fallback_retry", exhausted=model, attempt=attempt + 1, role=role, next=get_available_model(role))
                last_error = e
                continue
            raise

    raise last_error or Exception(f"All models exhausted for role '{role}'")
