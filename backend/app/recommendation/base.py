from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    title: str
    category: str
    description: str
    action_url: str | None = None
    priority: str = "Medium"  # "High", "Medium", "Low"


class RecommendationResult(BaseModel):
    recommendation_type: str
    items: list[RecommendationItem] = Field(default_factory=list)
    actionable_steps: list[str] = Field(default_factory=list)
