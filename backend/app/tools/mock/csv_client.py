from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from app.tools.erp.client import ERPClient

logger = logging.getLogger(__name__)


class MockCsvERPClient(ERPClient):
    """High-fidelity Mock ERP client backed by CSV demonstration records.
    
    Acts as a stand-in for live ERP APIs during development and testing.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._cache: dict[str, list[dict[str, Any]]] = {}

    def _read_csv(self, filename: str) -> list[dict[str, Any]]:
        if filename in self._cache:
            return self._cache[filename]
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [dict(row) for row in reader]
                self._cache[filename] = rows
                return rows
        except Exception as exc:
            logger.error(f"Error reading {file_path}: {exc}")
            return []

    async def get_student_profile(self, student_id: str, tenant_id: str) -> dict[str, Any] | None:
        rows = self._read_csv("students.csv")
        s_id = str(student_id).strip().lower()
        for r in rows:
            if str(r.get("student_id", "")).strip().lower() == s_id or str(r.get("id", "")).strip().lower() == s_id:
                return r
        # Return first student if generic/fallback query
        if rows:
            return rows[0]
        return None

    async def get_student_attendance(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("attendance.csv")
        s_id = str(student_id).strip().lower()
        matches = [
            r for r in rows
            if str(r.get("student_id", "")).strip().lower() == s_id or str(r.get("id", "")).strip().lower() == s_id
        ]
        return matches if matches else rows

    async def get_student_marks(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("exam_scores.csv")
        s_id = str(student_id).strip().lower()
        matches = [
            r for r in rows
            if str(r.get("student_id", "")).strip().lower() == s_id
        ]
        return matches if matches else rows

    async def get_exam_details(self, student_id: str, exam_id: str | None, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("exams.csv")
        if exam_id:
            return [r for r in rows if str(r.get("exam_id", "")).strip().lower() == str(exam_id).strip().lower()]
        return rows

    async def get_fee_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("fees.csv")
        s_id = str(student_id).strip().lower()
        matches = [
            r for r in rows
            if str(r.get("student_id", "")).strip().lower() == s_id
        ]
        return matches if matches else rows

    async def get_transport_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        # Mock transport data
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
        rows = self._read_csv("notices.csv")
        role_lower = role.lower()
        filtered = [
            r for r in rows
            if r.get("audience", "").lower() in ("all", role_lower, "public", "students", "parents", "teachers")
        ]
        return filtered if filtered else rows

    async def get_timetable(self, role: str, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return self._read_csv("timetable.csv")

    async def get_library_data(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return self._read_csv("library_books.csv")

    async def get_admission_details(self, enquiry_ref: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("admissions.csv")
        ref_lower = enquiry_ref.strip().lower()
        matches = [
            r for r in rows
            if str(r.get("enquiry_ref", "")).strip().lower() == ref_lower or str(r.get("id", "")).strip().lower() == ref_lower
        ]
        return matches if matches else rows

    async def get_staff_details(self, staff_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._read_csv("teachers.csv")
        s_lower = staff_id.strip().lower()
        matches = [
            r for r in rows
            if str(r.get("teacher_id", "")).strip().lower() == s_lower
        ]
        return matches if matches else rows

    async def get_events(self, tenant_id: str) -> list[dict[str, Any]]:
        return self._read_csv("events.csv")

    async def get_campus_facilities(self, tenant_id: str) -> list[dict[str, Any]]:
        return self._read_csv("campus_facilities.csv")

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
