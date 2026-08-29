# Original User Request

## Initial Request — 2026-08-25T20:46:21Z

You are the SWE Light orchestrator for the Prometheus project.
Working directory: c:\Users\brigh\project\prometheus\.agents\swe_1
Original Request is at: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md

Task:
Execute the single self-contained deployment and verification fix for Prometheus onto Google Cloud Vertex AI Agent Engine under project `gen-lang-client-0942141479` in `us-central1`.
1. Complete Vertex AI Agent Engine Deployment using `deploy_agent_engine.py` with project `gen-lang-client-0942141479` in `us-central1`. Ensure package packaging (`prometheus`), async event loop compatibility, and staging bucket artifacts resolve without container startup errors.
2. Verify remote Reasoning Engine resource is fully active and reachable with remote test query, verifying all 6 sub-agents, SQLite memory persistence, and Gemini 3.7 Flash synthesis return valid correlated blocker telemetry.
3. Verify local and cloud endpoints (`/dashboard`, `/healthz`, `/mcp/sse`) and ensure all local tests pass 100% (`pytest`).

Maintain progress in your working directory and report back with your completion report when all acceptance criteria are met.

## 2026-08-26T20:12:42Z

Use a full multi-agent team.

Deploy the Prometheus AI Chief of Staff platform to Google Cloud (Vertex AI Agent Engine and Cloud Run) and replace all mock telemetry tools with enterprise-grade live API integrations for GitHub, Jira, and Slack.

Working directory: c:\Users\brigh\project\prometheus
Integrity mode: development

## Requirements

### R1. Live Developer Telemetry & Communication Tools
Replace all mock data fixtures in GitHub, Jira, and Slack tools with fully functional live API clients:
- **GitHub**: Fetch live pull requests, review latency, reviewers, and GitHub Actions CI workflow run failures via GitHub REST/GraphQL API using `GITHUB_TOKEN`.
- **Jira**: Fetch live sprint issues, blocker statuses, dependencies, and burndown data via Jira Cloud REST API using `JIRA_INSTANCE_URL`, `JIRA_USER_EMAIL`, and `JIRA_API_TOKEN`.
- **Slack**: Ingest live public channel discussions and dispatch interactive action cards / direct messages for approved actions via Slack Web API using `SLACK_BOT_TOKEN`.
- Provide robust error handling, rate limiting, and clear validation for missing credentials.

### R2. Enterprise Google Cloud Deployment
Package, configure, and deploy the complete Prometheus platform to Google Cloud:
- Deploy the multi-agent reasoning fleet to Vertex AI Agent Engine (Reasoning Engine) using Gemini 3.7 Flash and Google Cloud Application Default Credentials (ADC).
- Deploy the FastAPI application & Model Context Protocol (MCP) server to Google Cloud Run.
- Integrate Google Cloud Secret Manager or secure environment configuration for external API tokens.

### R3. End-to-End Programmatic Verification
Implement and execute an automated verification suite that validates:
- Real-time API telemetry ingestion and correlation across the 6 sub-agents.
- ABAC scope perimeter isolation and prompt defense guardrails.
- Human-in-the-loop draft generation and approval dispatch lifecycle.
- Successful remote query execution against the deployed Vertex AI Agent Engine and Cloud Run instances.

## Acceptance Criteria

### Live API Ingestion & Action Dispatch
- [ ] GitHub tool retrieves real repository pull requests, review latency, and GitHub Actions CI build statuses via live API.
- [ ] Jira tool connects to Jira Cloud and queries active sprint issues, epics, and blocker dependencies via live API.
- [ ] Slack tool ingests real channel messages and dispatches HITL action messages when approved.

### Cloud Deployment & Execution
- [ ] Reasoning Engine is deployed to Vertex AI Agent Engine in `us-central1` under GCP project `gen-lang-client-0942141479` and responds to remote queries.
- [ ] Cloud Run service is built, containerized, and deployed with healthy MCP SSE/REST endpoints.
- [ ] Credentials and secrets are managed securely via Secret Manager / `.env` without exposure in logs.

### Automated Verification
- [ ] Programmatic end-to-end test suite executes against the live deployed GCP infrastructure with a 100% passing verification report.

## 2026-08-29T15:09:53Z

Refactor and enhance the Prometheus AI Chief of Staff platform with a bespoke, high-polish UI/UX redesign (Deep Obsidian & Electric Sapphire precision dark command console following frontend-design principles), fix front-to-back action card drafting and dispatch bugs (including inline draft editing and toast notifications), ensure 100% CI pipeline reliability across the test matrix, and preserve strict dual-namespace parity between prometheus/ and app/.

Working directory: c:\Users\brigh\project\prometheus
Integrity mode: development

## Requirements

### R1. Frontend UI/UX Redesign & Usability Overhaul
Overhaul the Executive Command Center (dashboard.html and documentation.html) into an intentional, high-precision dark command console:
- Apply the Deep Obsidian & Electric Sapphire aesthetic palette (#0a0d14, #121722, #1c2333, accent sapphire #3b82f6, emerald #10b981, amber #f59e0b, crimson #ef4444) with crisp 1px borders and purposeful typography hierarchy.
- Provide a persistent top navigation bar with active tenant switcher, Google OAuth profile avatar, real-time fleet connection status, and one-click "Run Fleet Ingest" action with SSE animated progress.
- Enhance the 4-stage pipeline visualizer, side-by-side blocker triage with collapsible root-cause evidence trees, interactive ABAC security perimeter sandbox, and responsive grid layouts.

### R2. Action Draft Card Lifecycle & Bug Fixes
- Fix all frontend JavaScript errors in dashboard.html (add null-coalescing on action_type, re-render overview-action-card-container upon workflow completion, safe escaping in event handlers).
- Introduce an Inline Action Card Editor Modal allowing engineering leads to edit message recipients, channel targets, and message body text prior to sign-off.
- Implement animated toast feedback notifications on approval, rejection, edits, and ingestion events.
- Ensure backend /api/v1/actions/{draft_id}/approve and /reject endpoints support custom edited content and return clear provenance metadata.

### R3. Dual-Namespace Invariant & CI Pipeline Optimization
- Mirror all modifications between prometheus/ and app/ using automated synchronization to maintain zero code drift.
- Optimize .github/workflows/ci.yml so that hermetic test runs execute reliably under Python 3.11 and 3.12 with clean mocks and zero flaky timeouts.
- Eliminate test suite deprecation warnings and ensure the full 159+ test matrix passes with 100% pass rate.

## Acceptance Criteria

### Frontend Quality & Usability
- [ ] Action cards render seamlessly on both the Overview tab and Action Cards tab with zero uncaught JavaScript errors in browser console.
- [ ] Users can edit draft content inline or in a modal before clicking "Approve & Dispatch".
- [ ] Live toast notifications provide clear visual confirmation for approvals, rejections, and workflow runs.
- [ ] UI features distinctive Deep Obsidian styling, accessible contrast ratios, and clean mobile responsiveness.

### Functional Resiliency & Parity
- [ ] Approving or rejecting action cards correctly updates SQLite state store, reflections on UI counters, and live Slack dispatch payloads.
- [ ] Dual-namespace parity test pytest tests/integration/test_m1_reviewer2_adversarial.py -k test_app_and_prometheus_namespace_parity passes with 0 failures.
- [ ] Full test suite (pytest tests/ -v) passes 100% (159+ tests) under CI environment flags (ENVIRONMENT=testing, USE_VERTEX_AI=false).


