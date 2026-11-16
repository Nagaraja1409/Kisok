from __future__ import annotations

import logging
from typing import Any
import httpx

from app.rag.embeddings import LocalEmbeddingService, cosine_similarity

logger = logging.getLogger(__name__)


_SHARED_MEMORY_POINTS: list[dict[str, Any]] = []


class QdrantVectorStore:
    """Qdrant client supporting both live Qdrant REST service and embedded memory fallback."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str = "",
        collection_name: str = "school_knowledge",
    ) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedder = LocalEmbeddingService()
        self._is_live_qdrant: bool | None = None
        self._auto_seed_if_empty()

    def _auto_seed_if_empty(self) -> None:
        global _SHARED_MEMORY_POINTS
        if not _SHARED_MEMORY_POINTS:
            from app.rag.ingestion import INITIAL_SCHOOL_DOCUMENTS
            for i, doc in enumerate(INITIAL_SCHOOL_DOCUMENTS):
                text = doc.get("content", "")
                vector = self.embedder.embed_text(text)
                _SHARED_MEMORY_POINTS.append({
                    "id": doc.get("document_id", f"doc_{i}"),
                    "vector": vector,
                    "payload": {
                        "content": text,
                        "title": doc.get("title", "Notice"),
                        "tenant_id": doc.get("tenant_id", "school_001"),
                        "role": doc.get("role", "all"),
                        "document_id": doc.get("document_id", f"doc_{i}"),
                        "document_type": doc.get("document_type", "circular"),
                        "department": doc.get("department", "general"),
                        "access_level": doc.get("access_level", "public"),
                    },
                })

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["api-key"] = self.api_key
        return h

    async def check_live(self) -> bool:
        if self._is_live_qdrant is not None:
            return self._is_live_qdrant
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.url}/healthz", headers=self._headers())
                self._is_live_qdrant = resp.status_code == 200
        except Exception:
            self._is_live_qdrant = False
        return self._is_live_qdrant

    async def upsert_documents(self, documents: list[dict[str, Any]]) -> int:
        """Upsert documents with metadata (tenant_id, role, access_level, document_type)."""
        points = []
        for i, doc in enumerate(documents):
            text = doc.get("content", "")
            vector = self.embedder.embed_text(text)
            point = {
                "id": doc.get("document_id", f"doc_{i}"),
                "vector": vector,
                "payload": {
                    "content": text,
                    "title": doc.get("title", "Notice"),
                    "tenant_id": doc.get("tenant_id", "school_001"),
                    "role": doc.get("role", "all"),
                    "document_id": doc.get("document_id", f"doc_{i}"),
                    "document_type": doc.get("document_type", "circular"),
                    "department": doc.get("department", "general"),
                    "access_level": doc.get("access_level", "public"),
                },
            }
            points.append(point)

        # Try live Qdrant if available
        if await self.check_live():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.put(
                        f"{self.url}/collections/{self.collection_name}/points",
                        headers=self._headers(),
                        json={"points": points},
                    )
                    return len(points)
            except Exception as exc:
                logger.warning(f"Live Qdrant upsert failed ({exc}), falling back to in-memory store.")

        # In-memory store fallback
        for pt in points:
            # Update or append
            existing = next((p for p in _SHARED_MEMORY_POINTS if p["id"] == pt["id"]), None)
            if existing:
                existing.update(pt)
            else:
                _SHARED_MEMORY_POINTS.append(pt)
        return len(points)

    async def search(
        self,
        query: str,
        role: str,
        tenant_id: str,
        limit: int = 4,
    ) -> list[dict[str, Any]]:
        """Search documents with strict tenant_id and role/access_level permission filtering."""
        query_vector = self.embedder.embed_text(query)

        # Role access rules
        role_lower = role.lower()
        allowed_access = {"public"}
        if "student" in role_lower or "parent" in role_lower:
            allowed_access.update({"student", "parent", "all"})
        elif "teacher" in role_lower or "staff" in role_lower:
            allowed_access.update({"student", "parent", "teacher", "staff", "internal", "all"})
        elif "alumni" in role_lower:
            allowed_access.update({"alumni", "all"})
        else:
            allowed_access.update({"visitor", "all"})

        # Try live Qdrant if available
        if await self.check_live():
            try:
                filter_payload = {
                    "must": [
                        {"key": "tenant_id", "match": {"value": tenant_id}},
                    ]
                }
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        f"{self.url}/collections/{self.collection_name}/points/search",
                        headers=self._headers(),
                        json={
                            "vector": query_vector,
                            "filter": filter_payload,
                            "limit": limit * 2,
                            "with_payload": True,
                        },
                    )
                    if resp.status_code == 200:
                        raw_hits = resp.json().get("result", [])
                        filtered = []
                        for hit in raw_hits:
                            payload = hit.get("payload", {})
                            doc_access = payload.get("access_level", "public").lower()
                            if doc_access in allowed_access:
                                filtered.append({
                                    "title": payload.get("title"),
                                    "content": payload.get("content"),
                                    "score": hit.get("score", 0.0),
                                    "metadata": payload,
                                })
                            if len(filtered) >= limit:
                                break
                        return filtered
            except Exception as exc:
                logger.warning(f"Live Qdrant search failed: {exc}, using in-memory store.")

        # Memory store search with cosine similarity
        scored: list[tuple[float, dict[str, Any]]] = []
        for pt in _SHARED_MEMORY_POINTS:
            payload = pt["payload"]
            # Tenant filter
            if payload.get("tenant_id") != tenant_id and payload.get("tenant_id") != "all":
                continue
            # Permission / Access level filter
            doc_access = payload.get("access_level", "public").lower()
            if doc_access not in allowed_access:
                continue

            sim = cosine_similarity(query_vector, pt["vector"])
            scored.append((sim, payload))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "title": item[1].get("title"),
                "content": item[1].get("content"),
                "score": round(item[0], 4),
                "metadata": item[1],
            }
            for item in scored[:limit]
        ]
