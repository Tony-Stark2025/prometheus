"""
Attribute-Based Access Control (ABAC) and deterministic Row-Level Security (RLS) filter.
Guarantees sub-agents only ingest and correlate data within authorized organizational scopes.

Formula:
  P(U, R) = IsAuthenticated(U) AND WithinOrgScope(U, R) AND NOT IsRestricted(R)
"""

from typing import List, Set, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str
    username: str
    is_authenticated: bool = True
    org_scopes: Set[str] = Field(default_factory=lambda: {"engineering", "platform"})
    roles: List[str] = Field(default_factory=lambda: ["developer"])
    is_admin: bool = False


class ResourceContext(BaseModel):
    resource_id: str
    resource_type: str  # "github_pr", "jira_issue", "slack_message", "ci_pipeline"
    required_scopes: Set[str]
    is_restricted: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ABACGuard:
    """
    Evaluates fine-grained access control before telemetry is routed to downstream LLMs.
    """

    @staticmethod
    def evaluate_access(user: UserContext, resource: ResourceContext) -> bool:
        """
        Determines if a user has permission to read/act upon a given resource.
        """
        if not user.is_authenticated:
            return False

        if user.is_admin:
            return True

        if resource.is_restricted:
            return False

        # WithinOrgScope: User scopes must intersect with the required scopes of the resource
        if not (user.org_scopes & resource.required_scopes):
            return False

        return True

    @staticmethod
    def filter_resources(user: UserContext, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch filters telemetry items against the user context.
        """
        authorized = []
        for item in resources:
            item_scopes = set(item.get("scopes", ["engineering"]))
            is_restricted = item.get("is_restricted", False)
            resource_ctx = ResourceContext(
                resource_id=str(item.get("id", "unknown")),
                resource_type=item.get("type", "generic"),
                required_scopes=item_scopes,
                is_restricted=is_restricted,
                metadata=item,
            )
            if ABACGuard.evaluate_access(user, resource_ctx):
                authorized.append(item)
        return authorized
