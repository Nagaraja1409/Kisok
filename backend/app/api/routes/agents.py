from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from app.agents.registry import get_agent_registry
from app.schemas.v1 import AgentInfo

router = APIRouter(prefix="/api/v1", tags=["Agents"])


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents(role: str | None = Query(default=None, description="Optional role filter")) -> list[dict[str, Any]]:
    """List registered role-aware AI agents."""
    registry = get_agent_registry()
    if role:
        return registry.list_agents_for_role(role)
    return registry.list_all_agents()
