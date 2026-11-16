from __future__ import annotations

from typing import Any
from app.agents.base import AgentOutput, BaseAgent


class TeacherCopilotAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="teacher_copilot_agent",
            name="Teacher Copilot Agent",
            role="teacher_staff",
            description="Assists teachers with daily period schedules, classroom duties, and staff briefings.",
            default_tools=["get_timetable", "get_staff_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_timetable")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Teacher daily timetable loaded.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class ClassAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="class_agent",
            name="Class Agent",
            role="teacher_staff",
            description="Manages assigned class roster, student cohorts, and section administration.",
            default_tools=["get_student_profile"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_student_profile")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Class roster records retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class AttendanceAnalysisAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="attendance_analysis_agent",
            name="Attendance Analysis Agent",
            role="teacher_staff",
            description="Class-level attendance monitoring, chronic absence alerts, and compliance scoring.",
            default_tools=["get_student_attendance"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_student_attendance")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Class attendance statistics computed.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_prediction=True,
            prediction_type="attendance_risk",
        )


class AssessmentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="assessment_agent",
            name="Assessment Agent",
            role="teacher_staff",
            description="Generates test blueprints, evaluates class performance, and identifies weak topics.",
            default_tools=["get_student_marks"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_student_marks")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Exam marks and weak topic analysis compiled.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_prediction=True,
            prediction_type="class_performance",
            requires_recommendation=True,
        )


class LessonAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="lesson_agent",
            name="Lesson Agent",
            role="teacher_staff",
            description="Formulates comprehensive lesson plans, pedagogical objectives, and quizzes.",
            default_tools=["get_library_data"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Lesson plan and quiz structure generated.",
            requires_recommendation=True,
        )


class StaffKnowledgeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="staff_knowledge_agent",
            name="Staff Knowledge Agent",
            role="teacher_staff",
            description="School policies, academic regulations, examination bylaws, and circulars.",
            default_tools=["rag_retrieval"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("rag_retrieval")
        res = await tool.run(self.role, user_id, tenant_id, query=query) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Staff policy retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class HRLeaveAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="hr_leave_agent",
            name="HR/Leave Agent",
            role="teacher_staff",
            description="Staff casual/medical leave balances and leave request preparation.",
            default_tools=["preview_leave_application"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        date = entities.get("date", "Tomorrow")
        reason = entities.get("reason", "Casual Leave")
        tool = self.tool_registry.get_tool("preview_leave_application")
        res = await tool.run(self.role, user_id, tenant_id, date=date, reason=reason) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Staff leave request preview prepared.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_confirmation=True,
            confirmation_message=f"I can prepare a casual leave request for {date}.\nReason: {reason}.\nWould you like me to submit it for Principal approval?",
        )


class ResourceAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="resource_agent",
            name="Resource Agent",
            role="teacher_staff",
            description="Lab apparatus requisitions, library reference texts, and teaching aids.",
            default_tools=["get_library_data"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_library_data")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Teaching resource catalog retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )
