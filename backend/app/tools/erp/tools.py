from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from app.core.security import SecurityValidator
from app.tools.base import BaseTool, ToolResult
from app.tools.erp.client import ERPClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class StudentIdSchema(BaseModel):
    student_id: str = Field(description="Student identifier (e.g. STU-1001 or 123)")


class ExamDetailsSchema(BaseModel):
    student_id: str = Field(description="Student identifier")
    exam_id: str | None = Field(default=None, description="Optional specific exam identifier")


class NoticesSchema(BaseModel):
    pass


class TimetableSchema(BaseModel):
    pass


class AdmissionSchema(BaseModel):
    enquiry_ref: str = Field(default="BCE/ENQ/2026/114", description="Application or enquiry reference")


class StaffSchema(BaseModel):
    staff_id: str = Field(description="Teacher or staff identifier")


class EmptySchema(BaseModel):
    pass


class LeaveApplicationSchema(BaseModel):
    date: str = Field(description="Date for requested leave (YYYY-MM-DD or descriptive date)")
    reason: str = Field(description="Reason for leave")


class AppointmentSchema(BaseModel):
    visitor_name: str = Field(description="Visitor or parent full name")
    date: str = Field(description="Requested appointment date")
    department: str = Field(default="Admissions Desk", description="Target department")


# ---------------------------------------------------------------------------
# Tools Implementation
# ---------------------------------------------------------------------------

class GetStudentProfileTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_student_profile",
            description="Retrieve student profile details (name, grade, section, roll number).",
            args_schema=StudentIdSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        is_allowed, reason = SecurityValidator.validate_data_access(
            requester_role, requester_user_id, "student_profile", student_id
        )
        if not is_allowed:
            return ToolResult(tool_name=self.name, success=False, error=reason)

        profile = await self.client.get_student_profile(student_id, tenant_id)
        sources = [{"module": "students", "record_id": student_id, "summary": "Student Profile"}]
        return ToolResult(tool_name=self.name, success=True, data=profile, sources=sources)


class GetStudentAttendanceTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_student_attendance",
            description="Retrieve student attendance records and percentage.",
            args_schema=StudentIdSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        is_allowed, reason = SecurityValidator.validate_data_access(
            requester_role, requester_user_id, "student_attendance", student_id
        )
        if not is_allowed:
            return ToolResult(tool_name=self.name, success=False, error=reason)

        attendance = await self.client.get_student_attendance(student_id, tenant_id)
        sources = [{"module": "attendance", "record_id": student_id, "summary": f"{len(attendance)} attendance records"}]
        return ToolResult(tool_name=self.name, success=True, data=attendance, sources=sources)


class GetStudentMarksTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_student_marks",
            description="Retrieve student academic exam scores, marks, and grades.",
            args_schema=StudentIdSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        is_allowed, reason = SecurityValidator.validate_data_access(
            requester_role, requester_user_id, "student_marks", student_id
        )
        if not is_allowed:
            return ToolResult(tool_name=self.name, success=False, error=reason)

        marks = await self.client.get_student_marks(student_id, tenant_id)
        sources = [{"module": "exam_scores", "record_id": student_id, "summary": f"{len(marks)} score entries"}]
        return ToolResult(tool_name=self.name, success=True, data=marks, sources=sources)


class GetExamDetailsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_exam_details",
            description="Retrieve exam schedule, syllabus, and guidelines.",
            args_schema=ExamDetailsSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        exam_id = kwargs.get("exam_id")
        exams = await self.client.get_exam_details(student_id, exam_id, tenant_id)
        sources = [{"module": "exams", "record_id": exam_id or "all", "summary": "Exam Schedule"}]
        return ToolResult(tool_name=self.name, success=True, data=exams, sources=sources)


class GetFeeDetailsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_fee_details",
            description="Retrieve student fee dues, payment history, and invoices.",
            args_schema=StudentIdSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        is_allowed, reason = SecurityValidator.validate_data_access(
            requester_role, requester_user_id, "fee_details", student_id
        )
        if not is_allowed:
            return ToolResult(tool_name=self.name, success=False, error=reason)

        fees = await self.client.get_fee_details(student_id, tenant_id)
        sources = [{"module": "fees", "record_id": student_id, "summary": "Fee ledger"}]
        return ToolResult(tool_name=self.name, success=True, data=fees, sources=sources)


class GetTransportDetailsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_transport_details",
            description="Retrieve school bus route, driver details, and timings.",
            args_schema=StudentIdSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        student_id = kwargs.get("student_id") or requester_user_id
        transport = await self.client.get_transport_details(student_id, tenant_id)
        sources = [{"module": "transport", "record_id": student_id, "summary": "Bus schedule & Route"}]
        return ToolResult(tool_name=self.name, success=True, data=transport, sources=sources)


class GetNoticesTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_notices",
            description="Retrieve official school notices, circulars, and announcements.",
            args_schema=NoticesSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        notices = await self.client.get_notices(requester_role, tenant_id)
        sources = [{"module": "notices", "record_id": "latest", "summary": f"{len(notices)} school circulars"}]
        return ToolResult(tool_name=self.name, success=True, data=notices, sources=sources)


class GetTimetableTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_timetable",
            description="Retrieve daily timetable, class periods, timings, and rooms.",
            args_schema=TimetableSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        timetable = await self.client.get_timetable(requester_role, requester_user_id, tenant_id)
        sources = [{"module": "timetable", "record_id": requester_user_id, "summary": "Timetable schedule"}]
        return ToolResult(tool_name=self.name, success=True, data=timetable, sources=sources)


class GetLibraryDataTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_library_data",
            description="Retrieve library book catalog, availability, and timings.",
            args_schema=EmptySchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        books = await self.client.get_library_data(requester_user_id, tenant_id)
        sources = [{"module": "library", "record_id": "catalog", "summary": "Library catalog"}]
        return ToolResult(tool_name=self.name, success=True, data=books, sources=sources)


class GetAdmissionDetailsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_admission_details",
            description="Retrieve admission application status, eligibility, and enquiry details.",
            args_schema=AdmissionSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        enquiry_ref = kwargs.get("enquiry_ref") or "BCE/ENQ/2026/114"
        admissions = await self.client.get_admission_details(enquiry_ref, tenant_id)
        sources = [{"module": "admissions", "record_id": enquiry_ref, "summary": "Admission records"}]
        return ToolResult(tool_name=self.name, success=True, data=admissions, sources=sources)


class GetStaffDetailsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_staff_details",
            description="Retrieve teacher/staff profile and assigned duties.",
            args_schema=StaffSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        staff_id = kwargs.get("staff_id") or requester_user_id
        staff = await self.client.get_staff_details(staff_id, tenant_id)
        sources = [{"module": "staff", "record_id": staff_id, "summary": "Staff assignment"}]
        return ToolResult(tool_name=self.name, success=True, data=staff, sources=sources)


class GetEventsTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_events",
            description="Retrieve school community events, Founders Day, and reunions.",
            args_schema=EmptySchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        events = await self.client.get_events(tenant_id)
        sources = [{"module": "events", "record_id": "school_calendar", "summary": "School events"}]
        return ToolResult(tool_name=self.name, success=True, data=events, sources=sources)


class GetCampusFacilitiesTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="get_campus_facilities",
            description="Retrieve campus facilities, laboratories, sports grounds, and locations.",
            args_schema=EmptySchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        facilities = await self.client.get_campus_facilities(tenant_id)
        sources = [{"module": "campus_facilities", "record_id": "campus_map", "summary": "Campus facilities"}]
        return ToolResult(tool_name=self.name, success=True, data=facilities, sources=sources)


class PreviewLeaveApplicationTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="preview_leave_application",
            description="Prepare leave application preview for review (requires human confirmation).",
            args_schema=LeaveApplicationSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        date = kwargs.get("date", "Tomorrow")
        reason = kwargs.get("reason", "Personal")
        preview = await self.client.preview_leave_application(requester_user_id, date, reason, tenant_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=preview,
            sources=[{"module": "leave_requests", "record_id": "preview", "summary": "Leave preview for human approval"}],
        )


class PreviewAppointmentTool(BaseTool):
    def __init__(self, client: ERPClient) -> None:
        super().__init__(
            name="preview_appointment",
            description="Prepare campus appointment preview for review (requires human confirmation).",
            args_schema=AppointmentSchema,
        )
        self.client = client

    async def run(
        self, requester_role: str, requester_user_id: str, tenant_id: str, **kwargs: Any
    ) -> ToolResult:
        if not self.validate_permission(requester_role):
            return ToolResult(tool_name=self.name, success=False, error=f"Permission denied for role {requester_role}")
        visitor_name = kwargs.get("visitor_name", requester_user_id)
        date = kwargs.get("date", "Tomorrow")
        department = kwargs.get("department", "Admissions")
        preview = await self.client.preview_appointment(visitor_name, date, department, tenant_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=preview,
            sources=[{"module": "appointments", "record_id": "preview", "summary": "Appointment preview"}],
        )
