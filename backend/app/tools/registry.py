from __future__ import annotations

from typing import Any
from app.core.config import CoreSettings, get_core_settings
from app.tools.base import BaseTool
from app.tools.erp.client import ERPClient
from app.tools.erp.http_client import HttpERPClient
from app.tools.erp.tools import (
    GetAdmissionDetailsTool,
    GetCampusFacilitiesTool,
    GetEventsTool,
    GetExamDetailsTool,
    GetFeeDetailsTool,
    GetLibraryDataTool,
    GetNoticesTool,
    GetStaffDetailsTool,
    GetStudentAttendanceTool,
    GetStudentMarksTool,
    GetStudentProfileTool,
    GetTimetableTool,
    GetTransportDetailsTool,
    PreviewAppointmentTool,
    PreviewLeaveApplicationTool,
)
from app.tools.erp.ui_client import DynamicUIERPClient


class ToolRegistry:
    """Central registry of all controlled tools in the platform."""

    def __init__(self, settings: CoreSettings | None = None) -> None:
        self.settings = settings or get_core_settings()
        self.client = self._create_erp_client()
        self._tools: dict[str, BaseTool] = {}
        self._register_tools()

    def _create_erp_client(self) -> ERPClient:
        if self.settings.erp_mode == "http":
            return HttpERPClient(
                base_url=self.settings.erp_base_url,
                api_key=self.settings.erp_api_key,
                timeout=self.settings.ai_timeout_seconds,
            )
        return DynamicUIERPClient()

    def _register_tools(self) -> None:
        from app.rag.qdrant import QdrantVectorStore
        from app.rag.retriever import RAGRetriever
        from app.tools.rag.rag_tool import RAGRetrievalTool

        vector_store = QdrantVectorStore(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
            collection_name=self.settings.qdrant_collection,
        )
        retriever = RAGRetriever(vector_store)

        tools: list[BaseTool] = [
            GetStudentProfileTool(self.client),
            GetStudentAttendanceTool(self.client),
            GetStudentMarksTool(self.client),
            GetExamDetailsTool(self.client),
            GetFeeDetailsTool(self.client),
            GetTransportDetailsTool(self.client),
            GetNoticesTool(self.client),
            GetTimetableTool(self.client),
            GetLibraryDataTool(self.client),
            GetAdmissionDetailsTool(self.client),
            GetStaffDetailsTool(self.client),
            GetEventsTool(self.client),
            GetCampusFacilitiesTool(self.client),
            PreviewLeaveApplicationTool(self.client),
            PreviewAppointmentTool(self.client),
            RAGRetrievalTool(retriever),
        ]
        for t in tools:
            self._tools[t.name] = t

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools_for_role(self, role: str) -> list[dict[str, Any]]:
        result = []
        for name, tool in self._tools.items():
            if tool.validate_permission(role):
                result.append({
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.args_schema.model_json_schema(),
                })
        return result

    def get_all_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.args_schema.model_json_schema(),
            }
            for tool in self._tools.values()
        ]


_REGISTRY: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ToolRegistry()
    return _REGISTRY
