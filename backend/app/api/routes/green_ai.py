from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.agents.registry import get_agent_registry
from app.copilot.copilot import get_copilot
from app.core.role_features import (
    WELCOME_MESSAGE,
    get_features_for_role,
    get_role_metadata,
)
from app.core.security import SecurityValidator
from app.repositories.session_store import SessionStore
from app.schemas.green_ai import (
    GreenAIAgentInfo,
    GreenAIChatRequest,
    GreenAIChatResponse,
    GreenAIFeature,
    GreenAIFeaturesResponse,
    GreenAISessionCreateRequest,
    GreenAISessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/green-ai", tags=["GREEN_AI"])


def get_session_store() -> SessionStore:
    from app.config import get_settings
    settings = get_settings()
    return SessionStore(db_path=settings.data_dir / "sessions.db")


@router.get("/features", response_model=GreenAIFeaturesResponse)
async def get_green_ai_features(
    role: str | None = Query(default=None, description="Requested user role"),
    session_id: str | None = Query(default=None, description="Optional conversation session ID"),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    authorization: str | None = Header(default=None),
) -> GreenAIFeaturesResponse:
    session_store = get_session_store()
    effective_sid = session_id or x_session_id
    session_role = None

    if effective_sid:
        sess = session_store.get_session(effective_sid)
        if sess:
            session_role = sess.role

    client_role = role or x_user_role
    is_authenticated = bool(authorization or session_role)

    effective_role, is_authorized = SecurityValidator.resolve_effective_role(
        session_role=session_role,
        client_role=client_role,
        is_authenticated=is_authenticated,
        allow_role_inquiry=True,
    )

    metadata = get_role_metadata(effective_role)
    raw_features = get_features_for_role(effective_role)
    features = [GreenAIFeature(**f) for f in raw_features]

    agent_registry = get_agent_registry()
    role_agents_raw = agent_registry.list_agents_for_role(effective_role)
    agents = [
        GreenAIAgentInfo(
            agent_id=a["agent_id"],
            name=a["name"],
            role=a["role"],
            description=a["description"],
            default_tools=a.get("default_tools", []),
            status="active",
        )
        for a in role_agents_raw
    ]

    suggested_q = []
    for f in features:
        for prompt in f.sample_prompts:
            if prompt not in suggested_q:
                suggested_q.append(prompt)
            if len(suggested_q) >= 6:
                break
        if len(suggested_q) >= 6:
            break

    return GreenAIFeaturesResponse(
        assistant_name="GREEN_AI",
        welcome_message=WELCOME_MESSAGE,
        effective_role=effective_role,
        role_label=metadata.get("role_label", "Campus Kiosk"),
        badge=metadata.get("badge", "Official Kiosk"),
        description=metadata.get("description", ""),
        primary_color=metadata.get("primary_color", "#ea580c"),
        features=features,
        agents=agents,
        suggested_questions=suggested_q,
    )


@router.get("/agents", response_model=list[GreenAIAgentInfo])
async def get_green_ai_agents(
    role: str | None = Query(default=None, description="Requested user role"),
    session_id: str | None = Query(default=None, description="Session ID"),
) -> list[GreenAIAgentInfo]:
    session_store = get_session_store()
    session_role = None
    if session_id:
        sess = session_store.get_session(session_id)
        if sess:
            session_role = sess.role

    effective_role, _ = SecurityValidator.resolve_effective_role(
        session_role=session_role,
        client_role=role,
        is_authenticated=bool(session_role),
        allow_role_inquiry=True,
    )

    agent_registry = get_agent_registry()
    raw_agents = agent_registry.list_agents_for_role(effective_role)
    return [
        GreenAIAgentInfo(
            agent_id=a["agent_id"],
            name=a["name"],
            role=a["role"],
            description=a["description"],
            default_tools=a.get("default_tools", []),
            status="active",
        )
        for a in raw_agents
    ]


@router.post("/chat", response_model=GreenAIChatResponse)
async def green_ai_chat(
    request: GreenAIChatRequest,
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    authorization: str | None = Header(default=None),
) -> GreenAIChatResponse:
    session_store = get_session_store()
    sid = request.session_id or x_session_id or f"session_{uuid.uuid4().hex[:10]}"
    sess = session_store.get_session(sid)
    session_role = sess.role if sess else None

    client_role = request.role or x_user_role
    has_ui_context = bool(request.ui_context and isinstance(request.ui_context, dict) and len(request.ui_context) > 0)
    is_authenticated = bool(authorization or session_role or has_ui_context)

    effective_role, is_valid_auth = SecurityValidator.resolve_effective_role(
        session_role=session_role,
        client_role=client_role,
        is_authenticated=is_authenticated,
    )

    if session_role and not is_valid_auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization failure: Session is bound to '{session_role}', cannot act as '{client_role}'.",
        )

    if not sess:
        try:
            sess = session_store.create_session(role=effective_role, title=request.message[:40])
            sid = sess.session_id
        except Exception as e:
            logger.warning(f"Could not auto-create session in SQLite: {e}")

    try:
        session_store.add_message(sid, "user", request.message, feature_tag=request.feature_tag)
    except Exception as e:
        logger.warning(f"Could not log user message in session store: {e}")

    copilot = get_copilot()
    user_id = request.user_id or "KioskUser"
    tenant_id = request.tenant_id or "school_001"

    try:
        copilot_result = await copilot.chat(
            user_id=user_id,
            role=effective_role,
            tenant_id=tenant_id,
            session_id=sid,
            message=request.message,
            provider_preference=request.provider,
            ui_context=request.ui_context,
        )
    except Exception as exc:
        logger.error(f"Error in GREEN_AI copilot execution: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"GREEN_AI Orchestration Error: {str(exc)}")

    agents_used = copilot_result.get("agents_used", [])
    selected_agent_id = agents_used[0] if agents_used else "green_ai_assistant"

    if not SecurityValidator.is_agent_authorized(effective_role, selected_agent_id):
        logger.error(f"Security Alert: Agent '{selected_agent_id}' is NOT authorized for role '{effective_role}'!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent '{selected_agent_id}' is not permitted for role '{effective_role}'.",
        )

    agent_registry = get_agent_registry()
    agent_instance = agent_registry.get_agent(selected_agent_id)
    selected_agent_name = agent_instance.name if agent_instance else "GREEN_AI Assistant"

    answer = copilot_result.get("answer", "I am sorry, I could not generate an answer at this time.")
    followup_suggestions = copilot_result.get("followup_questions", [])

    if not followup_suggestions:
        features = get_features_for_role(effective_role)
        for f in features:
            for prompt in f.get("sample_prompts", []):
                if prompt.lower() not in request.message.lower() and prompt not in followup_suggestions:
                    followup_suggestions.append(prompt)
                if len(followup_suggestions) >= 3:
                    break
            if len(followup_suggestions) >= 3:
                break

    try:
        session_store.add_message(
            sid,
            "assistant",
            answer,
            feature_tag=request.feature_tag,
            agent_steps=agents_used,
            reasoning_content=copilot_result.get("reasoning_content"),
            followup_questions=followup_suggestions,
        )
    except Exception as e:
        logger.warning(f"Could not log assistant message in session store: {e}")

    return GreenAIChatResponse(
        request_id=copilot_result.get("request_id", f"req_{uuid.uuid4().hex[:10]}"),
        assistant_name="GREEN_AI",
        role=effective_role,
        selected_agent=selected_agent_id,
        selected_agent_name=selected_agent_name,
        feature_tag=request.feature_tag,
        answer=answer,
        followup_suggestions=followup_suggestions,
        sources=copilot_result.get("sources", []),
        actions=copilot_result.get("actions", []),
        provider_used=copilot_result.get("provider_used", "deterministic"),
        latency_ms=copilot_result.get("latency_ms", 0.0),
        status="completed",
        reasoning_content=copilot_result.get("reasoning_content"),
    )


@router.post("/session", response_model=GreenAISessionResponse)
async def create_green_ai_session(
    body: GreenAISessionCreateRequest,
) -> GreenAISessionResponse:
    canonical = SecurityValidator.normalize_role(body.role)
    session_store = get_session_store()
    sess = session_store.create_session(role=canonical, title=body.title)
    return GreenAISessionResponse(
        session_id=sess.session_id,
        role=sess.role,
        title=sess.title,
        created_at=sess.created_at,
    )
