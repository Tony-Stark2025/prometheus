"""
Jira and Linear project management telemetry tools for Prometheus.
Tracks issue status, sprint blockers, epic dependencies, and burndown risks.
"""

from typing import List, Dict, Any, Optional


class JiraTools:
    """
    Ingests project tracker metadata and identifies blocker dependencies across teams.
    """

    MOCK_ISSUES: List[Dict[str, Any]] = [
        {
            "key": "PROJ-108",
            "summary": "Release v2.1 User Authentication & Federation Gateway",
            "type": "Epic",
            "status": "BLOCKED",
            "priority": "Highest",
            "sprint": "Sprint 24 - Core Platform",
            "assignee": "alex-lead",
            "reporter": "product-dan",
            "blocked_by": ["PR-402", "PR-415"],
            "blocker_reason": "Waiting on auth-service OAuth 2.1 PR review and web-gateway CI failure resolution.",
            "scopes": ["engineering", "platform"],
            "target_release_date": "2026-08-28",
        },
        {
            "key": "PROJ-112",
            "summary": "Implement Redis session caching for high-concurrency auth",
            "type": "Story",
            "status": "IN_PROGRESS",
            "priority": "Medium",
            "sprint": "Sprint 24 - Core Platform",
            "assignee": "dev-sarah",
            "reporter": "alex-lead",
            "blocked_by": [],
            "blocker_reason": None,
            "scopes": ["engineering", "platform"],
            "target_release_date": "2026-08-30",
        },
        {
            "key": "PROJ-99",
            "summary": "Fix billing reconciliation edge case in EU VAT calculation",
            "type": "Bug",
            "status": "IN_REVIEW",
            "priority": "High",
            "sprint": "Sprint 18 - Billing Squad",
            "assignee": "dev-marcus",
            "reporter": "support-lead",
            "blocked_by": [],
            "blocker_reason": None,
            "scopes": ["engineering", "finance"],
            "target_release_date": "2026-08-25",
        },
    ]

    @classmethod
    async def get_sprint_issues(cls, scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetches active sprint issues, optionally filtered by scope.
        """
        if not scopes:
            return cls.MOCK_ISSUES
        return [
            issue for issue in cls.MOCK_ISSUES
            if any(s in issue.get("scopes", []) for s in scopes)
        ]

    @classmethod
    async def get_blocked_issues(cls) -> List[Dict[str, Any]]:
        """
        Filters issues in blocked status or with active dependencies.
        """
        return [
            issue for issue in cls.MOCK_ISSUES
            if issue.get("status") == "BLOCKED" or len(issue.get("blocked_by", [])) > 0
        ]
