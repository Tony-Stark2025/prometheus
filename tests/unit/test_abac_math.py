"""
Tier 1 Unit Tests: Mathematical Property Testing for ABAC (Attribute-Based Access Control)
Formula:
  P(U, R) = IsAuthenticated(U) AND WithinOrgScope(U, R) AND NOT IsRestricted(R)
"""

import pytest
from prometheus.security.abac_guard import ABACGuard, UserContext, ResourceContext


@pytest.mark.unit
class TestABACMath:
    def test_unauthenticated_user_always_denied(self):
        """Unauthenticated user must be denied access regardless of scopes or admin flags."""
        user = UserContext(
            user_id="u_unauth",
            username="anon",
            is_authenticated=False,
            org_scopes={"engineering", "platform", "admin"},
            is_admin=True,
        )
        res = ResourceContext(
            resource_id="res-01",
            resource_type="github_pr",
            required_scopes={"engineering"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is False

    def test_admin_user_bypasses_scope_checks(self):
        """Authenticated admin user receives access regardless of scope mismatch (when unrestricted)."""
        user = UserContext(
            user_id="u_admin",
            username="superuser",
            is_authenticated=True,
            org_scopes=set(),
            is_admin=True,
        )
        res = ResourceContext(
            resource_id="res-02",
            resource_type="jira_issue",
            required_scopes={"finance", "legal"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is True

    def test_restricted_resource_denies_all_including_admin(self):
        """Restricted resource is denied even to authenticated admin users."""
        user = UserContext(
            user_id="u_admin",
            username="superuser",
            is_authenticated=True,
            org_scopes={"engineering", "finance", "legal"},
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-03",
            resource_type="secret_vault",
            required_scopes={"engineering"},
            is_restricted=True,
        )
        assert ABACGuard.evaluate_access(user, res) is False

    def test_empty_user_scopes_denies_access(self):
        """Standard user with empty org_scopes is denied access to scoped resources."""
        user = UserContext(
            user_id="u_empty",
            username="empty_user",
            is_authenticated=True,
            org_scopes=set(),
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-04",
            resource_type="slack_message",
            required_scopes={"engineering"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is False

    def test_empty_resource_scopes_denies_access(self):
        """Standard user is denied access if resource has empty required_scopes (empty intersection)."""
        user = UserContext(
            user_id="u_dev",
            username="developer",
            is_authenticated=True,
            org_scopes={"engineering"},
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-05",
            resource_type="ci_pipeline",
            required_scopes=set(),
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is False

    def test_single_scope_intersection_grants_access(self):
        """User with at least one matching scope is granted access."""
        user = UserContext(
            user_id="u_dev",
            username="developer",
            is_authenticated=True,
            org_scopes={"engineering"},
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-06",
            resource_type="github_pr",
            required_scopes={"engineering", "security"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is True

    def test_disjoint_scopes_denies_access(self):
        """User whose scopes do not intersect with resource required scopes is denied access."""
        user = UserContext(
            user_id="u_sales",
            username="sales_rep",
            is_authenticated=True,
            org_scopes={"sales", "marketing"},
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-07",
            resource_type="github_pr",
            required_scopes={"engineering", "platform"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is False

    def test_multi_scope_full_overlap_grants_access(self):
        """User with multiple overlapping scopes is granted access."""
        user = UserContext(
            user_id="u_lead",
            username="tech_lead",
            is_authenticated=True,
            org_scopes={"engineering", "platform", "infrastructure"},
            is_admin=False,
        )
        res = ResourceContext(
            resource_id="res-08",
            resource_type="jira_issue",
            required_scopes={"platform", "infrastructure"},
            is_restricted=False,
        )
        assert ABACGuard.evaluate_access(user, res) is True

    def test_batch_filter_resources_filtering(self):
        """filter_resources correctly partitions a mixed list of telemetry items."""
        user = UserContext(
            user_id="u_dev",
            username="dev_sarah",
            is_authenticated=True,
            org_scopes={"engineering", "platform"},
            is_admin=False,
        )
        items = [
            {"id": "PR-101", "scopes": ["engineering"], "title": "Eng PR"},
            {"id": "PR-102", "scopes": ["finance"], "title": "Finance PR"},
            {"id": "PR-103", "scopes": ["platform"], "title": "Platform PR"},
            {"id": "PR-104", "scopes": ["marketing"], "title": "Marketing PR"},
            {"id": "PR-105", "scopes": ["engineering"], "is_restricted": True, "title": "Restricted Eng PR"},
        ]
        filtered = ABACGuard.filter_resources(user, items)
        filtered_ids = [item["id"] for item in filtered]
        assert "PR-101" in filtered_ids
        assert "PR-103" in filtered_ids
        assert "PR-102" not in filtered_ids
        assert "PR-104" not in filtered_ids
        assert "PR-105" not in filtered_ids
        assert len(filtered) == 2

    def test_batch_filter_resources_default_scope_handling(self):
        """Items without explicit 'scopes' key default to ['engineering']."""
        user = UserContext(
            user_id="u_eng",
            username="dev_alex",
            is_authenticated=True,
            org_scopes={"engineering"},
            is_admin=False,
        )
        items = [
            {"id": "ITEM-DEFAULT", "title": "No explicit scope"},
        ]
        filtered = ABACGuard.filter_resources(user, items)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "ITEM-DEFAULT"
