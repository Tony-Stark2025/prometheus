"""
Main entrypoint for Prometheus Platform: FastAPI Web Server & Interactive CLI Runner.
"""

import sys
import asyncio
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.security.abac_guard import UserContext
from app.memory.state_store import state_store, DraftStatus
from app.tools.slack_tools import SlackTools
from app.workflows.prometheus_flow import PrometheusWorkflow, WorkflowExecutionResult

app = FastAPI(
    title="Prometheus: Chief of Staff Observability Platform",
    description="Enterprise Workstream Observability & Asynchronous Multi-Agent Orchestration Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request & Response Schemas
class TriggerDigestRequest(BaseModel):
    user_id: str = "user-101"
    username: str = "alex-lead"
    org_scopes: List[str] = Field(default_factory=lambda: ["engineering", "platform"])
    query: str = "Generate daily alignment briefing and identify delivery blockers"


class ActionApprovalRequest(BaseModel):
    approver_username: str = "alex-lead"


@app.get("/healthz", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
        "model": settings.gemini_model,
        "hitl_enforced": settings.enforce_human_in_the_loop,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Prometheus - Enterprise Workstream Observability Platform",
        "documentation": "/docs",
        "health": "/healthz",
    }


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
# Interactive CLI Runner
# ==============================================================================
async def cli_runner():
    print("=" * 70)
    print(" 🚀 Prometheus Chief of Staff - Interactive Multi-Agent Orchestration")
    print("=" * 70)

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
        print(f"\n[4/4] Simulating Human Sign-Off Approval for {first_draft_id}...")
        dispatch_res = await SlackTools.dispatch_approved_action(
            draft_id=first_draft_id,
            approver_username=user.username,
        )
        print(f"  ✓ {dispatch_res['result']}")

    print("\n" + "=" * 70)
    print(" ✨ Prometheus Workflow Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--cli", "-c"):
        asyncio.run(cli_runner())
    else:
        import uvicorn
        uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
