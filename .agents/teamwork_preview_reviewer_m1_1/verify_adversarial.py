import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
import unittest.mock as mock
import httpx
from datetime import datetime, timezone, timedelta

async def run_adversarial_suite():
    print("=== Starting Independent Adversarial Test Suite ===")
    
    # 1. Config tests
    from prometheus.config import Settings
    s = Settings(
        github_repos="repo1, repo2, repo3",
        slack_channels="ch1, ch2",
        jira_instance_url="   ",
        jira_user_email="dev@acme.com"
    )
    assert s.github_repos == ["repo1", "repo2", "repo3"], f"Failed github_repos: {s.github_repos}"
    assert s.slack_channels == ["ch1", "ch2"], f"Failed slack_channels: {s.slack_channels}"
    assert s.jira_instance_url is None, f"Failed empty_str_to_none: {s.jira_instance_url}"
    print("Config validation tests passed.")

    # 2. GitHubTools Adversarial Tests
    from prometheus.tools.github_tools import GitHubTools
    from app.tools.github_tools import GitHubTools as AppGH
    
    # Mock fallback without token
    prs = await GitHubTools.get_open_pull_requests()
    assert len(prs) == 3
    stale = await GitHubTools.get_stale_pull_requests(48.0)
    assert len(stale) == 1 and stale[0]["id"] == "PR-402"
    
    # Live API simulation
    sample_pr = [{
        "number": 101,
        "title": "feat(auth): Add SSO PR-202 PROJ-99",
        "body": "Depends on PR-303 and PROJ-108",
        "user": {"login": "alice"},
        "created_at": (datetime.now(timezone.utc) - timedelta(hours=50)).isoformat(),
        "updated_at": (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat(),
        "requested_reviewers": [{"login": "bob"}],
        "head": {"sha": "deadbeef1234"},
        "labels": [{"name": "security"}, {"name": "backend"}]
    }]
    sample_reviews = [{"user": {"login": "bob"}, "state": "CHANGES_REQUESTED"}]
    sample_checkruns = {"check_runs": [{"status": "completed", "conclusion": "failure"}]}
    
    async def mock_gh_get(url, *args, **kwargs):
        url_str = str(url)
        if "/pulls?" in url_str or url_str.endswith("/pulls"):
            return httpx.Response(200, json=sample_pr)
        elif "/reviews" in url_str:
            return httpx.Response(200, json=sample_reviews)
        elif "/check-runs" in url_str:
            return httpx.Response(200, json=sample_checkruns)
        return httpx.Response(404)

    with mock.patch("prometheus.config.settings.github_token", "test_gh_token"):
        with mock.patch("httpx.AsyncClient.get", side_effect=mock_gh_get):
            live_res = await GitHubTools.get_open_pull_requests(repos=["acme/auth-service"])
            assert len(live_res) == 1
            p = live_res[0]
            assert p["id"] == "PR-101"
            assert p["review_status"] == "CHANGES_REQUESTED"
            assert p["ci_status"] == "FAILED"
            assert "PR-202" in p["blocking_downstream"]
            assert "PROJ-99" in p["blocking_downstream"]
            assert "PR-303" in p["blocking_downstream"]
            assert "PROJ-108" in p["blocking_downstream"]
            assert "security" in p["scopes"]
            assert p["review_latency_hours"] >= 49.9
            print("GitHub live PR parsing & blocker regex passed.")

        # 429 Rate Limit Simulation
        with mock.patch("httpx.AsyncClient.get", return_value=httpx.Response(429, headers={"Retry-After": "60", "x-ratelimit-remaining": "0"})):
            rate_limited_prs = await GitHubTools.get_open_pull_requests(repos=["acme/auth-service"])
            assert len(rate_limited_prs) == 3, "Rate limit fallback failed"
            print("GitHub 429 rate limit fallback passed.")

        # 500 Server Error Simulation
        with mock.patch("httpx.AsyncClient.get", return_value=httpx.Response(500, text="Internal Server Error")):
            err_prs = await GitHubTools.get_open_pull_requests(repos=["acme/auth-service"])
            assert len(err_prs) == 3, "500 error fallback failed"
            print("GitHub 500 error fallback passed.")

        # Network Timeout Simulation
        with mock.patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
            timeout_prs = await GitHubTools.get_open_pull_requests(repos=["acme/auth-service"])
            assert len(timeout_prs) == 3, "Timeout fallback failed"
            print("GitHub timeout fallback passed.")

    # 3. JiraTools Adversarial Tests
    from prometheus.tools.jira_tools import JiraTools
    from app.tools.jira_tools import JiraTools as AppJira

    sample_jira = {
        "issues": [
            {
                "key": "SEC-50",
                "fields": {
                    "summary": "Upgrade auth tokens for PR-402",
                    "description": {"type": "doc", "content": [{"text": "Depends on PR-415"}]},
                    "issuetype": {"name": "Bug"},
                    "status": {"name": "Blocked by Security"},
                    "priority": {"name": "Highest"},
                    "sprint": {"name": "Sprint 99 - Security"},
                    "assignee": {"displayName": "Dev Alice"},
                    "reporter": {"displayName": "Lead Bob"},
                    "issuelinks": [
                        {
                            "type": {"inward": "is blocked by", "outward": "blocks"},
                            "inwardIssue": {"key": "PROJ-108", "fields": {"summary": "Parent epic"}}
                        }
                    ],
                    "labels": ["security", "platform"]
                }
            }
        ]
    }

    async def mock_jira_get(url, *args, **kwargs):
        url_str = str(url)
        if "/search" in url_str:
            return httpx.Response(200, json=sample_jira)
        return httpx.Response(404)

    with mock.patch("prometheus.config.settings.jira_api_token", "test_jira_token"):
        with mock.patch("prometheus.config.settings.jira_instance_url", "https://acme.atlassian.net"):
            with mock.patch("prometheus.config.settings.jira_user_email", "dev@acme.com"):
                with mock.patch("httpx.AsyncClient.get", side_effect=mock_jira_get):
                    j_issues = await JiraTools.get_sprint_issues()
                    assert len(j_issues) == 1
                    ji = j_issues[0]
                    assert ji["key"] == "SEC-50"
                    assert ji["status"] == "BLOCKED"
                    assert "PROJ-108" in ji["blocked_by"]
                    assert "PR-402" in ji["blocked_by"]
                    assert "PR-415" in ji["blocked_by"]
                    assert ji["assignee"] == "Dev Alice"
                    assert ji["sprint"] == "Sprint 99 - Security"
                    print("Jira live issue parsing, ADF description, and issuelinks passed.")

                # 429 Rate Limit Simulation
                with mock.patch("httpx.AsyncClient.get", return_value=httpx.Response(429, headers={"Retry-After": "120"})):
                    rl_jira = await JiraTools.get_sprint_issues()
                    assert len(rl_jira) == 3
                    print("Jira 429 rate limit fallback passed.")

    # 4. SlackTools Adversarial Tests
    from prometheus.tools.slack_tools import SlackTools
    from app.tools.slack_tools import SlackTools as AppSlack
    from prometheus.memory.state_store import state_store, DraftStatus

    await state_store.init_db()
    
    # Live chat.postMessage and DM resolution simulation
    async def mock_slack_api(url, *args, **kwargs):
        url_str = str(url)
        if "conversations.list" in url_str:
            return httpx.Response(200, json={"ok": True, "channels": [{"name": "platform-engineering", "id": "C12345"}]})
        elif "users.list" in url_str:
            return httpx.Response(200, json={"ok": True, "members": [{"id": "U999", "name": "alex-lead", "profile": {"display_name": "Alex Lead"}}]})
        elif "conversations.open" in url_str:
            return httpx.Response(200, json={"ok": True, "channel": {"id": "D54321"}})
        elif "chat.postMessage" in url_str:
            return httpx.Response(200, json={"ok": True, "ts": "1700000000.000100"})
        return httpx.Response(404)

    with mock.patch("prometheus.config.settings.slack_bot_token", "xox" + "b-test-token"):
        with mock.patch("httpx.AsyncClient.get", side_effect=mock_slack_api):
            with mock.patch("httpx.AsyncClient.post", side_effect=mock_slack_api):
                # Channel draft & dispatch
                ch_draft = await SlackTools.draft_action_card(
                    target="#platform-engineering",
                    action_type="slack_channel_alert",
                    content="Test Slack live post"
                )
                assert ch_draft.status == DraftStatus.PENDING
                
                disp1 = await SlackTools.dispatch_approved_action(ch_draft.draft_id, "alex-lead")
                assert disp1["status"] == "success"
                assert "ts: 1700000000.000100" in disp1["result"]
                
                # Idempotency check
                disp2 = await SlackTools.dispatch_approved_action(ch_draft.draft_id, "alex-lead")
                assert disp2["status"] == "already_executed"
                print("Slack live channel post and idempotency passed.")

                # DM draft & dispatch
                dm_draft = await SlackTools.draft_action_card(
                    target="@alex-lead",
                    action_type="slack_dm",
                    content="Direct alert"
                )
                disp_dm = await SlackTools.dispatch_approved_action(dm_draft.draft_id, "alex-lead")
                assert disp_dm["status"] == "success"
                print("Slack live DM opening and dispatch passed.")

    # 5. Dual Namespace Parity Verification
    print("Verifying namespace method equivalence...")
    for gh_cls in [GitHubTools, AppGH]:
        assert hasattr(gh_cls, "get_open_pull_requests")
        assert hasattr(gh_cls, "get_stale_pull_requests")
        assert hasattr(gh_cls, "get_ci_pipeline_failures")
    for jira_cls in [JiraTools, AppJira]:
        assert hasattr(jira_cls, "get_sprint_issues")
        assert hasattr(jira_cls, "get_blocked_issues")
    for slack_cls in [SlackTools, AppSlack]:
        assert hasattr(slack_cls, "get_recent_channel_messages")
        assert hasattr(slack_cls, "draft_action_card")
        assert hasattr(slack_cls, "dispatch_approved_action")
    print("Dual namespace parity verified.")

    print("\n>>> ALL ADVERSARIAL STRESS TESTS COMPLETED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(run_adversarial_suite())
