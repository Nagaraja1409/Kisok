from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    prediction_type: str
    risk_level: str  # "Low", "Medium", "High", "Unknown"
    score: float = 0.0
    trend: str = "Stable"
    insights: list[str] = Field(default_factory=list)
    confidence: float = 0.85
    sufficient_data: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
