# DISPATCH

## 2026-08-26T19:19:45Z

You are the Project Orchestrator for the Prometheus AI Chief of Staff platform.
Working directory: c:\Users\brigh\project\prometheus\.agents\teamwork_preview_orchestrator_1
Original Request is at: c:\Users\brigh\project\prometheus\.agents\ORIGINAL_REQUEST.md

Mission:
Execute full multi-agent engineering workflow to:
1. R1: Live Developer Telemetry & Communication Tools:
   - Replace all mock data fixtures in GitHub, Jira, and Slack tools with fully functional enterprise live API clients (GitHub REST/GraphQL for PRs, review latency, CI runs; Jira Cloud REST for sprint issues, blockers, dependencies; Slack Web API for channel message ingestion & interactive action cards / DMs).
   - Robust error handling, rate limiting, and clear validation for missing/present credentials.
2. R2: Enterprise Google Cloud Deployment:
   - Package, configure, and deploy the multi-agent reasoning fleet to Vertex AI Agent Engine (Reasoning Engine) using Gemini 3.7 Flash and Google Cloud Application Default Credentials (ADC) in us-central1 under GCP project gen-lang-client-0942141479.
   - Package, containerize, and deploy the FastAPI application & Model Context Protocol (MCP) server to Google Cloud Run.
   - Integrate Google Cloud Secret Manager / secure environment configuration for external API tokens.
3. R3: End-to-End Programmatic Verification:
   - Implement and execute an automated verification suite that validates real-time API telemetry ingestion/correlation across the 6 sub-agents, ABAC scope perimeter isolation, HITL draft generation & approval lifecycle, and successful remote query execution against the deployed Vertex AI Agent Engine and Cloud Run instances.
   - Ensure local and remote test suites pass 100%.

Decompose tasks, spawn specialist subagents (explorers, implementers, reviewers, testers), maintain plan.md and progress.md in your working directory, and notify parent sentinel upon completion with full evidence.
