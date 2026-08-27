# DISPATCH — Test Writer E2E Track

Working directory: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_test_writer_e2e
Original Request: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md
Project Scope: c:\Users\brigh\project\prometheus\PROJECT.md
Test Infrastructure Spec: c:\Users\brigh\project\prometheus\TEST_INFRA.md
Verification Survey: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_explorer_survey_verification\handoff.md

Mission:
Build the comprehensive 5-Tier automated test suite and test runner configuration:
1. Create `pytest.ini` with test discovery, markers (`unit`, `integration`, `e2e`, `adversarial`), and async mode configuration (`asyncio_mode = auto`).
2. Implement Tier 1 Unit Tests in `tests/unit/`:
   - `test_abac_math.py`: mathematical property testing for ABAC permissions, admin flags, empty scopes, restricted resources.
   - `test_guardrail_sanitizer.py`: PII masking across GitHub tokens, Gemini keys, Slack tokens, Bearer tokens, emails, phone numbers.
   - `test_mcp_protocol.py`: MCP JSON-RPC 2.0 schemas, tool definitions, tool list responses, error code mappings.
   - `test_state_store.py`: SQLite CRUD operations, blocker status queries, and draft state transitions.
   - `test_agent_registry.py`: All 6 sub-agents verification.
3. Implement Tier 2 Live API Integration Tests in `tests/integration/`:
   - `test_github_client.py`: live & mock fallback PR ingestion, review latency, CI failures, 401/429 handling.
   - `test_jira_client.py`: live & mock fallback sprint issues, blocker parsing, basic auth.
   - `test_slack_client.py`: live & mock fallback channel messages, Block Kit dispatch, approval idempotency.
4. Implement Tier 3 Multi-Agent Workflow Tests in `tests/integration/`:
   - `test_prometheus_dag.py`: full 6-agent DAG execution, blocker correlation, SHA-256 telemetry cache.
   - `test_hitl_lifecycle.py`: PENDING -> APPROVED -> EXECUTED transitions, idempotency, rejection, session checkpoints.
5. Implement Tier 4 Remote Cloud Tests in `tests/e2e/`:
   - `test_vertex_agent_engine_remote.py`: Remote Vertex AI Reasoning Engine query, list_agents, approve_action.
   - `test_cloud_run_remote.py`: Cloud Run `/healthz`, `/dashboard`, `/mcp/sse`, `/api/v1/digest`.
6. Implement Tier 5 Adversarial & Security Matrix in `tests/adversarial/`:
   - `test_adversarial_matrix.py`: Direct/indirect prompt injection payloads in PRs/Jira/Slack, cross-tenant ABAC privilege escalation, HITL concurrency race conditions (10 concurrent requests for same draft).
7. Run `pytest -v` across all tests, ensure all local tests pass 100%, and publish `TEST_READY.md` at project root.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All tests and implementations must be genuine. Do not write tests that tautologically pass or bypass actual system behavior.
