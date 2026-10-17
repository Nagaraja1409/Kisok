from __future__ import annotations

import logging
from typing import Any, Literal
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


class ProviderUpdateRequest(BaseModel):
    provider: Literal["auto", "groq", "nvidia", "deterministic"]


@router.get("/config")
async def get_admin_config() -> dict[str, Any]:
    """Return current LLM and system task mappings, providers, and health."""
    settings = get_settings()

    tasks = [
        {
            "id": "general_chat",
            "name": "General Chat & Student Copilot",
            "description": "Handles student and parent academic copilot, homework diagnostics, fee guidance, and multi-turn conversational reasoning.",
            "assigned_llm": "High-Reasoning LLM (Fast)",
            "model_identifier": settings.groq_model or "openai/gpt-oss-120b",
            "provider": "groq",
            "provider_label": "Groq Engine",
            "status": "Active" if settings.groq_api_key else "Configured",
            "latency": "< 0.8s"
        },
        {
            "id": "deep_reasoning",
            "name": "Deep Reasoning & Lesson Planning",
            "description": "Synthesizes complex curriculum blueprints, assessment matrices, and step-by-step mathematical reasoning.",
            "assigned_llm": "Deep Reasoning Kimi",
            "model_identifier": settings.nvidia_model or "moonshotai/kimi-k3",
            "provider": "nvidia",
            "provider_label": "NVIDIA NIM",
            "status": "Active" if settings.nvidia_api_key else "Configured",
            "latency": "~ 1.5s"
        },
        {
            "id": "document_vision",
            "name": "Visual Document Intelligence",
            "description": "Inspects uploaded student documents, transfer certificates, and birth certificates for validity and completeness.",
            "assigned_llm": "Multimodal Vision Kimi",
            "model_identifier": settings.nvidia_model or "moonshotai/kimi-k3",
            "provider": "nvidia",
            "provider_label": "NVIDIA NIM Vision",
            "status": "Active" if settings.nvidia_api_key else "Configured",
            "latency": "~ 2.0s"
        },
        {
            "id": "voice_stt",
            "name": "Speech-to-Text Recognition (STT)",
            "description": "Real-time voice capture tuned for Indian English pronunciation, accents, and school vocabulary.",
            "assigned_llm": "Deepgram Nova-2",
            "model_identifier": "nova-2 (language: en-IN)",
            "provider": "deepgram",
            "provider_label": "Deepgram Voice SDK",
            "status": "Active" if settings.deepgram_api_key else "Fallback Ready",
            "latency": "< 0.3s"
        },
        {
            "id": "voice_tts",
            "name": "Voice Narration & Synthesis (TTS)",
            "description": "Audio voice generation for reading responses aloud in natural Indian English accent.",
            "assigned_llm": "Deepgram Aura / WebSpeech",
            "model_identifier": "aura-asteria-en (en-IN)",
            "provider": "deepgram",
            "provider_label": "Deepgram Aura",
            "status": "Active",
            "latency": "< 0.4s"
        },
        {
            "id": "data_grounding",
            "name": "School Records Data Grounding",
            "description": "Deterministic retrieval from verified local school records (attendance, fee registers, timetables).",
            "assigned_llm": "CsvSchoolDataRepository",
            "model_identifier": "CSV Demonstration Store",
            "provider": "deterministic",
            "provider_label": "Local Data Store",
            "status": "Active",
            "latency": "< 0.05s"
        },
        {
            "id": "vector_rag",
            "name": "Semantic Knowledge Base (RAG)",
            "description": "Vector similarity search across campus policies, code of conduct, and administrative notices.",
            "assigned_llm": "Qdrant Vector Database",
            "model_identifier": "school_knowledge collection",
            "provider": "qdrant",
            "provider_label": "Qdrant Store",
            "status": "Active",
            "latency": "< 0.1s"
        }
    ]

    return {
        "app_name": settings.app_name,
        "school_name": settings.school_name,
        "current_default_provider": settings.ai_provider,
        "tasks": tasks,
        "providers_status": {
            "groq": {
                "name": "Groq High-Reasoning",
                "configured": bool(settings.groq_api_key),
                "model": settings.groq_model or "openai/gpt-oss-120b",
                "active_for": ["General Chat", "Follow-up Formulations"]
            },
            "nvidia": {
                "name": "NVIDIA NIM",
                "configured": bool(settings.nvidia_api_key),
                "model": settings.nvidia_model or "moonshotai/kimi-k3",
                "active_for": ["Deep Reasoning", "Multimodal Document Inspection"]
            },
            "deepgram": {
                "name": "Deepgram SDK",
                "configured": bool(settings.deepgram_api_key),
                "model": "nova-2 / aura-asteria-en",
                "language": "en-IN",
                "active_for": ["Indian English STT", "Voice Synthesis TTS"]
            }
        }
    }


@router.post("/set-provider")
async def set_default_provider(body: ProviderUpdateRequest) -> dict[str, Any]:
    """Change default LLM provider for the application."""
    settings = get_settings()
    settings.ai_provider = body.provider
    logger.info("Admin updated default AI provider to: %s", body.provider)
    return {
        "ok": True,
        "updated_provider": settings.ai_provider,
        "message": f"Default LLM provider updated to '{body.provider}'."
    }
