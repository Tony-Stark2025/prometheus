"""
Enterprise Agent Registry for Prometheus.
Provides publishing, versioning, governance, and discovery of fleet sub-agents
in accordance with the Fortified Enterprise Fleet specification.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    agent_id: str
    name: str
    version: str = "1.0.0"
    role: str
    description: str
    tier: str  # "PERIMETER", "INGESTION", "REASONING", "ACTION"
    model_requirement: str
    supported_scopes: List[str] = Field(default_factory=lambda: ["engineering", "platform"])
    security_controls: List[str] = Field(default_factory=list)
    tools_bound: List[str] = Field(default_factory=list)


class AgentRegistry:
    """
    Central repository for cataloging enterprise-approved sub-agents.
    """

    def __init__(self):
        self._registry: Dict[str, AgentMetadata] = {}
        self._register_default_fleet()

    def _register_default_fleet(self):
        fleet = [
            AgentMetadata(
                agent_id="agent-01-router",
                name="Router & Guardrail Agent",
                version="1.1.0",
                role="Perimeter Security & ABAC Routing",
                description="Validates incoming queries, checks token scopes, strips PII, and applies prompt defense filters.",
                tier="PERIMETER",
                model_requirement="Deterministic / Local Rule Engine",
                security_controls=["ABAC Scope Filtering", "PII Sanitizer", "Prompt Injection Defense"],
                tools_bound=["ABACGuard", "GuardrailService"],
            ),
            AgentMetadata(
                agent_id="agent-02-git",
                name="Git & CI/CD Ingestion Agent",
                version="1.0.0",
                role="Code Telemetry & Pipeline Health Ingestion",
                description="Scans PR review latency, stale branches (>48h unreviewed), and build failures across GitHub/GitLab via MCP/APIs.",
                tier="INGESTION",
                model_requirement="gemini-3.5-flash-lite",
                security_controls=["ABAC Resource Scoping", "Read-Only Isolation"],
                tools_bound=["GitHubTools.get_open_pull_requests", "GitHubTools.get_ci_pipeline_failures"],
            ),
            AgentMetadata(
                agent_id="agent-03-jira",
                name="Project Tracker Agent",
                version="1.0.0",
                role="Issue Status & Dependency Ingestion",
                description="Tracks issue status changes, epic progress, blocked states, and sprint burndown deviations from Jira/Linear.",
                tier="INGESTION",
                model_requirement="gemini-3.5-flash-lite",
                security_controls=["ABAC Resource Scoping", "Read-Only Isolation"],
                tools_bound=["JiraTools.get_sprint_issues", "JiraTools.get_blocked_issues"],
            ),
            AgentMetadata(
                agent_id="agent-04-workstream",
                name="Workstream Ingestion Agent",
                version="1.0.0",
                role="Public Communication & Chat Signal Ingestion",
                description="Synthesizes public channel discussions (Slack/Teams) and communication context.",
                tier="INGESTION",
                model_requirement="gemini-3.5-flash-lite",
                security_controls=["ABAC Channel Scoping", "PII Sanitization", "Read-Only Isolation"],
                tools_bound=["SlackTools.get_recent_channel_messages"],
            ),
            AgentMetadata(
                agent_id="agent-05-synthesis",
                name="Synthesis & Blocker Agent",
                version="1.2.0",
                role="Multi-Domain Telemetry Correlation & Root Cause Analysis",
                description="Correlates multi-source operational telemetry to identify root-cause delivery bottlenecks.",
                tier="REASONING",
                model_requirement="gemini-3.7-flash (with Cascade Pool)",
                security_controls=["No Direct External Mutation", "Model Cascade Fallback"],
                tools_bound=["GeminiPoolClient.generate_structured_synthesis"],
            ),
            AgentMetadata(
                agent_id="agent-06-action",
                name="Action & Drafting Agent",
                version="1.1.0",
                role="Human-in-the-Loop Action Drafting",
                description="Prepares scheduled executive digests and drafts action cards with require_confirmation=True.",
                tier="ACTION",
                model_requirement="gemini-3.5-flash-lite",
                security_controls=["Zero Unilateral Mutation", "Mandatory Human Sign-Off"],
                tools_bound=["SlackTools.draft_action_card", "SlackTools.dispatch_approved_action"],
            ),
        ]
        for agent in fleet:
            self._registry[agent.agent_id] = agent

    def list_agents(self) -> List[AgentMetadata]:
        return list(self._registry.values())

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        return self._registry.get(agent_id)


agent_registry = AgentRegistry()
