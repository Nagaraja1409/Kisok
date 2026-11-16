from __future__ import annotations

import logging
from typing import Any
from app.engines.context_engine import get_context_engine
from app.tools.erp.client import ERPClient

logger = logging.getLogger(__name__)

# Fallback in-memory school demonstration records (Zero CSV dependency)
DEFAULT_STUDENT_PROFILE = {
    "student_id": "STU-1001",
    "id": "STU-1001",
    "name": "Aditya Verma",
    "class_name": "Class VIII A",
    "section": "A",
    "roll_no": "12",
    "academic_year": "2026-2027",
    "guardian_name": "Dr. Rajesh Verma",
    "contact": "+91 98765 43210",
    "address": "42, Green Park Avenue, Bengaluru",
}

DEFAULT_ATTENDANCE = [
    {"student_id": "STU-1001", "month": "August", "class_held": 24, "present": 23, "absent": 1, "percentage": "95.8%", "status": "Present"},
    {"student_id": "STU-1001", "month": "September", "class_held": 22, "present": 20, "absent": 2, "percentage": "90.9%", "status": "Present"},
    {"student_id": "STU-1001", "month": "October", "class_held": 18, "present": 17, "absent": 1, "percentage": "94.4%", "status": "Present"},
]

DEFAULT_MARKS = [
    {"student_id": "STU-1001", "subject": "Mathematics", "exam": "Term-1", "marks": 92, "max_marks": 100, "grade": "A1"},
    {"student_id": "STU-1001", "subject": "Science", "exam": "Term-1", "marks": 88, "max_marks": 100, "grade": "A1"},
    {"student_id": "STU-1001", "subject": "English", "exam": "Term-1", "marks": 85, "max_marks": 100, "grade": "A2"},
    {"student_id": "STU-1001", "subject": "Social Studies", "exam": "Term-1", "marks": 90, "max_marks": 100, "grade": "A1"},
]

DEFAULT_EXAMS = [
    {"exam_id": "EXM-01", "name": "Mid-Term Examination 2026", "start_date": "2026-11-10", "end_date": "2026-11-20", "status": "Upcoming"},
    {"exam_id": "EXM-02", "name": "CBSE Board Pre-Board 1", "start_date": "2026-12-05", "end_date": "2026-12-18", "status": "Scheduled"},
]

DEFAULT_FEES = [
    {"student_id": "STU-1001", "year": "2026-27", "receivable": 45000, "collection": 26500, "concession": 0, "balance": 18500, "due": 18500, "fee_balance": 18500, "status": "Due"},
]

DEFAULT_TIMETABLE = [
    {"day": "Monday", "period": "Period 1", "time": "08:45 - 09:30 AM", "subject": "Mathematics", "teacher": "Mr. Sharma", "room": "Room 204"},
    {"day": "Monday", "period": "Period 2", "time": "09:30 - 10:15 AM", "subject": "English", "teacher": "Ms. Roy", "room": "Room 204"},
    {"day": "Monday", "period": "Period 3", "time": "10:30 - 11:15 AM", "subject": "Science Lab", "teacher": "Dr. Sen", "room": "Room 204"},
    {"day": "Monday", "period": "Period 4", "time": "11:15 - 12:00 PM", "subject": "Social Studies", "teacher": "Mrs. Menon", "room": "Room 204"},
]

DEFAULT_NOTICES = [
    {"id": "NOT-01", "title": "CBSE Competency-Based Assessment Term-2 Rubrics", "date": "14 Oct 2026", "audience": "all", "content": "CBSE rubrics aligned for class IX and X internal evaluation."},
    {"id": "NOT-02", "title": "Annual Science & STEM Robotics Exhibition 2026", "date": "14 Oct 2026", "audience": "all", "content": "Rosters for faculty mentors and students due by Friday, 24th Oct."},
    {"id": "NOT-03", "title": "Gandhi Jayanti Campus Holiday Notice", "date": "01 Oct 2026", "audience": "all", "content": "School campus remains closed for Gandhi Jayanti."},
]

DEFAULT_CAMPUS_FACILITIES = [
    {"facility_id": "FAC-01", "name": "Main Reception & Welcome Desk", "location": "Gate 1, Ground Floor", "hours": "08:00 AM - 04:30 PM"},
    {"facility_id": "FAC-02", "name": "Dr. APJ Abdul Kalam STEM Center", "location": "Science Block, 2nd Floor", "hours": "08:30 AM - 03:30 PM"},
    {"facility_id": "FAC-03", "name": "Admissions & Counseling Center", "location": "Vivekananda Block A, Room 104", "hours": "09:00 AM - 03:30 PM"},
    {"facility_id": "FAC-04", "name": "Central Sports Complex & Auditorium", "location": "West Campus", "hours": "06:30 AM - 06:00 PM"},
]

DEFAULT_ADMISSIONS = [
    {"enquiry_ref": "BCE/ENQ/2026/114", "id": "BCE/ENQ/2026/114", "student_name": "Rohan Sharma", "grade_applied": "Class VI", "status": "Documents Under Review", "next_step": "Campus Tour & Document Verification"},
]


class DynamicUIERPClient(ERPClient):
    """Dynamic ERP Client that seamlessly extracts data from the active Next.js UI context,
    with zero reliance on disk CSV files.
    """

    def __init__(self, context_engine=None) -> None:
        self.context_engine = context_engine or get_context_engine()

    def _get_context(self, user_id: str | None = None) -> dict[str, Any]:
        return self.context_engine.get_ui_context(user_id) or {}

    async def get_student_profile(self, student_id: str, tenant_id: str) -> dict[str, Any] | None:
        ctx = self._get_context(student_id)
        details = ctx.get("studentDetails") or ctx.get("profile")
        if details and isinstance(details, dict):
            return {
                "student_id": details.get("admNo") or details.get("student_id") or student_id,
                "name": details.get("name") or DEFAULT_STUDENT_PROFILE["name"],
                "class_name": details.get("className") or details.get("class_name") or "Class VIII A",
                "section": details.get("sectionName") or details.get("section") or "A",
                "roll_no": details.get("rollNo") or details.get("roll_no") or "12",
                "academic_year": details.get("academicYear") or details.get("academic_year") or "2026-2027",
                "email": details.get("email", ""),
                "mobile": details.get("mobile", ""),
                "father_name": details.get("fatherName", ""),
            }
        return DEFAULT_STUDENT_PROFILE

    async def get_student_attendance(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(student_id)
        raw_att = ctx.get("attendanceData") or ctx.get("attendance") or ctx.get("attendanceList")
        if raw_att and isinstance(raw_att, list):
            res = []
            for a in raw_att:
                m_name = a.get("month") or a.get("MONTH_NAME") or "Current"
                c_held = a.get("classHeld") or a.get("CLASS_HELD") or 20
                c_pres = a.get("totalPresent") or a.get("TOTAL_PRESENT") or 18
                pct = a.get("percentage")
                if pct is None and c_held > 0:
                    pct = round((c_pres / c_held) * 100, 1)
                pct_str = f"{pct}%" if not str(pct).endswith("%") else str(pct)
                res.append({
                    "student_id": student_id,
                    "month": m_name,
                    "class_held": c_held,
                    "present": c_pres,
                    "percentage": pct_str,
                    "status": "Present" if float(str(pct_str).replace("%", "")) >= 75.0 else "Absent Risk",
                })
            return res
        return DEFAULT_ATTENDANCE

    async def get_student_marks(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(student_id)
        raw_marks = ctx.get("examMarksData") or ctx.get("marks")
        if raw_marks and isinstance(raw_marks, list):
            res = []
            for m in raw_marks:
                res.append({
                    "student_id": student_id,
                    "subject": m.get("subject", "General"),
                    "exam": m.get("exam", "Term Exam"),
                    "marks": m.get("obtainedMarks") or m.get("marks", 0),
                    "score": m.get("obtainedMarks") or m.get("marks", 0),
                    "max_marks": m.get("maxMarks", 100),
                    "grade": m.get("grade", "A"),
                })
            return res
        return DEFAULT_MARKS

    async def get_exam_details(self, student_id: str, exam_id: str | None, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(student_id)
        raw_exams = ctx.get("examsList") or ctx.get("exams")
        if raw_exams and isinstance(raw_exams, list):
            return [
                {
                    "exam_id": e.get("id") or f"EXM-{i+1}",
                    "name": e.get("name") or e.get("exam_name", "Semester Exam"),
                    "status": "Scheduled",
                }
                for i, e in enumerate(raw_exams)
            ]
        return DEFAULT_EXAMS

    async def get_fee_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(student_id)
        raw_fees = ctx.get("feeData") or ctx.get("fees")
        if raw_fees and isinstance(raw_fees, list):
            res = []
            for f in raw_fees:
                bal = f.get("balance", 0)
                res.append({
                    "student_id": student_id,
                    "year": f.get("year", "2026-27"),
                    "receivable": f.get("receivable", 0),
                    "collection": f.get("collection", 0),
                    "balance": bal,
                    "due": bal,
                    "fee_balance": bal,
                    "status": f.get("status") or ("Due" if bal > 0 else "Cleared"),
                })
            return res
        return DEFAULT_FEES

    async def get_transport_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return [
            {
                "route_no": "Route 4",
                "bus_number": "KA-01-F-1234",
                "driver_name": "Ramesh Kumar",
                "driver_contact": "+91 98450 12345",
                "pickup_stop": "Richmond Town Junction",
                "pickup_time": "07:35 AM",
                "drop_time": "03:45 PM",
                "status": "On Schedule",
            }
        ]

    async def get_notices(self, role: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context()
        raw_notices = ctx.get("noticesData") or ctx.get("staffNotices") or ctx.get("notices")
        if raw_notices and isinstance(raw_notices, list):
            return [
                {
                    "id": str(n.get("id", "NOT-01")),
                    "title": n.get("title", "School Notice"),
                    "content": n.get("details") or n.get("content") or n.get("desc", ""),
                    "date": n.get("date") or n.get("startDate", "Today"),
                    "audience": "all",
                }
                for n in raw_notices
            ]
        return DEFAULT_NOTICES

    async def get_timetable(self, role: str, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(user_id)
        # Check for staff schedule
        raw_sched = ctx.get("teachingSchedule") or ctx.get("schedule")
        if raw_sched and isinstance(raw_sched, list):
            return [
                {
                    "day": s.get("day", "Monday"),
                    "period": f"Period {s.get('period', '1')}",
                    "time": s.get("time", "08:00 AM"),
                    "subject": s.get("subject", "Mathematics"),
                    "room": s.get("room", "Rm 204"),
                    "class_name": s.get("class", "Class 6 A"),
                    "topic": s.get("topic", "Classroom Session"),
                }
                for s in raw_sched
            ]
        # Check for student timetable
        tt = ctx.get("timetableData")
        if tt and isinstance(tt, dict) and tt.get("studentTT"):
            return [
                {
                    "day": item.get("ttmD_DayName", "Monday"),
                    "period": item.get("TTMP_PeriodName", "Period 1"),
                    "time": "Scheduled Hour",
                    "subject": item.get("ISMS_SubjectName", "Subject"),
                    "teacher": item.get("EmpName", "Faculty"),
                    "room": item.get("room", "Room 204"),
                }
                for item in tt.get("studentTT", [])
            ]
        return DEFAULT_TIMETABLE

    async def get_library_data(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return [
            {"book_id": "LIB-01", "title": "Science & Environment (Class VIII)", "author": "NCERT", "rack": "Rack 4B", "floor": "1st Floor", "availability": "Available"},
            {"book_id": "LIB-02", "title": "Foundation Mathematics", "author": "R.S. Aggarwal", "rack": "Rack 2A", "floor": "Ground Floor", "availability": "Available"},
            {"book_id": "LIB-03", "title": "Great Stories for Children", "author": "Ruskin Bond", "rack": "Rack 7C", "floor": "2nd Floor", "availability": "Checked In"},
        ]

    async def get_admission_details(self, enquiry_ref: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context()
        admissions = ctx.get("admissions") or ctx.get("admission")
        if admissions and isinstance(admissions, dict):
            return [admissions]
        return DEFAULT_ADMISSIONS

    async def get_staff_details(self, staff_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context(staff_id)
        session = ctx.get("session") or ctx.get("staffProfile")
        if session and isinstance(session, dict):
            return [{
                "teacher_id": str(session.get("userId") or session.get("empcode") or staff_id),
                "name": session.get("userName") or "Faculty Educator",
                "assigned_class": "Class VIII A",
                "subject": "Mathematics & Science",
                "next_period": "Class 8 A · Rm 208",
            }]
        return [{
            "teacher_id": staff_id,
            "name": "Prof. S. Ranganathan",
            "assigned_class": "Class VIII A",
            "subject": "Mathematics",
            "next_period": "Class 8 A · Rm 208",
        }]

    async def get_events(self, tenant_id: str) -> list[dict[str, Any]]:
        ctx = self._get_context()
        ev = ctx.get("eventsData") or ctx.get("events")
        if ev and isinstance(ev, list):
            return [
                {
                    "id": str(e.get("id", "EVT-01")),
                    "title": e.get("title", "Campus Event"),
                    "date": e.get("startDate", "Upcoming"),
                    "venue": e.get("venue", "Main Campus"),
                    "description": e.get("desc", ""),
                }
                for e in ev
            ]
        return [
            {"id": "EVT-01", "title": "Annual Founders Day Celebration", "date": "05 Nov 2026", "venue": "Main Auditorium", "description": "Annual ceremony honouring school foundation."},
            {"id": "EVT-02", "title": "Inter-School Science Olympiad 2026", "date": "18 Nov 2026", "venue": "STEM Center", "description": "National science competition."},
        ]

    async def get_campus_facilities(self, tenant_id: str) -> list[dict[str, Any]]:
        return DEFAULT_CAMPUS_FACILITIES

    async def preview_leave_application(
        self, user_id: str, date: str, reason: str, tenant_id: str
    ) -> dict[str, Any]:
        return {
            "status": "preview_pending_confirmation",
            "action": "leave_application",
            "user_id": user_id,
            "leave_date": date,
            "reason": reason,
            "confirmation_required": True,
            "message": f"I can prepare a leave request for {date} (Reason: {reason}). Would you like me to submit it?",
        }

    async def preview_appointment(
        self, visitor_name: str, date: str, department: str, tenant_id: str
    ) -> dict[str, Any]:
        return {
            "status": "preview_pending_confirmation",
            "action": "appointment_booking",
            "visitor_name": visitor_name,
            "appointment_date": date,
            "department": department,
            "confirmation_required": True,
            "message": f"I can schedule an appointment with {department} on {date} for {visitor_name}. Would you like me to confirm this booking?",
        }
