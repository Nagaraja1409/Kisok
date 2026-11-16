from __future__ import annotations

import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dynamic_ui_context_attendance():
    payload = {
        "message": "What is my attendance rate?",
        "role": "student_parent",
        "session_id": "test_dyn_att_01",
        "ui_context": {
            "attendanceData": [
                {"month": "October", "classHeld": 30, "totalPresent": 21, "percentage": "70.0%"}
            ]
        }
    }
    res = client.post("/api/v1/green-ai/chat", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "70" in data["answer"]
    assert data["selected_agent"] == "attendance_agent"


def test_dynamic_ui_context_fees():
    payload = {
        "message": "Do I have pending fee balance?",
        "role": "student_parent",
        "session_id": "test_dyn_fee_01",
        "ui_context": {
            "feeData": [
                {"year": "2026-27", "receivable": 50000, "collection": 37500, "balance": 12500, "status": "Due"}
            ]
        }
    }
    res = client.post("/api/v1/green-ai/chat", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "12,500" in data["answer"] or "12500" in data["answer"]
    assert data["selected_agent"] == "fee_agent"


def test_dynamic_ui_context_staff_schedule():
    payload = {
        "message": "What are my classes today?",
        "role": "teacher_staff",
        "session_id": "test_dyn_staff_01",
        "ui_context": {
            "teachingSchedule": [
                {"day": "Monday", "period": "1", "time": "08:00 AM", "class": "Class 10 A", "subject": "Calculus", "room": "Rm 401"}
            ]
        }
    }
    res = client.post("/api/v1/green-ai/chat", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["selected_agent"] in ("teacher_copilot_agent", "class_agent")
