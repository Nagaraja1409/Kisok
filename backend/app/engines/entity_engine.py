from __future__ import annotations

import re
from typing import Any


class EntityExtractionEngine:
    """Extracts school entities (student IDs, dates, subjects, amounts, refs)."""

    @classmethod
    def extract_entities(cls, text: str, user_id: str | None = None) -> dict[str, Any]:
        entities: dict[str, Any] = {}

        # 1. Student / User ID
        stu_match = re.search(r"\b(STU[-_]?\d+|[A-Z]{2,4}\d{3,6}|\b\d{3,6}\b)\b", text, re.IGNORECASE)
        if stu_match:
            entities["student_id"] = stu_match.group(1).upper()
        elif user_id:
            entities["student_id"] = user_id

        # 2. Enquiry reference (e.g. BCE/ENQ/2026/114)
        enq_match = re.search(r"\b([A-Z]{2,4}/[A-Z]{2,4}/\d{4}/\d{2,5})\b", text, re.IGNORECASE)
        if enq_match:
            entities["enquiry_ref"] = enq_match.group(1).upper()

        # 3. Dates
        date_match = re.search(
            r"\b(tomorrow|today|yesterday|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{4})?|\d{4}-\d{2}-\d{2})\b",
            text,
            re.IGNORECASE,
        )
        if date_match:
            entities["date"] = date_match.group(1)
        else:
            if "tomorrow" in text.lower():
                entities["date"] = "Tomorrow"
            elif "today" in text.lower():
                entities["date"] = "Today"

        # 4. Subjects
        subj_match = re.search(
            r"\b(mathematics|maths?|science|physics|chemistry|biology|english|history|geography|computer(?: science)?|hindi|kannada)\b",
            text,
            re.IGNORECASE,
        )
        if subj_match:
            entities["subject"] = subj_match.group(1).title()

        # 5. Class / Section
        class_match = re.search(
            r"\b(class\s+[IVXLCDM\d]+(?:\s*[A-Z])?|grade\s+\d+|standard\s+\d+)\b",
            text,
            re.IGNORECASE,
        )
        if class_match:
            entities["class_name"] = class_match.group(1).title()

        # 6. Reason for leave
        if "leave" in text.lower():
            reason_match = re.search(r"\b(?:reason|due to|because of|for)\s+([a-zA-Z\s]{3,30})\b", text, re.IGNORECASE)
            if reason_match:
                entities["reason"] = reason_match.group(1).strip()
            else:
                entities["reason"] = "Personal reasons"

        return entities
