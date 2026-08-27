# Telemetry & Communication Tools Survey Report (GitHub, Jira, Slack)

## Executive Summary
This report presents an in-depth architectural and code-level investigation of Prometheus's telemetry ingestion and communication tools (`GitHubTools`, `JiraTools`, and `SlackTools`), mock fixtures, sub-agent consumers, configuration schemas, authentication mechanisms, and dependencies. It outlines concrete implementation blueprints for replacing static fixtures with enterprise-grade live API integrations using asynchronous `httpx` clients while preserving offline/hermetic mock fallback and maintaining 100% test compatibility across the multi-agent fleet and Google Cloud Vertex AI Agent Engine.

---

## 1. Observation

### 1.1 Codebase Structure & Dual Namespace Layout
The repository contains both `prometheus/` (packaged module) and `app/` (mirror module):
- `setup.py` (lines 1-19) packages `prometheus` with version `1.1.0`.
- `refactor_namespace.py` (lines 4-20) refactored references to `from prometheus.*`.
- `Dockerfile` (line 39) executes `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`.
- `deploy_agent_engine.py` (lines 120-134) bundles both packages: `extra_packages=[pkg_prometheus, pkg_app]`.
- Existing tests (`tests/test_workflow.py` and `tests/test_endpoints.py`) import from `prometheus.*`.

### 1.2 GitHub Tool Implementation (`GitHubTools`)
- **File Locations**: `prometheus/tools/github_tools.py` (lines 1-105) and `app/tools/github_tools.py` (lines 1-105).
- **Current Mock Fixtures**:
  - `MOCK_PRS`: 3 sample pull requests (`PR-402`, `PR-415`, `PR-420`).
    - Key schema fields: `id` (str), `repo` (str, e.g. `"acme/auth-service"`), `title` (str), `author` (str), `created_at` (ISO timestamp), `updated_at` (ISO timestamp), `review_latency_hours` (float), `status` (`"OPEN"`), `reviewers` (List[str]), `review_status` (`"WAITING_REVIEW"` | `"CHANGES_REQUESTED"` | `"APPROVED"`), `ci_status` (`"PASSED"` | `"FAILED"`), `scopes` (List[str]), `blocking_downstream` (List[str]).
  - `MOCK_CI_FAILURES`: 1 sample failure (`CI-8902`).
    - Key schema fields: `id` (str), `repo` (str), `branch` (str), `commit` (str), `failed_step` (str), `error_summary` (str), `run_at` (ISO timestamp), `scopes` (List[str]).
- **Sub-Agent Consumers**:
  - `GitAgent.collect_telemetry` (`prometheus/agents/git_agent.py`, lines 21-50): Calls `GitHubTools.get_open_pull_requests()`, applies ABAC org-scope filtering via `ABACGuard.filter_resources(user, all_prs)`, filters stale PRs (`review_latency_hours >= 48.0` and `review_status == "WAITING_REVIEW"`), and fetches CI failures via `GitHubTools.get_ci_pipeline_failures()`.
  - `SynthesisAgent.synthesize` (`prometheus/agents/synthesis_agent.py`, lines 28-140): Correlates `stale_prs` and `ci_failures` with Jira blockers and Slack chatter using Gemini 3.7 Flash or heuristic fallback.

### 1.3 Jira Tool Implementation (`JiraTools`)
- **File Locations**: `prometheus/tools/jira_tools.py` (lines 1-80) and `app/tools/jira_tools.py` (lines 1-80).
- **Current Mock Fixtures**:
  - `MOCK_ISSUES`: 3 sample issues (`PROJ-108` [Epic, BLOCKED], `PROJ-112` [Story, IN_PROGRESS], `PROJ-99` [Bug, IN_REVIEW]).
    - Key schema fields: `key` (str), `summary` (str), `type` (str), `status` (str), `priority` (str), `sprint` (str), `assignee` (str), `reporter` (str), `blocked_by` (List[str], e.g. `["PR-402", "PR-415"]`), `blocker_reason` (Optional[str]), `scopes` (List[str]), `target_release_date` (str).
- **Sub-Agent Consumers**:
  - `JiraAgent.collect_telemetry` (`prometheus/agents/jira_agent.py`, lines 21-42): Calls `JiraTools.get_sprint_issues()`, applies `ABACGuard.filter_resources(user, all_issues)`, and extracts `blocked_issues` where `status == "BLOCKED"` or `len(blocked_by) > 0`.
  - `SynthesisAgent.synthesize` (`prometheus/agents/synthesis_agent.py`, lines 106-138): Matches `blocked_by` and `blocking_downstream` against PR IDs to construct multi-domain blocker records (`BlockerRecord`).

### 1.4 Slack Tool Implementation (`SlackTools`)
- **File Locations**: `prometheus/tools/slack_tools.py` (lines 1-111) and `app/tools/slack_tools.py` (lines 1-111).
- **Current Mock Fixtures & Action Methods**:
  - `MOCK_MESSAGES`: 3 sample messages (`MSG-901`, `MSG-905`, `MSG-912`).
    - Key schema fields: `id` (str), `channel` (str, e.g. `"#platform-engineering"`), `user` (str), `timestamp` (ISO timestamp), `text` (str), `scopes` (List[str]).
  - `draft_action_card(cls, target, action_type, content, context_blocker_id, require_confirmation)`: Creates an `ActionDraftRecord` in `state_store` with `DraftStatus.PENDING`.
  - `dispatch_approved_action(cls, draft_id, approver_username)`: Dispatches action strictly upon explicit human confirmation, transitioning status to `DraftStatus.EXECUTED`.
- **Sub-Agent Consumers**:
  - `WorkstreamAgent.collect_telemetry` (`prometheus/agents/workstream_agent.py`, lines 21-36): Ingests channel conversations and applies ABAC filtering.
  - `ActionAgent.create_action_drafts_for_blockers` (`prometheus/agents/action_agent.py`, lines 23-126): Employs "Propose, Don't Impose" to generate Slack DMs and channel broadcast drafts formatted with Slack Block Kit UI JSON.
  - `main.py` (`approve_action` endpoint line 153, webhook receiver line 213) and `engine_app.py` (`approve_action` line 87).

### 1.5 Configuration & Credentials State
- In `prometheus/config.py` (lines 58-62) and `app/config.py` (lines 58-62):
  ```python
  github_token: Optional[str] = None
  jira_api_token: Optional[str] = None
  jira_instance_url: Optional[str] = None
  slack_bot_token: Optional[str] = None
  ```
- **Identified Config Gap**: Jira Cloud REST API (Basic Auth) requires `JIRA_USER_EMAIL` in conjunction with `JIRA_API_TOKEN`. Currently, `jira_user_email` is **not** present in `Settings`.
- In `.env.example` (lines 28-31):
  ```env
  GITHUB_TOKEN=
  JIRA_API_TOKEN=
  JIRA_INSTANCE_URL=https://your-domain.atlassian.net
  SLACK_BOT_TOKEN=
  ```
  `JIRA_USER_EMAIL` should be added to `.env.example` and `Settings`.

### 1.6 Dependencies & Baseline Test Execution
- `requirements.txt`, `setup.py`, and `deploy_agent_engine.py` all include `httpx>=0.27.0` (async HTTP client), `pydantic>=2.6.0`, `aiosqlite>=0.20.0`, and `google-genai>=0.1.1`.
- Running `pytest -v` passed all 14 tests in 33.48s with 0 failures:
  - `tests/test_endpoints.py`: 6 passed (`test_healthz_endpoint`, `test_dashboard_endpoint`, `test_mcp_sse_endpoint`, `test_api_agents_registry_endpoint`, `test_api_digest_and_actions_workflow_endpoints`, `test_api_webhooks_endpoints`).
  - `tests/test_workflow.py`: 8 passed (`test_abac_scope_filtering`, `test_guardrails_pii_and_injection`, `test_agent_registry_discovery`, `test_mcp_server_protocol`, `test_gemini_pool_cache`, `test_sqlite_state_store_persistence`, `test_end_to_end_prometheus_workflow`, `test_prometheus_agent_engine_app_native_interface`).

---

## 2. Logic Chain

### 2.1 Preserving Agent Contract Integrity
1. The 6 sub-agents (`GitAgent`, `JiraAgent`, `WorkstreamAgent`, `SynthesisAgent`, `ActionAgent`, `RouterAgent`) and the `PrometheusWorkflow` rely on the normalized output dictionaries returned by the tool classes (`GitHubTools`, `JiraTools`, `SlackTools`).
2. Specifically:
   - `GitAgent` and `SynthesisAgent` expect pull request dicts to contain `id`, `repo`, `title`, `author`, `created_at`, `review_latency_hours`, `status`, `reviewers`, `review_status`, `ci_status`, `scopes`, and `blocking_downstream`.
   - `JiraAgent` and `SynthesisAgent` expect issue dicts to contain `key`, `summary`, `type`, `status`, `priority`, `sprint`, `assignee`, `reporter`, `blocked_by`, `blocker_reason`, `scopes`, and `target_release_date`.
   - `WorkstreamAgent` and `SynthesisAgent` expect message dicts to contain `id`, `channel`, `user`, `timestamp`, `text`, and `scopes`.
3. Therefore, live API implementations must normalize vendor-specific responses (GitHub REST/GraphQL payloads, Jira Cloud issue schemas, Slack Web API message objects) directly into these exact dictionary structures.

### 2.2 Live API Integration Architecture
1. **GitHub Tooling Architecture (`httpx.AsyncClient`)**:
   - **Auth**: `Authorization: Bearer <GITHUB_TOKEN>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`.
   - **Endpoints**:
     - Pull requests: `GET https://api.github.com/repos/{owner}/{repo}/pulls?state=open&sort=created&direction=desc&per_page=30` (or `GET https://api.github.com/user/repos` / configurable repository list).
     - Review latency & Reviewers: `GET https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews` and PR payload `requested_reviewers`. Review latency calculated as `(datetime.now(timezone.utc) - created_at_dt).total_seconds() / 3600.0`. Review status mapped from reviews (`CHANGES_REQUESTED`, `APPROVED`, `COMMENTED`, `WAITING_REVIEW`).
     - CI Failure Detection: `GET https://api.github.com/repos/{owner}/{repo}/actions/runs?status=failure&per_page=15` and `GET https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs`. Extract `failed_step`, `error_summary` from job steps with `conclusion == "failure"`.
   - **Rate Limiting**: Check response headers `x-ratelimit-remaining` and `x-ratelimit-reset`. If `x-ratelimit-remaining == 0` or HTTP 403/429, log warning and return mock/cached telemetry.
   - **Credential Fallback**: If `settings.github_token` is `None` or empty, log informational message and return `MOCK_PRS` / `MOCK_CI_FAILURES`.

2. **Jira Tooling Architecture (`httpx.AsyncClient`)**:
   - **Auth**: Basic Auth via HTTP Header `Authorization: Basic base64(f"{settings.jira_user_email}:{settings.jira_api_token}")` or Bearer token for PAT.
   - **Endpoints**:
     - Sprint issues & blockers: `GET {settings.jira_instance_url}/rest/api/3/search?jql=sprint in openSprints() ORDER BY priority DESC&fields=summary,status,issuetype,priority,assignee,reporter,issuelinks,customfield_*,duedate,labels`.
     - Blockers & Dependencies: Parse `issuelinks` where link type inward/outward indicates blocking (e.g. `"is blocked by"`, `"blocks"`, `"depends on"`), extracting inward/outward issue keys. Also scan summary/description/comments for PR references (e.g. `"PR-402"`, GitHub URLs).
     - Burndown & Sprint Metrics: `GET {settings.jira_instance_url}/rest/agile/1.0/board` and `/rest/agile/1.0/sprint/{sprint_id}` to compute committed vs completed story points, remaining estimate, and sprint velocity variance.
   - **Rate Limiting**: Inspect HTTP 429 and `Retry-After` header.
   - **Credential Fallback**: If `settings.jira_instance_url` or `settings.jira_api_token` is missing, log informational message and return `MOCK_ISSUES`.

3. **Slack Tooling Architecture (`httpx.AsyncClient`)**:
   - **Auth**: `Authorization: Bearer <settings.slack_bot_token>`, `Content-Type: application/json; charset=utf-8`.
   - **Endpoints**:
     - Message Ingestion:
       - `GET https://slack.com/api/conversations.list?types=public_channel&exclude_archived=true&limit=50` to discover public channel IDs and names.
       - `GET https://slack.com/api/conversations.history?channel={channel_id}&limit=20` to ingest recent discussions.
       - `GET https://slack.com/api/users.list` (cached) to resolve Slack user IDs (`U12345`) to readable usernames/display names (`@alex-lead`).
     - Action Card & DM Dispatch:
       - `POST https://slack.com/api/chat.postMessage` with `channel: channel_id`, `text: content`, and `blocks: slack_blocks` for public channel alerts.
       - `POST https://slack.com/api/conversations.open` with `users: user_id`, then `chat.postMessage` for direct messages.
   - **HITL Enforcement**: Message ingestion (`get_recent_channel_messages`) is read-only. `draft_action_card` strictly persists `ActionDraftRecord` in `state_store`. Only `dispatch_approved_action` triggers the live `chat.postMessage` call upon human confirmation.
   - **Rate Limiting**: Check HTTP 429 and response `{"ok": false, "error": "ratelimited"}` with `Retry-After` header.
   - **Credential Fallback**: If `settings.slack_bot_token` is missing, simulate dispatch, log audit trail in state store, and return `MOCK_MESSAGES`.

### 2.3 Zero Extra Dependencies Strategy
- By leveraging Python standard library + `httpx.AsyncClient`, all live API integrations require **zero additional external packages** (no heavy, synchronous, or unmaintained libraries like `PyGithub` or `jira` or `slack-sdk`).
- This ensures full async compatibility with FastAPI and avoids packaging or `cloudpickle` serialization errors when bundling with Vertex AI Reasoning Engine in `deploy_agent_engine.py`.

---

## 3. Caveats

1. **Enterprise Sandbox Scopes**: Live API calls against enterprise GitHub, Jira, or Slack instances require repository names, Jira project keys, or Slack channels to exist. If a user provides a token for a private repo or empty organization, the tools should safely return empty lists or fallback without crashing the workflow.
2. **Dual-Folder Synchronization**: Because both `prometheus/` and `app/` exist in the workspace, any updates to tool classes, models, or configurations must be mirrored across both directories (or synchronized via `refactor_namespace.py`) to prevent drift.
3. **Async Event Loop Compatibility**: All API calls must use `httpx.AsyncClient` so that `PrometheusAgentEngineApp.run_async` can execute seamlessly inside Vertex AI Reasoning Engine containers.

---

## 4. Conclusion & Concrete Recommendations for M1

### 4.1 Schema and Config Additions
1. Update `prometheus/config.py` and `app/config.py`:
   - Add `jira_user_email: Optional[str] = None` to `Settings`.
   - Add `github_repos: Optional[List[str]] = Field(default_factory=lambda: ["acme/auth-service", "acme/web-gateway", "acme/billing-core"])` or parse comma-separated string `GITHUB_REPOS`.
   - Add `slack_channels: Optional[List[str]] = Field(default_factory=lambda: ["platform-engineering", "billing-squad"])` or parse comma-separated string `SLACK_CHANNELS`.
2. Update `.env.example` to document `JIRA_USER_EMAIL`, `GITHUB_REPOS`, and `SLACK_CHANNELS`.

### 4.2 GitHub Tool (`GitHubTools`) Implementation Plan
- Keep `MOCK_PRS` and `MOCK_CI_FAILURES` as static fallback fixtures.
- Add helper methods:
  - `_fetch_live_prs(repos: List[str]) -> List[Dict[str, Any]]`
  - `_fetch_live_ci_failures(repos: List[str]) -> List[Dict[str, Any]]`
  - `_calculate_review_latency(pr_created_at: str, reviews: List[Dict[str, Any]]) -> float`
  - `_get_headers() -> Dict[str, str]`
- In `get_open_pull_requests` and `get_ci_pipeline_failures`, check `if settings.github_token: ...` else return mock fixtures.

### 4.3 Jira Tool (`JiraTools`) Implementation Plan
- Keep `MOCK_ISSUES` as static fallback fixtures.
- Add helper methods:
  - `_fetch_live_sprint_issues(jql: Optional[str] = None) -> List[Dict[str, Any]]`
  - `_parse_blockers_and_dependencies(issue_data: Dict[str, Any]) -> Tuple[List[str], Optional[str]]`
  - `_get_auth_headers() -> Dict[str, str]`
- In `get_sprint_issues` and `get_blocked_issues`, check `if settings.jira_instance_url and settings.jira_api_token: ...` else return mock fixtures.

### 4.4 Slack Tool (`SlackTools`) Implementation Plan
- Keep `MOCK_MESSAGES` as static fallback fixtures.
- Add helper methods:
  - `_fetch_live_channel_messages(channel_names: List[str]) -> List[Dict[str, Any]]`
  - `_dispatch_live_slack_message(target: str, action_type: str, content: str, blocks: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]`
  - `_resolve_channel_id(channel_name: str) -> Optional[str]`
  - `_resolve_user_id(username: str) -> Optional[str]`
- In `get_recent_channel_messages`, check `if settings.slack_bot_token: ...` else return mock fixtures.
- In `dispatch_approved_action`, execute live `_dispatch_live_slack_message` when `settings.slack_bot_token` is present, or return simulated success response in mock mode.

---

## 5. Verification Method

To independently verify all findings and validate future implementations:

1. **Run Local Baseline Test Suite**:
   ```powershell
   pytest -v
   ```
   *Expected Output*: 14 passed in `test_endpoints.py` and `test_workflow.py`.

2. **Verify Tool Ingestion & Hermetic Mock Fallback**:
   Execute Python one-liner to verify each tool loads and returns valid telemetry without credentials:
   ```powershell
   python -c "import asyncio; from prometheus.tools.github_tools import GitHubTools; from prometheus.tools.jira_tools import JiraTools; from prometheus.tools.slack_tools import SlackTools; async def test(): print('PRs:', len(await GitHubTools.get_open_pull_requests())); print('Issues:', len(await JiraTools.get_sprint_issues())); print('Messages:', len(await SlackTools.get_recent_channel_messages())); asyncio.run(test())"
   ```

3. **Verify End-to-End Workflow & Native Reasoning Engine App**:
   ```powershell
   python -c "from prometheus.engine_app import PrometheusAgentEngineApp; app = PrometheusAgentEngineApp(); app.set_up(); res = app.query(prompt='Scan cross-squad telemetry for active sprint blockers'); assert res['status'] == 'COMPLETED'; assert len(res['blockers']) > 0; print('Engine query successful, blockers detected:', len(res['blockers']))"
   ```

4. **Verify Cloud Endpoints and Healthz**:
   ```powershell
   python -c "from fastapi.testclient import TestClient; from prometheus.main import app; client = TestClient(app); res = client.get('/healthz'); assert res.status_code == 200; print('Healthz:', res.json())"
   ```

5. **Invalidation Conditions**:
   - Any modification that causes `pytest` to fail or drops test coverage.
   - Any live API implementation that raises unhandled network/HTTP exceptions when tokens are absent.
   - Any discrepancy in field names (`review_latency_hours`, `blocked_by`, `impacted_squads`) that causes `SynthesisAgent` or `ActionAgent` correlation heuristics to fail.
