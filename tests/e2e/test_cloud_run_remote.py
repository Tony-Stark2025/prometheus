"""
Tier 4 E2E Tests: Cloud Run Service & MCP Remote Endpoint Verification
Validates live Cloud Run HTTP/SSE endpoints or FastAPI application container locally and remotely.
"""

import pytest
import os
from starlette.testclient import TestClient
from prometheus.main import app
from prometheus.memory.state_store import state_store, ActionDraftRecord, DraftStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.e2e
class TestCloudRunRemote:
    def test_healthz_endpoint(self, client):
        """Verifies /healthz endpoint returns healthy status and platform flags."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "prometheus-chief-of-staff"
        assert data["hitl_enforced"] is True
        assert data["mcp_enabled"] is True

    def test_dashboard_and_root_endpoints(self, client):
        """Verifies /dashboard and / endpoints serve valid HTML user interface."""
        resp_root = client.get("/")
        assert resp_root.status_code == 200
        assert "text/html" in resp_root.headers.get("content-type", "")
        assert "Prometheus" in resp_root.text

        resp_dash = client.get("/dashboard")
        assert resp_dash.status_code == 200
        assert "text/html" in resp_dash.headers.get("content-type", "")
        assert "Prometheus" in resp_dash.text

    def test_api_agent_registry_endpoint(self, client):
        """Verifies /api/v1/registry/agents exposes all 6 sub-agents."""
        response = client.get("/api/v1/registry/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 6
        assert len(data["agents"]) == 6

    def test_api_digest_and_blockers_workflow(self, client):
        """Verifies /api/v1/digest triggers full workflow and /api/v1/blockers returns active blockers."""
        payload = {
            "query": "Review sprint delivery blockers for platform team",
            "user_id": "lead-01",
            "username": "alex-lead",
            "org_scopes": ["engineering", "platform"],
        }
        digest_resp = client.post("/api/v1/digest", json=payload)
        assert digest_resp.status_code == 200
        digest_data = digest_resp.json()
        assert digest_data["status"] == "COMPLETED"
        assert len(digest_data["blockers"]) >= 1

        # Check /api/v1/blockers
        blockers_resp = client.get("/api/v1/blockers")
        assert blockers_resp.status_code == 200
        blockers_data = blockers_resp.json()
        assert "blockers" in blockers_data
        assert blockers_data["total"] >= 1

    def test_api_hitl_approval_and_rejection_endpoints(self, client):
        """Verifies POST /api/v1/actions/{draft_id}/approve and reject endpoints."""
        # Query to populate a draft
        digest_resp = client.post("/api/v1/digest", json={
            "query": "Get blockers",
            "user_id": "lead-01",
            "username": "alex-lead",
            "org_scopes": ["engineering", "platform"],
        })
        drafts = digest_resp.json().get("action_drafts", [])
        assert len(drafts) > 0
        draft_id = drafts[0]["draft_id"]

        # Approve endpoint
        app_resp = client.post(f"/api/v1/actions/{draft_id}/approve", json={
            "approver_username": "alex-lead",
        })
        assert app_resp.status_code == 200
        app_data = app_resp.json()
        assert app_data["status"] in ("success", "already_executed")

        # Reject nonexistent draft
        rej_resp = client.post("/api/v1/actions/NONEXISTENT-DRAFT-99/reject", json={
            "approver_username": "alex-lead",
        })
        assert rej_resp.status_code == 404

    def test_api_webhooks_endpoints(self, client):
        """Verifies webhook ingress handlers for GitHub and Slack events."""
        gh_resp = client.post("/api/v1/webhooks/github", json={"action": "opened", "pull_request": {"number": 101}})
        assert gh_resp.status_code == 200
        assert gh_resp.json()["status"] == "received"

        slack_resp = client.post("/api/v1/webhooks/slack", json={"type": "event_callback", "event": {"text": "hello"}})
        assert slack_resp.status_code == 200
        assert slack_resp.json()["status"] == "received"

        # Slack url_verification challenge
        slack_challenge = client.post("/api/v1/webhooks/slack", json={"type": "url_verification", "challenge": "test_challenge_abc"})
        assert slack_challenge.status_code == 200
        assert slack_challenge.json()["challenge"] == "test_challenge_abc"
