import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_voice_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/voice/status")
        assert res.status_code == 200
        data = res.json()
        assert "default_language" in data
        assert data["default_language"] == "en-IN"
        assert "recommended_voice" in data
        assert data["recommended_voice"] == "flux-meena-en"
        assert "voice_agent_available" in data


@pytest.mark.asyncio
async def test_voice_speak_fallback():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/voice/speak", json={"text": "Hello campus assistant!"})
        assert res.status_code in (200, 404)
        if res.status_code == 404:
            assert res.json().get("fallback_browser") is True


@pytest.mark.asyncio
async def test_voice_transcribe_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("empty.wav", b"", "audio/wav")}
        res = await client.post("/api/voice/transcribe", files=files)
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_html_ui_renders_gemini_thinking_and_voice():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text
        # Verify Gemini thinking and down/up arrow toggle elements
        assert "gemini-thinking-block" in html
        assert "thinking-chevron-arrow" in html
        # Verify voice interactive elements
        assert "voice-interactive-banner" in html
        assert "en-IN" in html
        assert "dock-mic-btn" in html
        assert "voice-audio-pill" in html
        # Verify right-side Gemini Live Voice Assistant UI elements
        assert "gemini-voice-panel" in html
        assert "gemini-fluid-orb" in html
        assert "gemini-live-mic-btn" in html
        assert "voice-stage-container" in html
        assert "voice-transcript-feed" in html
        assert "gemini-eq-bars" in html
        assert "handsFreeCheck" in html
        # Verify VAPS AI branding
        assert "VAPS AI" in html
        assert "VAPS AI Agent" in html
        # Verify link to /admin exists
        assert "/admin" in html


@pytest.mark.asyncio
async def test_admin_page_and_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test /admin HTML page
        res = await client.get("/admin")
        assert res.status_code == 200
        assert "LLM Task Configuration Matrix" in res.text
        assert "tasksTableBody" in res.text

        # 2. Test /api/admin/config
        cfg_res = await client.get("/api/admin/config")
        assert cfg_res.status_code == 200
        cfg_data = cfg_res.json()
        assert "tasks" in cfg_data
        assert len(cfg_data["tasks"]) >= 5
        task_names = [t["name"] for t in cfg_data["tasks"]]
        assert any("General Chat" in n for n in task_names)
        assert any("Deep Reasoning" in n for n in task_names)
        assert any("Speech-to-Text" in n for n in task_names)

        # 3. Test /api/admin/set-provider
        update_res = await client.post("/api/admin/set-provider", json={"provider": "groq"})
        assert update_res.status_code == 200
        assert update_res.json().get("ok") is True
        assert update_res.json().get("updated_provider") == "groq"
