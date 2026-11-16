from __future__ import annotations

from typing import Any
from app.agents.alumni.agents import (
    AchievementAgent,
    AlumniAssistantAgent,
    CommunityAgent,
    EventAgent,
    OfficeSupportAgent,
    RecordsAgent,
)
from app.agents.base import BaseAgent
from app.agents.student.agents import (
    AcademicAgent,
    AttendanceAgent,
    ExamAgent,
    FamilySupportAgent,
    FeeAgent,
    LearningAgent,
    NoticeAgent,
    StudentAssistantAgent,
    TransportAgent,
)
from app.agents.teacher.agents import (
    AssessmentAgent,
    AttendanceAnalysisAgent,
    ClassAgent,
    HRLeaveAgent,
    LessonAgent,
    ResourceAgent,
    StaffKnowledgeAgent,
    TeacherCopilotAgent,
)
from app.agents.visitor.agents import (
    AdmissionAgent,
    ApplicationAgent,
    AppointmentAgent,
    CampusNavigationAgent,
    PublicKnowledgeAgent,
    VisitorAgent,
)
from app.core.security import SecurityValidator


class AgentRegistry:
    """Registry maintaining all role-aware agents in the system."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._register_all()

    def _register_all(self) -> None:
        all_agents = [
            # Student / Parent (9 agents)
            StudentAssistantAgent(),
            AttendanceAgent(),
            AcademicAgent(),
            ExamAgent(),
            FeeAgent(),
            TransportAgent(),
            NoticeAgent(),
            LearningAgent(),
            FamilySupportAgent(),
            # Teacher / Staff (8 agents)
            TeacherCopilotAgent(),
            ClassAgent(),
            AttendanceAnalysisAgent(),
            AssessmentAgent(),
            LessonAgent(),
            StaffKnowledgeAgent(),
            HRLeaveAgent(),
            ResourceAgent(),
            # Visitor / Applicant (6 agents)
            AdmissionAgent(),
            VisitorAgent(),
            CampusNavigationAgent(),
            AppointmentAgent(),
            ApplicationAgent(),
            PublicKnowledgeAgent(),
            # Alumni / Ex-Employee (6 agents)
            AlumniAssistantAgent(),
            EventAgent(),
            RecordsAgent(),
            CommunityAgent(),
            AchievementAgent(),
            OfficeSupportAgent(),
        ]
        for a in all_agents:
            self._agents[a.agent_id] = a

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list_agents_for_role(self, role: str) -> list[dict[str, Any]]:
        canonical = SecurityValidator.normalize_role(role)
        results = []
        for a in self._agents.values():
            if a.role == canonical:
                results.append({
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role,
                    "description": a.description,
                    "default_tools": a.default_tools,
                })
        return results

    def list_all_agents(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "role": a.role,
                "description": a.description,
                "default_tools": a.default_tools,
            }
            for a in self._agents.values()
        ]


_AGENT_REGISTRY = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    return _AGENT_REGISTRY
