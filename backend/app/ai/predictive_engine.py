
"""CSV-grounded statistical predictors for each role.

All predictions are deterministic and based purely on CSV demonstration data.
No external ML model is required — these run locally with zero API calls.
"""
from __future__ import annotations

from typing import Any


class PredictiveEngine:
    """Lightweight analytics engine powered by CSV row data."""

    # ------------------------------------------------------------------
    # Student / Parent predictions
    # ------------------------------------------------------------------
    @staticmethod
    def student_performance_prediction(
        exam_scores: list[dict[str, Any]],
        attendance: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Predict academic trajectory from exam scores and attendance."""
        scores = []
        for row in exam_scores:
            try:
                scores.append(float(row.get("marks", row.get("score", 0))))
            except (ValueError, TypeError):
                continue
        avg = round(sum(scores) / max(len(scores), 1), 1)

        att_pcts = []
        for row in attendance:
            try:
                raw = str(row.get("percentage", "0")).replace("%", "")
                att_pcts.append(float(raw))
            except (ValueError, TypeError):
                continue
        att_avg = round(sum(att_pcts) / max(len(att_pcts), 1), 1)

        risk = "Low"
        if avg < 45 or att_avg < 70:
            risk = "High"
        elif avg < 60 or att_avg < 80:
            risk = "Medium"

        trend = "Stable"
        if len(scores) >= 2:
            trend = "Improving" if scores[-1] > scores[0] else "Declining" if scores[-1] < scores[0] else "Stable"

        return {
            "average_score": avg,
            "attendance_pct": att_avg,
            "risk_level": risk,
            "trend": trend,
            "recommendation": (
                "Focus on consistent revision and attendance improvement."
                if risk != "Low"
                else "Performance is on track. Encourage advanced enrichment."
            ),
        }

    @staticmethod
    def attendance_risk(attendance: list[dict[str, Any]]) -> dict[str, Any]:
        """Flag attendance risk using simple threshold analysis."""
        absents = sum(1 for r in attendance if str(r.get("status", "")).lower() == "absent")
        total = max(len(attendance), 1)
        pct_present = round((total - absents) / total * 100, 1)
        risk = "High" if pct_present < 75 else "Medium" if pct_present < 85 else "Low"
        return {
            "total_days": total,
            "absent_days": absents,
            "present_pct": pct_present,
            "risk_level": risk,
            "alert": f"Attendance at {pct_present}% — {'immediate intervention needed' if risk == 'High' else 'monitor closely' if risk == 'Medium' else 'within safe range'}.",
        }

    # ------------------------------------------------------------------
    # Teacher predictions
    # ------------------------------------------------------------------
    @staticmethod
    def class_performance_insights(
        exam_scores: list[dict[str, Any]],
        attendance: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate class-level analytics for the teacher dashboard."""
        by_subject: dict[str, list[float]] = {}
        for row in exam_scores:
            subj = row.get("subject", "Unknown")
            try:
                by_subject.setdefault(subj, []).append(float(row.get("marks", row.get("score", 0))))
            except (ValueError, TypeError):
                continue
        subject_averages = {s: round(sum(v) / max(len(v), 1), 1) for s, v in by_subject.items()}
        weakest = min(subject_averages, key=subject_averages.get, default="N/A")  # type: ignore[arg-type]
        strongest = max(subject_averages, key=subject_averages.get, default="N/A")  # type: ignore[arg-type]
        return {
            "subject_averages": subject_averages,
            "weakest_subject": weakest,
            "strongest_subject": strongest,
            "students_at_risk": sum(1 for v in by_subject.values() for s in v if s < 40),
            "recommendation": f"Focus additional attention on {weakest}. Consider remedial sessions.",
        }

    # ------------------------------------------------------------------
    # Visitor — admission conversion
    # ------------------------------------------------------------------
    @staticmethod
    def admission_conversion_prediction(
        enquiries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Score the likelihood of an enquiry converting to enrollment."""
        if not enquiries:
            return {"score": 0, "label": "No data", "factors": []}
        row = enquiries[0]
        score = 50  # base score
        factors = []
        if row.get("status", "").lower() in ("active", "in progress", "counselling done"):
            score += 20
            factors.append("Active enquiry status (+20)")
        if row.get("documents_submitted"):
            score += 15
            factors.append("Documents submitted (+15)")
        if row.get("campus_visit", "").lower() in ("yes", "completed"):
            score += 10
            factors.append("Campus visit completed (+10)")
        if row.get("counselling", "").lower() in ("done", "completed"):
            score += 5
            factors.append("Counselling completed (+5)")
        score = min(score, 95)
        label = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
        return {"score": score, "label": label, "factors": factors}

    # ------------------------------------------------------------------
    # Alumni — engagement & mentorship
    # ------------------------------------------------------------------
    @staticmethod
    def alumni_engagement_score(
        alumni_records: list[dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Gauge alumni engagement from event attendance and profile activity."""
        score = 30
        factors = []
        if alumni_records:
            row = alumni_records[0]
            if row.get("last_engagement"):
                score += 20
                factors.append("Recent engagement recorded (+20)")
            if row.get("mentorship", "").lower() in ("active", "yes"):
                score += 15
                factors.append("Active mentorship (+15)")
            if row.get("donation", "").lower() not in ("", "none", "n/a"):
                score += 10
                factors.append("Past donation (+10)")
        event_count = len(events)
        if event_count >= 3:
            score += 15
            factors.append(f"Engaged with {event_count} events (+15)")
        elif event_count >= 1:
            score += 5
            factors.append(f"Attended {event_count} event(s) (+5)")
        score = min(score, 100)
        label = "Highly Engaged" if score >= 70 else "Moderately Engaged" if score >= 40 else "Low Engagement"
        return {"score": score, "label": label, "factors": factors}
