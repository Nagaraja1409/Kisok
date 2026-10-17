from __future__ import annotations

import logging
from typing import Any
from app.agents.base import AgentOutput, BaseAgent
from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


class AttendanceAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="attendance_agent",
            name="Attendance Agent",
            role="student_parent",
            description="Manages student attendance tracking, compliance, and absence analysis.",
            default_tools=["get_student_attendance"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_student_attendance")
        student_id = entities.get("student_id") or user_id
        tool_res = await tool.run(self.role, user_id, tenant_id, student_id=student_id) if tool else None

        tool_results = [tool_res] if tool_res else []
        sources = tool_res.sources if tool_res else []

        q_lower = query.lower()
        is_diagnostic = any(w in q_lower for w in ("why", "low", "falling", "drop", "risk", "trend"))
        needs_rec = any(w in q_lower for w in ("what should", "how to improve", "how can i improve", "suggestions", "help"))

        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Attendance records retrieved.",
            tool_results=tool_results,
            sources=sources,
            requires_prediction=is_diagnostic,
            prediction_type="attendance_risk" if is_diagnostic else None,
            requires_recommendation=needs_rec,
        )


class AcademicAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="academic_agent",
            name="Academic Agent",
            role="student_parent",
            description="Tracks academic performance, grades, and subject-wise progression.",
            default_tools=["get_student_marks"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_student_marks")
        student_id = entities.get("student_id") or user_id
        tool_res = await tool.run(self.role, user_id, tenant_id, student_id=student_id) if tool else None

        q_lower = query.lower()
        is_diagnostic = any(w in q_lower for w in ("why", "improve", "predict", "trajectory", "weak"))
        needs_rec = any(w in q_lower for w in ("how to", "suggest", "recommend", "study plan"))

        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Academic score report compiled.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
            requires_prediction=is_diagnostic,
            prediction_type="academic_performance" if is_diagnostic else None,
            requires_recommendation=needs_rec,
        )


class ExamAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="exam_agent",
            name="Exam Agent",
            role="student_parent",
            description="Provides examination timetables, syllabus guidelines, and test schedules.",
            default_tools=["get_exam_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_exam_details")
        tool_res = await tool.run(self.role, user_id, tenant_id, student_id=user_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Exam schedule loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
        )


class FeeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="fee_agent",
            name="Fee Agent",
            role="student_parent",
            description="Reports fee schedules, outstanding balances, and payment due dates.",
            default_tools=["get_fee_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_fee_details")
        student_id = entities.get("student_id") or user_id
        tool_res = await tool.run(self.role, user_id, tenant_id, student_id=student_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Fee statement loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
        )


class TransportAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="transport_agent",
            name="Transport Agent",
            role="student_parent",
            description="Provides bus route timings, pickup stops, and transport details.",
            default_tools=["get_transport_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_transport_details")
        student_id = entities.get("student_id") or user_id
        tool_res = await tool.run(self.role, user_id, tenant_id, student_id=student_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Transport details loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
        )


class NoticeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="notice_agent",
            name="Notice Agent",
            role="student_parent",
            description="Fetches school circulars, announcements, and policy notices.",
            default_tools=["get_notices", "rag_retrieval"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("rag_retrieval") or self.tool_registry.get_tool("get_notices")
        tool_res = await tool.run(self.role, user_id, tenant_id, query=query) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="School circulars loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
        )


class LearningAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="learning_agent",
            name="Learning Agent",
            role="student_parent",
            description="Provides study resources, reading recommendations, and revision materials.",
            default_tools=["get_library_data"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_library_data")
        tool_res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Library recommendations loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
            requires_recommendation=True,
        )


class FamilySupportAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="family_support_agent",
            name="Family Support Agent",
            role="student_parent",
            description="Assists parents with leave applications, certificates, and school communications.",
            default_tools=["preview_leave_application"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        date = entities.get("date", "Tomorrow")
        reason = entities.get("reason", "Personal reasons")
        tool = self.tool_registry.get_tool("preview_leave_application")
        tool_res = await tool.run(self.role, user_id, tenant_id, date=date, reason=reason) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Leave application preview prepared.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
            requires_confirmation=True,
            confirmation_message=f"I can prepare a leave request for {date}.\nReason: {reason}.\nWould you like me to submit it?",
        )


class StudentAssistantAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="student_assistant_agent",
            name="Student Assistant Agent",
            role="student_parent",
            description="Daily general student guidance, daily timetable, and schedule briefings.",
            default_tools=["get_timetable"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_timetable")
        tool_res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Timetable and schedule loaded.",
            tool_results=[tool_res] if tool_res else [],
            sources=tool_res.sources if tool_res else [],
        )
