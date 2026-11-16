from __future__ import annotations

import re
from typing import Any


class IntentEngine:
    """Classifies user query intent across all 4 school roles."""

    INTENT_PATTERNS = [
        # Attendance
        (r"\b(attendance|present|absent|leave|bunk|days attended)\b", "attendance"),
        # Fees
        (r"\b(fee|fees|due|dues|payment|balance|receipt|invoice|tuition)\b", "fees"),
        # Academic & Marks
        (r"\b(marks|grade|grades|score|scores|result|results|report card|percentage|academic|progress)\b", "marks"),
        # Exams
        (r"\b(exam|exams|test|tests|schedule|hall ticket|blueprint|midterm|final|board)\b", "exam"),
        # Timetable & Routine
        (r"\b(timetable|timing|timing|schedule|period|class time|tomorrow timing|school time|bell)\b", "timetable"),
        # Transport
        (r"\b(bus|transport|route|driver|pickup|drop|van)\b", "transport"),
        # Library
        (r"\b(library|book|books|borrow|catalog|author|edition)\b", "library"),
        # Notices & Circulars
        (r"\b(notice|circular|announcement|holiday|news|calendar|event)\b", "notices"),
        # Admissions
        (r"\b(admission|admissions|apply|enquiry|eligibility|fee structure|icse curriculum|prospectus|enrol)\b", "admissions"),
        # Staff & HR
        (r"\b(casual leave|medical leave|salary|payslip|colleague|substitute|lesson plan|quiz)\b", "staff_hr"),
        # Alumni
        (r"\b(alumni|reunion|founders day|batch|transcript|heritage|memories|contribute|donate|mentor)\b", "alumni"),
        # Leave application
        (r"\b(apply leave|request leave|leave application|sick leave|casual leave for)\b", "leave_application"),
    ]

    @classmethod
    def detect_intent(cls, message: str, role: str) -> str:
        msg_lower = message.lower()

        # Check for leave application first
        if re.search(r"\b(apply leave|request leave|take leave|need leave)\b", msg_lower):
            return "leave_application"

        # Check patterns
        for pattern, intent in cls.INTENT_PATTERNS:
            if re.search(pattern, msg_lower):
                # Distinguish deep attendance query
                if intent == "attendance":
                    if any(w in msg_lower for w in ("why", "low", "falling", "drop", "how to improve", "what should")):
                        return "attendance_analysis"
                    return "attendance_inquiry"
                if intent == "marks":
                    if any(w in msg_lower for w in ("why", "improve", "predict", "trajectory", "weak")):
                        return "academic_analysis"
                    return "marks_inquiry"
                return intent

        # Default fallback
        if "student" in role or "parent" in role:
            return "general_student_support"
        elif "teacher" in role or "staff" in role:
            return "teacher_assistance"
        elif "visitor" in role:
            return "admissions_inquiry"
        return "general_inquiry"
