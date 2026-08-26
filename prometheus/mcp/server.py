"""
Prometheus Model Context Protocol (MCP) Server.
Exposes Prometheus multi-agent telemetry and HITL actions as MCP tools over stdio and SSE.
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from prometheus.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPToolDefinition,
    MCPToolParameter,
    MCPListToolsResponse,
)
from prometheus.security.abac_guard import UserContext
from prometheus.memory.state_store import state_store, DraftStatus
from prometheus.tools.slack_tools import SlackTools
from prometheus.workflows.prometheus_flow import PrometheusWorkflow

logger = logging.getLogger(__name__)


class PrometheusMCPServer:
    """
    Standard Model Context Protocol (MCP) Server for Prometheus.
    """

    TOOLS: List[MCPToolDefinition] = [
        MCPToolDefinition(
            name="get_daily_digest",
            description="Triggers the multi-agent fleet to ingest telemetry and produce the daily alignment digest.",
            inputSchema=MCPToolParameter(
                properties={
                    "user_id": {"type": "string", "description": "Authenticated user ID"},
                    "username": {"type": "string", "description": "User handle"},
                    "scopes": {"type": "array", "items": {"type": "string"}, "description": "Authorized scopes"},
                    "query": {"type": "string", "description": "Investigation query"},
                },
                required=["username"],
            ),
        ),
        MCPToolDefinition(
            name="list_active_blockers",
            description="Lists all currently active delivery bottlenecks and correlated blockers.",
            inputSchema=MCPToolParameter(properties={}),
        ),
        MCPToolDefinition(
            name="list_pending_actions",
            description="Lists action drafts waiting for Human-In-The-Loop approval.",
            inputSchema=MCPToolParameter(properties={}),
        ),
        MCPToolDefinition(
            name="approve_action",
            description="Explicitly approves and dispatches an action draft to Slack/Jira.",
            inputSchema=MCPToolParameter(
                properties={
                    "draft_id": {"type": "string", "description": "ID of the action draft"},
                    "approver": {"type": "string", "description": "Username of the approver"},
                },
                required=["draft_id", "approver"],
            ),
        ),
        MCPToolDefinition(
            name="reject_action",
            description="Aborts a proposed action draft.",
            inputSchema=MCPToolParameter(
                properties={
                    "draft_id": {"type": "string", "description": "ID of the action draft"},
                    "approver": {"type": "string", "description": "Username of the rejector"},
                },
                required=["draft_id"],
            ),
        ),
    ]

    async def handle_jsonrpc(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Processes incoming JSON-RPC 2.0 requests according to MCP specifications."""
        req_id = request_dict.get("id")
        method = request_dict.get("method", "")
        params = request_dict.get("params", {})

        try:
            if method == "initialize":
                return JSONRPCResponse(
                    id=req_id,
                    result={
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "prometheus-mcp-server",
                            "version": "0.1.0",
                        },
                        "capabilities": {
                            "tools": {"listChanged": True},
                        },
                    },
                ).model_dump()

            elif method == "tools/list":
                return JSONRPCResponse(
                    id=req_id,
                    result=MCPListToolsResponse(tools=self.TOOLS).model_dump(),
                ).model_dump()

            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                res = await self._execute_tool(tool_name, args)
                return JSONRPCResponse(id=req_id, result=res).model_dump()

            else:
                return JSONRPCResponse(
                    id=req_id,
                    error={"code": -32601, "message": f"Method '{method}' not found"},
                ).model_dump()

        except Exception as e:
            logger.exception("Error handling MCP request: %s", e)
            return JSONRPCResponse(
                id=req_id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
            ).model_dump()

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "get_daily_digest":
            user = UserContext(
                user_id=args.get("user_id", "mcp-user"),
                username=args.get("username", "alex-lead"),
                is_authenticated=True,
                org_scopes=set(args.get("scopes", ["engineering", "platform"])),
            )
            result = await PrometheusWorkflow.run(
                user=user,
                query=args.get("query", "Scan cross-squad telemetry for active sprint blockers"),
            )
            return {"content": [{"type": "text", "text": json.dumps(result.model_dump(), default=str)}]}

        elif tool_name == "list_active_blockers":
            blockers = await state_store.get_active_blockers()
            return {"content": [{"type": "text", "text": json.dumps([b.model_dump() for b in blockers], default=str)}]}

        elif tool_name == "list_pending_actions":
            drafts = await state_store.list_drafts(status=DraftStatus.PENDING)
            return {"content": [{"type": "text", "text": json.dumps([d.model_dump() for d in drafts], default=str)}]}

        elif tool_name == "approve_action":
            draft_id = args.get("draft_id")
            approver = args.get("approver", "mcp-user")
            res = await SlackTools.dispatch_approved_action(draft_id, approver)
            return {"content": [{"type": "text", "text": json.dumps(res, default=str)}]}

        elif tool_name == "reject_action":
            draft_id = args.get("draft_id")
            approver = args.get("approver", "mcp-user")
            updated = await state_store.update_draft_status(
                draft_id=draft_id,
                status=DraftStatus.REJECTED,
                approver=approver,
                result="Action rejected via MCP.",
            )
            if not updated:
                raise ValueError(f"Draft '{draft_id}' not found.")
            return {"content": [{"type": "text", "text": json.dumps({"status": "rejected", "draft_id": draft_id})}]}

        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

    async def run_stdio(self):
        """Runs the standard I/O protocol loop for desktop assistants (Antigravity, Claude Desktop)."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                req_json = json.loads(line_str)
                resp = await self.handle_jsonrpc(req_json)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = JSONRPCResponse(
                    error={"code": -32700, "message": f"Parse error: {str(e)}"}
                ).model_dump()
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


mcp_server = PrometheusMCPServer()

if __name__ == "__main__":
    asyncio.run(mcp_server.run_stdio())
