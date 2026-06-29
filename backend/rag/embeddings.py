"""
MyAgent - Embeddings Configuration
Uses Qwen Cloud text-embedding-v4 for vector generation.
Compatible with OpenAI embeddings API.
"""

from langchain_openai import OpenAIEmbeddings
from config import get_settings


def get_embeddings():
    """
    Initialize Qwen Cloud Embeddings via OpenAI-compatible API.

    Model: text-embedding-v4
    Provider: Qwen Cloud (DashScope)
    """
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        base_url=settings.qwen_cloud_base_url,
        api_key=settings.qwen_cloud_api_key,
    )
