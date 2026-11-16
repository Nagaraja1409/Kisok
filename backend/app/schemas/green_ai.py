from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class GreenAIFeature(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    sample_prompts: list[str] = Field(default_factory=list)
    linked_agents: list[str] = Field(default_factory=list)
    status: str = Field(default="live", description="live | preview_only | read_only | simulated")
    data_mode: str = Field(default="grounded_csv", description="grounded_csv | live_erp")


class GreenAIAgentInfo(BaseModel):
    agent_id: str
    name: str
    role: str
    description: str
    default_tools: list[str] = Field(default_factory=list)
    status: str = "active"


class GreenAIFeaturesResponse(BaseModel):
    assistant_name: str = "GREEN_AI"
    welcome_message: str
    effective_role: str
    role_label: str
    badge: str
    description: str
    primary_color: str
    features: list[GreenAIFeature] = Field(default_factory=list)
    agents: list[GreenAIAgentInfo] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class GreenAIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="User question or query")
    session_id: str = Field(default="default_session", description="Conversation session id")
    user_id: str | None = Field(default=None, description="Optional user ID")
    role: str | None = Field(default=None, description="Client requested role")
    tenant_id: str = Field(default="school_001", description="Campus / Tenant identifier")
    feature_tag: str | None = Field(default=None, description="Optional explicit feature tag")
    provider: str | None = Field(default=None, description="Optional LLM provider override")
    ui_context: dict[str, Any] | None = Field(default=None, description="Dynamic UI and dashboard context sent directly from Next.js")


class GreenAIChatResponse(BaseModel):
    request_id: str
    assistant_name: str = "GREEN_AI"
    role: str
    selected_agent: str
    selected_agent_name: str
    feature_tag: str | None = None
    answer: str
    followup_suggestions: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    provider_used: str = "deterministic"
    latency_ms: float = 0.0
    status: str = "completed"
    reasoning_content: str | None = None


class GreenAISessionCreateRequest(BaseModel):
    role: str = Field(default="visitor_applicant", description="Initial role for session")
    user_id: str | None = Field(default=None, description="User identifier")
    title: str | None = Field(default=None, description="Session title")


class GreenAISessionResponse(BaseModel):
    session_id: str
    role: str
    title: str
    created_at: str
