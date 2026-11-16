from __future__ import annotations

import logging
from typing import Any, Literal
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    agent_execution_node,
    audit_logger_node,
    copilot_node,
    planner_node,
    prediction_node,
    recommendation_node,
    response_synthesis_node,
)
from app.graph.state import OrchestratorState

logger = logging.getLogger(__name__)


def route_after_agents(state: OrchestratorState) -> Literal["prediction", "recommendation", "response_synthesis"]:
    """Dynamic routing decision after agent execution."""
    if state.get("needs_prediction"):
        return "prediction"
    if state.get("needs_recommendation"):
        return "recommendation"
    return "response_synthesis"


def route_after_prediction(state: OrchestratorState) -> Literal["recommendation", "response_synthesis"]:
    """Dynamic routing decision after prediction."""
    if state.get("needs_recommendation"):
        return "recommendation"
    return "response_synthesis"


def build_orchestrator_graph() -> Any:
    """Builds and compiles the Dynamic LangGraph Orchestrator."""
    builder = StateGraph(OrchestratorState)

    # 1. Register Nodes
    builder.add_node("copilot", copilot_node)
    builder.add_node("planner", planner_node)
    builder.add_node("agent_execution", agent_execution_node)
    builder.add_node("prediction", prediction_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("response_synthesis", response_synthesis_node)
    builder.add_node("audit_logger", audit_logger_node)

    # 2. Linear Edge: START -> copilot -> planner -> agent_execution
    builder.add_edge(START, "copilot")
    builder.add_edge("copilot", "planner")
    builder.add_edge("planner", "agent_execution")

    # 3. Dynamic Conditional Edges
    builder.add_conditional_edges(
        "agent_execution",
        route_after_agents,
        {
            "prediction": "prediction",
            "recommendation": "recommendation",
            "response_synthesis": "response_synthesis",
        },
    )

    builder.add_conditional_edges(
        "prediction",
        route_after_prediction,
        {
            "recommendation": "recommendation",
            "response_synthesis": "response_synthesis",
        },
    )

    builder.add_edge("recommendation", "response_synthesis")
    builder.add_edge("response_synthesis", "audit_logger")
    builder.add_edge("audit_logger", END)

    return builder.compile()


_COMPILED_GRAPH = None


def get_orchestrator_graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_orchestrator_graph()
    return _COMPILED_GRAPH
