# DISPATCH — Reviewer 2 (M1 Live Telemetry)

Working directory: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_reviewer_m1_2
Original Request: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md
Project Scope: c:\Users\brigh\project\prometheus\PROJECT.md
Worker Handoff: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_worker_m1\handoff.md

Mission:
Perform independent, adversarial review of M1 Live Telemetry & Communication Tools:
- Review `github_tools.py`, `jira_tools.py`, `slack_tools.py`, `config.py`, `.env.example` in both `prometheus/` and `app/`.
- Verify error handling, rate limiting (429, headers), timeout handling, missing credentials fallback, and schema conformance with `GitAgent`, `JiraAgent`, `WorkstreamAgent`, `SynthesisAgent`, and `ActionAgent`.
- Run tests and check for regressions or edge-case crashes.
- Render your verdict: APPROVE or REQUEST_CHANGES in `handoff.md`.
