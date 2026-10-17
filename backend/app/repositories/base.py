from __future__ import annotations

from typing import Protocol

from app.models import Role, SchoolContext


class SchoolDataRepository(Protocol):
    def get_context(self, role: Role, user_ref: str | None = None) -> SchoolContext: ...
    def search(self, role: Role, user_ref: str | None, query: str) -> list[dict]: ...


class ErpApiSchoolDataRepository:
    """Future adapter seam. Implement the same methods when the ERP API contract is available."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_context(self, role: Role, user_ref: str | None = None) -> SchoolContext:
        raise NotImplementedError("ERP API adapter is intentionally not enabled in CSV-first release")

    def search(self, role: Role, user_ref: str | None, query: str) -> list[dict]:
        raise NotImplementedError("ERP API adapter is intentionally not enabled in CSV-first release")
