from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    reasoning_content: str | None = None
    provider_name: str
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    raw_response: dict[str, Any] = Field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers (NVIDIA NIM, Groq, Fallback)."""

    def __init__(self, provider_name: str, timeout: int = 30) -> None:
        self.provider_name = provider_name
        self.timeout = timeout

    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate conversational completion."""
        ...

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check provider connectivity and configuration."""
        ...
