"""Multimodal image / document pre-check engine.

Provides deterministic document validation and basic image inspection.
When an LLM provider with vision is available the image can be forwarded
for richer visual question answering.
"""
from __future__ import annotations

import base64
import io
from typing import Any


def validate_document_image(image_base64: str, role: str) -> dict[str, Any]:
    """Run a basic document pre-check on an uploaded image.

    In a production system this would use OCR + vision models.
    For the CSV-first demo we perform structural validation only.
    """
    try:
        raw = base64.b64decode(image_base64)
        size_kb = len(raw) / 1024
    except Exception:
        return {
            "status": "error",
            "message": "Could not decode the uploaded image. Please upload a valid JPEG or PNG file.",
            "checks": [],
        }

    checks: list[dict[str, Any]] = []

    # Size validation
    if size_kb < 5:
        checks.append({"check": "File size", "status": "⚠️ Warning", "detail": f"File is very small ({size_kb:.0f} KB). Ensure the document is legible."})
    elif size_kb > 10240:
        checks.append({"check": "File size", "status": "⚠️ Warning", "detail": f"File is large ({size_kb:.0f} KB). Consider compressing."})
    else:
        checks.append({"check": "File size", "status": "✅ OK", "detail": f"{size_kb:.0f} KB — within acceptable range."})

    # Format header check (JPEG / PNG)
    if raw[:3] == b'\xff\xd8\xff':
        checks.append({"check": "Format", "status": "✅ OK", "detail": "JPEG image detected."})
    elif raw[:8] == b'\x89PNG\r\n\x1a\n':
        checks.append({"check": "Format", "status": "✅ OK", "detail": "PNG image detected."})
    elif raw[:4] == b'%PDF':
        checks.append({"check": "Format", "status": "✅ OK", "detail": "PDF document detected."})
    else:
        checks.append({"check": "Format", "status": "⚠️ Warning", "detail": "Unknown format. JPEG, PNG, or PDF recommended."})

    # Dimensions (best-effort via Pillow)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        checks.append({"check": "Dimensions", "status": "✅ OK", "detail": f"{w}×{h} pixels."})
        if w < 300 or h < 300:
            checks.append({"check": "Resolution", "status": "⚠️ Warning", "detail": "Image resolution is low; text may not be readable."})
        else:
            checks.append({"check": "Resolution", "status": "✅ OK", "detail": "Resolution sufficient for document reading."})
    except Exception:
        checks.append({"check": "Dimensions", "status": "ℹ️ Skipped", "detail": "Could not determine image dimensions."})

    # Role-specific guidance
    doc_guidance = {
        "student": "Supported documents: Report Card, ID Card, Homework Sheet, Fee Receipt.",
        "parent": "Supported documents: Fee Receipt, Report Card, Transfer Certificate, Aadhaar/ID.",
        "teacher": "Supported documents: Lesson Plan, Question Paper, Attendance Register, Inventory List.",
        "visitor": "Supported documents: Birth Certificate, Transfer Certificate (TC), Mark Sheet, ID Proof.",
        "alumni": "Supported documents: Alumni ID, Transcript Request, Donation Receipt.",
    }
    checks.append({
        "check": "Document guidance",
        "status": "ℹ️ Info",
        "detail": doc_guidance.get(role, "Upload a school-related document for pre-check."),
    })

    all_ok = all(c["status"].startswith("✅") or c["status"].startswith("ℹ️") for c in checks)
    return {
        "status": "passed" if all_ok else "needs_review",
        "message": "Document pre-check completed." if all_ok else "Some checks need attention — review the details below.",
        "checks": checks,
    }


def describe_image_deterministic(image_base64: str) -> str:
    """Return a placeholder description when no vision LLM is available."""
    try:
        raw = base64.b64decode(image_base64)
        size_kb = len(raw) / 1024
    except Exception:
        return "Could not process the image. Please upload a valid JPEG or PNG."

    if raw[:3] == b'\xff\xd8\xff':
        fmt = "JPEG"
    elif raw[:8] == b'\x89PNG\r\n\x1a\n':
        fmt = "PNG"
    elif raw[:4] == b'%PDF':
        fmt = "PDF"
    else:
        fmt = "unknown format"

    return (
        f"Received a {fmt} file ({size_kb:.0f} KB). "
        "For detailed visual question answering, configure an AI provider with vision capabilities (e.g., NVIDIA NIM with a vision model). "
        "In the current deterministic mode, document pre-check validation is available."
    )
