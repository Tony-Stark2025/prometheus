"""
Synthesis & Blocker Agent for Prometheus.
Correlates multi-source operational telemetry to identify root-cause delivery bottlenecks.
Integrates with Google GenAI SDK (Gemini) with deterministic heuristic fallback.
"""

from typing import List, Dict, Any, Optional
import json
import logging
from app.config import settings
from app.memory.state_store import state_store, BlockerRecord

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """
    Sub-agent 5: Synthesis & Blocker Agent
    Correlates Git PR latency, Jira dependency graphs, and Slack discussions to pinpoint delivery blockers.
    """

    name: str = "SynthesisAndBlockerAgent"
    role: str = "Multi-Domain Telemetry Correlation & Root Cause Analysis"

    @classmethod
    async def synthesize(
        cls,
        git_telemetry: Dict[str, Any],
        jira_telemetry: Dict[str, Any],
        slack_telemetry: Dict[str, Any],
    ) -> List[BlockerRecord]:
        """
        Synthesizes telemetry across sub-agents and generates persistent blocker records.
        """
        blockers: List[BlockerRecord] = []

        stale_prs = git_telemetry.get("stale_prs", [])
        ci_failures = git_telemetry.get("ci_failures", [])
        blocked_issues = jira_telemetry.get("blocked_issues", [])
        messages = slack_telemetry.get("messages", [])

        # Try Gemini LLM Reasoning if API key is provided
        if settings.gemini_api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.gemini_api_key)
                prompt = f"""
You are the Prometheus Synthesis & Blocker Agent.
Analyze the following multi-domain engineering telemetry and identify root-cause delivery bottlenecks:

Git Telemetry:
Stale PRs: {json.dumps(stale_prs, default=str)}
CI Failures: {json.dumps(ci_failures, default=str)}

Jira Telemetry:
Blocked Issues: {json.dumps(blocked_issues, default=str)}

Slack Telemetry:
Messages: {json.dumps(messages, default=str)}

Return a JSON array of objects with:
- blocker_id: string (e.g. "BLK-01")
- title: string (concise summary)
- description: string (root cause and correlation detail)
- severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
- source_artifacts: list of strings (e.g. ["PR-402", "PROJ-108"])
- impacted_squads: list of strings (e.g. ["platform", "auth"])
"""
                response = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                if response.text:
                    parsed = json.loads(response.text)
                    if isinstance(parsed, list):
                        for item in parsed:
                            rec = BlockerRecord(
                                blocker_id=item.get("blocker_id", f"BLK-{len(blockers)+1:02d}"),
                                title=item.get("title", "Detected Blocker"),
                                description=item.get("description", ""),
                                severity=item.get("severity", "HIGH"),
                                source_artifacts=item.get("source_artifacts", []),
                                impacted_squads=item.get("impacted_squads", ["engineering"]),
                                metadata={"engine": "gemini"},
                            )
                            await state_store.save_blocker(rec)
                            blockers.append(rec)
                        return blockers
            except Exception as e:
                logger.warning("Gemini LLM synthesis fallback to heuristic correlation: %s", e)

        # Deterministic Heuristic Correlation Engine (Zero-dependency & offline reliable)
        # Check cross-domain correlation: PR-402 is stale + blocks PROJ-108 + has Slack mention
        for pr in stale_prs:
            pr_id = pr.get("id")
            blocking = pr.get("blocking_downstream", [])
            
            # Find related Jira tickets
            related_jira = [
                issue for issue in blocked_issues
                if pr_id in issue.get("blocked_by", []) or issue.get("key") in blocking
            ]
            
            # Find related Slack mentions
            related_slack = [
                m for m in messages
                if pr_id in m.get("text", "")
            ]

            artifacts = [pr_id] + [j["key"] for j in related_jira] + [s["id"] for s in related_slack]
            
            description = (
                f"PR {pr_id} ('{pr.get('title')}') has been waiting for review for {pr.get('review_latency_hours')} hours "
                f"from reviewer(s) {', '.join(pr.get('reviewers', []))}. "
            )
            if related_jira:
                description += f"It is directly blocking high-priority Jira Epic(s): {', '.join([j['key'] for j in related_jira])}. "
            if ci_failures:
                description += f"Downstream CI pipeline is also failing due to interface mismatch with unmerged changes."

            blocker = BlockerRecord(
                blocker_id=f"BLK-{len(blockers)+1:02d}",
                title=f"Stale PR {pr_id} blocking Epic {related_jira[0]['key'] if related_jira else 'Delivery'}",
                description=description,
                severity="CRITICAL" if related_jira else "HIGH",
                source_artifacts=artifacts,
                impacted_squads=pr.get("scopes", ["engineering"]),
                metadata={"engine": "heuristic_correlation"},
            )
            await state_store.save_blocker(blocker)
            blockers.append(blocker)

        return blockers
