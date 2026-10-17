from __future__ import annotations

import logging
import time
from typing import Any
import httpx

from app.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class NIMProvider(BaseLLMProvider):
    """NVIDIA NIM provider with high-reasoning parameter support."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model: str = "moonshotai/kimi-k3",
        reasoning_effort: str = "max",
        max_tokens: int = 8192,
        timeout: int = 30,
    ) -> None:
        super().__init__(provider_name="nvidia_nim", timeout=timeout)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens

    async def is_healthy(self) -> bool:
        if not self.api_key or not self.api_key.strip():
            return False
        return True

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        if not await self.is_healthy():
            raise ValueError("NVIDIA NIM API key is not configured.")

        t0 = time.perf_counter()
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }
        if "kimi" in self.model.lower():
            payload["reasoning_effort"] = self.reasoning_effort

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - t0) * 1000.0
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "")
        reasoning = msg.get("reasoning_content")

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            reasoning_content=reasoning,
            provider_name=self.provider_name,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            raw_response=data,
        )
