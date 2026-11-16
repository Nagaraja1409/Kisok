from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field

from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)


class AgentOutput(BaseModel):
    agent_id: str
    name: str
    role: str
    status: str = "completed"
    findings: str
    tool_results: list[ToolResult] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    requires_prediction: bool = False
    prediction_type: str | None = None
    requires_recommendation: bool = False
    requires_confirmation: bool = False
    confirmation_message: str | None = None


class BaseAgent(ABC):
    """Abstract base class for role-aware agents in the AI Harness system."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: str,
        default_tools: list[str] | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.default_tools = default_tools or []
        self.tool_registry = tool_registry or get_tool_registry()

    @abstractmethod
    async def process(
        self,
        query: str,
        intent: str,
        entities: dict[str, Any],
        user_id: str,
        tenant_id: str,
    ) -> AgentOutput:
        """Process user request and invoke appropriate tools/engines."""
        ...
