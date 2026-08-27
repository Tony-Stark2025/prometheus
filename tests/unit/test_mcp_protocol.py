"""
Tier 1 Unit Tests: Model Context Protocol (MCP) JSON-RPC 2.0 Schemas & Server
Validates protocol serialization, schemas, tool definitions, and error handling.
"""

import pytest
import json
from prometheus.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPToolParameter,
    MCPToolDefinition,
    MCPListToolsResponse,
)
from prometheus.mcp.server import PrometheusMCPServer
from prometheus.memory.state_store import state_store, ActionDraftRecord, DraftStatus


@pytest.fixture
def mcp_server():
    return PrometheusMCPServer()


@pytest.mark.unit
class TestMCPProtocol:
    def test_jsonrpc_request_schema_serialization(self):
        """Validates standard JSON-RPC 2.0 Request structure."""
        req = JSONRPCRequest(
            id="req-123",
            method="tools/call",
            params={"name": "list_active_blockers", "arguments": {}},
        )
        data = req.model_dump()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "req-123"
        assert data["method"] == "tools/call"
        assert data["params"]["name"] == "list_active_blockers"

    def test_jsonrpc_response_schema_serialization(self):
        """Validates JSON-RPC 2.0 Response with result or error."""
        res_success = JSONRPCResponse(id="req-123", result={"status": "ok"})
        assert res_success.model_dump()["result"] == {"status": "ok"}
        assert res_success.model_dump()["error"] is None

        res_err = JSONRPCResponse(id="req-456", error={"code": -32601, "message": "Method not found"})
        assert res_err.model_dump()["error"]["code"] == -32601

    def test_tool_definition_and_list_response_schema(self):
        """Validates MCP Tool definitions and schema models."""
        param = MCPToolParameter(
            properties={"draft_id": {"type": "string"}},
            required=["draft_id"],
        )
        tool = MCPToolDefinition(
            name="test_tool",
            description="A test tool description",
            inputSchema=param,
        )
        list_resp = MCPListToolsResponse(tools=[tool])
        assert len(list_resp.tools) == 1
        assert list_resp.tools[0].name == "test_tool"
        assert "draft_id" in list_resp.tools[0].inputSchema.properties

    @pytest.mark.asyncio
    async def test_mcp_initialize_method(self, mcp_server):
        """Validates MCP initialize handshake message."""
        payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = await mcp_server.handle_jsonrpc(payload)
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert "result" in resp
        result = resp["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "prometheus-mcp-server"
        assert "tools" in result["capabilities"]

    @pytest.mark.asyncio
    async def test_mcp_tools_list_contains_all_fleet_tools(self, mcp_server):
        """Validates MCP tools/list exposes all required tools."""
        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = await mcp_server.handle_jsonrpc(payload)
        assert resp["id"] == 2
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "get_daily_digest",
            "list_active_blockers",
            "list_pending_actions",
            "approve_action",
            "reject_action",
        ]
        for expected in expected_tools:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_mcp_unknown_method_error_code(self, mcp_server):
        """Validates JSON-RPC -32601 error on unregistered method."""
        payload = {"jsonrpc": "2.0", "id": 99, "method": "unsupported_mcp_call", "params": {}}
        resp = await mcp_server.handle_jsonrpc(payload)
        assert "error" in resp
        assert resp["error"]["code"] == -32601
        assert "Method 'unsupported_mcp_call' not found" in resp["error"]["message"]

    @pytest.mark.asyncio
    async def test_mcp_call_tool_list_active_blockers(self, mcp_server):
        """Validates MCP tools/call for list_active_blockers."""
        payload = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "list_active_blockers", "arguments": {}},
        }
        resp = await mcp_server.handle_jsonrpc(payload)
        assert "result" in resp
        assert "content" in resp["result"]
        assert len(resp["result"]["content"]) > 0
        assert resp["result"]["content"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_mcp_call_tool_list_pending_actions(self, mcp_server):
        """Validates MCP tools/call for list_pending_actions."""
        await state_store.init_db()
        payload = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "list_pending_actions", "arguments": {}},
        }
        resp = await mcp_server.handle_jsonrpc(payload)
        assert "result" in resp
        assert "content" in resp["result"]
        assert resp["result"]["content"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_mcp_call_tool_approve_and_reject_action(self, mcp_server):
        """Validates MCP tools/call for approve_action and reject_action."""
        await state_store.init_db()
        # Save a test draft
        draft = ActionDraftRecord(
            draft_id="DRAFT-MCP-UNIT-TEST",
            target_channel_or_user="#platform-engineering",
            action_type="slack_channel_alert",
            content="MCP approval test",
            status=DraftStatus.PENDING,
        )
        await state_store.save_draft(draft)

        # Approve via MCP
        app_payload = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "approve_action",
                "arguments": {"draft_id": "DRAFT-MCP-UNIT-TEST", "approver": "mcp-tester"},
            },
        }
        resp_app = await mcp_server.handle_jsonrpc(app_payload)
        assert "result" in resp_app
        content_text = json.loads(resp_app["result"]["content"][0]["text"])
        assert content_text["status"] == "success"

        # Nonexistent draft error handling
        rej_err_payload = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "reject_action",
                "arguments": {"draft_id": "NONEXISTENT-DRAFT", "approver": "mcp-tester"},
            },
        }
        resp_rej_err = await mcp_server.handle_jsonrpc(rej_err_payload)
        assert "error" in resp_rej_err
        assert resp_rej_err["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_mcp_call_unregistered_tool(self, mcp_server):
        """Validates tools/call with unknown tool name returns internal error code -32603."""
        payload = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {"name": "unregistered_tool_xyz", "arguments": {}},
        }
        resp = await mcp_server.handle_jsonrpc(payload)
        assert "error" in resp
        assert resp["error"]["code"] == -32603
        assert "Unknown MCP tool" in resp["error"]["message"]
