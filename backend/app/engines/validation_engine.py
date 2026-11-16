from __future__ import annotations

import re
from typing import Any
from app.core.security import SecurityValidator


class ValidationEngine:
    """Validates input, safety boundaries, and response integrity."""

    @staticmethod
    def validate_request(
        user_id: str,
        role: str,
        tenant_id: str,
        message: str,
    ) -> tuple[bool, str]:
        if not message or not message.strip():
            return False, "Message cannot be empty."
        if len(message) > 4000:
            return False, "Message exceeds maximum allowed character limit (4000)."
        if not user_id or not user_id.strip():
            return False, "User ID is required."
        if not tenant_id or not tenant_id.strip():
            return False, "Tenant ID is required."
        return True, "Valid request"

    @staticmethod
    def validate_response_safety(
        response_text: str,
        requester_role: str,
    ) -> str:
        canonical = SecurityValidator.normalize_role(requester_role)

        # Ensure student cannot see salary or teacher private HR tags
        if canonical == "student_parent":
            response_text = re.sub(r"\b(salary|payroll|ctc|bank\s+account)\s*:\s*\S+", "[REDACTED]", response_text, flags=re.IGNORECASE)

        return response_text
