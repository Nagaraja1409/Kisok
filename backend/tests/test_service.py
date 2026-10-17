import pytest
from fastapi.testclient import TestClient

from app.main import ai, app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data_mode"] == "csv-first"


def test_all_roles_have_dashboard():
    for role in ("student", "parent", "teacher", "visitor", "alumni"):
        response = client.get(f"/api/dashboard/{role}")
        assert response.status_code == 200
        assert len(response.json()["cards"]) == 4


def test_student_answer_is_grounded():
    response = client.post("/api/ai/answer", json={"role": "student", "question": "What is my next class?", "provider": "deterministic"})
    assert response.status_code == 200
    body = response.json()
    assert "Room 204" in body["answer"]
    assert body["provider"] == "deterministic"
    assert body["sources"]


def test_role_feature_filter():
    response = client.get("/api/ai/features", params={"role": "visitor", "pillar": "Agentic AI"})
    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert "AI Admission Counsellor" in names
    assert "AI Study Planner" not in names


def test_payment_is_preview_only():
    response = client.post(
        "/api/requests/preview",
        json={
            "role": "parent",
            "user_ref": "PAR-0817",
            "request_type": "payment_guidance",
            "details": "Prepare the ₹18,500 fee balance guidance.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Prepared for review only"
    assert "not submitted" in body["safety_boundary"]


@pytest.mark.asyncio
async def test_provider_falls_back_without_key():
    orig_key = ai.groq.api_key
    ai.groq.api_key = ""
    try:
        response = await ai.answer(
            __import__("app.models", fromlist=["AIAnswerRequest"]).AIAnswerRequest(
                role="student", question="What is my fee balance?", provider="groq"
            )
        )
        assert response.provider == "deterministic-fallback"
        assert "₹" in response.answer
    finally:
        ai.groq.api_key = orig_key
