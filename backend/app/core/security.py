from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

CanonicalRole = Literal[
    "student_parent",
    "teacher_staff",
    "visitor_applicant",
    "alumni_ex_employee",
]

ROLE_MAPPINGS: dict[str, CanonicalRole] = {
    "student_parent": "student_parent",
    "student": "student_parent",
    "parent": "student_parent",
    "teacher_staff": "teacher_staff",
    "teacher": "teacher_staff",
    "staff": "teacher_staff",
    "admin": "teacher_staff",
    "visitor_applicant": "visitor_applicant",
    "visitor": "visitor_applicant",
    "applicant": "visitor_applicant",
    "guest": "visitor_applicant",
    "alumni_ex_employee": "alumni_ex_employee",
    "alumni": "alumni_ex_employee",
    "ex_employee": "alumni_ex_employee",
    "ex-staff": "alumni_ex_employee",
    "former-staff": "alumni_ex_employee",
}

ROLE_PERMISSIONS: dict[CanonicalRole, set[str]] = {
    "student_parent": {
        "get_student_profile",
        "get_student_attendance",
        "get_student_marks",
        "get_exam_details",
        "get_fee_details",
        "get_transport_details",
        "get_notices",
        "get_timetable",
        "get_library_data",
        "preview_leave_application",
        "rag_retrieval",
    },
    "teacher_staff": {
        "get_student_profile",
        "get_student_attendance",
        "get_student_marks",
        "get_exam_details",
        "get_class_details",
        "get_staff_details",
        "get_notices",
        "get_timetable",
        "get_library_data",
        "get_hr_leave_details",
        "preview_leave_application",
        "preview_requisition",
        "rag_retrieval",
    },
    "visitor_applicant": {
        "get_admission_details",
        "get_campus_facilities",
        "get_notices",
        "get_events",
        "preview_enquiry",
        "preview_appointment",
        "rag_retrieval",
    },
    "alumni_ex_employee": {
        "get_alumni_profile",
        "get_events",
        "get_notices",
        "preview_transcript_request",
        "preview_donation",
        "rag_retrieval",
    },
}

SELECT_AGENTS_MAP: dict[CanonicalRole, set[str]] = {
    "student_parent": {
        "student_assistant_agent",
        "attendance_agent",
        "academic_agent",
        "exam_agent",
        "fee_agent",
        "transport_agent",
        "notice_agent",
        "learning_agent",
        "family_support_agent",
    },
    "teacher_staff": {
        "teacher_copilot_agent",
        "class_agent",
        "attendance_analysis_agent",
        "assessment_agent",
        "lesson_agent",
        "staff_knowledge_agent",
        "hr_leave_agent",
        "resource_agent",
    },
    "visitor_applicant": {
        "admission_agent",
        "visitor_agent",
        "campus_navigation_agent",
        "appointment_agent",
        "application_agent",
        "public_knowledge_agent",
    },
    "alumni_ex_employee": {
        "alumni_assistant_agent",
        "event_agent",
        "records_agent",
        "community_agent",
        "achievement_agent",
        "office_support_agent",
    },
}
ROLE_AGENT_PERMISSIONS = SELECT_AGENTS_MAP


class SecurityValidator:
    @staticmethod
    def normalize_role(role: str) -> CanonicalRole:
        norm = role.strip().lower()
        if norm in ROLE_MAPPINGS:
            return ROLE_MAPPINGS[norm]
        logger.warning(f"Unknown role '{role}', falling back to 'visitor_applicant'")
        return "visitor_applicant"

    @classmethod
    def is_tool_authorized(cls, role: str, tool_name: str) -> bool:
        canonical = cls.normalize_role(role)
        allowed = ROLE_PERMISSIONS.get(canonical, set())
        return tool_name in allowed

    @classmethod
    def is_agent_authorized(cls, role: str, agent_id: str) -> bool:
        canonical = cls.normalize_role(role)
        allowed = ROLE_AGENT_PERMISSIONS.get(canonical, set())
        return agent_id in allowed

    @classmethod
    def resolve_effective_role(
        cls,
        session_role: str | None = None,
        client_role: str | None = None,
        is_authenticated: bool = False,
        allow_role_inquiry: bool = False,
    ) -> tuple[CanonicalRole, bool]:
        if session_role:
            canonical_session = cls.normalize_role(session_role)
            if client_role:
                canonical_client = cls.normalize_role(client_role)
                if canonical_client != canonical_session:
                    logger.warning(
                        f"Role mismatch detected: session role is '{canonical_session}', "
                        f"but client claimed '{canonical_client}'"
                    )
                    return canonical_session, False
            return canonical_session, True

        if (is_authenticated or allow_role_inquiry) and client_role:
            return cls.normalize_role(client_role), True

        if client_role:
            canonical_client = cls.normalize_role(client_role)
            if canonical_client == "visitor_applicant":
                return "visitor_applicant", True
            logger.warning(f"Unauthenticated request attempted privileged role '{client_role}'. Clamped to visitor.")
            return "visitor_applicant", False

        return "visitor_applicant", True

    @classmethod
    def validate_data_access(
        cls,
        requester_role: str,
        requester_user_id: str,
        target_resource: str,
        target_user_id: str | None = None,
    ) -> tuple[bool, str]:
        canonical = cls.normalize_role(requester_role)

        if canonical == "student_parent":
            if target_resource in ("hr", "staff", "payroll", "teacher_records"):
                return False, f"Role '{requester_role}' is not authorized to access staff/HR resources."
            if target_user_id and str(target_user_id).strip().lower() != str(requester_user_id).strip().lower():
                return False, f"Students/Parents cannot access records of other students ({target_user_id})."

        if canonical == "visitor_applicant":
            if target_resource not in ("admissions", "campus", "events", "public_notices", "enquiry"):
                return False, "Visitors can only access public information and their own application."

        if canonical == "alumni_ex_employee":
            if target_resource in ("student_marks", "student_attendance", "hr_payroll"):
                return False, "Alumni cannot access current student or active staff records."


        return True, "Access granted"
