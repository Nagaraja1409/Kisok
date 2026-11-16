from __future__ import annotations

from typing import Any
from app.agents.base import AgentOutput, BaseAgent


class AdmissionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="admission_agent",
            name="Admission Agent",
            role="visitor_applicant",
            description="Guides prospective parents on admissions criteria, eligibility, and fee structure.",
            default_tools=["get_admission_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_admission_details")
        ref = entities.get("enquiry_ref", "BCE/ENQ/2026/114")
        res = await tool.run(self.role, user_id, tenant_id, enquiry_ref=ref) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Admission guidelines loaded.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_recommendation=True,
        )


class VisitorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="visitor_agent",
            name="Visitor Agent",
            role="visitor_applicant",
            description="Welcomes campus visitors, providing information desk hours and hospitality support.",
            default_tools=["get_campus_facilities"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_campus_facilities")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Visitor desk info loaded.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class CampusNavigationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="campus_navigation_agent",
            name="Campus Navigation Agent",
            role="visitor_applicant",
            description="Provides directions to laboratories, sports complexes, libraries, and hostels.",
            default_tools=["get_campus_facilities"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_campus_facilities")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Campus facilities map loaded.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class AppointmentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="appointment_agent",
            name="Appointment Agent",
            role="visitor_applicant",
            description="Assists with scheduling meetings with the Admissions Officer or Principal.",
            default_tools=["preview_appointment"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        date = entities.get("date", "Tomorrow")
        tool = self.tool_registry.get_tool("preview_appointment")
        res = await tool.run(self.role, user_id, tenant_id, visitor_name=user_id, date=date, department="Admissions") if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Appointment booking preview prepared.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_confirmation=True,
            confirmation_message=f"I can prepare a campus visit appointment for {date}.\nDepartment: Admissions Desk.\nWould you like me to book this visit?",
        )


class ApplicationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="application_agent",
            name="Application Agent",
            role="visitor_applicant",
            description="Tracks application stages, enquiry numbers, and document checklist completion.",
            default_tools=["get_admission_details"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_admission_details")
        ref = entities.get("enquiry_ref", "BCE/ENQ/2026/114")
        res = await tool.run(self.role, user_id, tenant_id, enquiry_ref=ref) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Application status verified.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_prediction=True,
            prediction_type="admission_conversion",
        )


class PublicKnowledgeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="public_knowledge_agent",
            name="Public Knowledge Agent",
            role="visitor_applicant",
            description="Answers public questions regarding ICSE curriculum, school affiliations, and timings.",
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
            findings="Public knowledge query retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )
