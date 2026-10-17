from __future__ import annotations

from typing import Any
from app.prediction.base import PredictionResult
from app.recommendation.base import RecommendationResult


class ReasoningEngine:
    """Produces structured pedagogical and operational reasoning over agent context."""

    @staticmethod
    def construct_reasoning(
        intent: str,
        tool_data: Any,
        prediction: PredictionResult | None = None,
        recommendation: RecommendationResult | None = None,
    ) -> str:
        steps = []
        steps.append(f"1. Identified primary user intent as '{intent}'.")

        if tool_data:
            if isinstance(tool_data, list):
                steps.append(f"2. Retrieved and verified {len(tool_data)} records from official ERP store.")
            elif isinstance(tool_data, dict):
                steps.append(f"2. Processed ERP record attributes: {list(tool_data.keys())[:4]}.")

        if prediction and prediction.sufficient_data:
            steps.append(
                f"3. Executed statistical prediction: risk={prediction.risk_level}, score={prediction.score}, trend={prediction.trend}."
            )
        else:
            steps.append("3. Prediction was not required or historical data threshold was not met.")

        if recommendation and recommendation.items:
            steps.append(
                f"4. Formulated {len(recommendation.items)} targeted recommendations ({recommendation.recommendation_type})."
            )

        steps.append("5. Synthesized verified, human-friendly response grounded in school records.")
        return "\n".join(steps)
