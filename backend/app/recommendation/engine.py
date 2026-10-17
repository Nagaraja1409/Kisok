from __future__ import annotations

import logging
from typing import Any
from app.prediction.base import PredictionResult
from app.recommendation.base import RecommendationItem, RecommendationResult

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Reusable Recommendation Engine invoked dynamically when requested."""

    @staticmethod
    def recommend_attendance_improvement(
        prediction: PredictionResult | None = None,
    ) -> RecommendationResult:
        items = [
            RecommendationItem(
                title="Establish Regular Morning Routine",
                category="Habit & Routine",
                description="Ensure structured wake-up and departure timings to eliminate frequent late arrivals.",
                priority="High",
            ),
            RecommendationItem(
                title="Proactive Leave Notification",
                category="Compliance",
                description="Submit advance medical slips or parental leave requests through the portal to avoid unexcused absence flags.",
                priority="Medium",
            ),
            RecommendationItem(
                title="Attendance Recovery Consultation",
                category="Academic Support",
                description="Schedule a short check-in with the Class Teacher to plan attendance catch-up and note-sharing.",
                priority="High",
            ),
        ]
        steps = [
            "Monitor weekly attendance via parent portal.",
            "Contact class teacher if medical leave exceeds 3 days.",
            "Review catch-up worksheets for missed laboratory/lecture sessions.",
        ]
        return RecommendationResult(
            recommendation_type="attendance_improvement",
            items=items,
            actionable_steps=steps,
        )

    @staticmethod
    def recommend_academic_study(
        weak_subject: str | None = None,
        prediction: PredictionResult | None = None,
    ) -> RecommendationResult:
        subj = weak_subject or "Mathematics & Science"
        items = [
            RecommendationItem(
                title=f"Structured Revision for {subj}",
                category="Study Plan",
                description=f"Dedicate 45 minutes daily to foundational concept review and formula practice in {subj}.",
                priority="High",
            ),
            RecommendationItem(
                title="Library Recommended Reference Textbooks",
                category="Books & Resources",
                description=f"Borrow 'ICSE Concept Master: {subj}' and previous 5-year solved question papers from Library.",
                priority="High",
            ),
            RecommendationItem(
                title="Peer Study Group & Teacher Office Hours",
                category="Mentorship",
                description=f"Attend weekly zero-period doubt resolution sessions with the {subj} faculty.",
                priority="Medium",
            ),
        ]
        steps = [
            f"Review last term's {subj} exam errors.",
            "Complete 2 practice problem sets this weekend.",
            "Schedule a 15-minute doubt-clearing session with subject teacher.",
        ]
        return RecommendationResult(
            recommendation_type="study_recommendations",
            items=items,
            actionable_steps=steps,
        )

    @staticmethod
    def recommend_teacher_interventions(
        weak_subject: str | None = None,
        at_risk_count: int = 0,
    ) -> RecommendationResult:
        items = [
            RecommendationItem(
                title=f"Targeted Remedial Cohort ({weak_subject or 'General'})",
                category="Classroom Intervention",
                description="Establish twice-weekly 20-minute remedial tutorials focusing on core problem-solving competencies.",
                priority="High",
            ),
            RecommendationItem(
                title="Interactive Visual Worksheets",
                category="Pedagogy",
                description="Utilize concept-map worksheets and peer-led explanations to demystify complex curriculum units.",
                priority="Medium",
            ),
            RecommendationItem(
                title="Parent-Teacher Alignment Advisory",
                category="Communication",
                description="Share structured home-study check-lists with parents of at-risk students.",
                priority="Medium",
            ),
        ]
        steps = [
            "Group students by diagnostic score bands.",
            "Distribute targeted revision worksheets before unit tests.",
            "Track score progression after 2 weeks of intervention.",
        ]
        return RecommendationResult(
            recommendation_type="teacher_interventions",
            items=items,
            actionable_steps=steps,
        )

    @staticmethod
    def recommend_visitor_next_steps(
        conversion_prediction: PredictionResult | None = None,
    ) -> RecommendationResult:
        items = [
            RecommendationItem(
                title="Schedule Guided Campus & Lab Tour",
                category="Campus Visit",
                description="Experience the STEM innovation laboratories, digital library, and Olympic-size sports infrastructure.",
                priority="High",
            ),
            RecommendationItem(
                title="One-on-One Academic Counselling Session",
                category="Admissions Guidance",
                description="Discuss curriculum choice (ICSE / ISC streams) with the Principal and Academic Dean.",
                priority="High",
            ),
            RecommendationItem(
                title="Document Pre-Verification Desk",
                category="Documentation",
                description="Bring transfer certificate and birth certificate copies for express eligibility clearance.",
                priority="Medium",
            ),
        ]
        steps = [
            "Select a convenient weekday morning for campus visit (09:00 AM - 02:00 PM).",
            "Prepare transfer certificate and academic progress reports.",
            "Submit online application form with registration fee.",
        ]
        return RecommendationResult(
            recommendation_type="admission_guidance",
            items=items,
            actionable_steps=steps,
        )

    @staticmethod
    def recommend_alumni_activities() -> RecommendationResult:
        items = [
            RecommendationItem(
                title="Founders Day Annual Reunion Registration",
                category="Events",
                description="Join fellow graduates for the annual commemorative dinner and batch milestone celebration.",
                priority="High",
            ),
            RecommendationItem(
                title="Student Mentorship Circle Enrollment",
                category="Mentorship",
                description="Mentor senior Class XI & XII students preparing for engineering, medicine, and management careers.",
                priority="High",
            ),
            RecommendationItem(
                title="School Archive Heritage Contribution",
                category="School Heritage",
                description="Share historical photographs, memorabilia, and batch recollections with the school museum.",
                priority="Low",
            ),
        ]
        steps = [
            "RSVP for the upcoming Founders Day reunion.",
            "Indicate industry and career mentorship availability.",
            "Connect with your local regional alumni chapter.",
        ]
        return RecommendationResult(
            recommendation_type="alumni_engagement",
            items=items,
            actionable_steps=steps,
        )
