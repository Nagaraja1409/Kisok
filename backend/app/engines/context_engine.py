from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    intent: str | None = None
    entities: dict[str, Any] = Field(default_factory=dict)


class SessionContext(BaseModel):
    session_id: str
    user_id: str
    role: str
    tenant_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    active_intent: str | None = None
    accumulated_entities: dict[str, Any] = Field(default_factory=dict)
    ui_context: dict[str, Any] = Field(default_factory=dict)


class ContextEngine:
    """Manages short-term conversation context, user scope, and memory."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._ui_contexts: dict[str, dict[str, Any]] = {}

    def set_ui_context(self, key: str, ui_context: dict[str, Any] | None) -> None:
        if ui_context and isinstance(ui_context, dict):
            self._ui_contexts[key] = ui_context
            if key in self._sessions:
                self._sessions[key].ui_context = ui_context

    def get_ui_context(self, key: str | None = None) -> dict[str, Any]:
        if key and key in self._ui_contexts:
            return self._ui_contexts[key]
        return {}

    def get_or_create_session(
        self, session_id: str, user_id: str, role: str, tenant_id: str
    ) -> SessionContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(
                session_id=session_id,
                user_id=user_id,
                role=role,
                tenant_id=tenant_id,
            )
        ctx = self._sessions[session_id]
        ctx.user_id = user_id
        ctx.role = role
        ctx.tenant_id = tenant_id
        return ctx

    def update_session(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        intent: str,
        entities: dict[str, Any],
    ) -> None:
        ctx = self._sessions.get(session_id)
        if not ctx:
            return
        ctx.active_intent = intent
        ctx.accumulated_entities.update(entities)
        ctx.turns.append(ConversationTurn(role="user", content=user_message, intent=intent, entities=entities))
        ctx.turns.append(ConversationTurn(role="assistant", content=assistant_message))
        # Keep recent 8 turns (16 messages) to avoid token bloat
        if len(ctx.turns) > 16:
            ctx.turns = ctx.turns[-16:]

    def format_recent_history(self, session_id: str, max_turns: int = 4) -> list[dict[str, str]]:
        ctx = self._sessions.get(session_id)
        if not ctx or not ctx.turns:
            return []
        recent = ctx.turns[-max_turns * 2 :]
        return [{"role": t.role, "content": t.content} for t in recent]


_CONTEXT_ENGINE = ContextEngine()


def get_context_engine() -> ContextEngine:
    return _CONTEXT_ENGINE
