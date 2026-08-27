# Project: Prometheus AI Chief of Staff Platform

## Architecture
Prometheus is an enterprise-grade multi-agent autonomous Chief of Staff platform designed for engineering leadership. It orchestrates a 6-sub-agent reasoning fleet atop Google Gemini 3.7 Flash and Vertex AI Reasoning Engine, integrated with FastAPI and Model Context Protocol (MCP) server endpoints on Google Cloud Run.

```
                  ┌──────────────────────────────────────────────────────────┐
                  │                External Ingress Channels                 │
                  │   • Web Dashboard (/dashboard)  • REST API (/api/v1/*)   │
                  │   • MCP Stream (/mcp/sse)       • Webhooks (/webhooks/*) │
                  └─────────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            Prometheus Multi-Agent Reasoning Fleet (DAG)                                  │
│                                                                                                          │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ [1] RouterAgent (agent-01-router): ABAC Scope Perimeter & Prompt Defense Sanitization            │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
│                                                 │                                                        │
│                    ┌────────────────────────────┼────────────────────────────┐                           │
│                    ▼                            ▼                            ▼                           │
│   ┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐        │
│   │ [2] GitAgent (agent-02-git) │ │ [3] JiraAgent (agent-03)    │ │ [4] WorkstreamAgent (04)    │        │
│   │ • GitHub Live REST/GraphQL  │ │ • Jira Cloud REST Ingestion │ │ • Slack Channel Ingestion   │        │
│   │ • PRs, CI, Review Latency   │ │ • Sprint Blockers, Burndown │ │ • Sentiment & Discussion    │        │
│   └──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘        │
│                  └──────────────────────────────┼───────────────────────────────┘                        │
│                                                 ▼                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ [5] SynthesisAgent (agent-05-synthesis): Multi-Domain Blocker Correlation & Root Cause Analysis  │   │
│   │ • Gemini 3.7 Flash Telemetry Synthesis + SHA-256 TelemetryCache + Heuristic Deterministic Engine │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
│                                                 ▼                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ [6] ActionAgent (agent-06-action): Human-In-The-Loop (HITL) Action Card & Alignment Briefing     │   │
│   │ • "Propose, Don't Impose" Draft Generation • Block Kit UI Cards • SQLite StateStore Persistence  │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
│                                                 ▼                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ SlackTools.dispatch_approved_action: Human Authorization & Idempotent Slack/DM Dispatch          │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Code Layout
- `prometheus/` & `app/`: Dual root application packages:
  - `agents/`: The 6 sub-agents (`router_agent.py`, `git_agent.py`, `jira_agent.py`, `workstream_agent.py`, `synthesis_agent.py`, `action_agent.py`).
  - `tools/`: Enterprise telemetry & communication tools (`github_tools.py`, `jira_tools.py`, `slack_tools.py`).
  - `security/`: ABAC scope perimeter (`abac_guard.py`) and prompt injection/PII sanitizer (`guardrails.py`).
  - `memory/`: Async SQLite state persistence (`state_store.py`).
  - `llm/`: Gemini 3.7 Flash engine, SHA-256 cache, heuristic fallback (`gemini_pool.py`).
  - `mcp/`: JSON-RPC 2.0 Model Context Protocol server (`server.py`).
  - `workflows/`: DAG orchestrator (`prometheus_flow.py`).
  - `registry/`: Agent discovery and metadata registry (`agent_registry.py`).
  - `config.py`: Environment settings and credential loading.
  - `main.py`: FastAPI web server, REST endpoints, SSE stream, webhook handlers.
  - `engine_app.py`: Vertex AI Reasoning Engine SDK application interface.
- `deploy_agent_engine.py`: Packaging and deployment script for Vertex AI Reasoning Engine.
- `deploy_cloud_run.sh`: Automated build and deployment script for Google Cloud Run.
- `Dockerfile`: Multi-stage container definition.
- `tests/`: 5-Tier comprehensive verification suite:
  - `tests/unit/`: Tier 1 hermetic unit & component tests.
  - `tests/integration/`: Tier 2 Live API clients & Tier 3 Multi-Agent DAG workflow tests.
  - `tests/e2e/`: Tier 4 Remote Cloud endpoints verification (Vertex AI Agent Engine + Cloud Run).
  - `tests/adversarial/`: Tier 5 Adversarial prompt injection, ABAC boundary escalation, race condition fuzzing.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | GitHub Live PR Ingestion | Query open pull requests via GitHub REST/GraphQL API using `GITHUB_TOKEN` | M1 | ORIGINAL_REQUEST §R1 |
| 2 | GitHub Review Latency Calculation | Calculate stale PR review latency in hours and reviewer assignments | M1 | ORIGINAL_REQUEST §R1 |
| 3 | GitHub Actions CI Failures | Ingest failing GitHub Actions workflow runs and error summaries | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Jira Cloud Sprint Issues Ingestion | Ingest active sprint issues, epics, priorities via Jira Cloud REST API | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Jira Blocker & Dependency Graph | Parse `issuelinks` (`is blocked by`, `blocks`) and cross-domain PR links | M1 | ORIGINAL_REQUEST §R1 |
| 6 | Slack Channel Ingestion | Ingest public channel discussions via Slack Web API conversations history | M1 | ORIGINAL_REQUEST §R1 |
| 7 | Slack Action Card & DM Dispatch | Dispatch Block Kit interactive action cards and DMs upon human approval | M1 | ORIGINAL_REQUEST §R1 |
| 8 | Telemetry Rate Limiting & Auth Handling | Handle 401/403/429 with retry-after headers, credential validation & hermetic fallbacks | M1 | ORIGINAL_REQUEST §R1 |
| 9 | Vertex AI Reasoning Engine Packaging | Package `prometheus` & `app` with `_tar_filter` and deploy to Agent Engine | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Gemini 3.7 Flash & ADC Configuration | Standardize LLM synthesis on Gemini 3.7 Flash using Google Cloud ADC | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Cloud Run Containerization & Deployment | Build container image and deploy FastAPI + MCP server to Cloud Run | M2 | ORIGINAL_REQUEST §R2 |
| 12 | Secret Manager & Secure Env Vars | Manage credentials securely via Secret Manager / Cloud Run env vars | M2 | ORIGINAL_REQUEST §R2 |
| 13 | Tier 1 Hermetic Unit Test Suite | Test ABAC logic, PII masking, MCP JSON-RPC, StateStore SQLite CRUD | M3 / E2E Track | ORIGINAL_REQUEST §R3 |
| 14 | Tier 2 Live API Integration Suite | Test live API clients with credentials and offline mock fallbacks | M3 / E2E Track | ORIGINAL_REQUEST §R3 |
| 15 | Tier 3 Multi-Agent DAG & HITL Suite | Test 6-agent execution DAG, blocker correlation, approval idempotency | M3 / E2E Track | ORIGINAL_REQUEST §R3 |
| 16 | Tier 4 Remote Cloud Endpoints Suite | Verify remote Vertex AI Agent Engine and Cloud Run HTTP/SSE endpoints | M3 / E2E Track | ORIGINAL_REQUEST §R3 |
| 17 | Tier 5 Adversarial & Security Matrix | Fuzz prompt injections, ABAC cross-tenant leaks, HITL concurrency races | M3 / E2E Track | ORIGINAL_REQUEST §R3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Live Developer Telemetry & Tools | Implement live API clients for GitHub, Jira Cloud, and Slack in `prometheus/tools/` & `app/tools/`, update `config.py` schemas (`jira_user_email`, `github_repos`, `slack_channels`), add rate limiting and hermetic fallback | none | IN_PROGRESS |
| 2 | M2: Enterprise Google Cloud Deployment | Package & deploy Vertex AI Agent Engine (`deploy_agent_engine.py`), create `deploy_cloud_run.sh`, build & deploy Cloud Run service, configure Secret Manager / environment variables | M1 | PLANNED |
| 3 | M3: 5-Tier E2E & Remote Verification | Execute complete 5-Tier automated verification suite locally and remotely against deployed GCP endpoints, verifying 100% pass rate | M1, M2 | PLANNED |

## Interface Contracts
### GitHub Tools (`GitHubTools`)
- `get_open_pull_requests(repos: Optional[List[str]] = None) -> List[Dict[str, Any]]`:
  Returns normalized dictionaries with `id`, `repo`, `title`, `author`, `created_at`, `updated_at`, `review_latency_hours`, `status`, `reviewers`, `review_status`, `ci_status`, `scopes`, `blocking_downstream`.
- `get_ci_pipeline_failures(repos: Optional[List[str]] = None) -> List[Dict[str, Any]]`:
  Returns normalized dictionaries with `id`, `repo`, `branch`, `commit`, `failed_step`, `error_summary`, `run_at`, `scopes`.

### Jira Tools (`JiraTools`)
- `get_sprint_issues(jql: Optional[str] = None) -> List[Dict[str, Any]]`:
  Returns normalized dictionaries with `key`, `summary`, `type`, `status`, `priority`, `sprint`, `assignee`, `reporter`, `blocked_by`, `blocker_reason`, `scopes`, `target_release_date`.
- `get_blocked_issues() -> List[Dict[str, Any]]`:
  Returns filtered list of blocked issues with dependency chains.

### Slack Tools (`SlackTools`)
- `get_recent_channel_messages(channel_names: Optional[List[str]] = None) -> List[Dict[str, Any]]`:
  Returns normalized dictionaries with `id`, `channel`, `user`, `timestamp`, `text`, `scopes`.
- `draft_action_card(target: str, action_type: str, content: str, context_blocker_id: Optional[str] = None, require_confirmation: bool = True) -> ActionDraftRecord`:
  Creates draft in `PENDING` state in SQLite.
- `dispatch_approved_action(draft_id: str, approver_username: str) -> Dict[str, Any]`:
  Dispatches to live Slack API if `slack_bot_token` is present; updates draft to `EXECUTED`. Idempotent on repeated calls.

### Reasoning Engine Interface (`PrometheusAgentEngineApp`)
- `set_up()`: Async DB initialization.
- `query(prompt: str, user_id: str = ..., username: str = ..., org_scopes: List[str] = ...) -> Dict[str, Any]`: Returns `{"session_id": str, "status": str, "blockers": List[Dict], "action_drafts": List[Dict], "briefing": Dict}`.
- `list_agents() -> List[Dict[str, Any]]`: Returns metadata for all 6 sub-agents.
- `approve_action(draft_id: str, approver_username: str) -> Dict[str, Any]`: Executes approved action.
- `reject_action(draft_id: str, approver_username: str) -> Dict[str, Any]`: Rejects pending action.
