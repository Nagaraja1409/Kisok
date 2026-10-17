from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])

VOICE_AGENT_PROMPT = """You are a general-purpose virtual assistant speaking to users over the phone.
Be warm, friendly, professional, concise, and natural. Keep most responses to one or two
sentences and under 120 characters unless the caller asks for detail. Do not use markdown.
Ask for clarification when needed. Never provide legal, financial, or medical advice; recommend
a licensed professional instead. Always ask if there is anything else you can help with before
closing, then thank the caller warmly. Start with: Hi there, I'm your virtual assistant—how can I help today?"""


def _voice_agent_settings() -> dict[str, Any]:
    return {
        "type": "Settings",
        "audio": {
            "input": {"encoding": "linear16", "sample_rate": 48000},
            "output": {"encoding": "linear16", "sample_rate": 24000, "container": "none"},
        },
        "agent": {
            "language": "en",
            "greeting": "Hello! How may I help you?",
            "listen": {"provider": {"type": "deepgram", "version": "v1", "model": "nova-3", "language": "en"}},
            # No endpoint or separate OpenAI key: Deepgram uses its managed LLM
            # service and authenticates the Voice Agent with DEEPGRAM_API_KEY.
            "think": {"provider": {"type": "open_ai", "model": "gpt-4o-mini"}, "prompt": VOICE_AGENT_PROMPT},
            "speak": {"provider": {"type": "deepgram", "version": "v2", "model": "flux-meena-en"}},
        },
    }


@router.websocket("/agent")
async def voice_agent(websocket: WebSocket) -> None:
    """Proxy browser PCM audio and Deepgram Voice Agent events without exposing API keys."""
    await websocket.accept()
    settings = get_settings()
    if not settings.voice_agent_enabled or not settings.deepgram_api_key:
        await websocket.send_json({"type": "Error", "message": "Deepgram Voice Agent is not configured."})
        await websocket.close(code=1013)
        return

    try:
        from deepgram import AsyncDeepgramClient
        from deepgram.agent.v1.types import AgentV1Settings
    except ImportError:
        await websocket.send_json({"type": "Error", "message": "deepgram-sdk is not installed."})
        await websocket.close(code=1011)
        return

    client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
    try:
        async with client.agent.v1.connect() as agent:
            # The SDK model validates and serializes the Settings payload for Agent v1.
            agent_settings = AgentV1Settings(**_voice_agent_settings())
            first = await agent.recv()
            first_type = getattr(first, "type", None) or (first.get("type") if isinstance(first, dict) else None)
            if first_type != "Welcome":
                await websocket.send_json({"type": "Error", "message": "Deepgram did not send a Welcome event."})
                return
            await agent.send_settings(agent_settings)
            applied = await agent.recv()
            applied_type = getattr(applied, "type", None) or (applied.get("type") if isinstance(applied, dict) else None)
            if applied_type != "SettingsApplied":
                await websocket.send_json({"type": "Error", "message": "Deepgram did not apply Voice Agent settings."})
                return
            await websocket.send_json({"type": "SettingsApplied"})

            async def browser_to_deepgram() -> None:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        return
                    if message.get("bytes"):
                        await agent.send_media(message["bytes"])
                    elif message.get("text"):
                        command = json.loads(message["text"])
                        if command.get("type") == "KeepAlive":
                            await agent.send_keep_alive()

            async def deepgram_to_browser() -> None:
                while True:
                    message = await agent.recv()
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        payload = message.model_dump(mode="json") if hasattr(message, "model_dump") else message.dict() if hasattr(message, "dict") else message
                        await websocket.send_json(payload)

            sender = asyncio.create_task(browser_to_deepgram())
            receiver = asyncio.create_task(deepgram_to_browser())
            done, pending = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except WebSocketDisconnect:
        logger.info("Voice Agent browser disconnected")
    except Exception as exc:
        logger.warning("Deepgram Voice Agent failed: %s", exc)
        try:
            await websocket.send_json({"type": "Error", "message": "Voice Agent connection failed."})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


class SpeakRequest(BaseModel):
    text: str
    model: str = "aura-asteria-en"


@router.get("/status")
async def voice_status(x_deepgram_key: str | None = Header(default=None)) -> dict[str, Any]:
    settings = get_settings()
    has_dg = bool(x_deepgram_key or settings.deepgram_api_key)
    has_groq = bool(settings.groq_api_key)
    return {
        "deepgram_available": has_dg,
        "voice_agent_available": bool(settings.voice_agent_enabled and has_dg),
        "groq_whisper_available": has_groq,
        "default_language": "en-IN",
        "language_label": "English (India) · en-IN",
        "recommended_voice": "flux-meena-en",
    }


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "en-IN",
    x_deepgram_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """Transcribe user audio into text using Deepgram SDK (with Groq Whisper fallback)."""
    settings = get_settings()
    dg_key = x_deepgram_key or settings.deepgram_api_key
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    # 1. Try Deepgram SDK if key provided
    if dg_key:
        try:
            from deepgram import DeepgramClient, PrerecordedOptions

            dg_client = DeepgramClient(dg_key)
            payload = {"buffer": content}
            options = PrerecordedOptions(
                model="nova-2",
                language=language or "en-IN",
                smart_format=True,
                punctuate=True,
            )
            response = dg_client.listen.rest.v("1").transcribe_file(payload, options)
            transcript = ""
            if response and response.results and response.results.channels:
                ch = response.results.channels[0]
                if ch.alternatives:
                    transcript = ch.alternatives[0].transcript

            if transcript.strip():
                return {
                    "text": transcript.strip(),
                    "provider": "deepgram",
                    "language": language or "en-IN",
                    "confidence": getattr(response.results.channels[0].alternatives[0], "confidence", 1.0)
                }
        except Exception as exc:
            logger.warning("Deepgram SDK transcription failed: %s; attempting fallback", exc)

    # 2. Fallback to Groq Whisper if Groq API key available
    if settings.groq_api_key:
        try:
            filename = file.filename or "audio.webm"
            files = {
                "file": (filename, content, file.content_type or "audio/webm"),
            }
            data = {
                "model": "whisper-large-v3",
                "language": "en",
                "temperature": "0.0",
                "prompt": "Indian English conversational campus speech",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    files=files,
                    data=data,
                )
                if res.status_code == 200:
                    resp_json = res.json()
                    transcribed = resp_json.get("text", "")
                    return {
                        "text": transcribed.strip(),
                        "provider": "groq_whisper",
                        "language": language or "en-IN",
                    }
                else:
                    logger.warning("Groq whisper error: %s %s", res.status_code, res.text)
        except Exception as exc:
            logger.warning("Groq whisper transcription failed: %s", exc)

    return {
        "text": "",
        "provider": "none",
        "error": "No voice recognition provider succeeded. Please check Deepgram or Groq API keys, or use browser speech."
    }


@router.post("/speak")
async def speak_text(
    body: SpeakRequest,
    x_deepgram_key: str | None = Header(default=None),
) -> Response:
    """Generate audio speech from text using Deepgram Aura TTS."""
    settings = get_settings()
    dg_key = x_deepgram_key or settings.deepgram_api_key
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text for TTS")

    # Clean text of markdown symbols before speaking
    import re
    clean_text = re.sub(r'[*_#`~\[\]\(\)]', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    # Limit TTS length for voice preview
    if len(clean_text) > 800:
        clean_text = clean_text[:800] + "..."

    if dg_key:
        try:
            url = f"https://api.deepgram.com/v1/speak?model={body.model or 'aura-asteria-en'}"
            headers = {
                "Authorization": f"Token {dg_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json={"text": clean_text})
                if resp.status_code == 200:
                    return Response(content=resp.content, media_type="audio/mpeg")
                else:
                    logger.warning("Deepgram TTS error %s: %s", resp.status_code, resp.text)
        except Exception as exc:
            logger.warning("Deepgram TTS failed: %s", exc)

    # Return 404 with fallback hint so client will use browser SpeechSynthesis
    return Response(
        content=b'{"fallback_browser": true}',
        media_type="application/json",
        status_code=404,
    )
