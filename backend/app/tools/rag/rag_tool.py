from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.rag.retriever import RAGRetriever
from app.tools.base import BaseTool, ToolResult


class RAGSearchSchema(BaseModel):
    query: str = Field(description="Search question or policy query")


class RAGRetrievalTool(BaseTool):
    def __init__(self, retriever: RAGRetriever) -> None:
        super().__init__(
            name="rag_retrieval",
            description="Search school policies, circulars, exam guidelines, and knowledge documents.",
            args_schema=RAGSearchSchema,
        )
        self.retriever = retriever

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        query = kwargs.get("query", "")
        hits = await self.retriever.retrieve(
            query=query, role=requester_role, tenant_id=tenant_id, limit=3
        )
        sources = [
            {
                "module": "rag_knowledge",
                "record_id": h.get("metadata", {}).get("document_id", "doc"),
                "summary": h.get("title", "Document"),
            }
            for h in hits
        ]
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"results": hits},
            sources=sources,
        )
