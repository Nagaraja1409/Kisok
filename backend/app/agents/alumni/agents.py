from __future__ import annotations

from typing import Any
from app.agents.base import AgentOutput, BaseAgent


class AlumniAssistantAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="alumni_assistant_agent",
            name="Alumni Assistant Agent",
            role="alumni_ex_employee",
            description="General alumni guidance, engagement opportunities, and school connection services.",
            default_tools=["get_events"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_events")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Alumni network status retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
            requires_recommendation=True,
        )


class EventAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="event_agent",
            name="Event Agent",
            role="alumni_ex_employee",
            description="Founders Day, batch reunions, and regional alumni chapter gatherings.",
            default_tools=["get_events"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("get_events")
        res = await tool.run(self.role, user_id, tenant_id) if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Upcoming reunion events loaded.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class RecordsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="records_agent",
            name="Records Agent",
            role="alumni_ex_employee",
            description="Transcript requests, duplicate certificate applications, and archive retrieval.",
            default_tools=["get_notices"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Official transcript guidance retrieved.",
            requires_confirmation=True,
            confirmation_message="I can prepare an official transcript request for your graduating batch.\nProcessing time: 3 working days.\nWould you like me to initiate this request?",
        )


class CommunityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="community_agent",
            name="Community Agent",
            role="alumni_ex_employee",
            description="Student mentorship circles, career talks, and alumni networking.",
            default_tools=["get_events"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Mentorship circle matching active.",
            requires_recommendation=True,
        )


class AchievementAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="achievement_agent",
            name="Achievement Agent",
            role="alumni_ex_employee",
            description="Notable alumni hall of fame, recognitions, and school honours.",
            default_tools=["rag_retrieval"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        tool = self.tool_registry.get_tool("rag_retrieval")
        res = await tool.run(self.role, user_id, tenant_id, query="alumni achievements") if tool else None
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Hall of Fame records retrieved.",
            tool_results=[res] if res else [],
            sources=res.sources if res else [],
        )


class OfficeSupportAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_id="office_support_agent",
            name="Office Support Agent",
            role="alumni_ex_employee",
            description="Support for ex-employees, service certificates, and administrative coordination.",
            default_tools=["get_notices"],
        )

    async def process(
        self, query: str, intent: str, entities: dict[str, Any], user_id: str, tenant_id: str
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            findings="Administrative service records referenced.",
        )
