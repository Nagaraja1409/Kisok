from __future__ import annotations

import logging
from typing import Any
import httpx

from app.tools.erp.client import ERPClient

logger = logging.getLogger(__name__)


class HttpERPClient(ERPClient):
    """Production HTTP ERP client for live school ERP backend integration."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, tenant_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Tenant-ID": tenant_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get(self, endpoint: str, tenant_id: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._headers(tenant_id)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def _post(self, endpoint: str, tenant_id: str, data: dict[str, Any]) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._headers(tenant_id)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()

    async def get_student_profile(self, student_id: str, tenant_id: str) -> dict[str, Any] | None:
        data = await self._get(f"students/{student_id}", tenant_id)
        return data if isinstance(data, dict) else None

    async def get_student_attendance(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"students/{student_id}/attendance", tenant_id)

    async def get_student_marks(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"students/{student_id}/marks", tenant_id)

    async def get_exam_details(self, student_id: str, exam_id: str | None, tenant_id: str) -> list[dict[str, Any]]:
        params = {"exam_id": exam_id} if exam_id else None
        return await self._get(f"students/{student_id}/exams", tenant_id, params=params)

    async def get_fee_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"students/{student_id}/fees", tenant_id)

    async def get_transport_details(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"students/{student_id}/transport", tenant_id)

    async def get_notices(self, role: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get("notices", tenant_id, params={"role": role})

    async def get_timetable(self, role: str, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get("timetable", tenant_id, params={"role": role, "user_id": user_id})

    async def get_library_data(self, student_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"students/{student_id}/library", tenant_id)

    async def get_admission_details(self, enquiry_ref: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"admissions/{enquiry_ref}", tenant_id)

    async def get_staff_details(self, staff_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get(f"staff/{staff_id}", tenant_id)

    async def get_events(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get("events", tenant_id)

    async def get_campus_facilities(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._get("campus/facilities", tenant_id)

    async def preview_leave_application(
        self, user_id: str, date: str, reason: str, tenant_id: str
    ) -> dict[str, Any]:
        return await self._post("leave/preview", tenant_id, {"user_id": user_id, "date": date, "reason": reason})

    async def preview_appointment(
        self, visitor_name: str, date: str, department: str, tenant_id: str
    ) -> dict[str, Any]:
        return await self._post(
            "appointments/preview",
            tenant_id,
            {"visitor_name": visitor_name, "date": date, "department": department},
        )
