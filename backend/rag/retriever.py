"""
MyAgent - RAG Retriever
Queries the vector store for relevant document chunks based on user questions.
Supports pgvector (PostgreSQL) as the vector backend.
"""

from typing import List, Optional

from config import get_settings
from rag.embeddings import get_embeddings


# In-memory fallback for development (simple keyword matching)
_FALLBACK_DOCS = [
    {
        "content": "To process a phone recharge: 1. Ask for destination country and phone number. 2. Confirm the amount. 3. Execute the recharge via the system. 4. Provide the confirmation ticket to the client.",
        "metadata": {"source": "Operations Manual - Recharges"},
    },
    {
        "content": "For package registration: 1. Count packages from the carrier. 2. Scan barcodes with the Smart POS. 3. Confirm storage location. 4. Packages have 7 days before automatic return.",
        "metadata": {"source": "Operations Manual - Logistics"},
    },
    {
        "content": "Energy contracts: Commission is 25€ per signed contract. Required data: client DNI, full name, phone, current consumption in kWh. The change takes effect in the next billing cycle (max 21 days).",
        "metadata": {"source": "Operations Manual - Energy"},
    },
    {
        "content": "Digital PINs: Available platforms include Netflix, Spotify, PlayStation, Xbox, Steam, Nintendo, Disney+, HBO Max, Apple, Google Play. Each activation generates a commission between 1-5€ depending on the platform.",
        "metadata": {"source": "Operations Manual - Digital Products"},
    },
    {
        "content": "Troubleshooting: If the Smart POS does not respond, restart the device. If recharge fails, verify the phone number format and try again. For persistent errors, contact support at support@enterprise.com.",
        "metadata": {"source": "Operations Manual - Technical Support"},
    },
    {
        "content": "Package delivery verification: Accept PIN code or last 4 digits of client ID. Never deliver without verification. Commission per delivery: 0.30€. Log all deliveries in the system.",
        "metadata": {"source": "Operations Manual - Package Delivery"},
    },
    {
        "content": "Returns policy: Packages not collected within 7 days are automatically returned. Mark package for return in the system. Print return label. No commission for returns but activity is logged.",
        "metadata": {"source": "Operations Manual - Returns"},
    },
    {
        "content": "Commission structure: Energy contracts 15-35€, Package delivery 0.25-0.35€, Phone recharges 5-8%, Digital PINs 1-5€, Gift cards 2-3%. Monthly targets: 5 energy contracts, 100 deliveries, 50 recharges.",
        "metadata": {"source": "Operations Manual - Commissions"},
    },
]


class SimpleVectorStore:
    """Simple in-memory vector store for development. Uses keyword matching as fallback."""

    def __init__(self):
        self._docs = _FALLBACK_DOCS

    def similarity_search_with_score(self, query: str, k: int = 3):
        """Simple keyword-based search (fallback when no vector DB is available)."""
        from dataclasses import dataclass

        @dataclass
        class Doc:
            page_content: str
            metadata: dict

        query_lower = query.lower()
        scored = []
        for doc in self._docs:
            content_lower = doc["content"].lower()
            # Simple word overlap scoring
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            score = overlap / max(len(query_words), 1)
            scored.append((Doc(page_content=doc["content"], metadata=doc["metadata"]), score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


_vectorstore = None


def get_vectorstore():
    """Get vector store instance. Falls back to simple search in development."""
    global _vectorstore
    if _vectorstore is None:
        settings = get_settings()
        # TODO: Connect to pgvector when PostgreSQL is available in production
        # For now, use the simple fallback store
        _vectorstore = SimpleVectorStore()
    return _vectorstore


async def query_knowledge_base(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[dict]:
    """
    Query the knowledge base for relevant documents.

    Args:
        query: User question
        top_k: Number of results to return
        score_threshold: Minimum similarity score (0-1)
    """
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query=query, k=top_k)

    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": round(float(score), 4),
            "source": doc.metadata.get("source", "unknown"),
        })

    return formatted_results


async def get_context_for_agent(query: str, max_context_length: int = 2000) -> str:
    """Get formatted context string for agent consumption."""
    results = await query_knowledge_base(query, top_k=3)

    if not results:
        return "No relevant information found in the knowledge base."

    context_parts = []
    total_length = 0

    for result in results:
        content = result["content"]
        source = result["source"]
        entry = f"[Source: {source}]\n{content}\n"

        if total_length + len(entry) > max_context_length:
            break

        context_parts.append(entry)
        total_length += len(entry)

    return "\n---\n".join(context_parts)
