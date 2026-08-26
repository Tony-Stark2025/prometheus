"""
Model Context Protocol (MCP) Ecosystem for Prometheus.
Includes Prometheus MCP Server (stdio & SSE) and MCP Client adapter.
"""

from prometheus.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPToolDefinition,
    MCPCallToolRequest,
    MCPListToolsResponse,
)
from prometheus.mcp.server import PrometheusMCPServer, mcp_server
from prometheus.mcp.client import PrometheusMCPClient, mcp_client

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "MCPToolDefinition",
    "MCPCallToolRequest",
    "MCPListToolsResponse",
    "PrometheusMCPServer",
    "mcp_server",
    "PrometheusMCPClient",
    "mcp_client",
]
