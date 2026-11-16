from __future__ import annotations

from typing import Any
from app.rag.qdrant import QdrantVectorStore


class RAGRetriever:
    """Semantic retriever with tenant isolation and permission checks."""

    def __init__(self, vector_store: QdrantVectorStore) -> None:
        self.vector_store = vector_store

    async def retrieve(
        self, query: str, role: str, tenant_id: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        return await self.vector_store.search(
            query=query, role=role, tenant_id=tenant_id, limit=limit
        )
