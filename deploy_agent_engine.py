"""
Deploy Prometheus Multi-Agent Fleet directly to Vertex AI Agent Engine (Gemini Enterprise Agent Platform).
Uses Vertex AI Reasoning Engine SDK for native agent lifecycle, enterprise IAM, and Model Armor.
"""

import os
import sys
import argparse
import asyncio
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.workflows.prometheus_flow import PrometheusWorkflow
from app.security.abac_guard import UserContext
from app.memory.state_store import state_store, DraftStatus
from app.tools.slack_tools import SlackTools
from app.registry.agent_registry import agent_registry


class PrometheusAgentEngineApp:
    """
    Native Agent Application packaged for Google Cloud Vertex AI Agent Engine (Reasoning Engine).
    """

    def __init__(self, model: str = "gemini-3.7-flash"):
        self.model = model
        self.agent_name = "prometheus-chief-of-staff"

    def set_up(self):
        """Initializes state store and tools on Agent Engine startup."""
        import asyncio
        asyncio.run(state_store.init_db())

    def query(
        self,
        prompt: str = "Scan cross-squad telemetry for active sprint blockers",
        user_id: str = "lead-01",
        username: str = "alex-lead",
        org_scopes: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Main query entrypoint for Gemini Enterprise Agent Platform.
        Executes asynchronous multi-agent telemetry correlation and action drafting.
        """
        if org_scopes is None:
            org_scopes = ["engineering", "platform"]

        user = UserContext(
            user_id=user_id,
            username=username,
            is_authenticated=True,
            org_scopes=set(org_scopes),
        )

        result = asyncio.run(PrometheusWorkflow.run(user=user, query=prompt))
        return {
            "session_id": result.session_id,
            "status": result.status,
            "summary": result.summary,
            "blockers": result.blockers,
            "action_drafts": result.action_drafts,
            "daily_digest": result.daily_digest.model_dump() if result.daily_digest else None,
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        """Returns the Fortified Enterprise Fleet registry of all 6 sub-agents."""
        return [a.model_dump() for a in agent_registry.list_agents()]

    def approve_action(self, draft_id: str, approver_username: str = "alex-lead") -> Dict[str, Any]:
        """Human-in-the-loop action approval endpoint."""
        res = asyncio.run(SlackTools.dispatch_approved_action(draft_id, approver_username))
        return res


def deploy_to_vertex_agent_engine(
    project_id: str,
    location: str = "us-central1",
    staging_bucket: str = None,
):
    """
    Deploys the Prometheus Agent Engine application to Vertex AI Reasoning Engine.
    """
    print("=" * 75)
    print(" 🚀 Deploying Prometheus to Vertex AI Agent Engine (Gemini Enterprise Agent Platform)")
    print("=" * 75)
    print(f" Project ID : {project_id}")
    print(f" Location   : {location}")
    print(f" Model      : {settings.gemini_model} (Vertex AI)")
    print("=" * 75)

    try:
        import vertexai
        from vertexai.preview import reasoning_engines

        vertexai.init(
            project=project_id,
            location=location,
            staging_bucket=staging_bucket,
        )

        app_instance = PrometheusAgentEngineApp(model=settings.gemini_model)

        print("\n1. Packaging and creating Vertex AI Reasoning Engine...")
        remote_agent = reasoning_engines.ReasoningEngine.create(
            app_instance,
            requirements=[
                "google-cloud-aiplatform>=1.70.0",
                "google-genai>=1.0.0",
                "pydantic>=2.0.0",
                "pydantic-settings>=2.0.0",
                "aiosqlite>=0.20.0",
                "httpx>=0.27.0",
            ],
            display_name="prometheus-chief-of-staff",
            description="Autonomous AI Chief of Staff & Workstream Observability Platform",
        )

        print("\n" + "=" * 75)
        print(" ✨ Prometheus Successfully Deployed to Vertex AI Agent Engine!")
        print(f" 🆔 Resource Name : {remote_agent.resource_name}")
        print(" 🏛️ Platform      : Gemini Enterprise Agent Platform")
        print(f" 🤖 Model Engine  : {settings.gemini_model}")
        print("=" * 75)
        return remote_agent

    except Exception as e:
        print(f"\n⚠️ Deployment failed: {e}")
        print("\nEnsure you have authenticated via:")
        print("  gcloud auth application-default login")
        print(f"  gcloud config set project {project_id}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Prometheus to Vertex AI Agent Engine")
    parser.add_argument("--project", default=settings.gcp_project_id or os.getenv("GCP_PROJECT_ID"), help="GCP Project ID")
    parser.add_argument("--location", default=settings.gcp_location or "us-central1", help="GCP Region")
    parser.add_argument("--bucket", default=None, help="GCS Staging Bucket (gs://bucket-name)")

    args = parser.parse_args()

    if not args.project:
        print("⚠️ Error: GCP Project ID required. Provide --project <PROJECT_ID> or set GCP_PROJECT_ID in .env")
        sys.exit(1)

    deploy_to_vertex_agent_engine(
        project_id=args.project,
        location=args.location,
        staging_bucket=args.bucket,
    )
