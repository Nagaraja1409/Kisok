from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal[
    "student", "parent", "teacher", "visitor", "alumni",
    "student_parent", "teacher_staff", "visitor_applicant", "alumni_ex_employee"
]


# ---------------------------------------------------------------------------
# Source & Context models (unchanged)
# ---------------------------------------------------------------------------

class SourceRecord(BaseModel):
    module: str
    record_id: str
    date: str | None = None
    summary: str


class SchoolContext(BaseModel):
    role: Role
    user_ref: str | None = None
    profile: dict[str, Any] = Field(default_factory=dict)
    records: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Legacy AI answer models (kept for backward-compat on /api/ai/answer)
# ---------------------------------------------------------------------------

class AIAnswerRequest(BaseModel):
    role: Role
    user_ref: str | None = None
    question: str = Field(min_length=2, max_length=500)
    provider: Literal["auto", "deterministic", "groq", "grok", "nvidia"] = "auto"


class AIAnswer(BaseModel):
    role: Role
    intent: str
    answer: str
    sources: list[SourceRecord]
    next_action: str
    safety_boundary: str
    provider: str
    reasoning_content: str | None = None
    followup_questions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Request preview models (unchanged)
# ---------------------------------------------------------------------------

class RequestPreviewRequest(BaseModel):
    role: Role
    user_ref: str | None = None
    request_type: str = Field(min_length=2, max_length=80)
    details: str = Field(min_length=2, max_length=500)


class RequestPreview(BaseModel):
    request_type: str
    role: Role
    user_ref: str | None
    details: str
    status: str = "Prepared for review only"
    safety_boundary: str = (
        "This request was not submitted, paid, sent, stored, or changed; it is only a review preview."
    )


# ---------------------------------------------------------------------------
# Session & conversation history models
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    role: Role
    title: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    role: Role
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatMessage(BaseModel):
    """A single message in a conversation thread."""
    id: str
    session_id: str
    role_sender: Literal["user", "assistant", "system"]
    content: str
    timestamp: str
    feature_tag: str | None = None
    sources: list[SourceRecord] = Field(default_factory=list)
    safety_boundary: str | None = None
    agent_steps: list[str] = Field(default_factory=list)
    image_path: str | None = None
    reasoning_content: str | None = None
    followup_questions: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    session_id: str
    message: str = Field(min_length=1, max_length=2000)
    feature_tag: str | None = None
    provider: Literal["auto", "deterministic", "groq", "grok", "nvidia"] = "auto"
    image_base64: str | None = None
    image_url: str | None = None


class ChatResponse(BaseModel):
    """Response to a chat request."""
    message: ChatMessage
    provider_used: str


class ChatHistoryResponse(BaseModel):
    session: SessionInfo
    messages: list[ChatMessage]


# ---------------------------------------------------------------------------
# Feature matrix models
# ---------------------------------------------------------------------------

class FeatureInfo(BaseModel):
    id: str
    name: str
    description: str
    sample_prompts: list[str] = Field(default_factory=list)
    icon: str = "💡"


class RoleFeatureMatrix(BaseModel):
    role: Role
    role_label: str
    features: list[FeatureInfo]
