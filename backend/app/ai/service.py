from __future__ import annotations

from typing import Any, AsyncGenerator
import json

import httpx

from app.config import Settings
from app.models import AIAnswer, AIAnswerRequest, SchoolContext, SourceRecord
from app.repositories.csv_repository import CsvSchoolDataRepository

FEATURES = [
    ("Intelligence", "AI Personal Academic Copilot", ["student", "parent"]),
    ("Intelligence", "Predictive Analytics", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Intelligence", "AI Student Risk Detection", ["teacher"]),
    ("Intelligence", "Intent Detection", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Intelligence", "AI Recommendation Engine", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Agentic AI", "AI Task Preparation", ["teacher"]),
    ("Agentic AI", "AI Workflow Agent", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Agentic AI", "AI Admission Counsellor", ["parent", "visitor"]),
    ("Agentic AI", "AI Study Planner", ["student", "parent", "teacher"]),
    ("Agentic AI", "AI Request Agent", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Multimodal AI", "AI Document Pre-Check", ["parent", "visitor"]),
    ("Multimodal AI", "AI Voice Assistant", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Multimodal AI", "AI Image Understanding", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Multimodal AI", "AI Campus Vision Assistant", ["visitor", "student", "parent", "teacher"]),
    ("Multimodal AI", "AI Multilingual Assistant", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Knowledge AI", "AI RAG Knowledge Assistant", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Knowledge AI", "AI Institutional Knowledge Search", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Knowledge AI", "AI Document Summarizer", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Knowledge AI", "AI Library Assistant", ["student", "parent", "teacher", "alumni"]),
    (
        "Knowledge AI",
        "AI Historical / Alumni Knowledge Assistant",
        ["student", "parent", "teacher", "visitor", "alumni"],
    ),
    ("Personalization", "AI Personalized Daily Digest", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Personalization", "AI Personalized Learning", ["student", "parent", "teacher"]),
    ("Personalization", "AI Personalized Notifications", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Personalization", "AI Personalized Recommendations", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Personalization", "AI Role-Based AI Experience", ["student", "parent", "teacher", "visitor", "alumni"]),
    ("Predictive AI", "AI Student Performance Prediction", ["student", "parent", "teacher"]),
    ("Predictive AI", "AI Attendance Risk Prediction", ["student", "parent", "teacher"]),
    ("Predictive AI", "AI Admission Conversion Prediction", ["visitor"]),
    ("Predictive AI", "AI Resource Demand Prediction", ["teacher"]),
    ("Predictive AI", "AI Engagement Prediction", ["teacher", "alumni"]),
]

KEYWORDS = {
    "timetable": ["timetable", "next class", "period", "science lab", "room"],
    "homework": ["homework", "assignment", "due", "study"],
    "attendance": ["attendance", "absent", "present"],
    "fees": ["fee", "fees", "balance", "installment", "payment", "receipt", "upi", "bank"],
    "exams": ["exam", "score", "marks", "test", "hall ticket"],
    "library": ["book", "library", "rack", "borrow"],
    "admission": ["admission", "enquiry", "counselling", "document", "application"],
    "events": ["event", "founders", "annual day", "sports", "holiday", "notice"],
    "hostel": ["hostel", "room", "warden", "residence"],
}


import asyncio
import re


def parse_response_and_suggestions(raw_text: str) -> tuple[str, list[str]]:
    """Split response into main answer content and structured follow-up suggestions."""
    if not raw_text:
        return "", []
    
    text = raw_text.strip()
    followups: list[str] = []
    
    # Check for Suggestions / Next Questions section at the end
    pattern = r"(?i)(?:\n\n|\n)(?:###?\s*(?:Suggestions|Recommended Follow-ups|Suggested Next Steps|Follow-up Questions|Next Steps)|(?:\*{1,2}(?:Suggestions|Recommended Follow-ups|Suggested Next Steps|Follow-up Questions|Next Steps)\*{1,2}:?|Suggestions:))\s*\n([\s\S]*)$"
    match = re.search(pattern, text)
    if match:
        main_content = text[: match.start()].strip()
        suggestions_block = match.group(1).strip()
        lines = [line.strip() for line in suggestions_block.split("\n") if line.strip()]
        for line in lines:
            cleaned = re.sub(r"^[-*•\d\.\)]+\s*", "", line).strip()
            # remove surrounding quotes
            cleaned = re.sub(r'^["\']|["\']$', "", cleaned).strip()
            if cleaned and len(cleaned) > 5 and len(cleaned) < 120:
                followups.append(cleaned)
        if main_content:
            return main_content, followups[:3]

    # Best-effort extract trailing questions if formatted as bullet points
    lines = text.split("\n")
    trailing_q = []
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-*•]\s+.*\?\s*$", stripped):
            q_text = re.sub(r"^[-*•]\s*", "", stripped).strip()
            if len(q_text) < 120:
                trailing_q.append(q_text)
                continue
        content_lines.append(line)

    if trailing_q and len(trailing_q) <= 3 and len(content_lines) >= 1:
        return "\n".join(content_lines).strip(), trailing_q[:3]

    return text, []


class DeterministicProvider:
    name = "deterministic"

    async def generate(self, question: str, context: SchoolContext) -> str:
        return ""


def _get_chat_completions_url(base_url: str) -> str:
    url = (base_url or "https://api.groq.com").rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    if url.endswith("/openai"):
        return f"{url}/v1/chat/completions"
    return f"{url}/openai/v1/chat/completions"


class GroqProvider:
    """High-reasoning, ultra-fast provider for Groq (openai/gpt-oss-120b)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        timeout: int = 25,
    ):
        self.name = "groq"
        self.base_url = base_url.rstrip("/") if base_url else "https://api.groq.com"
        self.api_key = api_key
        self.model = model or "openai/gpt-oss-120b"
        self.timeout = timeout

    def _endpoint(self) -> str:
        return _get_chat_completions_url(self.base_url)

    async def generate_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> dict[str, Any]:
        if not self.api_key or not self.model:
            raise RuntimeError("Groq provider not configured")

        formatted_messages = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if p.get("type") == "text"]
                formatted_messages.append({"role": m.get("role", "user"), "content": " ".join(text_parts)})
            else:
                formatted_messages.append({"role": m.get("role", "user"), "content": str(content)})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self._endpoint(), headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]["message"]
            raw_content = choice.get("content") or ""
            reasoning = choice.get("reasoning") or choice.get("reasoning_content") or ""

            cleaned_content, suggestions = parse_response_and_suggestions(raw_content)
            return {
                "content": cleaned_content,
                "reasoning_content": reasoning,
                "followup_questions": suggestions,
                "model": self.model,
            }

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> AsyncGenerator[dict[str, Any], None]:
        if not self.api_key or not self.model:
            raise RuntimeError("Groq provider not configured")

        formatted_messages = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if p.get("type") == "text"]
                formatted_messages.append({"role": m.get("role", "user"), "content": " ".join(text_parts)})
            else:
                formatted_messages.append({"role": m.get("role", "user"), "content": str(content)})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self._endpoint(), headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        r_delta = delta.get("reasoning") or delta.get("reasoning_content") or ""
                        c_delta = delta.get("content") or ""
                        if r_delta or c_delta:
                            yield {
                                "reasoning_chunk": r_delta,
                                "content_chunk": c_delta,
                            }
                    except Exception:
                        continue

    async def generate(self, question: str, context: SchoolContext) -> str:
        prompt = (
            "You are the VAPS AI Agent for the campus kiosk. Answer warmly, deeply, and helpfully based on the school context.\n"
            f"Role: {context.role}\nRecords: {context.records}\nQuestion: {question}\n"
            "At the end, suggest 2 helpful follow-up questions under 'Suggestions:'."
        )
        res = await self.generate_chat([{"role": "user", "content": prompt}])
        return res["content"]


class OpenAICompatibleProvider:
    def __init__(self, name: str, base_url: str, api_key: str, model: str, timeout: int):
        self.name, self.base_url, self.api_key, self.model = name, base_url, api_key, model
        self.timeout = timeout

    async def generate(self, question: str, context: SchoolContext) -> str:
        if not self.api_key or not self.model:
            raise RuntimeError("provider not configured")
        prompt = (
            "Answer only from the supplied school records. If absent, say it is unavailable. Return concise guidance.\n"
        )
        prompt += f"Role: {context.role}\nRecords: {context.records}\nQuestion: {question}"
        endpoint = _get_chat_completions_url(self.base_url)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class NvidiaKimiProvider:
    """High-reasoning, multimodal provider for Moonshot AI Kimi-K3 via NVIDIA NIM."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "moonshotai/kimi-k3",
        reasoning_effort: str = "max",
        max_tokens: int = 16384,
        timeout: int = 15,
    ):
        self.name = "nvidia"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def generate_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        image_base64: str | None = None,
        image_url: str | None = None,
        temperature: float = 1.0,
    ) -> dict[str, Any]:
        """Invoke Kimi-K3 with reasoning_effort='max' and optional multimodal image input."""
        if not self.api_key:
            raise RuntimeError("NVIDIA API key not configured")

        formatted_messages = []
        for idx, m in enumerate(messages):
            role = m.get("role", "user")
            content = m.get("content", "")
            # If this is the last user message and an image is attached, structure as multimodal content array
            if role == "user" and idx == len(messages) - 1 and (image_base64 or image_url):
                content_parts: list[dict[str, Any]] = [{"type": "text", "text": content}]
                if image_url:
                    content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
                elif image_base64:
                    # Detect format or default to jpeg data URI
                    prefix = "data:image/jpeg;base64,"
                    if image_base64.startswith("data:"):
                        img_uri = image_base64
                    else:
                        img_uri = f"{prefix}{image_base64}"
                    content_parts.append({"type": "image_url", "image_url": {"url": img_uri}})
                formatted_messages.append({"role": role, "content": content_parts})
            else:
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "seed": 0,
            "temperature": temperature,
            "reasoning_effort": self.reasoning_effort,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Attempt call with fast fallback
        last_error: Exception | None = None
        for attempt in range(1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code == 429:
                        response.raise_for_status()
                    response.raise_for_status()
                    data = response.json()
                    choice = data["choices"][0]["message"]
                    raw_content = choice.get("content") or ""
                    reasoning = choice.get("reasoning_content") or ""

                    # Check for inline <think> tags if reasoning_content was empty
                    if not reasoning and "<think>" in raw_content:
                        think_match = re.search(r"<think>([\s\S]*?)</think>", raw_content)
                        if think_match:
                            reasoning = think_match.group(1).strip()
                            raw_content = re.sub(r"<think>[\s\S]*?</think>", "", raw_content).strip()

                    cleaned_content, suggestions = parse_response_and_suggestions(raw_content)

                    return {
                        "content": cleaned_content,
                        "reasoning_content": reasoning,
                        "followup_questions": suggestions,
                        "model": self.model,
                    }
            except Exception as exc:
                last_error = exc

        if last_error:
            raise last_error
        raise RuntimeError("Failed to invoke NVIDIA Kimi-K3")

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        image_base64: str | None = None,
        image_url: str | None = None,
        temperature: float = 1.0,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chunks from Kimi-K3 via NVIDIA NIM SSE."""
        if not self.api_key:
            raise RuntimeError("NVIDIA API key not configured")

        formatted_messages = []
        for idx, m in enumerate(messages):
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "user" and idx == len(messages) - 1 and (image_base64 or image_url):
                content_parts: list[dict[str, Any]] = [{"type": "text", "text": content}]
                if image_url:
                    content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
                elif image_base64:
                    prefix = "data:image/jpeg;base64,"
                    img_uri = image_base64 if image_base64.startswith("data:") else f"{prefix}{image_base64}"
                    content_parts.append({"type": "image_url", "image_url": {"url": img_uri}})
                formatted_messages.append({"role": role, "content": content_parts})
            else:
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "seed": 0,
            "temperature": temperature,
            "stream": True,
            "reasoning_effort": self.reasoning_effort,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        reasoning_delta = delta.get("reasoning_content") or ""
                        content_delta = delta.get("content") or ""
                        if reasoning_delta or content_delta:
                            yield {
                                "reasoning_chunk": reasoning_delta,
                                "content_chunk": content_delta,
                            }
                    except Exception:
                        continue

    async def generate(self, question: str, context: SchoolContext) -> str:
        prompt = (
            "You are the School AI Copilot. Answer clearly and warmly based only on the supplied school records.\n"
            f"Role: {context.role}\nRecords: {context.records}\nQuestion: {question}\n"
            "At the end, suggest 2 helpful follow-up questions starting with 'Suggestions:'."
        )
        res = await self.generate_chat([{"role": "user", "content": prompt}])
        return res["content"]


class AIService:
    def __init__(self, repository: CsvSchoolDataRepository, settings: Settings):
        self.repository, self.settings = repository, settings
        self.groq = GroqProvider(
            settings.groq_base_url,
            settings.groq_api_key,
            settings.groq_model or "openai/gpt-oss-120b",
            settings.ai_timeout_seconds,
        )
        self.nvidia = NvidiaKimiProvider(
            settings.nvidia_base_url,
            settings.nvidia_api_key,
            settings.nvidia_model or "moonshotai/kimi-k3",
            settings.nvidia_reasoning_effort or "max",
            settings.nvidia_max_tokens or 16384,
            settings.ai_timeout_seconds,
        )

    def features(self, role: str, pillar: str | None = None) -> list[dict[str, Any]]:
        return [
            {"pillar": p, "name": n, "roles": roles, "eligible": role in roles}
            for p, n, roles in FEATURES
            if role in roles and (not pillar or p == pillar)
        ]

    def intent(self, question: str) -> str:
        q = question.lower()
        for name, terms in KEYWORDS.items():
            if any(term in q for term in terms):
                return name
        return "general"

    def _answer(self, role: str, intent: str, records: list[dict[str, Any]]) -> tuple[str, str]:
        if intent == "timetable" and records:
            row = next((r for r in records if r.get("subject") == "Science Lab"), records[0])
            return (
                f"Your next timetable record is {row.get('subject', 'the scheduled class')} at {row.get('time', 'the listed time')} in {row.get('room', 'the listed room')}.",
                "Open TimeTable",
            )
        if intent == "homework" and records:
            row = records[0]
            return (
                f"The current assignment is {row.get('assignment', 'listed in Homework')} for {row.get('subject', 'your subject')}, due {row.get('due', 'the listed date')}.",
                "Open Homework",
            )
        if intent == "attendance" and records:
            summary = next((r for r in records if r.get("percentage")), records[0])
            return (
                f"Attendance record: {summary.get('percentage', summary.get('status', 'review the attendance table'))}. The detailed register is available by date and period.",
                "Open Attendance",
            )
        if intent == "fees" and records:
            due = next((r for r in records if r.get("status") == "Due"), records[0])
            return (
                f"Fee guidance: ₹{due.get('amount', due.get('fee_balance', '18,500'))} is due by {due.get('due_date', '15 September 2026')}. Payment guidance is view-only and no payment was initiated.",
                "Prepare payment request preview",
            )
        if intent == "exams" and records:
            row = records[0]
            return (
                f"Exam information: {row.get('subject', 'the next subject')} is scheduled for {row.get('date', 'the listed date')} at {row.get('session', 'the listed session')}.",
                "Open Exams",
            )
        if intent == "library" and records:
            row = records[0]
            return (
                f"Library match: {row.get('title', 'a school library title')} is listed at {row.get('rack', 'the listed rack')} on {row.get('floor', 'the listed floor')}; availability is {row.get('availability', 'shown in the table')}.",
                "Open Library",
            )
        if intent == "admission" and records:
            row = records[0]
            return (
                f"Admission guidance: reference {row.get('enquiry_id', row.get('application_id', 'BCE/ENQ/2026/114'))} is {row.get('status', 'under review')}. Next step: {row.get('next_step', row.get('counselling', 'contact the Front Office'))}.",
                "Open Admission",
            )
        if intent == "events" and records:
            row = records[0]
            return (
                f"Upcoming school information: {row.get('title', 'school event')} on {row.get('date', 'the listed date')} at {row.get('time', 'the listed time')} in {row.get('venue', row.get('location', 'the listed venue'))}.",
                "Open Events & Notices",
            )
        return (
            f"School information is available for the {role} route. Select a feature or ask about timetable, homework, attendance, fees, exams, library, admission, events, sports, hostel, or notices.",
            "Open AI Features",
        )

    async def answer(self, request: AIAnswerRequest) -> AIAnswer:
        context = self.repository.get_context(request.role, request.user_ref)
        intent = self.intent(request.question)
        records = self.repository.search(request.role, request.user_ref, request.question)
        if not records and intent in context.records:
            records = [{"module": intent, **row} for row in context.records[intent][:3]]
        answer, next_action = self._answer(request.role, intent, records)
        provider_name = "deterministic"
        reasoning_content: str | None = None
        followup_questions: list[str] = []

        chosen_provider = request.provider
        if chosen_provider == "auto":
            chosen_provider = self.settings.ai_provider

        if chosen_provider in {"groq", "nvidia"} and chosen_provider != "deterministic":
            provider = self.nvidia if chosen_provider == "nvidia" else self.groq
            if provider is not None:
                try:
                    if isinstance(provider, NvidiaKimiProvider):
                        prompt = (
                            "You are the School AI Copilot. Answer clearly and warmly based only on the supplied school records.\n"
                            f"Role: {context.role}\nRecords: {context.records}\nQuestion: {request.question}\n"
                            "At the end, suggest 2 helpful follow-up questions starting with 'Suggestions:'."
                        )
                        res = await provider.generate_chat([{"role": "user", "content": prompt}])
                        if res.get("content", "").strip():
                            answer = res["content"].strip()
                            reasoning_content = res.get("reasoning_content")
                            followup_questions = res.get("followup_questions", [])
                            provider_name = provider.name
                    else:
                        generated = await provider.generate(request.question, context)
                        if generated.strip():
                            cleaned, suggestions = parse_response_and_suggestions(generated.strip())
                            answer = cleaned
                            followup_questions = suggestions
                            provider_name = provider.name
                except (RuntimeError, httpx.HTTPError, KeyError, IndexError, TypeError):
                    provider_name = "deterministic-fallback"
        sources = [
            SourceRecord(
                module=r.get("module", intent),
                record_id=r.get("record_id", r.get("event_id", "demo")),
                date=r.get("date"),
                summary="; ".join(f"{k}: {v}" for k, v in r.items() if k not in {"module", "record_id"})[:180],
            )
            for r in records[:3]
        ]
        return AIAnswer(
            role=request.role,
            intent=intent,
            answer=answer,
            sources=sources,
            next_action=next_action,
            safety_boundary="CSV demonstration information only; no live record was changed; nothing was submitted, paid, or sent.",
            provider=provider_name,
            reasoning_content=reasoning_content,
            followup_questions=followup_questions,
        )
