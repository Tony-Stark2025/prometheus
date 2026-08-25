"""
Main entrypoint for Prometheus Platform: FastAPI Web Server, MCP SSE Stream, & Interactive CLI.
"""

import os
import sys

# Ensure project root is in sys.path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.security.abac_guard import UserContext
from app.memory.state_store import state_store, DraftStatus
from app.tools.slack_tools import SlackTools
from app.registry.agent_registry import agent_registry
from app.mcp.server import mcp_server
from app.workflows.prometheus_flow import PrometheusWorkflow, WorkflowExecutionResult
from app.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize persistent SQLite store and background scheduler
    await state_store.init_db()
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()


app = FastAPI(
    title="Prometheus: Chief of Staff Observability Platform",
    description="Enterprise Workstream Observability & Asynchronous Multi-Agent Orchestration Platform",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Pydantic Request Models
# ==============================================================================
class TriggerDigestRequest(BaseModel):
    user_id: str = "lead-01"
    username: str = "alex-lead"
    org_scopes: List[str] = Field(default_factory=lambda: ["engineering", "platform"])
    query: str = "Generate daily alignment briefing and identify delivery blockers"


class ActionApprovalRequest(BaseModel):
    approver_username: str = "alex-lead"


# ==============================================================================
# Dashboard & Core REST API Endpoints
# ==============================================================================
DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "dashboard", "dashboard.html")


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def serve_dashboard():
    """
    Renders the Prometheus Executive Chief of Staff Web Dashboard.
    """
    if os.path.exists(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Prometheus Dashboard: dashboard.html not found.</h1>")


@app.get("/healthz", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
        "platform": "Gemini Enterprise Agent Platform (Agent Engine)",
        "model": settings.gemini_model,
        "location": settings.gcp_location,
        "agent_engine": {
            "app_id": settings.agent_engine_app_id,
            "location": settings.agent_engine_location,
        },
        "hitl_enforced": settings.enforce_human_in_the_loop,
        "mcp_enabled": settings.mcp_enabled,
    }


@app.get("/api/v1/blockers", tags=["Blockers"])
async def list_blockers():
    """
    Returns all active correlated delivery blockers.
    """
    return await state_store.get_active_blockers()


@app.post("/api/v1/digest", response_model=WorkflowExecutionResult, tags=["Workflows"])
async def trigger_alignment_digest(req: TriggerDigestRequest):
    """
    Executes the multi-agent workflow to ingest telemetry, correlate blockers, and draft action cards.
    """
    user = UserContext(
        user_id=req.user_id,
        username=req.username,
        is_authenticated=True,
        org_scopes=set(req.org_scopes),
    )
    result = await PrometheusWorkflow.run(user=user, query=req.query)
    return result


@app.get("/api/v1/registry/agents", tags=["Fortified Enterprise Fleet"])
async def list_registered_agents():
    """
    Agent Registry: Discovers and inspects capabilities and security controls of all 6 sub-agents.
    """
    return agent_registry.list_agents()


@app.get("/api/v1/actions", tags=["Human-in-the-Loop"])
async def list_actions(status: Optional[DraftStatus] = None):
    """
    Lists proposed action cards waiting for human confirmation.
    """
    return await state_store.list_drafts(status=status)


@app.post("/api/v1/actions/{draft_id}/approve", tags=["Human-in-the-Loop"])
async def approve_action(draft_id: str, req: ActionApprovalRequest):
    """
    Explicit Human Sign-Off: Dispatches an action card only upon approval.
    """
    try:
        res = await SlackTools.dispatch_approved_action(
            draft_id=draft_id,
            approver_username=req.approver_username,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/actions/{draft_id}/reject", tags=["Human-in-the-Loop"])
async def reject_action(draft_id: str, req: ActionApprovalRequest):
    """
    Aborts a proposed action draft.
    """
    updated = await state_store.update_draft_status(
        draft_id=draft_id,
        status=DraftStatus.REJECTED,
        approver=req.approver_username,
        result="Action rejected by user.",
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' not found.")
    return {"status": "rejected", "draft_id": draft_id}


# ==============================================================================
# Model Context Protocol (MCP) Server-Sent Events (SSE) Endpoint
# ==============================================================================
@app.post("/mcp/sse", tags=["Model Context Protocol"])
async def mcp_sse_endpoint(request: Request):
    """
    HTTP/SSE endpoint for external agent fleets to consume Prometheus MCP tools.
    """
    body = await request.json()
    response = await mcp_server.handle_jsonrpc(body)
    return response


# ==============================================================================
# Webhook Ingress Receivers
# ==============================================================================
@app.post("/api/v1/webhooks/github", tags=["Webhooks"])
async def github_webhook_receiver(payload: Dict[str, Any]):
    """
    Receives real-time GitHub PR and CI status webhooks and routes to GitAgent.
    """
    event_type = payload.get("action", "unknown")
    pr_id = payload.get("pull_request", {}).get("number", "unknown")
    return {
        "status": "received",
        "event": f"github_pr_{event_type}",
        "resource": f"PR-{pr_id}",
    }


@app.post("/api/v1/webhooks/slack", tags=["Webhooks"])
async def slack_webhook_receiver(payload: Dict[str, Any]):
    """
    Receives real-time Slack message events and HITL interactive button callbacks.
    """
    if "type" in payload and payload["type"] == "url_verification":
        return {"challenge": payload.get("challenge")}

    if "actions" in payload:
        # Handle Slack interactive button callback
        action = payload["actions"][0]
        draft_id = action.get("value")
        action_id = action.get("action_id")
        user = payload.get("user", {}).get("username", "slack-user")

        if action_id == "approve_action":
            res = await SlackTools.dispatch_approved_action(draft_id, user)
            return {"text": f"✓ {res['result']}"}
        else:
            await state_store.update_draft_status(draft_id, DraftStatus.REJECTED, user, "Rejected via Slack button.")
            return {"text": "Action dismissed."}

    return {"status": "received"}


# ==============================================================================
# Interactive CLI Runner
# ==============================================================================
async def cli_runner():
    await state_store.init_db()
    print("=" * 75)
    print(" 🚀 Prometheus Chief of Staff - Interactive Multi-Agent Orchestration")
    print("=" * 75)

    user = UserContext(
        user_id="lead-01",
        username="alex-lead",
        is_authenticated=True,
        org_scopes={"engineering", "platform"},
    )

    print("\n[1/4] Triggering Asynchronous Multi-Agent Ingestion & Synthesis...")
    result = await PrometheusWorkflow.run(
        user=user,
        query="Scan cross-squad telemetry for active sprint blockers",
    )

    print(f"\n Session ID: {result.session_id}")
    print(f" Status: {result.status}")
    print(f" Summary: {result.summary}")

    print("\n[2/4] Correlated Delivery Blockers:")
    for b in result.blockers:
        print(f"  • [{b['severity']}] {b['title']}")
        print(f"    Impact: {b['impacted_squads']} | Sources: {b['source_artifacts']}")

    print("\n[3/4] Proposed Action Cards (Human-in-the-Loop):")
    for d in result.action_drafts:
        print(f"  • Draft ID: {d['draft_id']} -> Target: {d['target_channel_or_user']}")
        print(f"    Action: {d['action_type']}")
        print(f"    Content: {d['content']}")
        print(f"    Status: {d['status']}")

    if result.action_drafts:
        first_draft_id = result.action_drafts[0]["draft_id"]
        print(f"\n[4/4] Interactive Human-In-The-Loop Approval Checkpoint for {first_draft_id}:")
        print("  Options: [Y] Approve & Dispatch | [N] Discard | [E] Edit")
        print(f"  Simulating human sign-off [Y]...")
        dispatch_res = await SlackTools.dispatch_approved_action(
            draft_id=first_draft_id,
            approver_username=user.username,
        )
        print(f"  ✓ {dispatch_res['result']}")

    print("\n" + "=" * 75)
    print(" ✨ Prometheus Workflow Completed Successfully!")
    print("=" * 75)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--cli", "-c"):
        asyncio.run(cli_runner())
    else:
        import uvicorn
        uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
