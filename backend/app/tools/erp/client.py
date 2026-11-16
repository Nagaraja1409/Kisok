from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ERPClient(ABC):
    """Abstract interface defining the ERP API contract.
    
    Both MockCsvERPClient and HttpERPClient implement this interface identically,
    allowing agents and tools to remain completely unchanged when swapping backends.
    """

    @abstractmethod
    async def get_student_profile(self, student_id: str, tenant_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def get_student_attendance(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_student_marks(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_exam_details(self, student_id: str, exam_id: str | None, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_fee_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_transport_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_notices(self, role: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_timetable(self, role: str, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_library_data(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_admission_details(self, enquiry_ref: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_staff_details(self, staff_id: str, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_events(self, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_campus_facilities(self, tenant_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def preview_leave_application(
        self, user_id: str, date: str, reason: str, tenant_id: str
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def preview_appointment(
        self, visitor_name: str, date: str, department: str, tenant_id: str
    ) -> dict[str, Any]:
        ...
