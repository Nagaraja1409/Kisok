from __future__ import annotations

import logging
from typing import Any
from app.rag.qdrant import QdrantVectorStore

logger = logging.getLogger(__name__)

INITIAL_SCHOOL_DOCUMENTS: list[dict[str, Any]] = [
    {
        "document_id": "policy_fee_01",
        "title": "School Fee Payment and Due Date Policy",
        "document_type": "policy",
        "department": "accounts",
        "role": "all",
        "access_level": "public",
        "tenant_id": "school_001",
        "content": "Fees must be paid on or before the 10th of every term. A grace period of 5 days is allowed before a late fee of ₹100 per week applies. Online payments via net banking, UPI, and school portal are accepted. Fee receipts are generated within 24 hours.",
    },
    {
        "document_id": "policy_attendance_01",
        "title": "Mandatory Attendance and Leave Regulation",
        "document_type": "policy",
        "department": "academics",
        "role": "student_parent",
        "access_level": "student",
        "tenant_id": "school_001",
        "content": "A minimum of 75% overall attendance is mandatory to appear for term-end board and internal examinations. Parents must submit medical certificates for leaves exceeding 3 days. Any student with attendance below 70% is flagged for academic counseling.",
    },
    {
        "document_id": "circular_exam_2026",
        "title": "Annual ICSE Examination Schedule & Guidelines 2026",
        "document_type": "circular",
        "department": "examination",
        "role": "all",
        "access_level": "public",
        "tenant_id": "school_001",
        "content": "The 2026 ICSE Mid-Term examinations commence on October 12, 2026. Hall tickets will be issued one week prior. Electronic devices are strictly prohibited in examination halls. Reporting time is 08:30 AM sharp.",
    },
    {
        "document_id": "policy_hr_leave_01",
        "title": "Staff Casual and Medical Leave Policy",
        "document_type": "policy",
        "department": "hr",
        "role": "teacher_staff",
        "access_level": "staff",
        "tenant_id": "school_001",
        "content": "Teaching staff are entitled to 12 casual leaves and 10 medical leaves per academic year. Prior notice of at least 48 hours is required for casual leaves unless an emergency occurs. Substitute teacher arrangements must be coordinated with the Academic Coordinator.",
    },
    {
        "document_id": "admissions_guide_2026",
        "title": "School Admissions Procedure and Criteria",
        "document_type": "guide",
        "department": "admissions",
        "role": "visitor_applicant",
        "access_level": "public",
        "tenant_id": "school_001",
        "content": "Admissions for Academic Year 2026-2027 are open for Nursery through Class XI. Applicants must submit student birth certificate, previous school transfer certificate, and 3 passport-size photographs. Campus tours operate Monday through Friday from 09:00 AM to 03:30 PM.",
    },
    {
        "document_id": "alumni_guidelines_01",
        "title": "Alumni Mentorship and Founders Day Registration",
        "document_type": "circular",
        "department": "alumni_relations",
        "role": "alumni_ex_employee",
        "access_level": "public",
        "tenant_id": "school_001",
        "content": "Founders Day celebration is held on the first Saturday of September. Alumni can participate in student career mentorship programs, batch reunions, and school heritage archive contributions. Transcripts can be requested through the alumni desk with 3 business days turnaround.",
    },
]


class RAGIngestionService:
    def __init__(self, vector_store: QdrantVectorStore) -> None:
        self.vector_store = vector_store

    async def seed_initial_knowledge(self) -> int:
        count = await self.vector_store.upsert_documents(INITIAL_SCHOOL_DOCUMENTS)
        logger.info(f"Successfully seeded {count} school policy and circular documents into Qdrant store.")
        return count
