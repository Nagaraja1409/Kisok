from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from app.schemas.v1 import ToolInfo
from app.tools.registry import get_tool_registry

router = APIRouter(prefix="/api/v1", tags=["Tools"])


@router.get("/tools")
async def list_tools(role: str | None = Query(default=None, description="Optional role filter")) -> list[dict[str, Any]]:
    """List registered controlled tools and their schemas."""
    registry = get_tool_registry()
    if role:
        return registry.list_tools_for_role(role)
    return registry.get_all_tools()
