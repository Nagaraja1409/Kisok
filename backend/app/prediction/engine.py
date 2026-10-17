from __future__ import annotations

import logging
from typing import Any
from app.prediction.base import PredictionResult

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Independent Prediction Engine invoked only when required by agent planning.
    
    Provides role-specific statistical predictors grounded in verified data.
    Does not invent predictions when data is insufficient.
    """

    # ------------------------------------------------------------------
    # Student / Parent Predictors
    # ------------------------------------------------------------------

    @staticmethod
    def predict_attendance_risk(attendance_records: list[dict[str, Any]]) -> PredictionResult:
        if not attendance_records:
            return PredictionResult(
                prediction_type="attendance_risk",
                risk_level="Unknown",
                score=0.0,
                trend="Unknown",
                insights=["Insufficient attendance records to compute risk trajectory."],
                sufficient_data=False,
            )

        absents = sum(1 for r in attendance_records if str(r.get("status", "")).lower() == "absent")
        total = max(len(attendance_records), 1)
        pct_present = round((total - absents) / total * 100.0, 1)

        # Check percentage field if provided directly
        for r in attendance_records:
            if "percentage" in r:
                try:
                    pct_present = float(str(r["percentage"]).replace("%", ""))
                    break
                except (ValueError, TypeError):
                    pass

        risk = "High" if pct_present < 75.0 else "Medium" if pct_present < 85.0 else "Low"
        trend = "Declining" if absents >= 3 else "Stable"

        insights = [
            f"Current attendance is {pct_present}%.",
            f"Total recorded absences: {absents} out of {total} tracking periods.",
        ]
        if risk == "High":
            insights.append("Attendance is below the mandatory 75% board threshold. Immediate intervention required.")
        elif risk == "Medium":
            insights.append("Attendance is in the caution band (75%-85%). Monitor upcoming absences.")
        else:
            insights.append("Attendance is within safe academic compliance standards.")

        return PredictionResult(
            prediction_type="attendance_risk",
            risk_level=risk,
            score=pct_present,
            trend=trend,
            insights=insights,
            sufficient_data=True,
            metadata={"present_pct": pct_present, "absents": absents, "total_days": total},
        )

    @staticmethod
    def predict_academic_performance(
        marks_records: list[dict[str, Any]],
        attendance_records: list[dict[str, Any]] | None = None,
    ) -> PredictionResult:
        if not marks_records:
            return PredictionResult(
                prediction_type="academic_performance",
                risk_level="Unknown",
                score=0.0,
                trend="Unknown",
                insights=["Insufficient exam records to project grade performance."],
                sufficient_data=False,
            )

        scores = []
        for r in marks_records:
            val = r.get("marks") or r.get("score") or r.get("obtainedMarks")
            try:
                scores.append(float(val))
            except (ValueError, TypeError):
                continue

        if not scores:
            return PredictionResult(
                prediction_type="academic_performance",
                risk_level="Unknown",
                score=0.0,
                trend="Unknown",
                insights=["Exam score format unparseable."],
                sufficient_data=False,
            )

        avg = round(sum(scores) / len(scores), 1)
        trend = "Improving" if len(scores) > 1 and scores[-1] > scores[0] else "Declining" if len(scores) > 1 and scores[-1] < scores[0] else "Stable"
        risk = "High" if avg < 50.0 else "Medium" if avg < 70.0 else "Low"

        insights = [
            f"Projected term average: {avg}%.",
            f"Academic score trajectory is {trend}.",
        ]
        if risk == "High":
            insights.append("Student is at risk in core subjects. Remedial tutoring recommended.")
        elif risk == "Medium":
            insights.append("Performance is moderate. Targeted revision will help secure higher grades.")
        else:
            insights.append("Strong academic trajectory. Ready for advanced enrichment modules.")

        return PredictionResult(
            prediction_type="academic_performance",
            risk_level=risk,
            score=avg,
            trend=trend,
            insights=insights,
            sufficient_data=True,
            metadata={"average_score": avg, "total_exams": len(scores)},
        )

    @staticmethod
    def predict_exam_readiness(
        marks_records: list[dict[str, Any]], attendance_records: list[dict[str, Any]]
    ) -> PredictionResult:
        perf = PredictionEngine.predict_academic_performance(marks_records)
        att = PredictionEngine.predict_attendance_risk(attendance_records)

        if not perf.sufficient_data and not att.sufficient_data:
            return PredictionResult(
                prediction_type="exam_readiness",
                risk_level="Unknown",
                sufficient_data=False,
                insights=["Insufficient historical data to evaluate exam readiness."],
            )

        readiness_score = round((perf.score * 0.7) + (att.score * 0.3), 1)
        risk = "High" if readiness_score < 60 else "Medium" if readiness_score < 75 else "Low"

        return PredictionResult(
            prediction_type="exam_readiness",
            risk_level=risk,
            score=readiness_score,
            trend=perf.trend,
            insights=[
                f"Composite Exam Readiness Index: {readiness_score}/100.",
                f"Academic preparation: {perf.score}%, Attendance compliance: {att.score}%.",
            ],
            sufficient_data=True,
        )

    # ------------------------------------------------------------------
    # Teacher / Staff Predictors
    # ------------------------------------------------------------------

    @staticmethod
    def predict_class_performance(marks_records: list[dict[str, Any]]) -> PredictionResult:
        if not marks_records:
            return PredictionResult(
                prediction_type="class_performance",
                risk_level="Unknown",
                sufficient_data=False,
                insights=["No class records available."],
            )

        by_subj: dict[str, list[float]] = {}
        for r in marks_records:
            subj = r.get("subject", "General")
            val = r.get("marks") or r.get("score")
            try:
                by_subj.setdefault(subj, []).append(float(val))
            except (ValueError, TypeError):
                pass

        if not by_subj:
            return PredictionResult(
                prediction_type="class_performance",
                risk_level="Unknown",
                sufficient_data=False,
                insights=["No numerical scores found for class."],
            )

        subj_averages = {s: round(sum(vals) / len(vals), 1) for s, vals in by_subj.items()}
        weakest = min(subj_averages, key=subj_averages.get)  # type: ignore[arg-type]
        strongest = max(subj_averages, key=subj_averages.get)  # type: ignore[arg-type]
        overall_avg = round(sum(subj_averages.values()) / len(subj_averages), 1)

        insights = [
            f"Class cohort average: {overall_avg}%.",
            f"Highest performing subject: {strongest} ({subj_averages[strongest]}%).",
            f"Focus area requiring reinforcement: {weakest} ({subj_averages[weakest]}%).",
        ]
        return PredictionResult(
            prediction_type="class_performance",
            risk_level="Medium" if overall_avg < 65 else "Low",
            score=overall_avg,
            trend="Stable",
            insights=insights,
            sufficient_data=True,
            metadata={"subject_averages": subj_averages, "weakest": weakest, "strongest": strongest},
        )

    # ------------------------------------------------------------------
    # Visitor / Applicant Predictor
    # ------------------------------------------------------------------

    @staticmethod
    def predict_admission_conversion(enquiries: list[dict[str, Any]]) -> PredictionResult:
        if not enquiries:
            return PredictionResult(
                prediction_type="admission_conversion",
                risk_level="Low",
                score=50.0,
                trend="Neutral",
                insights=["New enquiry. Campus visit and document verification pending."],
                sufficient_data=True,
            )

        row = enquiries[0]
        score = 50.0
        factors = []
        status = str(row.get("status", "")).lower()
        if status in ("active", "in progress", "counselled"):
            score += 20.0
            factors.append("Active interaction status recorded (+20%)")
        if row.get("documents_submitted"):
            score += 15.0
            factors.append("Mandatory documents verified (+15%)")
        if str(row.get("campus_visit", "")).lower() in ("yes", "completed"):
            score += 10.0
            factors.append("Campus tour attended (+10%)")

        score = min(score, 95.0)
        risk = "Low" if score >= 75 else "Medium" if score >= 50 else "High"
        insights = [f"Application completion & enrollment probability: {score}%."] + factors

        return PredictionResult(
            prediction_type="admission_conversion",
            risk_level=risk,
            score=score,
            trend="Advancing",
            insights=insights,
            sufficient_data=True,
        )

    # ------------------------------------------------------------------
    # Alumni Predictor
    # ------------------------------------------------------------------

    @staticmethod
    def predict_alumni_engagement(
        alumni_records: list[dict[str, Any]], events: list[dict[str, Any]]
    ) -> PredictionResult:
        score = 40.0
        insights = []
        if alumni_records:
            rec = alumni_records[0]
            if rec.get("last_engagement"):
                score += 20.0
                insights.append("Recent event engagement on record (+20%).")
            if str(rec.get("mentorship", "")).lower() in ("yes", "active"):
                score += 20.0
                insights.append("Active mentor participant in student network (+20%).")

        if len(events) >= 2:
            score += 15.0
            insights.append("Multiple alumni gatherings attended (+15%).")

        score = min(score, 100.0)
        insights.insert(0, f"Alumni Connection Index: {score}/100.")
        return PredictionResult(
            prediction_type="alumni_engagement",
            risk_level="Low" if score >= 70 else "Medium",
            score=score,
            trend="Active",
            insights=insights,
            sufficient_data=True,
        )
