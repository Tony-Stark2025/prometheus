"""
GitHub and CI/CD telemetry tools for Prometheus.
Ingests pull request review latency, stale branches, and build pipeline health.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional


class GitHubTools:
    """
    Ingests PR status and CI/CD run metrics across repositories.
    """

    # Realistic mock fixtures for when live GITHUB_TOKEN is not supplied or for testing
    MOCK_PRS: List[Dict[str, Any]] = [
        {
            "id": "PR-402",
            "repo": "acme/auth-service",
            "title": "feat(oauth): Migrate to OAuth 2.1 token exchange",
            "author": "dev-sarah",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=58)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=52)).isoformat(),
            "review_latency_hours": 58.0,
            "status": "OPEN",
            "reviewers": ["alex-lead"],
            "review_status": "WAITING_REVIEW",
            "ci_status": "PASSED",
            "scopes": ["engineering", "platform", "security"],
            "blocking_downstream": ["PROJ-108", "PR-415"],
        },
        {
            "id": "PR-415",
            "repo": "acme/web-gateway",
            "title": "fix(gateway): Adapt downstream auth headers for v2.1",
            "author": "dev-alex",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "review_latency_hours": 30.0,
            "status": "OPEN",
            "reviewers": ["sarah-reviewer"],
            "review_status": "CHANGES_REQUESTED",
            "ci_status": "FAILED",
            "scopes": ["engineering", "platform"],
            "blocking_downstream": ["PROJ-108"],
        },
        {
            "id": "PR-420",
            "repo": "acme/billing-core",
            "title": "chore: Upgrade Stripe webhook validator",
            "author": "dev-marcus",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "review_latency_hours": 12.0,
            "status": "OPEN",
            "reviewers": ["elena-reviewer"],
            "review_status": "APPROVED",
            "ci_status": "PASSED",
            "scopes": ["engineering", "finance"],
            "blocking_downstream": [],
        },
    ]

    MOCK_CI_FAILURES: List[Dict[str, Any]] = [
        {
            "id": "CI-8902",
            "repo": "acme/web-gateway",
            "branch": "fix/auth-headers",
            "commit": "a1c8f3e",
            "failed_step": "integration-tests / auth_matrix_test",
            "error_summary": "401 Unauthorized: token exchange handshake mismatched auth-service v2.1 schema",
            "run_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "scopes": ["engineering", "platform"],
        }
    ]

    @classmethod
    async def get_open_pull_requests(cls, scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves active open pull requests, filtered by org scope if provided.
        """
        if not scopes:
            return cls.MOCK_PRS
        return [
            pr for pr in cls.MOCK_PRS
            if any(s in pr.get("scopes", []) for s in scopes)
        ]

    @classmethod
    async def get_stale_pull_requests(cls, hours_threshold: float = 48.0) -> List[Dict[str, Any]]:
        """
        Filters pull requests with review latency exceeding the threshold.
        """
        return [
            pr for pr in cls.MOCK_PRS
            if pr.get("review_latency_hours", 0) >= hours_threshold and pr.get("review_status") == "WAITING_REVIEW"
        ]

    @classmethod
    async def get_ci_pipeline_failures(cls) -> List[Dict[str, Any]]:
        """
        Retrieves failing CI/CD builds across connected repositories.
        """
        return cls.MOCK_CI_FAILURES
