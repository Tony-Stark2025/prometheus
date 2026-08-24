"""
Mock telemetry fixtures and test data generators for Prometheus.
"""

from typing import List, Dict, Any


def get_sample_pr_telemetry() -> List[Dict[str, Any]]:
    return [
        {
            "id": "PR-402",
            "repo": "acme/auth-service",
            "title": "feat(oauth): Migrate to OAuth 2.1 token exchange",
            "author": "dev-sarah",
            "review_latency_hours": 58.0,
            "status": "OPEN",
            "reviewers": ["alex-lead"],
            "review_status": "WAITING_REVIEW",
            "ci_status": "PASSED",
            "scopes": ["engineering", "platform"],
            "blocking_downstream": ["PROJ-108"],
        }
    ]


def get_sample_jira_telemetry() -> List[Dict[str, Any]]:
    return [
        {
            "key": "PROJ-108",
            "summary": "Release v2.1 User Authentication & Federation Gateway",
            "type": "Epic",
            "status": "BLOCKED",
            "priority": "Highest",
            "assignee": "alex-lead",
            "blocked_by": ["PR-402"],
            "scopes": ["engineering", "platform"],
        }
    ]


def get_sample_slack_telemetry() -> List[Dict[str, Any]]:
    return [
        {
            "id": "MSG-901",
            "channel": "#platform-engineering",
            "user": "dev-sarah",
            "text": "PR #402 is blocking the gateway release.",
            "scopes": ["engineering", "platform"],
        }
    ]
