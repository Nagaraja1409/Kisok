from typing import Any, TypedDict


class OrchestratorState(TypedDict, total=False):
    # Request parameters
    user_id: str
    role: str
    tenant_id: str
    session_id: str
    message: str
    provider_preference: str | None
    ui_context: dict[str, Any]

    # Planner outputs
    intent: str
    entities: dict[str, Any]
    selected_agents: list[str]
    selected_tools: list[str]
    needs_prediction: bool
    prediction_type: str | None
    needs_recommendation: bool
    needs_rag: bool
    requires_confirmation: bool
    confirmation_message: str | None

    # Execution outputs
    agent_outputs: list[dict[str, Any]]
    tool_data: Any
    sources: list[dict[str, Any]]
    prediction: dict[str, Any] | None
    recommendation: dict[str, Any] | None

    # Response & Audit
    final_answer: str
    reasoning_content: str | None
    followup_questions: list[str]
    provider_used: str
    latency_ms: float
    success: bool
    error: str | None
