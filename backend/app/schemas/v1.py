from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ChatV1Request(BaseModel):
    user_id: str = Field(description="User identifier", min_length=1)
    role: str = Field(description="User role (student_parent, teacher_staff, visitor_applicant, alumni_ex_employee)")
    tenant_id: str = Field(default="school_001", description="School / Tenant identifier")
    session_id: str = Field(default="session_default", description="Conversation session identifier")
    message: str = Field(description="User query or message", min_length=1)
    provider: str | None = Field(default=None, description="Optional provider preference (nvidia, groq, deterministic)")


class ActionItem(BaseModel):
    action_type: str
    status: str
    message: str


class ChatV1Response(BaseModel):
    request_id: str
    answer: str
    intent: str
    agents_used: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    reasoning_content: str | None = None
    followup_questions: list[str] = Field(default_factory=list)
    provider_used: str = "deterministic"
    latency_ms: float = 0.0


class HealthV1Response(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    app_name: str
    erp_mode: str
    ai_provider: str
    providers_health: dict[str, Any]


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    role: str
    description: str
    default_tools: list[str]


class ToolInfo(BaseModel):
    name: str
    description: str
    schema_: dict[str, Any] = Field(alias="schema")
