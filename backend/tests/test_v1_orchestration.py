from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.copilot.planner import QueryPlanningEngine
from app.core.security import SecurityValidator
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test API Metadata Endpoints
# ---------------------------------------------------------------------------

def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "erp_mode" in data
    assert "ai_provider" in data
    assert "providers_health" in data


def test_api_v1_agents():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) >= 29  # 9 student + 8 teacher + 6 visitor + 6 alumni

    # Test role filtering
    resp_student = client.get("/api/v1/agents?role=student_parent")
    assert resp_student.status_code == 200
    student_agent_ids = {a["agent_id"] for a in resp_student.json()}
    assert "attendance_agent" in student_agent_ids
    assert "academic_agent" in student_agent_ids
    assert "fee_agent" in student_agent_ids
    assert "teacher_copilot_agent" not in student_agent_ids


def test_api_v1_tools():
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    tools = response.json()
    tool_names = {t["name"] for t in tools}
    assert "get_student_attendance" in tool_names
    assert "get_student_marks" in tool_names
    assert "get_fee_details" in tool_names
    assert "get_timetable" in tool_names
    assert "rag_retrieval" in tool_names


# ---------------------------------------------------------------------------
# Scenario 1: Factual / Minimal Query (Tomorrow's school timing)
# ---------------------------------------------------------------------------

def test_scenario_1_minimal_factual_query():
    """Query: 'What is tomorrow's school timing?'
    
    Verifies:
    - Intent: timetable
    - Agents: student_assistant_agent
    - Tools: get_timetable
    - Prediction NOT called (needs_prediction = False)
    - Recommendation NOT called (needs_recommendation = False)
    """
    plan = QueryPlanningEngine.create_plan(
        query="What is tomorrow's school timing?",
        role="student_parent",
        user_id="STU-1001",
        tenant_id="school_001",
    )
    assert plan.intent == "timetable"
    assert plan.selected_agents == ["student_assistant_agent"]
    assert plan.selected_tools == ["get_timetable"]
    assert not plan.needs_prediction
    assert not plan.needs_recommendation

    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "STU-1001",
            "role": "student_parent",
            "tenant_id": "school_001",
            "session_id": "sess_timing_01",
            "message": "What is tomorrow's school timing?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "timing" in data["answer"].lower() or "08:30" in data["answer"]
    assert "student_assistant_agent" in data["agents_used"]


# ---------------------------------------------------------------------------
# Scenario 2: Attendance Diagnostic Query (Why is my child's attendance low?)
# ---------------------------------------------------------------------------

def test_scenario_2_attendance_diagnostic():
    """Query: 'Why is my child's attendance low?'
    
    Verifies:
    - Intent: attendance_analysis
    - Agents: attendance_agent
    - Tool: get_student_attendance
    - Prediction Engine IS invoked (needs_prediction = True)
    - Recommendation NOT invoked
    """
    plan = QueryPlanningEngine.create_plan(
        query="Why is my child's attendance low?",
        role="student_parent",
        user_id="STU-1001",
        tenant_id="school_001",
    )
    assert plan.intent == "attendance_analysis"
    assert "attendance_agent" in plan.selected_agents
    assert "get_student_attendance" in plan.selected_tools
    assert plan.needs_prediction
    assert plan.prediction_type == "attendance_risk"
    assert not plan.needs_recommendation

    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "STU-1001",
            "role": "student_parent",
            "tenant_id": "school_001",
            "session_id": "sess_att_diag",
            "message": "Why is my child's attendance low?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "attendance" in data["answer"].lower()
    assert "Risk" in data["answer"]
    assert "attendance_agent" in data["agents_used"]


# ---------------------------------------------------------------------------
# Scenario 3: Complex Multi-Engine Query (Low attendance + Recommendation)
# ---------------------------------------------------------------------------

def test_scenario_3_attendance_with_recommendations():
    """Query: 'Why is my child's attendance low and what should we do?'
    
    Verifies:
    - Intent: attendance_analysis
    - Agents: attendance_agent
    - Tool: get_student_attendance
    - Prediction Engine IS invoked (needs_prediction = True)
    - Recommendation Engine IS dynamically invoked (needs_recommendation = True)
    """
    plan = QueryPlanningEngine.create_plan(
        query="Why is my child's attendance low and what should we do?",
        role="student_parent",
        user_id="STU-1001",
        tenant_id="school_001",
    )
    assert plan.intent == "attendance_analysis"
    assert "attendance_agent" in plan.selected_agents
    assert plan.needs_prediction
    assert plan.needs_recommendation

    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "STU-1001",
            "role": "student_parent",
            "tenant_id": "school_001",
            "session_id": "sess_att_rec",
            "message": "Why is my child's attendance low and what should we do?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "attendance" in data["answer"].lower()
    assert "Risk" in data["answer"]
    assert "Recommended Action Plan" in data["answer"]


# ---------------------------------------------------------------------------
# Scenario 4: Policy / RAG Query
# ---------------------------------------------------------------------------

def test_scenario_4_policy_rag_query():
    """Query: 'What is the school fee payment policy and late fee?'
    
    Verifies:
    - RAG retrieval is triggered
    - Sources returned with policy references
    """
    plan = QueryPlanningEngine.create_plan(
        query="What is the school fee payment policy and circular?",
        role="student_parent",
        user_id="STU-1001",
        tenant_id="school_001",
    )
    assert plan.needs_rag

    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "STU-1001",
            "role": "student_parent",
            "tenant_id": "school_001",
            "session_id": "sess_policy_01",
            "message": "What is the school fee payment policy and circular?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) > 0


# ---------------------------------------------------------------------------
# Scenario 5: Sensitive State Mutation / Human Approval
# ---------------------------------------------------------------------------

def test_scenario_5_human_approval_leave_request():
    """Query: 'Apply leave for tomorrow.'
    
    Verifies:
    - Requires confirmation flag is set
    - Preview message formulated
    - Action item returned in response
    - Does NOT mutate data without user confirmation
    """
    plan = QueryPlanningEngine.create_plan(
        query="Apply leave for tomorrow due to fever.",
        role="student_parent",
        user_id="STU-1001",
        tenant_id="school_001",
    )
    assert plan.requires_confirmation
    assert plan.confirmation_message is not None
    assert "Would you like me to submit it?" in plan.confirmation_message

    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "STU-1001",
            "role": "student_parent",
            "tenant_id": "school_001",
            "session_id": "sess_leave_01",
            "message": "Apply leave for tomorrow due to fever.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["actions"]) == 1
    assert data["actions"][0]["action_type"] == "confirm_sensitive_request"
    assert data["actions"][0]["status"] == "pending_human_approval"
    assert "Would you like me to submit it?" in data["answer"]


# ---------------------------------------------------------------------------
# Scenario 6: Role Permission Boundary Enforcement
# ---------------------------------------------------------------------------

def test_scenario_6_role_permission_boundary():
    """Student cannot access teacher HR / salary records or another student's data."""
    # 1. Student accessing HR resource
    allowed, msg = SecurityValidator.validate_data_access(
        requester_role="student_parent",
        requester_user_id="STU-1001",
        target_resource="hr",
    )
    assert not allowed
    assert "not authorized" in msg

    # 2. Student accessing another student's data
    allowed_other, msg_other = SecurityValidator.validate_data_access(
        requester_role="student_parent",
        requester_user_id="STU-1001",
        target_resource="student_marks",
        target_user_id="STU-9999",
    )
    assert not allowed_other
    assert "cannot access records of other students" in msg_other
