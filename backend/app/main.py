
# VAPS AI Agent Service
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.ai.graphs import SchoolAgentEngine, BaldwinAgentEngine
from app.ai.service import AIService
from app.config import get_settings
from app.models import (
    AIAnswerRequest,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    FeatureInfo,
    RequestPreview,
    RequestPreviewRequest,
    Role,
    RoleFeatureMatrix,
    SessionCreate,
    SessionInfo,
)
from app.repositories.csv_repository import CsvSchoolDataRepository
from app.repositories.session_store import SessionStore

settings = get_settings()
repository = CsvSchoolDataRepository(settings.data_dir)
ai = AIService(repository, settings)

# LangGraph agent engine
agent_engine = SchoolAgentEngine(repository, settings)

# Session store (persisted in data/ directory)
session_store = SessionStore(db_path=settings.data_dir / "sessions.db")

app = FastAPI(
    title=settings.app_name, version="2.0.0", description="Role-aware conversational AI service for the school with multi-session chat history."
)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parents[1] / "static"), name="static")

# Mount production v1 routers
from app.api.routes.agents import router as agents_v1_router
from app.api.routes.chat import router as chat_v1_router
from app.api.routes.health import router as health_v1_router
from app.api.routes.tools import router as tools_v1_router
from app.api.routes.voice import router as voice_v1_router
from app.api.routes.admin import router as admin_v1_router
from app.api.routes.green_ai import router as green_ai_router
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from app.rag.ingestion import RAGIngestionService
from app.rag.qdrant import QdrantVectorStore

app.include_router(chat_v1_router)
app.include_router(health_v1_router)
app.include_router(agents_v1_router)
app.include_router(tools_v1_router)
app.include_router(voice_v1_router)
app.include_router(admin_v1_router)
app.include_router(green_ai_router)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        vs = QdrantVectorStore()
        ingestion = RAGIngestionService(vs)
        await ingestion.seed_initial_knowledge()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Startup knowledge seed skipped: {e}")

ROLES = ["student", "parent", "teacher", "visitor", "alumni"]
ROLE_LABELS = {
    "student": "Student",
    "parent": "Parent",
    "teacher": "Teacher / Staff",
    "visitor": "Visitor",
    "alumni": "Alumni / Ex-Staff",
}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    html = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page() -> HTMLResponse:
    admin_path = Path(__file__).resolve().parents[1] / "static" / "admin.html"
    if admin_path.exists():
        html = admin_path.read_text(encoding="utf-8")
    else:
        html = "<html><body><h1>Admin Dashboard</h1></body></html>"
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# Health & metadata
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "data_mode": "csv-first", "provider": settings.ai_provider}


@app.get("/api/roles")
async def roles() -> list[dict[str, str]]:
    return [{"id": role, "label": ROLE_LABELS.get(role, role.title())} for role in ROLES]


@app.get("/api/modules")
async def modules(role: Role) -> list[str]:
    return sorted(repository.get_context(role).records.keys())


# ---------------------------------------------------------------------------
# Dashboard (legacy)
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/{role}")
async def dashboard(role: Role, user_ref: str | None = None) -> dict:
    context = repository.get_context(role, user_ref)
    profile = context.profile
    cards = []
    if role in ("student", "parent"):
        cards = [
            {"label": "Attendance", "value": profile.get("attendance", "92%")},
            {"label": "Fee balance", "value": f"₹{profile.get('fee_balance', '18,500')}"},
            {"label": "Next class", "value": "Science Lab · Room 204"},
            {"label": "Next exam", "value": "Mathematics · 12 Sep 2026"},
        ]
    elif role == "teacher":
        cards = [
            {"label": "Next period", "value": profile.get("next_period", "Science Lab · 10:10")},
            {"label": "Assigned class", "value": profile.get("assigned_class", "Class VIII A")},
            {"label": "Tasks", "value": "3 awaiting review"},
            {"label": "Leave balance", "value": "6 casual days"},
        ]
    elif role == "visitor":
        cards = [
            {"label": "Admissions desk", "value": "09:00–15:30"},
            {"label": "Next event", "value": "Founders Day · 05 Sep"},
            {"label": "Campus facilities", "value": "2 guided locations"},
            {"label": "Application", "value": "BCE/ENQ/2026/114"},
        ]
    else:
        cards = [
            {"label": "Community event", "value": "Founders Day · 05 Sep"},
            {"label": "Last engagement", "value": profile.get("last_engagement", "Founders Day")},
            {"label": "Mentorship", "value": "3 open matches"},
            {"label": "School connection", "value": profile.get("connection", "Class of 2018")},
        ]
    return {
        "role": role,
        "user_ref": user_ref,
        "profile": profile,
        "cards": cards,
        "brief": "This brief is grounded in local school CSV records and is view-only.",
        "provider": settings.ai_provider,
        "data_mode": "CSV demonstration data",
    }


# ---------------------------------------------------------------------------
# Legacy AI endpoints (backward-compat)
# ---------------------------------------------------------------------------

@app.get("/api/ai/features")
async def features(role: Role, pillar: str | None = None) -> list[dict]:
    return ai.features(role, pillar)


@app.post("/api/ai/answer")
async def answer(request: AIAnswerRequest):
    return await ai.answer(request)


@app.post("/api/ai/demo")
async def demo(request: AIAnswerRequest):
    return await ai.answer(request)


@app.post("/api/requests/preview", response_model=RequestPreview)
async def request_preview(request: RequestPreviewRequest) -> RequestPreview:
    return RequestPreview(
        role=request.role, user_ref=request.user_ref, request_type=request.request_type, details=request.details
    )


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@app.get("/api/sessions", response_model=list[SessionInfo])
async def list_sessions():
    return session_store.list_sessions()


@app.post("/api/sessions", response_model=SessionInfo)
async def create_session(body: SessionCreate):
    return session_store.create_session(body.role, body.title)


@app.get("/api/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session_history(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = session_store.get_messages(session_id)
    return ChatHistoryResponse(session=session, messages=messages)


@app.patch("/api/sessions/{session_id}")
async def rename_session(session_id: str, body: dict):
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not session_store.rename_session(session_id, title):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if not session_store.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Conversational chat (LangGraph-powered)
# ---------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Image payload preview representation if present
    img_repr = body.image_url
    if not img_repr and body.image_base64:
        if body.image_base64.startswith("data:"):
            img_repr = body.image_base64
        else:
            img_repr = f"data:image/jpeg;base64,{body.image_base64}"

    # Save user message
    session_store.add_message(
        session.session_id, "user", body.message,
        feature_tag=body.feature_tag,
        image_path=img_repr,
    )

    # Get conversation history for context
    history = session_store.recent_messages_for_context(session.session_id, limit=20)

    # Run LangGraph agent
    result = await agent_engine.run(
        role=session.role,
        question=body.message,
        user_ref=None,
        feature_tag=body.feature_tag,
        image_base64=body.image_base64,
        image_url=body.image_url,
        conversation_history=history[:-1],  # exclude the current message (already in graph input)
        provider_override=body.provider if body.provider != "auto" else None,
    )

    # Build source records
    from app.models import SourceRecord
    sources = [SourceRecord(**s) for s in result.get("sources", [])]

    # Save assistant message
    assistant_msg = session_store.add_message(
        session.session_id,
        "assistant",
        result["answer"],
        sources=sources,
        safety_boundary="CSV demonstration data only — no live record was changed, nothing was submitted, paid, or sent.",
        agent_steps=result.get("agent_steps", []),
        reasoning_content=result.get("reasoning_content"),
        followup_questions=result.get("followup_questions", []),
    )

    # Auto-rename session from first message
    if session.message_count <= 1:
        title = body.message[:50].strip()
        if title:
            session_store.rename_session(session.session_id, title)

    return ChatResponse(message=assistant_msg, provider_used=result.get("provider_used", "deterministic"))


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest):
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Image payload preview representation if present
    img_repr = body.image_url
    if not img_repr and body.image_base64:
        if body.image_base64.startswith("data:"):
            img_repr = body.image_base64
        else:
            img_repr = f"data:image/jpeg;base64,{body.image_base64}"

    # Save user message
    session_store.add_message(
        session.session_id, "user", body.message,
        feature_tag=body.feature_tag,
        image_path=img_repr,
    )

    history = session_store.recent_messages_for_context(session.session_id, limit=20)

    async def event_generator():
        final_answer = ""
        reasoning_content = None
        followup_questions = []
        sources = []
        agent_steps = []
        provider_used = "deterministic"

        try:
            async for chunk in agent_engine.stream_run(
                role=session.role,
                question=body.message,
                user_ref=None,
                feature_tag=body.feature_tag,
                image_base64=body.image_base64,
                image_url=body.image_url,
                conversation_history=history[:-1],
                provider_override=body.provider if body.provider != "auto" else None,
            ):
                chunk_type = chunk.get("type")
                if chunk_type == "done":
                    final_answer = chunk.get("answer", "")
                    reasoning_content = chunk.get("reasoning_content")
                    followup_questions = chunk.get("followup_questions", [])
                    sources = chunk.get("sources", [])
                    agent_steps = chunk.get("agent_steps", [])
                    provider_used = chunk.get("provider_used", "deterministic")
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

        # Save assistant message to session store upon completion
        from app.models import SourceRecord
        src_objs = [SourceRecord(**s) for s in sources]
        assistant_msg = session_store.add_message(
            session.session_id,
            "assistant",
            final_answer,
            sources=src_objs,
            safety_boundary="CSV demonstration data only — no live record was changed, nothing was submitted, paid, or sent.",
            agent_steps=agent_steps,
            reasoning_content=reasoning_content,
            followup_questions=followup_questions,
        )

        if session.message_count <= 1:
            title = body.message[:50].strip()
            if title:
                session_store.rename_session(session.session_id, title)

        yield f"data: {json.dumps({'type': 'message_saved', 'message': assistant_msg.model_dump(), 'provider_used': provider_used})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Feature matrix
# ---------------------------------------------------------------------------

@app.get("/api/features/matrix", response_model=list[RoleFeatureMatrix])
async def feature_matrix():
    result = []
    for role_id in ROLES:
        features = agent_engine.get_features(role_id)
        result.append(RoleFeatureMatrix(
            role=role_id,
            role_label=ROLE_LABELS.get(role_id, role_id.title()),
            features=[FeatureInfo(**f) for f in features],
        ))
    return result


@app.get("/api/features/{role}", response_model=list[FeatureInfo])
async def role_features(role: Role):
    features = agent_engine.get_features(role)
    return [FeatureInfo(**f) for f in features]
