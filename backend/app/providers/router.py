from __future__ import annotations

import logging
from typing import Any, Literal

from app.core.config import CoreSettings, get_core_settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.providers.deterministic import DeterministicProvider
from app.providers.groq import GroqProvider
from app.providers.nim import NIMProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    """Manages LLM providers with automatic fallback and health monitoring."""

    def __init__(self, settings: CoreSettings | None = None) -> None:
        self.settings = settings or get_core_settings()
        self.nim = NIMProvider(
            api_key=self.settings.effective_nim_key,
            base_url=self.settings.nvidia_base_url,
            model=self.settings.nvidia_model,
            reasoning_effort=self.settings.nvidia_reasoning_effort,
            max_tokens=self.settings.nvidia_max_tokens,
            timeout=self.settings.ai_timeout_seconds,
        )
        self.groq = GroqProvider(
            api_key=self.settings.groq_api_key,
            base_url=self.settings.groq_base_url,
            model=self.settings.groq_model,
            timeout=self.settings.ai_timeout_seconds,
        )
        self.deterministic = DeterministicProvider()

    def get_provider_chain(self, preference: str | None = None) -> list[BaseLLMProvider]:
        pref = (preference or self.settings.ai_provider).lower()
        if pref in ("nvidia", "nim"):
            return [self.nim, self.groq, self.deterministic]
        elif pref == "groq":
            return [self.groq, self.nim, self.deterministic]
        elif pref == "deterministic":
            return [self.deterministic]
        else:
            return [self.nim, self.groq, self.deterministic]

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        preference: str | None = None,
    ) -> LLMResponse:
        chain = self.get_provider_chain(preference)
        last_error: Exception | None = None

        for provider in chain:
            if not await provider.is_healthy():
                continue
            try:
                response = await provider.generate_response(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                )
                return response
            except Exception as exc:
                logger.warning(
                    f"Provider {provider.provider_name} failed: {exc}. Trying next fallback..."
                )
                last_error = exc

        logger.info("All external providers exhausted; returning deterministic fallback.")
        return await self.deterministic.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

    async def get_health_status(self) -> dict[str, Any]:
        return {
            "nvidia_nim_configured": await self.nim.is_healthy(),
            "groq_configured": await self.groq.is_healthy(),
            "deterministic_active": True,
            "default_provider": self.settings.ai_provider,
        }
