"""
Prometheus Model Context Protocol (MCP) Client Adapter.
Connects to external MCP servers (e.g. GitHub MCP, Jira MCP, Slack MCP) with hermetic offline fallbacks.
"""

from typing import Dict, Any, List, Optional
import logging
from app.tools.github_tools import GitHubTools
from app.tools.jira_tools import JiraTools
from app.tools.slack_tools import SlackTools

logger = logging.getLogger(__name__)


class PrometheusMCPClient:
    """
    Client adapter facilitating tool execution across external MCP tool providers.
    """

    def __init__(self):
        self._connected_servers: Dict[str, Any] = {}

    async def fetch_github_telemetry(self, org_scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Invokes GitHub MCP server (or falls back to local hermetic adapter)."""
        logger.info("📡 [MCPClient] Querying GitHub MCP server for open pull requests...")
        return await GitHubTools.get_open_pull_requests(scopes=org_scope)

    async def fetch_jira_telemetry(self, org_scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Invokes Jira MCP server (or falls back to local hermetic adapter)."""
        logger.info("📡 [MCPClient] Querying Jira MCP server for sprint issues...")
        return await JiraTools.get_sprint_issues(scopes=org_scope)

    async def fetch_slack_telemetry(self, org_scope: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Invokes Slack MCP server (or falls back to local hermetic adapter)."""
        logger.info("📡 [MCPClient] Querying Slack MCP server for channel discussions...")
        return await SlackTools.get_recent_channel_messages(scopes=org_scope)


mcp_client = PrometheusMCPClient()
