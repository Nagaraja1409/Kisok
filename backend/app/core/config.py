from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "School AI Platform"
    school_name: str = Field(default="The School", alias="SCHOOL_NAME")
    environment: str = "production"
    log_level: str = "INFO"

    # ERP Configuration
    erp_mode: Literal["mock", "http"] = "mock"
    erp_base_url: str = Field(default="http://localhost:8080/api", alias="ERP_BASE_URL")
    erp_api_key: str = Field(default="", alias="ERP_API_KEY")
    data_dir: Path = ROOT_DIR / "data"

    # AI Providers
    ai_provider: str = Field(default="nvidia", alias="AI_PROVIDER")
    ai_timeout_seconds: int = Field(default=30, alias="AI_TIMEOUT_SECONDS")
    ai_max_context_records: int = Field(default=12, alias="AI_MAX_CONTEXT_RECORDS")

    # NVIDIA NIM
    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nim_api_key: str = Field(default="", alias="NIM_API_KEY")
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL"
    )
    nvidia_model: str = Field(
        default="moonshotai/kimi-k3", alias="NVIDIA_MODEL"
    )
    nvidia_reasoning_effort: str = Field(
        default="max", alias="NVIDIA_REASONING_EFFORT"
    )
    nvidia_max_tokens: int = Field(default=8192, alias="NVIDIA_MAX_TOKENS")

    # Groq
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL"
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile", alias="GROQ_MODEL"
    )

    # Deepgram Voice
    deepgram_api_key: str = Field(default="", alias="DEEPGRAM_API_KEY")

    # Qdrant Vector Database
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(
        default="school_knowledge", alias="QDRANT_COLLECTION"
    )

    @property
    def effective_nim_key(self) -> str:
        return self.nim_api_key or self.nvidia_api_key


@lru_cache
def get_core_settings() -> CoreSettings:
    return CoreSettings()
