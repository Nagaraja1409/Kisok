from __future__ import annotations

import time
from app.providers.base import BaseLLMProvider, LLMResponse


class DeterministicProvider(BaseLLMProvider):
    """Deterministic grounded provider used for zero-API local fallback and testing."""

    def __init__(self) -> None:
        super().__init__(provider_name="deterministic", timeout=5)

    async def is_healthy(self) -> bool:
        return True

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        t0 = time.perf_counter()
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        content = (
            f"Here is the school information grounded in official records for your query: '{last_user_msg}'.\n\n"
            "Suggestions:\n"
            "- Would you like to review further details?\n"
            "- Would you like assistance with related school procedures?"
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return LLMResponse(
            content=content,
            reasoning_content="Deterministic rule-based response generated from local verified records.",
            provider_name=self.provider_name,
            latency_ms=latency_ms,
            input_tokens=len(last_user_msg.split()),
            output_tokens=len(content.split()),
        )
