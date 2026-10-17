from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.copilot.copilot import get_copilot
from app.schemas.v1 import ChatV1Request, ChatV1Response

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat", response_model=ChatV1Response)
async def chat_v1(request: ChatV1Request) -> ChatV1Response:
    """Primary chat endpoint for role-aware AI Harness orchestration."""
    try:
        copilot = get_copilot()
        result = await copilot.chat(
            user_id=request.user_id,
            role=request.role,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            message=request.message,
            provider_preference=request.provider,
        )
        return ChatV1Response(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
