"""
Tier 1 Unit Tests: Fortified Enterprise Fleet Agent Registry
Validates discovery, metadata, security controls, and tool bindings across all 6 sub-agents.
"""

import pytest
from prometheus.registry.agent_registry import AgentRegistry, AgentMetadata, agent_registry


@pytest.mark.unit
class TestAgentRegistry:
    def test_all_six_agents_registered(self):
        """Asserts all 6 sub-agents are registered in the global catalog."""
        agents = agent_registry.list_agents()
        assert len(agents) == 6
        agent_ids = {a.agent_id for a in agents}
        expected_ids = {
            "agent-01-router",
            "agent-02-git",
            "agent-03-jira",
            "agent-04-workstream",
            "agent-05-synthesis",
            "agent-06-action",
        }
        assert agent_ids == expected_ids

    def test_router_agent_metadata(self):
        """Validates Router & Guardrail Agent properties."""
        agent = agent_registry.get_agent("agent-01-router")
        assert agent is not None
        assert agent.tier == "PERIMETER"
        assert "ABAC Scope Filtering" in agent.security_controls
        assert "Prompt Injection Defense" in agent.security_controls
        assert "ABACGuard" in agent.tools_bound

    def test_git_agent_metadata(self):
        """Validates Git & CI/CD Ingestion Agent properties."""
        agent = agent_registry.get_agent("agent-02-git")
        assert agent is not None
        assert agent.tier == "INGESTION"
        assert "gemini-3.7-flash" in agent.model_requirement
        assert "GitHubTools.get_open_pull_requests" in agent.tools_bound
        assert "GitHubTools.get_ci_pipeline_failures" in agent.tools_bound

    def test_jira_agent_metadata(self):
        """Validates Project Tracker Agent properties."""
        agent = agent_registry.get_agent("agent-03-jira")
        assert agent is not None
        assert agent.tier == "INGESTION"
        assert "gemini-3.7-flash" in agent.model_requirement
        assert "JiraTools.get_sprint_issues" in agent.tools_bound

    def test_workstream_agent_metadata(self):
        """Validates Workstream Ingestion Agent properties."""
        agent = agent_registry.get_agent("agent-04-workstream")
        assert agent is not None
        assert agent.tier == "INGESTION"
        assert "PII Sanitization" in agent.security_controls
        assert "SlackTools.get_recent_channel_messages" in agent.tools_bound

    def test_synthesis_agent_metadata(self):
        """Validates Synthesis & Blocker Agent properties."""
        agent = agent_registry.get_agent("agent-05-synthesis")
        assert agent is not None
        assert agent.tier == "REASONING"
        assert "No Direct External Mutation" in agent.security_controls
        assert "gemini-3.7-flash" in agent.model_requirement

    def test_action_agent_metadata(self):
        """Validates Action & Drafting Agent properties."""
        agent = agent_registry.get_agent("agent-06-action")
        assert agent is not None
        assert agent.tier == "ACTION"
        assert "Mandatory Human Sign-Off" in agent.security_controls
        assert "SlackTools.draft_action_card" in agent.tools_bound
        assert "SlackTools.dispatch_approved_action" in agent.tools_bound

    def test_four_architectural_tiers_present(self):
        """Ensures all 4 architectural tiers (PERIMETER, INGESTION, REASONING, ACTION) are covered."""
        tiers = {a.tier for a in agent_registry.list_agents()}
        assert tiers == {"PERIMETER", "INGESTION", "REASONING", "ACTION"}

    def test_get_nonexistent_agent_returns_none(self):
        """Querying unregistered agent ID safely returns None."""
        assert agent_registry.get_agent("agent-99-unknown") is None
