# DISPATCH — Worker M1 (Live Telemetry & Communication Tools)

Working directory: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_worker_m1
Original Request: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md
Project Scope: c:\Users\brigh\project\prometheus\PROJECT.md
Survey Report: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_explorer_survey_telemetry\handoff.md

Mission:
Implement live enterprise API clients for GitHub, Jira Cloud, and Slack in `prometheus/tools/` and synchronize to `app/tools/`:
1. `github_tools.py`:
   - Use `httpx.AsyncClient` with `GITHUB_TOKEN`.
   - Implement `get_open_pull_requests`: query live GitHub REST API (`/repos/{owner}/{repo}/pulls?state=open`), calculate `review_latency_hours`, extract `reviewers` and review status, normalize schema.
   - Implement `get_ci_pipeline_failures`: query live GitHub Actions workflow runs (`/repos/{owner}/{repo}/actions/runs?status=failure`), extract `failed_step` and `error_summary`.
   - Graceful fallback to `MOCK_PRS` and `MOCK_CI_FAILURES` if `GITHUB_TOKEN` is missing or rate limited.
2. `jira_tools.py`:
   - Use `httpx.AsyncClient` with Basic Auth (`JIRA_USER_EMAIL` + `JIRA_API_TOKEN`) or Bearer token to `JIRA_INSTANCE_URL`.
   - Implement `get_sprint_issues`: JQL search (`/rest/api/3/search`), extract epics, statuses, blockers from `issuelinks` (`is blocked by`, `blocks`), normalize schema.
   - Implement `get_blocked_issues`.
   - Graceful fallback to `MOCK_ISSUES` if `JIRA_API_TOKEN` is missing.
3. `slack_tools.py`:
   - Use `httpx.AsyncClient` with `SLACK_BOT_TOKEN`.
   - Implement `get_recent_channel_messages`: query `conversations.history` for public channels, normalize schema.
   - Implement `dispatch_approved_action`: post live Block Kit cards / DMs via `chat.postMessage` when token is present; update SQLite state store to `EXECUTED` with idempotency.
   - Graceful fallback to `MOCK_MESSAGES` and simulated dispatch if `SLACK_BOT_TOKEN` is missing.
4. Update `config.py` in `prometheus/` and `app/`:
   - Add `jira_user_email`, `github_repos`, `slack_channels` settings.
   - Update `.env.example`.
5. Maintain dual namespace synchronization between `prometheus/` and `app/`.
6. Run `pytest -v` to ensure 100% tests pass.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-08-26T20:21:51Z
**Context**: M1 Telemetry Implementer Finalization
**Content**: Please write your final handoff.md in c:\Users\brigh\project\prometheus\.agents\teamwork_preview_worker_m1\handoff.md detailing all code changes, test results, and verification evidence, and notify parent.
**Action**: Write handoff.md and send completion notification.
