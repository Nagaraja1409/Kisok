import pytest
from app.ai.service import parse_response_and_suggestions, NvidiaKimiProvider
from app.config import get_settings
from app.models import ChatMessage, ChatRequest
from app.repositories.session_store import SessionStore


def test_parse_response_and_suggestions_clean():
    raw = """Based on your records, your next class is Science Lab at 09:30 AM in Room 204.
Please be sure to bring your lab coat and completed experiment worksheet.

Suggestions:
- What homework is due for Science Lab?
- Show my complete weekly timetable
- Who is the faculty in charge?
"""
    answer, suggestions = parse_response_and_suggestions(raw)
    assert "Science Lab at 09:30 AM" in answer
    assert "Suggestions:" not in answer
    assert len(suggestions) == 3
    assert suggestions[0] == "What homework is due for Science Lab?"
    assert suggestions[1] == "Show my complete weekly timetable"


def test_parse_response_with_trailing_questions():
    raw = """Here is your attendance summary: 92% present across 45 school days.
- How can I improve my attendance?
- Show attendance records by subject?
"""
    answer, suggestions = parse_response_and_suggestions(raw)
    assert "attendance summary: 92%" in answer
    assert len(suggestions) == 2
    assert "How can I improve my attendance?" in suggestions[0]


def test_session_store_reasoning_and_followup_persistence(tmp_path):
    db_file = tmp_path / "test_sessions.db"
    store = SessionStore(db_path=db_file)
    session = store.create_session("student", "Test Kimi Session")
    
    msg = store.add_message(
        session.session_id,
        "assistant",
        "Here is the study plan for Mathematics.",
        reasoning_content="Step 1: Check exam schedule. Step 2: Formulate 4-day revision schedule.",
        followup_questions=["Schedule Math practice quiz", "Show weak topics"]
    )
    
    assert msg.reasoning_content is not None
    assert "Step 1" in msg.reasoning_content
    assert len(msg.followup_questions) == 2
    
    # Retrieve and verify round-trip
    messages = store.get_messages(session.session_id)
    assert len(messages) == 1
    assert messages[0].reasoning_content == msg.reasoning_content
    assert messages[0].followup_questions == ["Schedule Math practice quiz", "Show weak topics"]


def test_nvidia_kimi_provider_initialization():
    settings = get_settings()
    provider = NvidiaKimiProvider(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="test-key",
        model="moonshotai/kimi-k3",
        reasoning_effort="max",
        max_tokens=16384,
    )
    assert provider.name == "nvidia"
    assert provider.model == "moonshotai/kimi-k3"
    assert provider.reasoning_effort == "max"
    assert provider.max_tokens == 16384


def test_chat_stream_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app, session_store
    client = TestClient(app)
    
    session = session_store.create_session("student", "Test Stream Session")
    resp = client.post("/api/chat/stream", json={
        "session_id": session.session_id,
        "message": "What is my fee balance?",
        "provider": "deterministic"
    })
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    text = resp.text
    assert "data: " in text
    assert '"type": "done"' in text
    assert '"type": "message_saved"' in text


@pytest.mark.asyncio
async def test_agent_stream_run_deterministic():
    from app.main import agent_engine
    chunks = []
    async for chunk in agent_engine.stream_run(
        role="visitor",
        question="What is the admission procedure?",
        provider_override="deterministic"
    ):
        chunks.append(chunk)
    assert len(chunks) >= 2
    types = [c.get("type") for c in chunks]
    assert "step" in types
    assert "done" in types
    done_chunk = next(c for c in chunks if c.get("type") == "done")
    assert len(done_chunk.get("answer", "")) > 10
    assert len(done_chunk.get("followup_questions", [])) > 0

