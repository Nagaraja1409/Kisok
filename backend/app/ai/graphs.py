"""LangGraph-based multi-role agent engine for School AI Service.

Architecture
------------
One ``StateGraph`` per role (student_parent, teacher_staff, visitor, alumni).
Each graph follows a common pattern:

    input → intent_router → [feature tool nodes] → response_builder → output

LLM provider priority:  NVIDIA NIM  →  Groq  →  Deterministic fallback.
When no API key is configured the graph runs entirely deterministically
using grounded CSV data — no external call is made.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Annotated, TypedDict, AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.ai.predictive_engine import PredictiveEngine
from app.ai.multimodal import validate_document_image, describe_image_deterministic
from app.ai.service import NvidiaKimiProvider, GroqProvider, parse_response_and_suggestions
from app.config import Settings
from app.models import Role, SchoolContext, SourceRecord
from app.repositories.csv_repository import CsvSchoolDataRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role → Feature registry  (drives the chat UI feature cards)
# ---------------------------------------------------------------------------

ROLE_FEATURES: dict[str, list[dict[str, Any]]] = {
    "student": [
        {"id": "academic_copilot", "name": "AI Personal Academic Copilot", "icon": "🎓",
         "description": "Study Planner, Homework Assistant, Academic Guidance & Diagnostics",
         "sample_prompts": ["Plan my study schedule for exams", "What homework is due this week?", "Guide me on improving my Science marks"]},
        {"id": "recommendation", "name": "AI Personalized Recommendation Engine", "icon": "💡",
         "description": "Learning Recommendations, Course/Content Recommendations",
         "sample_prompts": ["Suggest books for Mathematics improvement", "Recommend study resources for Physics"]},
        {"id": "knowledge_rag", "name": "AI Knowledge & RAG Assistant", "icon": "📚",
         "description": "FAQ, Institutional Search, Library Assistant",
         "sample_prompts": ["What are the library timings?", "Search for Science Lab books", "School holiday calendar"]},
        {"id": "request_agent", "name": "AI Request & Intent Agent", "icon": "📋",
         "description": "Intent Detection, Request Understanding, Task Routing",
         "sample_prompts": ["I need a bonafide certificate", "Check my fee balance", "Request leave for tomorrow"]},
        {"id": "predictive", "name": "Predictive Analytics & Risk", "icon": "📊",
         "description": "Student Performance Prediction, Attendance Risk Analysis",
         "sample_prompts": ["Predict my exam performance", "Am I at attendance risk?", "Show my academic trend"]},
        {"id": "image_understanding", "name": "Visual Document Intelligence", "icon": "🖼️",
         "description": "Multimodal Document / Report Card / Homework Inspection",
         "sample_prompts": ["Check my uploaded report card", "Analyze this question paper image", "Inspect my fee receipt"]},
    ],
    "parent": [
        {"id": "academic_copilot", "name": "AI Personal Academic Copilot", "icon": "🎓",
         "description": "Child's Progress, Homework Tracking, Exam Preparation",
         "sample_prompts": ["What is my child's homework?", "How is my child performing in Science?", "Upcoming exam schedule"]},
        {"id": "recommendation", "name": "AI Personalized Recommendation Engine", "icon": "💡",
         "description": "Learning Recommendations, Co-curricular Suggestions",
         "sample_prompts": ["Suggest learning activities for my child", "Recommend extra classes for Math"]},
        {"id": "knowledge_rag", "name": "AI Knowledge & RAG Assistant", "icon": "📚",
         "description": "Fee Schedules, Transport, School Calendar, PTM Dates",
         "sample_prompts": ["Fee payment schedule and balance?", "School transport routes", "When is the next PTM?"]},
        {"id": "request_agent", "name": "AI Request & Intent Agent", "icon": "📋",
         "description": "Leave Applications, Fee Receipts, Status Enquiries",
         "sample_prompts": ["Apply for leave for my child", "Request fee receipt", "Check admission status"]},
        {"id": "predictive", "name": "Predictive Analytics", "icon": "📊",
         "description": "Performance Prediction, Attendance Risk, Progress Tracking",
         "sample_prompts": ["Predict my child's performance trajectory", "Check attendance risk alerts"]},
        {"id": "image_understanding", "name": "Visual Document Intelligence", "icon": "🖼️",
         "description": "Fee Receipts, Transfer Certificates, Grade Sheet Verification",
         "sample_prompts": ["Check this fee receipt", "Verify uploaded transfer certificate"]},
    ],
    "teacher": [
        {"id": "teacher_copilot", "name": "AI Teacher Copilot", "icon": "👩‍🏫",
         "description": "Teaching tasks, classroom decisions, timetable, and schedule briefings",
         "sample_prompts": ["Prepare for my next period", "What are my pending tasks today?", "Summarize today's schedule"]},
        {"id": "performance_insights", "name": "AI Performance & Risk Insights", "icon": "📈",
         "description": "Student marks, attendance trends, risk diagnosis for Class VIII A",
         "sample_prompts": ["Which students are at risk in Class VIII A?", "Subject-wise performance breakdown", "Attendance trends this month"]},
        {"id": "lesson_generator", "name": "AI Lesson & Content Generator", "icon": "📝",
         "description": "Lesson plans, worksheets, quizzes, activities, and teaching materials",
         "sample_prompts": ["Generate a lesson plan for Photosynthesis", "Create a quiz on Fractions", "Design a group activity for English"]},
        {"id": "assessment_intelligence", "name": "AI Assessment Intelligence", "icon": "📄",
         "description": "Question papers with blueprints, marking schemes, weak area analysis",
         "sample_prompts": ["Generate a Mathematics question paper with blueprint", "Analyze last exam results", "Identify weak topics for Class VIII A"]},
        {"id": "knowledge_assistant", "name": "AI Knowledge Assistant", "icon": "📚",
         "description": "School policies, academic documents, circulars, HR information",
         "sample_prompts": ["What is the leave policy?", "Latest school circulars", "Lab equipment requisition procedure"]},
        {"id": "workflow_agent", "name": "AI Workflow Agent", "icon": "⚙️",
         "description": "Draft leave requests, requisition slips, and marks submission reports",
         "sample_prompts": ["Draft a casual leave request", "Prepare lab equipment requisition", "Draft marks submission report"]},
        {"id": "daily_intelligence", "name": "AI Daily Staff Intelligence", "icon": "🌅",
         "description": "Morning briefing covering classes, meetings, duties, notices, and alerts",
         "sample_prompts": ["Give me my morning briefing", "What meetings do I have today?", "Any urgent student alerts?"]},
    ],
    "visitor": [
        {"id": "admission_counsellor", "name": "AI Admission Counsellor", "icon": "🏫",
         "description": "Admission guidance, eligibility, ICSE curriculum, fee structure, FAQs",
         "sample_prompts": ["What is the admission process for Class VI?", "Age eligibility for Nursery / Class I?", "Fee structure for ICSE"]},
        {"id": "admission_agent", "name": "AI Admission Workflow Agent", "icon": "📋",
         "description": "Application tracking, enquiry reference lookup, visit scheduling",
         "sample_prompts": ["Track my enquiry BCE/ENQ/2026/114", "Schedule a campus visit", "Check application status"]},
        {"id": "knowledge_rag", "name": "AI Knowledge & RAG Assistant", "icon": "📚",
         "description": "Campus facilities, sports grounds, science labs, hostels, bus routes",
         "sample_prompts": ["What campus facilities are available?", "Transport routes and bus coverage", "Hostel boarding facilities"]},
        {"id": "document_intelligence", "name": "Visual Document Intelligence", "icon": "📑",
         "description": "Document Pre-Check and Visual Document Inspection",
         "sample_prompts": ["Check my uploaded birth certificate", "Verify transfer certificate", "Is my mark sheet complete?"]},
        {"id": "admission_recommendation", "name": "AI Admission Recommendation", "icon": "🎯",
         "description": "Course and stream recommendations based on student profile",
         "sample_prompts": ["Recommend streams for a student interested in science", "Best co-curricular programs?"]},
        {"id": "conversion_prediction", "name": "Admission Conversion Prediction", "icon": "📊",
         "description": "Predict likelihood of application and enrollment completion",
         "sample_prompts": ["What are my admission chances?", "Conversion score for my application"]},
        {"id": "appointment_assistant", "name": "AI Appointment Assistant", "icon": "📅",
         "description": "Booking and scheduling meetings with Admissions Office",
         "sample_prompts": ["Book a meeting with admissions office", "Reschedule my campus tour"]},
    ],
    "alumni": [
        {"id": "relationship_assistant", "name": "AI Alumni Relationship Assistant", "icon": "🤝",
         "description": "Alumni services, transcript requests, donation guidance, contributions",
         "sample_prompts": ["How can I contribute to the school?", "Request my old transcript", "Donation and scholarship options"]},
        {"id": "knowledge_assistant", "name": "AI School Memories & Knowledge Assistant", "icon": "📚",
         "description": "School history, heritage, past principals, archives, school song",
         "sample_prompts": ["History of the School", "List of past principals", "School song lyrics and heritage"]},
        {"id": "event_assistant", "name": "AI Alumni Event Assistant", "icon": "🎉",
         "description": "Founders Day, reunions, regional chapter meetups, alumni gatherings",
         "sample_prompts": ["Upcoming Founders Day schedule", "Regional alumni chapter meetups", "How to register for reunion"]},
        {"id": "networking_mentorship", "name": "AI Alumni Networking & Mentorship", "icon": "🌐",
         "description": "Mentorship matching with current students and young alumni",
         "sample_prompts": ["Match me with current students in engineering", "Connect with alumni in healthcare"]},
        {"id": "achievement_discovery", "name": "AI Achievement Discovery", "icon": "🏆",
         "description": "Hall of Fame, notable alumni, success stories, school recognitions",
         "sample_prompts": ["Notable alumni in technology", "Hall of Fame entries", "Recent alumni achievements"]},
        {"id": "personalized_digest", "name": "AI Personalized Alumni Digest", "icon": "📰",
         "description": "Personalized quarterly updates, batch news, events",
         "sample_prompts": ["My personalized quarterly digest", "Latest school news for Class of 2018"]},
        {"id": "sentiment_insights", "name": "AI Community Sentiment Insights", "icon": "💬",
         "description": "Alumni engagement trends, reunion feedback, community sentiment",
         "sample_prompts": ["Alumni engagement trends", "Community feedback summary", "Reunion satisfaction scores"]},
    ],
}

# ---------------------------------------------------------------------------
# System prompts per role (Engineered for High Reasoning & Human Touch)
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS: dict[str, str] = {
    "student": (
        "You are the VAPS AI Agent for students at the school kiosk. You provide academic guidance, homework help, "
        "lesson planning, test blueprints, study planning, timetable insights, exam preparation, and personalized learning recommendations.\n\n"
        "Guidelines for High-Reasoning & Human-Feel Experience:\n"
        "1. Voice & Persona: Speak warmly, supportively, and clearly like an inspiring educator and mentor. Avoid cold or robotic answers.\n"
        "2. Deep Reasoning: When answering academic questions, creating lesson plans (such as linear algebra or science experiments), diagnosing weak areas, or planning study schedules, reason through the problem step-by-step and provide detailed, comprehensive, beautifully structured content.\n"
        "3. School Grounding: Base all factual details (classes, times, marks, homework, fees, rooms) on the supplied school records when relevant. If records don't mention a specific curriculum topic requested, provide the complete pedagogical guide anyway while noting school schedule context.\n"
        "4. Proactive Follow-ups: At the very end of your response, provide 2 to 3 tailored, actionable next steps or follow-up questions for the student under the exact header 'Suggestions:' formatted with bullet points.\n"
        "5. Safety: Advisory only. Do not execute payments, submit forms, or modify records."
    ),
    "parent": (
        "You are the VAPS AI Agent for parents at the school kiosk. You assist parents with understanding their child's "
        "academic progress, attendance, fee schedules, homework, exam timetables, and school events.\n\n"
        "Guidelines for High-Reasoning & Human-Feel Experience:\n"
        "1. Voice & Persona: Professional, empathetic, reassuring, and articulate.\n"
        "2. Deep Reasoning: Provide clear context and actionable recommendations for supporting their child's education at home.\n"
        "3. School Grounding: Ground answers in the supplied school records (attendance percentage, fee dues, exam dates).\n"
        "4. Proactive Follow-ups: At the very end of your response, provide 2 to 3 tailored follow-up questions or next steps under the exact header 'Suggestions:' formatted with bullet points.\n"
        "5. Safety: Advisory only. No payments are initiated; drafts are for preview only."
    ),
    "teacher": (
        "You are the VAPS AI Agent for teachers and staff at the school kiosk. You assist with comprehensive lesson planning, "
        "assessment blueprint creation, student performance and risk diagnostics, daily morning briefings, and workflow drafts (leave requests, requisitions).\n\n"
        "Guidelines for High-Reasoning & Human-Feel Experience:\n"
        "1. Voice & Persona: Highly competent, organized, collaborative, and professional.\n"
        "2. Deep Reasoning: When asked for lesson plans, quizzes, or student risk analysis, generate thorough, structured, pedagogically sound content with clear objectives and evaluation criteria.\n"
        "3. School Grounding: Use student scores, class lists (Class VIII A), and timetable data from the provided records.\n"
        "4. Proactive Follow-ups: At the very end of your response, suggest 2 to 3 logical follow-up actions under 'Suggestions:' formatted with bullet points.\n"
        "5. Safety: All workflow drafts and requisitions are for preview and confirmation only."
    ),
    "visitor": (
        "You are the VAPS AI Admission Counsellor for prospective parents and visitors at the school kiosk. You provide comprehensive "
        "guidance on admissions eligibility, ICSE curriculum, fee structures, facilities (labs, sports, hostels), document requirements, and campus visit scheduling.\n\n"
        "Guidelines for High-Reasoning & Human-Feel Experience:\n"
        "1. Voice & Persona: Exceptionally welcoming, hospitable, informative, and proud of the school's heritage.\n"
        "2. Deep Reasoning: If a document or image is uploaded, inspect its clarity, validity, and completeness thoroughly and explain the evaluation clearly.\n"
        "3. School Grounding: Use admission dates, fee amounts, and facility descriptions from the school records.\n"
        "4. Proactive Follow-ups: At the end of your response, provide 2 to 3 next steps under 'Suggestions:' formatted with bullet points.\n"
        "5. Safety: All bookings and applications are draft previews for front-office verification."
    ),
    "alumni": (
        "You are the VAPS AI Alumni Relationship Assistant for the school kiosk. You help alumni stay connected with the school, "
        "discover mentorship matches with current students, explore historical archives and principal records, register for Founders Day reunions, and request transcripts.\n\n"
        "Guidelines for High-Reasoning & Human-Feel Experience:\n"
        "1. Voice & Persona: Warm, nostalgic, respectful, and community-centric.\n"
        "2. Deep Reasoning: Match alumni domain skills with student needs intelligently and provide rich context on school traditions.\n"
        "3. School Grounding: Ground all references in the provided alumni, events, and facilities data.\n"
        "4. Proactive Follow-ups: At the end of your response, suggest 2 to 3 community actions under 'Suggestions:' formatted with bullet points.\n"
        "5. Safety: All transcript requests and contributions are preview drafts."
    ),
}


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    role: str
    user_ref: str | None
    feature_tag: str | None
    image_base64: str | None
    image_url: str | None
    provider_override: str | None
    context_records: dict[str, Any]
    sources: list[dict[str, Any]]
    agent_steps: list[str]
    final_answer: str
    reasoning_content: str | None
    followup_questions: list[str]
    provider_used: str


# ---------------------------------------------------------------------------
# LangGraph Agent Builder
# ---------------------------------------------------------------------------

class SchoolAgentEngine:
    """Builds and runs role-specific LangGraph agents with high reasoning."""

    def __init__(self, repository: CsvSchoolDataRepository, settings: Settings):
        self.repository = repository
        self.settings = settings
        self.predictor = PredictiveEngine()
        self.kimi_provider = NvidiaKimiProvider(
            settings.nvidia_base_url,
            settings.nvidia_api_key,
            settings.nvidia_model or "moonshotai/kimi-k3",
            settings.nvidia_reasoning_effort or "max",
            settings.nvidia_max_tokens or 16384,
            timeout=settings.ai_timeout_seconds,
        )
        self.groq_provider = GroqProvider(
            settings.groq_base_url,
            settings.groq_api_key,
            settings.groq_model or "openai/gpt-oss-120b",
            settings.ai_timeout_seconds,
        )
        self._llm: BaseChatModel | None = None
        self._llm_name = "deterministic"
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialise secondary/fallback LLM providers."""
        if self.settings.groq_api_key and self.settings.groq_model:
            try:
                from langchain_groq import ChatGroq
                self._llm = ChatGroq(
                    model=self.settings.groq_model,
                    api_key=self.settings.groq_api_key,
                    base_url=self.settings.groq_base_url,
                    temperature=0.1,
                    max_tokens=2048,
                    timeout=self.settings.ai_timeout_seconds,
                )
                self._llm_name = "groq"
                logger.info("Fallback LLM provider: Groq (%s)", self.settings.groq_model)
            except Exception as exc:
                logger.warning("Groq init failed: %s", exc)

    # ------------------------------------------------------------------
    # Intent keywords (reused from original service)
    # ------------------------------------------------------------------
    KEYWORDS: dict[str, list[str]] = {
        "timetable": ["timetable", "next class", "period", "science lab", "room", "schedule"],
        "homework": ["homework", "assignment", "due", "study", "project"],
        "attendance": ["attendance", "absent", "present", "leave"],
        "fees": ["fee", "fees", "balance", "installment", "payment", "receipt", "upi", "bank"],
        "exams": ["exam", "score", "marks", "test", "hall ticket", "result", "grade"],
        "library": ["book", "library", "rack", "borrow", "reading"],
        "admission": ["admission", "enquiry", "counselling", "document", "application", "eligibility"],
        "events": ["event", "founders", "annual day", "sports day", "holiday", "notice", "reunion"],
        "hostel": ["hostel", "room", "warden", "residence"],
        "lesson": ["lesson plan", "worksheet", "quiz", "activity", "teaching material"],
        "assessment": ["question paper", "blueprint", "rubric", "grading"],
        "performance": ["performance", "risk", "prediction", "trend", "analytics", "insight"],
        "workflow": ["leave request", "requisition", "draft", "approval", "submit"],
        "mentorship": ["mentor", "mentorship", "match", "connect", "networking"],
        "digest": ["digest", "news", "update", "newsletter"],
        "sentiment": ["sentiment", "feedback", "survey", "engagement trend"],
        "appointment": ["appointment", "meeting", "book", "reschedule", "slot"],
        "achievement": ["achievement", "notable", "hall of fame", "success", "alumni achievement"],
    }

    def _detect_intent(self, question: str) -> str:
        q = question.lower()
        for name, terms in self.KEYWORDS.items():
            if any(term in q for term in terms):
                return name
        return "general"

    # ------------------------------------------------------------------
    # Graph node functions
    # ------------------------------------------------------------------

    def _node_retrieve_context(self, state: AgentState) -> dict[str, Any]:
        """Retrieve CSV records scoped to the user's role."""
        role = state["role"]
        user_ref = state.get("user_ref")
        context = self.repository.get_context(role, user_ref)  # type: ignore[arg-type]
        last_msg = ""
        for m in reversed(state["messages"]):
            if hasattr(m, "content") and isinstance(m.content, str):
                last_msg = m.content
                break

        search_results = self.repository.search(role, user_ref, last_msg)  # type: ignore[arg-type]
        intent = self._detect_intent(last_msg)

        sources = [
            {"module": r.get("module", intent), "record_id": r.get("record_id", r.get("event_id", "demo")),
             "date": r.get("date"), "summary": "; ".join(f"{k}: {v}" for k, v in r.items() if k not in {"module", "record_id"})[:180]}
            for r in search_results[:5]
        ]

        return {
            "context_records": {"role": role, "intent": intent, "records": context.records, "profile": context.profile},
            "sources": sources,
            "agent_steps": [f"🔍 Searched {len(context.records)} data modules for '{intent}' context"],
        }

    def _node_analytics(self, state: AgentState) -> dict[str, Any]:
        """Run predictive analytics if relevant."""
        ctx = state.get("context_records", {})
        role = state["role"]
        records = ctx.get("records", {})
        intent = ctx.get("intent", "")
        steps = list(state.get("agent_steps", []))

        if intent in ("performance", "predictive") or "risk" in " ".join(m.content for m in state["messages"] if hasattr(m, "content")).lower():
            if role in ("student", "parent"):
                result = self.predictor.student_performance_prediction(
                    records.get("exam_scores", []), records.get("attendance", [])
                )
                steps.append(f"📊 Ran student performance prediction → Risk: {result['risk_level']}, Trend: {result['trend']}")
                ctx["prediction"] = result
            elif role == "teacher":
                result = self.predictor.class_performance_insights(
                    records.get("exam_scores", []), records.get("attendance", [])
                )
                steps.append(f"📊 Ran class performance insights → Weakest: {result['weakest_subject']}")
                ctx["prediction"] = result
            elif role == "visitor":
                result = self.predictor.admission_conversion_prediction(
                    records.get("admissions", records.get("preadmissions", []))
                )
                steps.append(f"📊 Ran admission conversion prediction → Score: {result['score']}")
                ctx["prediction"] = result
            elif role == "alumni":
                result = self.predictor.alumni_engagement_score(
                    records.get("alumni", []), records.get("events", [])
                )
                steps.append(f"📊 Ran alumni engagement scoring → {result['label']}")
                ctx["prediction"] = result

        return {"context_records": ctx, "agent_steps": steps}

    def _node_image_check(self, state: AgentState) -> dict[str, Any]:
        """Process uploaded images if present."""
        image_b64 = state.get("image_base64")
        steps = list(state.get("agent_steps", []))
        ctx = state.get("context_records", {})

        if image_b64:
            doc_result = validate_document_image(image_b64, state["role"])
            ctx["document_check"] = doc_result
            steps.append(f"🖼️ Document pre-check validation → {doc_result['status']}")

        return {"context_records": ctx, "agent_steps": steps}

    async def _node_generate_response(self, state: AgentState) -> dict[str, Any]:
        """Generate the final response using Moonshot Kimi-K3, Groq, or deterministic fallback."""
        ctx = state.get("context_records", {})
        role = state["role"]
        intent = ctx.get("intent", "general")
        steps = list(state.get("agent_steps", []))
        provider_override = state.get("provider_override")

        # Build context summary
        context_text = self._build_context_text(ctx)
        system_prompt = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["student"])
        system_prompt += f"\n\n[Grounded School CSV Records & Context]\n{context_text}"

        messages = state.get("messages", [])
        raw_messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for m in messages:
            if isinstance(m, HumanMessage):
                raw_messages.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                raw_messages.append({"role": "assistant", "content": m.content})

        target_provider = provider_override or self.settings.ai_provider or "nvidia"
        if target_provider == "grok":
            target_provider = "groq"
        if target_provider == "auto":
            target_provider = "nvidia" if self.settings.nvidia_api_key else "groq" if self.settings.groq_api_key else "deterministic"

        # 1. Try NVIDIA NIM Moonshot Kimi-K3 (Preferred High-Reasoning & Multimodal)
        if target_provider in ("nvidia", "auto") and self.settings.nvidia_api_key:
            try:
                steps.append("🧠 Engaging Moonshot AI Kimi-K3 with maximum reasoning effort...")
                res = await self.kimi_provider.generate_chat(
                    raw_messages,
                    image_base64=state.get("image_base64"),
                    image_url=state.get("image_url"),
                    temperature=1.0,
                )
                answer = res["content"]
                reasoning = res.get("reasoning_content")
                followups = res.get("followup_questions", [])

                if reasoning:
                    steps.append("💡 Deep reasoning chain synthesized")
                if followups:
                    steps.append(f"✨ Formulated {len(followups)} proactive follow-up suggestions")

                return {
                    "final_answer": answer,
                    "reasoning_content": reasoning,
                    "followup_questions": followups,
                    "provider_used": "nvidia",
                    "agent_steps": steps,
                }
            except Exception as exc:
                logger.warning("NVIDIA Kimi-K3 call failed, checking fallback: %s", exc)
                steps.append(f"⚠️ NVIDIA Kimi-K3 unavailable ({exc.__class__.__name__}), trying fallback")

        # 2. Try High-Reasoning Groq (openai/gpt-oss-120b)
        if target_provider in ("groq", "nvidia", "auto") and self.settings.groq_api_key:
            try:
                steps.append("⚡ Engaging Groq High-Reasoning Engine (openai/gpt-oss-120b)...")
                res = await self.groq_provider.generate_chat(raw_messages, temperature=0.6)
                answer = res["content"]
                reasoning = res.get("reasoning_content")
                followups = res.get("followup_questions", [])
                if reasoning:
                    steps.append("💡 High-reasoning chain synthesized")
                if followups:
                    steps.append(f"✨ Formulated {len(followups)} proactive follow-up suggestions")
                return {
                    "final_answer": answer,
                    "reasoning_content": reasoning,
                    "followup_questions": followups,
                    "provider_used": "groq",
                    "agent_steps": steps,
                }
            except Exception as exc:
                logger.warning("Groq call failed: %s", exc)
                steps.append(f"⚠️ Groq unavailable ({exc.__class__.__name__}), using deterministic grounded engine")

        # 3. Deterministic Grounded Engine
        answer, followups = self._deterministic_answer(role, intent, ctx)
        steps.append("📋 Generated deterministic grounded response from local CSV records")
        return {
            "final_answer": answer,
            "reasoning_content": None,
            "followup_questions": followups,
            "provider_used": "deterministic",
            "agent_steps": steps,
        }

    def _build_context_text(self, ctx: dict[str, Any]) -> str:
        """Summarise context records into a text block for the LLM prompt."""
        parts = []
        profile = ctx.get("profile", {})
        if profile:
            parts.append(f"Profile: {json.dumps(profile, default=str)[:300]}")

        records = ctx.get("records", {})
        for module, rows in records.items():
            if rows:
                sample = rows[:3]
                parts.append(f"{module}: {json.dumps(sample, default=str)[:400]}")

        prediction = ctx.get("prediction")
        if prediction:
            parts.append(f"Analytics: {json.dumps(prediction, default=str)}")

        doc_check = ctx.get("document_check")
        if doc_check:
            parts.append(f"Document Check: {json.dumps(doc_check, default=str)[:300]}")

        return "\n".join(parts)[:3000]

    def _deterministic_answer(self, role: str, intent: str, ctx: dict[str, Any]) -> tuple[str, list[str]]:
        """Build a grounded answer and suggestions without any LLM call."""
        records = ctx.get("records", {})
        profile = ctx.get("profile", {})
        prediction = ctx.get("prediction")
        doc_check = ctx.get("document_check")

        parts = []
        followups = []

        # Document check results
        if doc_check:
            parts.append(f"**Document Pre-Check**: {doc_check['message']}")
            for c in doc_check.get("checks", []):
                parts.append(f"  - {c['status']} {c['check']}: {c['detail']}")
            followups = [
                "What documents are required for Class VI admission?",
                "How do I upload a higher resolution document?",
                "Contact the Admissions Helpdesk"
            ]
            return "\n".join(parts), followups

        # Prediction results
        if prediction:
            parts.append("**📊 Analytics & Risk Report**")
            for k, v in prediction.items():
                label = k.replace("_", " ").title()
                if isinstance(v, dict):
                    parts.append(f"  - **{label}**: {json.dumps(v)}")
                elif isinstance(v, list):
                    parts.append(f"  - **{label}**: {', '.join(str(i) for i in v)}")
                else:
                    parts.append(f"  - **{label}**: {v}")
            followups = [
                "How can I improve my weakest subject score?",
                "Show detailed attendance breakdown",
                "Recommend study timetable for upcoming exams"
            ]
            return "\n".join(parts), followups

        # Intent-specific grounded answers
        if intent == "timetable" and "timetable" in records and records["timetable"]:
            rows = records["timetable"][:5]
            parts.append("**📅 Timetable Schedule**")
            for r in rows:
                parts.append(f"  - {r.get('subject', 'N/A')} at {r.get('time', 'N/A')} in {r.get('room', 'N/A')}")
            followups = [
                "What homework is due for my next class?",
                "Show full weekly timetable",
                "Who is the teacher for Science Lab?"
            ]
            return "\n".join(parts), followups

        if intent == "homework" and "homework" in records and records["homework"]:
            rows = records["homework"][:3]
            parts.append("**📝 Homework & Assignments**")
            for r in rows:
                parts.append(f"  - **{r.get('subject', 'N/A')}**: {r.get('assignment', 'N/A')} — Due: {r.get('due', 'N/A')}")
            followups = [
                "Help me draft a study plan for this assignment",
                "What are the upcoming exam dates?",
                "Recommend library reference books"
            ]
            return "\n".join(parts), followups

        if intent == "attendance" and "attendance" in records and records["attendance"]:
            risk = self.predictor.attendance_risk(records["attendance"])
            parts.append("**📋 Attendance Summary**")
            parts.append(f"  - Present: {risk['present_pct']}% ({risk['total_days']} days, {risk['absent_days']} absent)")
            parts.append(f"  - Risk Level: {risk['risk_level']}")
            parts.append(f"  - {risk['alert']}")
            followups = [
                "How many more days can I miss safely?",
                "Draft a leave request for review",
                "Show attendance by subject"
            ]
            return "\n".join(parts), followups

        if intent == "fees" and "fees" in records and records["fees"]:
            rows = records["fees"][:3]
            parts.append("**💰 Fee Information**")
            for r in rows:
                status = r.get("status", "N/A")
                parts.append(f"  - {r.get('fee_type', r.get('description', 'Fee'))}: ₹{r.get('amount', 'N/A')} — {status} (Due: {r.get('due_date', 'N/A')})")
            parts.append("\n*Fee guidance is view-only. No payment was initiated.*")
            followups = [
                "Prepare payment guidance preview",
                "Show previous payment receipts",
                "What is the fee structure for next term?"
            ]
            return "\n".join(parts), followups

        if intent == "exams" and "exams" in records and records["exams"]:
            rows = records["exams"][:3]
            parts.append("**📝 Exam Schedule**")
            for r in rows:
                parts.append(f"  - {r.get('subject', 'N/A')} — {r.get('date', 'N/A')} at {r.get('session', r.get('time', 'N/A'))}")
            followups = [
                "Create a revision plan for Mathematics",
                "Show my previous exam marks",
                "What is the exam hall ticket number?"
            ]
            return "\n".join(parts), followups

        if intent == "library" and "library_books" in records and records["library_books"]:
            rows = records["library_books"][:3]
            parts.append("**📚 Library Results**")
            for r in rows:
                parts.append(f"  - *{r.get('title', 'N/A')}* — {r.get('rack', 'N/A')}, {r.get('floor', 'N/A')} — {r.get('availability', 'N/A')}")
            followups = [
                "Search for Physics reference books",
                "What are the library borrowing rules?",
                "Recommend books for Class VIII Science"
            ]
            return "\n".join(parts), followups

        if intent == "admission":
            for key in ("admissions", "preadmissions"):
                if key in records and records[key]:
                    r = records[key][0]
                    parts.append("**🏫 Admission Information**")
                    parts.append(f"  - Reference: {r.get('enquiry_id', r.get('application_id', 'N/A'))}")
                    parts.append(f"  - Status: {r.get('status', 'N/A')}")
                    parts.append(f"  - Next Step: {r.get('next_step', r.get('counselling', 'Contact the Front Office'))}")
                    followups = [
                        "Schedule a campus tour",
                        "What is the fee structure for Class VI?",
                        "Check document pre-check requirements"
                    ]
                    return "\n".join(parts), followups

        if intent == "events" and "events" in records and records["events"]:
            rows = records["events"][:3]
            parts.append("**🎉 Upcoming Events**")
            for r in rows:
                parts.append(f"  - **{r.get('title', 'Event')}** — {r.get('date', 'N/A')} at {r.get('time', 'N/A')} in {r.get('venue', r.get('location', 'N/A'))}")
            followups = [
                "How do I register for Founders Day?",
                "What sports facilities are open this weekend?",
                "Show latest school circulars"
            ]
            return "\n".join(parts), followups

        if intent == "lesson" and role == "teacher":
            parts.append("**📝 Lesson Plan Generator**")
            parts.append("I can help you create a structured lesson plan. Here's a template based on your assigned classes:")
            parts.append(f"  - **Class**: {profile.get('assigned_class', profile.get('class_name', 'Class VIII A'))}")
            parts.append(f"  - **Subject**: {profile.get('subject', 'General')}")
            parts.append("  - **Structure**: Learning Objectives → Warm-up Activity → Main Teaching → Practice → Assessment → Closure")
            parts.append("\nPlease specify the topic and I'll generate a detailed plan.")
            followups = [
                "Generate a lesson plan for Photosynthesis",
                "Create a 10-minute starter quiz",
                "Design a group activity for Class VIII"
            ]
            return "\n".join(parts), followups

        if intent == "assessment" and role == "teacher":
            parts.append("**📄 Assessment Intelligence**")
            parts.append("I can generate question papers with blueprint. Provide:")
            parts.append("  - Subject and chapter/unit")
            parts.append("  - Difficulty distribution (Easy/Medium/Hard)")
            parts.append("  - Question types (MCQ, Short Answer, Long Answer)")
            if "exam_scores" in records and records["exam_scores"]:
                insights = self.predictor.class_performance_insights(records["exam_scores"], records.get("attendance", []))
                parts.append(f"\n**Class Insights**: Weakest subject is **{insights['weakest_subject']}** — consider extra focus here.")
            followups = [
                "Generate a 25-mark Mathematics quiz with blueprint",
                "Analyze recent test scores for Class VIII A",
                "Suggest remedial worksheets for weak students"
            ]
            return "\n".join(parts), followups

        if intent == "workflow":
            parts.append("**⚙️ Workflow Draft**")
            parts.append("I can prepare the following drafts for your review:")
            if role == "teacher":
                parts.append("  - 📝 Leave application draft")
                parts.append("  - 🔬 Lab / resource requisition slip")
                parts.append("  - 📊 Marks submission report")
                followups = [
                    "Draft a casual leave request for Friday",
                    "Prepare science lab equipment requisition",
                    "Draft student attendance warning notice"
                ]
            else:
                parts.append("  - 📋 Certificate request draft")
                parts.append("  - 💰 Fee payment guidance preview")
                parts.append("  - 📧 Communication draft")
                followups = [
                    "Request a Bonafide Certificate",
                    "Prepare fee payment installment preview",
                    "Draft an enquiry message for Front Office"
                ]
            parts.append("\n*All drafts are for review only — nothing is submitted or sent.*")
            return "\n".join(parts), followups

        if intent == "mentorship" and role == "alumni":
            parts.append("**🌐 Mentorship & Networking**")
            parts.append("School Alumni Mentorship matches alumni with current students or young graduates by career domain.")
            if "alumni" in records and records["alumni"]:
                r = records["alumni"][0]
                parts.append(f"  - Your profile: {r.get('name', 'Alumni')} — {r.get('batch', 'N/A')}")
            parts.append("  - 3 open mentorship requests available")
            parts.append("  - Domains: Engineering, Medicine, Business, Arts, Education")
            followups = [
                "Match me with current engineering students",
                "View Class of 2018 reunion details",
                "How to contribute to the student scholarship fund"
            ]
            return "\n".join(parts), followups

        if intent == "appointment" and role == "visitor":
            parts.append("**📅 Appointment Scheduling**")
            parts.append("Available meeting slots with the Admissions Office:")
            parts.append("  - Monday–Friday: 09:00–15:30")
            parts.append("  - Saturday: 09:00–12:00 (by appointment)")
            parts.append("\n*This is a draft booking preview. The appointment is not confirmed until verified by the office.*")
            followups = [
                "Book a morning campus tour for Saturday",
                "What documents should I bring to the visit?",
                "Track existing enquiry BCE/ENQ/2026/114"
            ]
            return "\n".join(parts), followups

        # General fallback
        available_modules = ", ".join(records.keys()) if records else "general school information"
        parts.append(f"I am your **School AI Copilot**. I have access to records from: **{available_modules}**.")
        parts.append(f"\nAs a **{role}**, you have access to specialized AI features. Try asking about:")
        features = ROLE_FEATURES.get(role, [])
        for f in features[:4]:
            sample = f['sample_prompts'][0] if f['sample_prompts'] else f['description']
            parts.append(f"  - {f['icon']} **{f['name']}**: *\"{sample}\"*")
            followups.append(sample)
        return "\n".join(parts), followups[:3]

    # ------------------------------------------------------------------
    # Build & run graph
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("retrieve", self._node_retrieve_context)
        graph.add_node("analytics", self._node_analytics)
        graph.add_node("image_check", self._node_image_check)
        graph.add_node("generate", self._node_generate_response)

        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "analytics")
        graph.add_edge("analytics", "image_check")
        graph.add_edge("image_check", "generate")
        graph.add_edge("generate", END)

        return graph

    async def run(
        self,
        role: str,
        question: str,
        *,
        user_ref: str | None = None,
        feature_tag: str | None = None,
        image_base64: str | None = None,
        image_url: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        provider_override: str | None = None,
    ) -> dict[str, Any]:
        """Execute the agent graph and return the result."""
        # Build message history
        messages = []
        if conversation_history:
            for msg in conversation_history[-15:]:  # last 15 messages for context window
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=question))

        initial_state: AgentState = {
            "messages": messages,
            "role": role,
            "user_ref": user_ref,
            "feature_tag": feature_tag,
            "image_base64": image_base64,
            "image_url": image_url,
            "provider_override": provider_override,
            "context_records": {},
            "sources": [],
            "agent_steps": [],
            "final_answer": "",
            "reasoning_content": None,
            "followup_questions": [],
            "provider_used": "deterministic",
        }

        graph = self._build_graph()
        compiled = graph.compile()
        result = await compiled.ainvoke(initial_state)

        return {
            "answer": result.get("final_answer", ""),
            "reasoning_content": result.get("reasoning_content"),
            "followup_questions": result.get("followup_questions", []),
            "sources": result.get("sources", []),
            "agent_steps": result.get("agent_steps", []),
            "provider_used": result.get("provider_used", "deterministic"),
        }

    async def stream_run(
        self,
        role: str,
        question: str,
        *,
        user_ref: str | None = None,
        feature_tag: str | None = None,
        image_base64: str | None = None,
        image_url: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        provider_override: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream execution tokens and steps."""
        messages = []
        if conversation_history:
            for msg in conversation_history[-15:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=question))

        state: AgentState = {
            "messages": messages,
            "role": role,
            "user_ref": user_ref,
            "feature_tag": feature_tag,
            "image_base64": image_base64,
            "image_url": image_url,
            "provider_override": provider_override,
            "context_records": {},
            "sources": [],
            "agent_steps": [],
            "final_answer": "",
            "reasoning_content": None,
            "followup_questions": [],
            "provider_used": "deterministic",
        }

        # Step 1: Context retrieval
        ret_res = self._node_retrieve_context(state)
        state["context_records"] = ret_res["context_records"]
        state["sources"] = ret_res["sources"]
        state["agent_steps"] = list(ret_res["agent_steps"])
        for s in ret_res["agent_steps"]:
            yield {"type": "step", "text": s}

        # Step 2: Analytics
        ana_res = self._node_analytics(state)
        new_steps = [s for s in ana_res["agent_steps"] if s not in state["agent_steps"]]
        state["context_records"] = ana_res["context_records"]
        state["agent_steps"] = list(ana_res["agent_steps"])
        for s in new_steps:
            yield {"type": "step", "text": s}

        # Step 3: Image check
        img_res = self._node_image_check(state)
        new_steps = [s for s in img_res["agent_steps"] if s not in state["agent_steps"]]
        state["context_records"] = img_res["context_records"]
        state["agent_steps"] = list(img_res["agent_steps"])
        for s in new_steps:
            yield {"type": "step", "text": s}

        target_provider = provider_override or self.settings.ai_provider or "nvidia"
        if target_provider == "grok":
            target_provider = "groq"
        if target_provider == "auto":
            target_provider = "nvidia" if self.settings.nvidia_api_key else "groq" if self.settings.groq_api_key else "deterministic"

        # Attempt streaming from NVIDIA Kimi-K3
        if target_provider in ("nvidia", "auto") and self.settings.nvidia_api_key:
            yield {"type": "step", "text": "🧠 Engaging Moonshot AI Kimi-K3 with maximum reasoning effort..."}
            context_text = self._build_context_text(state["context_records"])
            system_prompt = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["student"])
            system_prompt += f"\n\n[Grounded School CSV Records & Context]\n{context_text}"

            raw_messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
            for m in messages:
                if isinstance(m, HumanMessage):
                    raw_messages.append({"role": "user", "content": m.content})
                elif isinstance(m, AIMessage):
                    raw_messages.append({"role": "assistant", "content": m.content})

            accumulated_reasoning = ""
            accumulated_content = ""
            stream_success = False

            try:
                async for chunk in self.kimi_provider.stream_chat(
                    raw_messages,
                    image_base64=image_base64,
                    image_url=image_url,
                    temperature=1.0,
                ):
                    stream_success = True
                    r_delta = chunk.get("reasoning_chunk")
                    c_delta = chunk.get("content_chunk")
                    if r_delta:
                        accumulated_reasoning += r_delta
                        yield {"type": "reasoning", "delta": r_delta}
                    if c_delta:
                        accumulated_content += c_delta
                        yield {"type": "content", "delta": c_delta}

                if stream_success and accumulated_content:
                    clean_answer, followups = parse_response_and_suggestions(accumulated_content)
                    yield {
                        "type": "done",
                        "answer": clean_answer,
                        "reasoning_content": accumulated_reasoning or None,
                        "followup_questions": followups,
                        "sources": state["sources"],
                        "agent_steps": state["agent_steps"] + [
                            "💡 Deep reasoning chain synthesized",
                            f"✨ Formulated {len(followups)} proactive follow-up suggestions"
                        ] if followups else state["agent_steps"],
                        "provider_used": "nvidia",
                    }
                    return
            except Exception as exc:
                logger.warning("Streaming NVIDIA Kimi-K3 failed, falling back: %s", exc)
                yield {"type": "step", "text": f"⚠️ NVIDIA stream unavailable ({exc.__class__.__name__}), engaging Groq..."}

        # Attempt streaming from Groq (Ultra-fast & High Reasoning)
        if (target_provider in ("groq", "nvidia", "auto")) and self.settings.groq_api_key:
            yield {"type": "step", "text": "⚡ Streaming from Groq High-Reasoning Engine (openai/gpt-oss-120b)..."}
            context_text = self._build_context_text(state["context_records"])
            system_prompt = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["student"])
            system_prompt += f"\n\n[Grounded School CSV Records & Context]\n{context_text}"

            raw_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                if isinstance(m, HumanMessage):
                    raw_messages.append({"role": "user", "content": m.content})
                elif isinstance(m, AIMessage):
                    raw_messages.append({"role": "assistant", "content": m.content})

            accumulated_reasoning = ""
            accumulated_content = ""
            groq_success = False

            try:
                async for chunk in self.groq_provider.stream_chat(raw_messages, temperature=0.6):
                    groq_success = True
                    r_delta = chunk.get("reasoning_chunk")
                    c_delta = chunk.get("content_chunk")
                    if r_delta:
                        accumulated_reasoning += r_delta
                        yield {"type": "reasoning", "delta": r_delta}
                    if c_delta:
                        accumulated_content += c_delta
                        yield {"type": "content", "delta": c_delta}

                if groq_success and accumulated_content:
                    clean_answer, followups = parse_response_and_suggestions(accumulated_content)
                    yield {
                        "type": "done",
                        "answer": clean_answer,
                        "reasoning_content": accumulated_reasoning or None,
                        "followup_questions": followups,
                        "sources": state["sources"],
                        "agent_steps": state["agent_steps"] + [
                            "💡 High-reasoning chain synthesized",
                            f"✨ Formulated {len(followups)} proactive follow-up suggestions",
                        ] if followups else state["agent_steps"],
                        "provider_used": "groq",
                    }
                    return
            except Exception as exc:
                logger.warning("Streaming Groq failed, falling back: %s", exc)
                yield {"type": "step", "text": f"⚠️ Groq stream unavailable ({exc.__class__.__name__}), generating grounded response"}

        # Fallback to standard execution
        gen_res = await self._node_generate_response(state)
        # Emit reasoning and content if available
        if gen_res.get("reasoning_content"):
            yield {"type": "reasoning", "delta": gen_res["reasoning_content"]}
        if gen_res.get("final_answer"):
            yield {"type": "content", "delta": gen_res["final_answer"]}

        yield {
            "type": "done",
            "answer": gen_res.get("final_answer", ""),
            "reasoning_content": gen_res.get("reasoning_content"),
            "followup_questions": gen_res.get("followup_questions", []),
            "sources": state["sources"],
            "agent_steps": gen_res.get("agent_steps", state["agent_steps"]),
            "provider_used": gen_res.get("provider_used", "deterministic"),
        }

    def get_features(self, role: str) -> list[dict[str, Any]]:
        """Return the feature matrix for a given role."""
        return ROLE_FEATURES.get(role, [])


# Backward compatibility and user-requested alias
SchoolAgent = SchoolAgentEngine
BaldwinAgentEngine = SchoolAgentEngine