from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Type
from pydantic import BaseModel, Field

from app.core.security import SecurityValidator

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class BaseTool(ABC):
    """Controlled Tool interface with schema validation, RBAC, and logging."""

    name: str
    description: str
    args_schema: Type[BaseModel]

    def __init__(self, name: str, description: str, args_schema: Type[BaseModel]) -> None:
        self.name = name
        self.description = description
        self.args_schema = args_schema

    @abstractmethod
    async def run(
        self,
        requester_role: str,
        requester_user_id: str,
        tenant_id: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the tool safely with permission checks."""
        ...

    def validate_permission(self, role: str) -> bool:
        return SecurityValidator.is_tool_authorized(role, self.name)
