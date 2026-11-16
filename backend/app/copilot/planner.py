from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from app.core.security import SecurityValidator
from app.engines.entity_engine import EntityExtractionEngine
from app.engines.intent_engine import IntentEngine

logger = logging.getLogger(__name__)


class ExecutionPlan(BaseModel):
    user_id: str
    role: str
    tenant_id: str
    query: str
    intent: str
    entities: dict[str, Any] = Field(default_factory=dict)
    selected_agents: list[str] = Field(default_factory=list)
    selected_tools: list[str] = Field(default_factory=list)
    needs_prediction: bool = False
    prediction_type: str | None = None
    needs_recommendation: bool = False
    needs_rag: bool = False
    requires_confirmation: bool = False
    confirmation_message: str | None = None


class QueryPlanningEngine:
    @classmethod
    def create_plan(
        cls,
        query: str,
        role: str,
        user_id: str,
        tenant_id: str,
        session_context: Any = None,
        feature_tag: str | None = None,
    ) -> ExecutionPlan:
        canonical_role = SecurityValidator.normalize_role(role)
        intent = IntentEngine.detect_intent(query, canonical_role)
        entities = EntityExtractionEngine.extract_entities(query, user_id=user_id)

        q_lower = query.lower()
        selected_agents: list[str] = []
        selected_tools: list[str] = []
        needs_prediction = False
        prediction_type = None
        needs_recommendation = False
        needs_rag = False
        requires_confirmation = False
        confirmation_msg = None

        # 1. STUDENT / PARENT ROLE GROUP
        if canonical_role == "student_parent":
            if "apply leave" in q_lower or "request leave" in q_lower or intent == "leave_application":
                requires_confirmation = True
                date = entities.get("date", "Tomorrow")
                reason = entities.get("reason", "Personal reasons")
                confirmation_msg = (
                    f"I can prepare a leave request for {date}.\n"
                    f"Reason: {reason}.\n"
                    "Would you like me to submit it?"
                )
                selected_agents = ["family_support_agent"]
                selected_tools = ["preview_leave_application"]

            elif any(w in q_lower for w in ("policy", "circular", "handbook", "guideline", "rule")):
                needs_rag = True
                selected_agents = ["notice_agent"]
                selected_tools = ["rag_retrieval"]

            elif any(w in q_lower for w in ("book", "library", "reading", "study resources", "ruskin bond", "study plan", "homework")):
                selected_agents = ["learning_agent"]
                selected_tools = ["get_library_data"]
                needs_recommendation = True

            elif any(w in q_lower for w in ("bus", "transport", "pickup", "van", "route")):
                selected_agents = ["transport_agent"]
                selected_tools = ["get_transport_details"]

            elif intent == "exam" or any(w in q_lower for w in ("exam", "test schedule", "hall ticket", "date sheet")):
                selected_agents = ["exam_agent"]
                selected_tools = ["get_exam_details"]

            elif intent == "fees" or any(w in q_lower for w in ("fee", "fees", "balance", "dues", "installment", "receipt")):
                selected_agents = ["fee_agent"]
                selected_tools = ["get_fee_details"]

            elif intent in ("attendance_inquiry", "attendance_analysis") or "attendance" in q_lower or "absent" in q_lower:
                selected_agents = ["attendance_agent"]
                selected_tools = ["get_student_attendance"]
                if any(w in q_lower for w in ("why", "low", "falling", "drop", "risk", "trend", "threshold", "cbse")):
                    needs_prediction = True
                    prediction_type = "attendance_risk"
                if any(w in q_lower for w in ("improve", "how can i", "suggestion", "help", "what should")):
                    needs_recommendation = True

            elif intent in ("marks_inquiry", "academic_analysis") or any(w in q_lower for w in ("mark", "score", "grade", "science", "math", "report card")):
                selected_agents = ["academic_agent"]
                selected_tools = ["get_student_marks"]
                if any(w in q_lower for w in ("why", "improve", "predict", "trajectory", "weak", "performance")):
                    needs_prediction = True
                    prediction_type = "academic_performance"
                if any(w in q_lower for w in ("how to", "suggest", "recommend", "study")):
                    needs_recommendation = True

            elif intent == "notices" or any(w in q_lower for w in ("notice", "circular", "holiday", "announcement")):
                needs_rag = True
                selected_agents = ["notice_agent"]
                selected_tools = ["rag_retrieval"]

            elif intent == "timetable" or any(w in q_lower for w in ("timetable", "schedule", "period", "class today")):
                selected_agents = ["student_assistant_agent"]
                selected_tools = ["get_timetable"]

            else:
                selected_agents = ["student_assistant_agent"]
                selected_tools = ["get_timetable"]

        # 2. TEACHER / STAFF ROLE GROUP
        elif canonical_role == "teacher_staff":
            if "apply leave" in q_lower or "request leave" in q_lower or "casual leave" in q_lower or "leave balance" in q_lower:
                selected_agents = ["hr_leave_agent"]
                selected_tools = ["preview_leave_application"]
                requires_confirmation = True
                date = entities.get("date", "Tomorrow")
                reason = entities.get("reason", "Casual Leave")
                confirmation_msg = (
                    f"I can prepare a casual leave request for {date}.\n"
                    f"Reason: {reason}.\n"
                    "Would you like me to submit it for Principal approval?"
                )

            elif any(w in q_lower for w in ("roster", "cohort", "assigned class", "enrolled students", "class viii a students")):
                selected_agents = ["class_agent"]
                selected_tools = ["get_student_profile"]

            elif intent in ("attendance_inquiry", "attendance_analysis") or any(w in q_lower for w in ("attendance", "absenteeism", "chronic", "average attendance")):
                selected_agents = ["attendance_analysis_agent"]
                selected_tools = ["get_student_attendance"]
                needs_prediction = True
                prediction_type = "attendance_risk"
                needs_recommendation = True

            elif intent in ("marks_inquiry", "academic_analysis") or any(w in q_lower for w in ("assessment", "exam score", "weak topic", "blueprint", "marksheet")):
                selected_agents = ["assessment_agent"]
                selected_tools = ["get_student_marks"]
                needs_prediction = True
                prediction_type = "class_performance"
                needs_recommendation = True

            elif any(w in q_lower for w in ("lesson", "pedagogy", "quiz", "worksheet", "activity", "photosynthesis", "fractions")):
                selected_agents = ["lesson_agent"]
                selected_tools = ["get_library_data"]
                needs_recommendation = True

            elif intent == "notices" or any(w in q_lower for w in ("policy", "regulation", "bylaw", "cbse norm", "handbook")):
                needs_rag = True
                selected_agents = ["staff_knowledge_agent"]
                selected_tools = ["rag_retrieval"]

            elif any(w in q_lower for w in ("apparatus", "projector", "lab equipment", "store", "requisition", "resource")):
                selected_agents = ["resource_agent"]
                selected_tools = ["get_library_data"]

            elif intent == "timetable" or any(w in q_lower for w in ("timetable", "schedule", "period", "briefing", "duty", "next class")):
                selected_agents = ["teacher_copilot_agent"]
                selected_tools = ["get_timetable"]

            else:
                selected_agents = ["teacher_copilot_agent"]
                selected_tools = ["get_timetable"]

        # 3. VISITOR / APPLICANT ROLE GROUP
        elif canonical_role == "visitor_applicant":
            if any(w in q_lower for w in ("track", "application", "enquiry ref", "bce/enq", "documents pending", "conversion")):
                selected_agents = ["application_agent"]
                selected_tools = ["get_admission_details"]
                needs_prediction = True
                prediction_type = "admission_conversion"

            elif any(w in q_lower for w in ("where is", "direction", "navigation", "map", "how to reach", "auditorium", "sports ground", "lab location")):
                selected_agents = ["campus_navigation_agent"]
                selected_tools = ["get_campus_facilities"]

            elif any(w in q_lower for w in ("appointment", "schedule visit", "book tour", "meet principal", "meet admissions")):
                selected_agents = ["appointment_agent"]
                selected_tools = ["preview_appointment"]
                requires_confirmation = True
                date = entities.get("date", "Tomorrow")
                confirmation_msg = f"I can prepare a campus visit appointment for {date}.\nDepartment: Admissions Desk.\nWould you like me to book this visit?"

            elif any(w in q_lower for w in ("curriculum", "affiliation", "cbse", "icse", "naac", "accreditation", "school hours")):
                needs_rag = True
                selected_agents = ["public_knowledge_agent"]
                selected_tools = ["rag_retrieval"]

            elif intent == "admissions" or any(w in q_lower for w in ("admission", "eligibility", "fee structure", "nursery", "class vi")):
                selected_agents = ["admission_agent"]
                selected_tools = ["get_admission_details"]
                needs_recommendation = True

            else:
                selected_agents = ["visitor_agent"]
                selected_tools = ["get_campus_facilities"]

        # 4. ALUMNI / EX-EMPLOYEE ROLE GROUP
        else:
            if any(w in q_lower for w in ("ex-employee", "former staff", "service certificate", "experience letter", "retirement")):
                selected_agents = ["office_support_agent"]
                selected_tools = ["get_notices"]

            elif any(w in q_lower for w in ("event", "reunion", "founders day", "gathering", "meetup")):
                selected_agents = ["event_agent"]
                selected_tools = ["get_events"]

            elif any(w in q_lower for w in ("transcript", "duplicate marksheet", "archive", "certificate", "records")):
                selected_agents = ["records_agent"]
                selected_tools = ["get_notices"]
                requires_confirmation = True
                confirmation_msg = "I can prepare an official transcript request for your graduating batch.\nProcessing time: 3 working days.\nWould you like me to initiate this request?"

            elif any(w in q_lower for w in ("mentor", "mentorship", "career", "networking", "volunteer")):
                selected_agents = ["community_agent"]
                selected_tools = ["get_events"]
                needs_recommendation = True

            elif any(w in q_lower for w in ("hall of fame", "achievements", "notable alumni", "honours", "awards")):
                needs_rag = True
                selected_agents = ["achievement_agent"]
                selected_tools = ["rag_retrieval"]

            else:
                selected_agents = ["alumni_assistant_agent"]
                selected_tools = ["get_events"]
                needs_recommendation = True

        # CRITICAL AUTHORIZATION BOUNDARY ENFORCEMENT
        authorized_agents = [
            agent_id for agent_id in selected_agents
            if SecurityValidator.is_agent_authorized(canonical_role, agent_id)
        ]

        if not authorized_agents:
            logger.warning(
                f"Selected agents {selected_agents} unauthorized for role '{canonical_role}'. "
                f"Falling back to default authorized agent."
            )
            default_map = {
                "student_parent": "student_assistant_agent",
                "teacher_staff": "teacher_copilot_agent",
                "visitor_applicant": "visitor_agent",
                "alumni_ex_employee": "alumni_assistant_agent",
            }
            authorized_agents = [default_map.get(canonical_role, "visitor_agent")]

        return ExecutionPlan(
            user_id=user_id,
            role=canonical_role,
            tenant_id=tenant_id,
            query=query,
            intent=intent,
            entities=entities,
            selected_agents=authorized_agents,
            selected_tools=selected_tools,
            needs_prediction=needs_prediction,
            prediction_type=prediction_type,
            needs_recommendation=needs_recommendation,
            needs_rag=needs_rag,
            requires_confirmation=requires_confirmation,
            confirmation_message=confirmation_msg,
        )
