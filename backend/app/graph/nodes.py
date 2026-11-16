from __future__ import annotations

import logging
import time
from typing import Any

from app.agents.registry import get_agent_registry
from app.copilot.planner import QueryPlanningEngine
from app.core.logging import AgentAuditLog, get_audit_logger
from app.core.security import SecurityValidator
from app.engines.context_engine import get_context_engine
from app.engines.reasoning_engine import ReasoningEngine
from app.engines.response_engine import ResponseGenerationEngine
from app.engines.validation_engine import ValidationEngine
from app.graph.state import OrchestratorState
from app.prediction.base import PredictionResult
from app.prediction.engine import PredictionEngine
from app.providers.router import ProviderRouter
from app.recommendation.base import RecommendationResult
from app.recommendation.engine import RecommendationEngine

logger = logging.getLogger(__name__)


async def copilot_node(state: OrchestratorState) -> dict[str, Any]:
    """Copilot Intake: validates request and loads session context."""
    user_id = state.get("user_id", "")
    role = state.get("role", "visitor_applicant")
    tenant_id = state.get("tenant_id", "school_001")
    message = state.get("message", "")
    session_id = state.get("session_id", "default_session")

    is_valid, err_msg = ValidationEngine.validate_request(user_id, role, tenant_id, message)
    if not is_valid:
        return {"error": err_msg, "success": False}

    canonical_role = SecurityValidator.normalize_role(role)
    context_engine = get_context_engine()
    ctx = context_engine.get_or_create_session(session_id, user_id, canonical_role, tenant_id)
    ui_context = state.get("ui_context")
    if ui_context:
        context_engine.set_ui_context(user_id, ui_context)
        context_engine.set_ui_context(session_id, ui_context)

    return {
        "role": canonical_role,
        "success": True,
    }


async def planner_node(state: OrchestratorState) -> dict[str, Any]:
    """Dynamic Planner: constructs execution plan tailored to query complexity."""
    if state.get("error"):
        return {}

    message = state.get("message", "")
    role = state.get("role", "visitor_applicant")
    user_id = state.get("user_id", "")
    tenant_id = state.get("tenant_id", "school_001")

    plan = QueryPlanningEngine.create_plan(
        query=message,
        role=role,
        user_id=user_id,
        tenant_id=tenant_id,
    )

    return {
        "intent": plan.intent,
        "entities": plan.entities,
        "selected_agents": plan.selected_agents,
        "selected_tools": plan.selected_tools,
        "needs_prediction": plan.needs_prediction,
        "prediction_type": plan.prediction_type,
        "needs_recommendation": plan.needs_recommendation,
        "needs_rag": plan.needs_rag,
        "requires_confirmation": plan.requires_confirmation,
        "confirmation_message": plan.confirmation_message,
    }


async def agent_execution_node(state: OrchestratorState) -> dict[str, Any]:
    """Executes ONLY the agents selected by the dynamic planner."""
    if state.get("error"):
        return {}

    selected_agents = state.get("selected_agents", [])
    query = state.get("message", "")
    intent = state.get("intent", "general")
    entities = state.get("entities", {})
    user_id = state.get("user_id", "")
    tenant_id = state.get("tenant_id", "school_001")

    registry = get_agent_registry()
    agent_outputs = []
    combined_sources: list[dict[str, Any]] = []
    tool_data: Any = None
    requires_conf = state.get("requires_confirmation", False)
    conf_msg = state.get("confirmation_message")

    for agent_id in selected_agents:
        agent = registry.get_agent(agent_id)
        if not agent:
            continue
        try:
            output = await agent.process(query, intent, entities, user_id, tenant_id)
            agent_outputs.append(output.model_dump())
            combined_sources.extend(output.sources)
            if output.requires_confirmation:
                requires_conf = True
                conf_msg = output.confirmation_message

            for tr in output.tool_results:
                if tr.success and tr.data is not None:
                    tool_data = tr.data
        except Exception as exc:
            logger.error(f"Error executing agent {agent_id}: {exc}")

    return {
        "agent_outputs": agent_outputs,
        "sources": combined_sources,
        "tool_data": tool_data,
        "requires_confirmation": requires_conf,
        "confirmation_message": conf_msg,
    }


async def prediction_node(state: OrchestratorState) -> dict[str, Any]:
    """Executes statistical prediction ONLY when flagged by planning."""
    if state.get("error") or not state.get("needs_prediction"):
        return {"prediction": None}

    ptype = state.get("prediction_type", "attendance_risk")
    tool_data = state.get("tool_data")
    pred_result: PredictionResult | None = None

    if ptype == "attendance_risk":
        records = tool_data if isinstance(tool_data, list) else []
        pred_result = PredictionEngine.predict_attendance_risk(records)
    elif ptype == "academic_performance":
        records = tool_data if isinstance(tool_data, list) else []
        pred_result = PredictionEngine.predict_academic_performance(records)
    elif ptype == "class_performance":
        records = tool_data if isinstance(tool_data, list) else []
        pred_result = PredictionEngine.predict_class_performance(records)
    elif ptype == "admission_conversion":
        records = tool_data if isinstance(tool_data, list) else []
        pred_result = PredictionEngine.predict_admission_conversion(records)

    return {"prediction": pred_result.model_dump() if pred_result else None}


async def recommendation_node(state: OrchestratorState) -> dict[str, Any]:
    """Generates personalized action steps ONLY when flagged by planning."""
    if state.get("error") or not state.get("needs_recommendation"):
        return {"recommendation": None}

    intent = state.get("intent", "")
    role = state.get("role", "")
    pred_data = state.get("prediction")
    pred_obj = PredictionResult(**pred_data) if pred_data else None

    rec_result: RecommendationResult | None = None

    if "attendance" in intent:
        rec_result = RecommendationEngine.recommend_attendance_improvement(pred_obj)
    elif "marks" in intent or "academic" in intent:
        rec_result = RecommendationEngine.recommend_academic_study(prediction=pred_obj)
    elif "visitor" in role or "admission" in intent:
        rec_result = RecommendationEngine.recommend_visitor_next_steps(pred_obj)
    elif "alumni" in role:
        rec_result = RecommendationEngine.recommend_alumni_activities()
    elif "teacher" in role:
        rec_result = RecommendationEngine.recommend_teacher_interventions()
    else:
        rec_result = RecommendationEngine.recommend_attendance_improvement(pred_obj)

    return {"recommendation": rec_result.model_dump() if rec_result else None}


async def response_synthesis_node(state: OrchestratorState) -> dict[str, Any]:
    """Synthesizes human-friendly response and applies validation checks."""
    if state.get("error"):
        return {
            "final_answer": f"Error: {state.get('error')}",
            "reasoning_content": "Validation error prevented execution.",
            "provider_used": "system",
        }

    role = state.get("role", "visitor_applicant")
    query = state.get("message", "")
    intent = state.get("intent", "general")
    tool_data = state.get("tool_data")
    conf_msg = state.get("confirmation_message")

    pred_data = state.get("prediction")
    pred_obj = PredictionResult(**pred_data) if pred_data else None

    rec_data = state.get("recommendation")
    rec_obj = RecommendationResult(**rec_data) if rec_data else None

    # Step-by-step reasoning trace
    reasoning = ReasoningEngine.construct_reasoning(
        intent=intent,
        tool_data=tool_data,
        prediction=pred_obj,
        recommendation=rec_obj,
    )

    # Human-friendly response synthesis
    raw_answer = ResponseGenerationEngine.format_response(
        role=role,
        query=query,
        intent=intent,
        tool_data=tool_data,
        prediction=pred_obj,
        recommendation=rec_obj,
        confirmation_msg=conf_msg,
    )

    # Safety validation & Redaction
    safe_answer = ValidationEngine.validate_response_safety(raw_answer, role)

    followups = [
        "Would you like detailed records?",
        "Would you like guidance on next procedures?",
    ]

    return {
        "final_answer": safe_answer,
        "reasoning_content": reasoning,
        "followup_questions": followups,
        "provider_used": "deterministic-engine",
    }


async def audit_logger_node(state: OrchestratorState) -> dict[str, Any]:
    """Records structured audit trace."""
    logger_svc = get_audit_logger()
    entry = AgentAuditLog(
        request_id=f"req_{int(time.time()*1000)}",
        session_id=state.get("session_id", "unknown"),
        user_id=state.get("user_id", "unknown"),
        tenant_id=state.get("tenant_id", "school_001"),
        role=state.get("role", "unknown"),
        intent=state.get("intent", "unknown"),
        selected_agents=state.get("selected_agents", []),
        selected_tools=state.get("selected_tools", []),
        api_calls=state.get("selected_tools", []),
        model_provider=state.get("provider_used", "deterministic"),
        latency_ms=state.get("latency_ms", 12.5),
        token_usage={},
        success=state.get("success", True) and not bool(state.get("error")),
        error=state.get("error"),
        final_response_status="pending_confirmation" if state.get("requires_confirmation") else "completed",
        requires_confirmation=state.get("requires_confirmation", False),
    )
    logger_svc.log(entry)
    return {}
