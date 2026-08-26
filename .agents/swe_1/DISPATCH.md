## 2026-08-25T20:46:21Z

You are the SWE Light orchestrator for the Prometheus project.
Working directory: c:\Users\brigh\project\prometheus\.agents\swe_1
Original Request is at: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md

Task:
Execute the single self-contained deployment and verification fix for Prometheus onto Google Cloud Vertex AI Agent Engine under project `gen-lang-client-0942141479` in `us-central1`.
1. Complete Vertex AI Agent Engine Deployment using `deploy_agent_engine.py` with project `gen-lang-client-0942141479` in `us-central1`. Ensure package packaging (`prometheus`), async event loop compatibility, and staging bucket artifacts resolve without container startup errors.
2. Verify remote Reasoning Engine resource is fully active and reachable with remote test query, verifying all 6 sub-agents, SQLite memory persistence, and Gemini 3.7 Flash synthesis return valid correlated blocker telemetry.
3. Verify local and cloud endpoints (`/dashboard`, `/healthz`, `/mcp/sse`) and ensure all local tests pass 100% (`pytest`).

Maintain progress in your working directory and report back with your completion report when all acceptance criteria are met.
