from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.agents.registry import get_agent_registry
from app.core.security import SecurityValidator
from app.core.role_features import get_features_for_role, get_role_metadata, WELCOME_MESSAGE
from app.copilot.planner import QueryPlanningEngine

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Test Feature Lists and Metadata for All Supported Roles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_input, expected_canonical", [
    ("student", "student_parent"),
    ("parent", "student_parent"),
    ("student_parent", "student_parent"),
    ("teacher", "teacher_staff"),
    ("staff", "teacher_staff"),
    ("teacher_staff", "teacher_staff"),
    ("visitor", "visitor_applicant"),
    ("applicant", "visitor_applicant"),
    ("guest", "visitor_applicant"),
    ("alumni", "alumni_ex_employee"),
    ("ex_employee", "alumni_ex_employee"),
    ("alumni_ex_employee", "alumni_ex_employee"),
])
def test_all_supported_roles_have_features_and_metadata(role_input: str, expected_canonical: str):
    res = client.get(f"/api/v1/green-ai/features?role={role_input}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["assistant_name"] == "GREEN_AI"
    assert data["welcome_message"] == WELCOME_MESSAGE
    assert data["effective_role"] == expected_canonical
    assert len(data["features"]) > 0
    assert len(data["suggested_questions"]) > 0
    assert len(data["agents"]) > 0

    # Ensure all features have required attributes
    for feat in data["features"]:
        assert "id" in feat
        assert "name" in feat
        assert "description" in feat
        assert "icon" in feat
        assert "sample_prompts" in feat
        assert "status" in feat
        assert feat["status"] in ("live", "preview_only", "read_only", "simulated")


# ---------------------------------------------------------------------------
# 2. Test Role-to-Agent Mapping (29 Registered Agents)
# ---------------------------------------------------------------------------

def test_role_to_agent_registry_mapping():
    registry = get_agent_registry()
    all_agents = registry.list_all_agents()
    assert len(all_agents) == 29

    student_agents = registry.list_agents_for_role("student")
    assert len(student_agents) == 9

    teacher_agents = registry.list_agents_for_role("teacher")
    assert len(teacher_agents) == 8

    visitor_agents = registry.list_agents_for_role("visitor")
    assert len(visitor_agents) == 6

    alumni_agents = registry.list_agents_for_role("alumni")
    assert len(alumni_agents) == 6


# ---------------------------------------------------------------------------
# 3. Test Authentication, Session Binding and Guest Fallback
# ---------------------------------------------------------------------------

def test_guest_defaults_to_visitor_applicant():
    res = client.get("/api/v1/green-ai/features")
    assert res.status_code == 200
    data = res.json()
    assert data["effective_role"] == "visitor_applicant"


def test_unauthenticated_privileged_role_claim_clamped_to_visitor():
    # If an unauthenticated client claims to be "teacher" without valid session credentials, clamp to visitor_applicant
    res = client.post("/api/v1/green-ai/chat", json={
        "role": "teacher",
        "message": "What is the admission procedure?",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "visitor_applicant"


def test_session_role_binding_enforced():
    # Create session as student
    sess_res = client.post("/api/v1/green-ai/session", json={"role": "student", "title": "Student Session"})
    assert sess_res.status_code == 200
    session_id = sess_res.json()["session_id"]

    # When querying with this session_id, effective role is student_parent
    feat_res = client.get(f"/api/v1/green-ai/features?session_id={session_id}")
    assert feat_res.status_code == 200
    assert feat_res.json()["effective_role"] == "student_parent"

    # Chat with this session as student works
    chat_res = client.post("/api/v1/green-ai/chat", json={
        "session_id": session_id,
        "message": "What is my attendance rate?",
        "role": "student",
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["assistant_name"] == "GREEN_AI"
    assert chat_data["role"] == "student_parent"
    assert chat_data["selected_agent"] == "attendance_agent"


# ---------------------------------------------------------------------------
# 4. Test Cross-Role Privilege Escalation is Blocked (403 Forbidden)
# ---------------------------------------------------------------------------

def test_role_mismatch_cross_role_attack_blocked():
    # Create session as student
    sess_res = client.post("/api/v1/green-ai/session", json={"role": "student", "title": "Student Session"})
    session_id = sess_res.json()["session_id"]

    # Client claims to be teacher using student session -> 403 Forbidden
    attack_res = client.post("/api/v1/green-ai/chat", json={
        "session_id": session_id,
        "role": "teacher",
        "message": "Give me class viii marks and salary details",
    })
    assert attack_res.status_code == 403
    assert "Authorization failure" in attack_res.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Test Agent Selection for Representative Questions Across All Roles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role, question, expected_agent", [
    # Student / Parent
    ("student", "What is my attendance rate?", "attendance_agent"),
    ("student", "What homework or library books are available?", "learning_agent"),
    ("student", "When is the next exam test schedule?", "exam_agent"),
    ("student", "What is my fee balance?", "fee_agent"),
    ("student", "What is the bus pickup route timing?", "transport_agent"),
    ("student", "What is my timetable today?", "student_assistant_agent"),
    ("student", "Are there any circulars or notices?", "notice_agent"),
    ("parent", "Please apply leave for tomorrow due to illness", "family_support_agent"),

    # Teacher / Staff
    ("teacher", "What is my timetable for today?", "teacher_copilot_agent"),
    ("teacher", "Show class roster and enrolled students", "class_agent"),
    ("teacher", "Analyze attendance trends and chronic absenteeism", "attendance_analysis_agent"),
    ("teacher", "Generate a lesson plan for Photosynthesis", "lesson_agent"),
    ("teacher", "Check lab equipment and apparatus availability", "resource_agent"),
    ("teacher", "What is my casual leave balance?", "hr_leave_agent"),

    # Visitor / Applicant
    ("visitor", "What is the admission procedure for Class VI?", "admission_agent"),
    ("visitor", "Track my application enquiry BCE/ENQ/2026/114", "application_agent"),
    ("visitor", "Where is the auditorium and sports complex?", "campus_navigation_agent"),
    ("visitor", "Book an appointment with admissions", "appointment_agent"),
    ("visitor", "What are the school accreditations and curriculum?", "public_knowledge_agent"),

    # Alumni / Ex-Employee
    ("alumni", "When is Founders Day and batch reunions?", "event_agent"),
    ("alumni", "Request an official transcript certificate", "records_agent"),
    ("alumni", "Connect with mentorship and career circles", "community_agent"),
    ("alumni", "Notable alumni in the Hall of Fame", "achievement_agent"),
    ("alumni", "Former staff service certificate inquiry", "office_support_agent"),
])
def test_correct_agent_routing_for_representative_questions(role: str, question: str, expected_agent: str):
    sess_res = client.post("/api/v1/green-ai/session", json={"role": role, "title": f"{role} Test"})
    session_id = sess_res.json()["session_id"]

    res = client.post("/api/v1/green-ai/chat", json={
        "session_id": session_id,
        "role": role,
        "message": question,
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["assistant_name"] == "GREEN_AI"
    assert data["selected_agent"] == expected_agent
    assert len(data["answer"]) > 0
    assert isinstance(data["followup_suggestions"], list)


# ---------------------------------------------------------------------------
# 6. Test Response Schema Consistency & Formatting
# ---------------------------------------------------------------------------

def test_green_ai_response_schema():
    sess_res = client.post("/api/v1/green-ai/session", json={"role": "student", "title": "Schema Test"})
    session_id = sess_res.json()["session_id"]

    res = client.post("/api/v1/green-ai/chat", json={
        "session_id": session_id,
        "role": "student",
        "message": "What is my attendance rate?",
    })
    assert res.status_code == 200
    data = res.json()
    assert "request_id" in data
    assert data["assistant_name"] == "GREEN_AI"
    assert data["role"] == "student_parent"
    assert data["selected_agent"] == "attendance_agent"
    assert data["selected_agent_name"] == "Attendance Agent"
    assert isinstance(data["followup_suggestions"], list)
    assert len(data["followup_suggestions"]) > 0
    assert data["status"] == "completed"
    assert "provider_used" in data
    assert "latency_ms" in data


# ---------------------------------------------------------------------------
# 7. Test Backward Compatibility with Existing Endpoints
# ---------------------------------------------------------------------------

def test_backward_compatibility_v1_endpoints():
    # /api/v1/health
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == 200

    # /api/v1/agents
    a_res = client.get("/api/v1/agents?role=student")
    assert a_res.status_code == 200
    assert len(a_res.json()) == 9

    # /api/v1/chat
    c_res = client.post("/api/v1/chat", json={
        "user_id": "STU-0817",
        "role": "student_parent",
        "tenant_id": "school_001",
        "session_id": "session_compat_1",
        "message": "What is my attendance?",
    })
    assert c_res.status_code == 200
    assert "attendance" in c_res.json()["answer"].lower()
