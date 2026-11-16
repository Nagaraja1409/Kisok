from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from app.core.security import SecurityValidator
from app.engines.context_engine import get_context_engine
from app.graph.graph import get_orchestrator_graph
from app.graph.state import OrchestratorState

logger = logging.getLogger(__name__)


class AICopilot:
    """Central AI Copilot managing conversational intake and LangGraph execution."""

    def __init__(self) -> None:
        self.graph = get_orchestrator_graph()
        self.context_engine = get_context_engine()

    async def chat(
        self,
        user_id: str,
        role: str,
        tenant_id: str,
        session_id: str,
        message: str,
        provider_preference: str | None = None,
        ui_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        request_id = f"req_{uuid.uuid4().hex[:10]}"

        initial_state: OrchestratorState = {
            "user_id": user_id,
            "role": role,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "message": message,
            "provider_preference": provider_preference,
            "ui_context": ui_context or {},
            "success": True,
        }

        # Execute through LangGraph dynamic orchestrator
        final_state: OrchestratorState = await self.graph.ainvoke(initial_state)

        latency_ms = (time.perf_counter() - t0) * 1000.0

        answer = final_state.get("final_answer", "No response generated.")
        intent = final_state.get("intent", "general")
        agents_used = final_state.get("selected_agents", [])
        sources = final_state.get("sources", [])
        requires_conf = final_state.get("requires_confirmation", False)

        actions = []
        if requires_conf:
            actions.append({
                "action_type": "confirm_sensitive_request",
                "status": "pending_human_approval",
                "message": final_state.get("confirmation_message", "Confirmation required."),
            })

        # Update session memory
        self.context_engine.update_session(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
            intent=intent,
            entities=final_state.get("entities", {}),
        )

        return {
            "request_id": request_id,
            "answer": answer,
            "intent": intent,
            "agents_used": agents_used,
            "sources": sources,
            "actions": actions,
            "reasoning_content": final_state.get("reasoning_content"),
            "followup_questions": final_state.get("followup_questions", []),
            "latency_ms": round(latency_ms, 1),
            "provider_used": final_state.get("provider_used", "deterministic"),
        }


_COPILOT: AICopilot | None = None


def get_copilot() -> AICopilot:
    global _COPILOT
    if _COPILOT is None:
        _COPILOT = AICopilot()
    return _COPILOT
