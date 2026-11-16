from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from app.models import Role, SchoolContext
from app.engines.context_engine import get_context_engine

logger = logging.getLogger(__name__)

ROLE_FILES: dict[Role, str] = {
    "student": "students.csv",
    "parent": "parents.csv",
    "teacher": "teachers.csv",
    "visitor": "campus_facilities.csv",
    "alumni": "alumni.csv",
}

DEFAULT_IN_MEMORY_MODULES: dict[str, list[dict[str, Any]]] = {
    "students": [
        {"student_id": "STU-1001", "name": "Aditya Verma", "class_name": "Class VIII A", "section": "A", "roll_no": "12", "attendance": "92%", "fee_balance": "18,500"},
    ],
    "parents": [
        {"parent_id": "PAR-0817", "student_id": "STU-1001", "name": "Dr. Rajesh Verma", "class_name": "Class VIII A", "attendance": "92%", "fee_balance": "18,500"},
    ],
    "teachers": [
        {"staff_id": "TCH-201", "name": "Prof. S. Ranganathan", "assigned_class": "Class VIII A", "next_period": "Science Lab · 10:10", "leave_balance": "6 casual days"},
    ],
    "timetable": [
        {"subject": "Science Lab", "time": "10:10 AM", "room": "Room 204", "teacher": "Prof. S. Ranganathan", "class_name": "Class VIII A"},
        {"subject": "Mathematics", "time": "08:45 AM", "room": "Room 204", "teacher": "Mr. Sharma", "class_name": "Class VIII A"},
    ],
    "attendance": [
        {"student_id": "STU-1001", "month": "Current Term", "percentage": "92%", "status": "Present", "class_name": "Class VIII A"},
    ],
    "fees": [
        {"student_id": "STU-1001", "fee_balance": "18,500", "amount": "18,500", "due_date": "15 September 2026", "status": "Due", "class_name": "Class VIII A"},
    ],
    "fee_payments": [
        {"receipt_id": "REC-2026-901", "amount": "26,500", "date": "10 July 2026", "status": "Success", "class_name": "Class VIII A"},
    ],
    "homework": [
        {"subject": "Science", "assignment": "Light Reflection & Refraction Lab Record", "due": "Friday", "class_name": "Class VIII A"},
    ],
    "exams": [
        {"subject": "Mathematics", "date": "12 Sep 2026", "session": "09:30 AM", "room": "Hall 3", "class_name": "Class VIII A"},
    ],
    "exam_scores": [
        {"subject": "Mathematics", "score": "92", "grade": "A1", "class_name": "Class VIII A"},
        {"subject": "Science", "score": "88", "grade": "A1", "class_name": "Class VIII A"},
    ],
    "library_books": [
        {"title": "Science Lab Manual Class VIII", "rack": "Rack 4B", "floor": "1st Floor", "availability": "Available"},
    ],
    "events": [
        {"title": "Founders Day", "date": "05 Sep", "time": "09:30 AM", "venue": "Main Auditorium"},
    ],
    "notices": [
        {"title": "Term-2 Assessment Guidelines", "content": "CBSE aligned competency assessment.", "date": "14 Oct 2026"},
    ],
    "campus_facilities": [
        {"name": "Admissions Desk", "hours": "09:00–15:30", "location": "Gate 1"},
        {"name": "Dr. APJ Abdul Kalam STEM Center", "hours": "08:30–15:30", "location": "Science Block"},
    ],
    "admissions": [
        {"enquiry_id": "BCE/ENQ/2026/114", "status": "Under Review", "counselling": "Contact Admissions Desk"},
    ],
    "alumni": [
        {"alumni_id": "ALM-2015-01", "name": "Rohan Sharma", "connection": "Class of 2015", "last_engagement": "Founders Day"},
    ],
}


class CsvSchoolDataRepository:
    """School Data Repository with in-memory fallbacks and dynamic UI Context support.
    
    Operates smoothly even if no CSV files exist on disk.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._cache: dict[str, list[dict[str, Any]]] = {}

    def read(self, filename: str) -> list[dict[str, Any]]:
        if filename in self._cache:
            return self._cache[filename]
        
        path = self.data_dir / filename
        if path.exists():
            try:
                with path.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                    self._cache[filename] = rows
                    return rows
            except Exception as e:
                logger.warning(f"Error reading {filename}: {e}")

        # In-memory dynamic fallback
        stem = Path(filename).stem
        fallback_rows = DEFAULT_IN_MEMORY_MODULES.get(stem, [])
        self._cache[filename] = fallback_rows
        return fallback_rows

    def _profile(self, role: Role, user_ref: str | None) -> dict[str, Any]:
        target_file = ROLE_FILES.get(role, "students.csv")
        rows = self.read(target_file)
        if role == "visitor":
            return {"role": "visitor", "access": "public campus information"}
        if not user_ref:
            return rows[0] if rows else {"role": role}
        key = "student_id" if role in ("student", "parent") else "staff_id" if role == "teacher" else "alumni_id"
        return next((row for row in rows if row.get(key) == user_ref), rows[0] if rows else {"role": role})

    def get_context(self, role: Role, user_ref: str | None = None) -> SchoolContext:
        profile = self._profile(role, user_ref)
        records: dict[str, list[dict[str, Any]]] = {}
        allowed = [
            "timetable",
            "homework",
            "attendance",
            "fees",
            "fee_payments",
            "exams",
            "exam_scores",
            "library_books",
            "events",
            "notices",
            "sports",
            "hostel",
            "notifications",
        ]
        if role == "teacher":
            allowed += ["hrms", "inventory"]
        if role == "visitor":
            allowed = [
                "admissions",
                "preadmissions",
                "events",
                "notices",
                "campus_facilities",
                "sports",
                "notifications",
            ]
        if role == "alumni":
            allowed = ["alumni", "events", "notices", "sports", "notifications", "campus_facilities"]
        for module in allowed:
            filename = f"{module}.csv"
            # Read either from CSV if present or in-memory fallback
            rows = self.read(filename)
            if rows:
                records[module] = self._scope_rows(role, profile, module, rows)
        return SchoolContext(role=role, user_ref=user_ref, profile=profile, records=records)

    def _scope_rows(
        self, role: Role, profile: dict[str, Any], module: str, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if role == "visitor" or role == "alumni":
            return rows
        class_name = profile.get("class_name", "Class VIII A")
        if module in {"timetable", "homework", "attendance", "fees", "fee_payments", "exams", "exam_scores", "hostel"}:
            return [row for row in rows if not row.get("class_name") or row.get("class_name") == class_name]
        return rows

    def search(self, role: Role, user_ref: str | None, query: str) -> list[dict[str, Any]]:
        context = self.get_context(role, user_ref)
        query_lower = query.lower()
        results = []
        for module, rows in context.records.items():
            for row in rows:
                if query_lower in " ".join(str(value) for value in row.values()).lower():
                    results.append({"module": module, **row})
        return results[:12]
