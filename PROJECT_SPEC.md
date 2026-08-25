# PROJECT GOAL & SYSTEM SPECIFICATION: PROMETHEUS
## Enterprise Workstream Observability & Asynchronous Orchestration Platform

> **Target Platform:** Gemini Enterprise Agent Platform (Agent Engine) & Cloud Native  
> **Core Architecture:** Multi-Agent Fleet on Vertex AI with Gemini 3.7 Flash (`google-genai`)  
> **Core Objective:** Build and deploy an enterprise-grade, asynchronous AI Chief of Staff agent system that ingests cross-functional developer telemetry (GitHub, Jira, Slack, CI/CD), correlates delivery blockers, isolates data strictly via ABAC/RLS, and proposes contextual remediation actions for human sign-off ("Propose, Don't Impose").

---

## 1. Executive Summary & Problem Statement

### The Problem
In modern, decentralized, and flat engineering organizations, delivery velocity degrades due to:
- **Cross-Functional Misalignment:** Teams operate in disjoint tool silos (GitHub/GitLab, Jira/Linear, Slack/Teams, CI/CD pipelines).
- **Invisible Delivery Bottlenecks:** Stale PRs waiting on unassigned reviewers, upstream API changes breaking CI, or blocked tickets without notifications.
- **Status Reporting Overhead:** High-friction manual status standups, sprint updates, and fragmented Slack pings drain engineering focus.

### The Solution: Prometheus
Prometheus functions as an autonomous **AI Chief of Staff** that continuously correlates objective work artifacts across enterprise systems, detects delivery blockers, and drafts high-value remediation actions for human approval on the Gemini Enterprise Agent Platform.

### Core Operational Principles
1. **Focus on Objective Work Artifacts:** Evaluates PRs, commit velocity, deployment logs, and RFCs rather than subjective self-reporting.
2. **Propose, Don't Impose (Human-in-the-Loop):** Action agents generate actionable *drafts* (Slack pings, Jira updates) that require explicit human approval before external mutation.
3. **Deterministic Context Isolation:** ABAC and Row-Level Security guarantee that agents only access authorized organizational data:
   $$P(U,R) = \text{IsAuthenticated}(U) \land \text{WithinOrgScope}(U, R) \land \neg\text{IsRestricted}$$
4. **Radical Transparency:** Operational insights and metrics visible to leadership are equally accessible to the respective delivery squads.

---

## 2. Architecture & Enterprise Track Alignment

| Architectural Pillar | Platform Implementation | Tech Stack Component |
| :--- | :--- | :--- |
| **Discovery & Lifecycle** | Cataloging and versioning of 6 specialized sub-agents. | Google ADK / Modular Sub-Agent Registry |
| **Core Execution & State** | Long-running asynchronous execution graph with durable SQLite checkpoints. | FastAPI + aiosqlite / Async DAG + Agent Engine |
| **Memory Bank** | Multi-week tracking of cross-squad blocker lifecycles and PR staleness. | Persistent SQLite (`aiosqlite`) / Cloud SQL |
| **Security & Governance** | Zero-trust IAM (Google ADC), deterministic ABAC scope enforcement, and inline prompt defense. | Modular Guardrails + Gemini Safety Filters + PII Sanitizer |
| **Telemetry & Observability** | Full trajectory logging of tool invocations, token usage, and sub-agent decision paths. | OpenTelemetry + Structured Logging & Tracing |

---

## 3. Multi-Agent Topology & Sub-Agent Roster

```text
                          [ User Query / 08:00 AM Cron / Event Webhook ]
                                                │
                                                ▼
                               ┌───────────────────────────────────┐
                               │    Router & Guardrail Agent       │
                               │   - ABAC & Scope Check            │
                               │   - Prompt Defense / PII Filter   │
                               └────────────────┬──────────────────┘
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
             ┌──────────────────────┐ ┌───────────────────┐ ┌──────────────────────┐
             │ Git & CI/CD Ingestion│ │  Project Tracker  │ │ Workstream Ingestion │
             │ - GitHub / GitLab    │ │  - Jira / Linear  │ │ - Public Slack/Teams │
             │ - PR latency / CI    │ │  - Epics/Blockers │ │ - Calendar Metadata  │
             └──────────┬───────────┘ └─────────┬─────────┘ └──────────┬───────────┘
                         │                      │                      │
                         └──────────────────────┼──────────────────────┘
                                                │ (Aggregated Telemetry)
                                                ▼
                               ┌───────────────────────────────────┐
                               │    Synthesis & Blocker Agent      │
                               │    - Multi-domain Correlation     │
                               │    - Gemini Reasoning Engine      │
                               │    - Root-Cause Bottleneck Finder │
                               └────────────────┬──────────────────┘
                                                │
                                                ▼
                               ┌───────────────────────────────────┐
                               │     Action & Drafting Agent       │
                               │     - "Propose, Don't Impose"     │
                               │     - Prepares Action Drafts      │
                               └────────────────┬──────────────────┘
                                                │
                                                ▼
                                 [ Human Approval Checkpoint ]
                                 (Approve / Edit / Discard)
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                           [ Approved: Dispatch ]   [ Rejected: Abort ]
                            - Slack DM / Jira SDK
```

### Sub-Agent Roles & Tools

1. **Router & Guardrail Agent:** Validates incoming user queries, checks token scopes, strips PII, and runs prompt sanitization and safety filters.
2. **Git & CI/CD Ingestion Agent:** Scans PR review latency, stale branches (>48h unreviewed), and build failures across GitHub/GitLab via MCP/APIs.
3. **Project Tracker Agent:** Tracks issue status changes, epic progress, blocked states, and sprint burndown deviations from Jira/Linear.
4. **Workstream Ingestion Agent:** Synthesizes public channel discussions (Slack/Teams) and calendar availability metadata.
5. **Synthesis & Blocker Agent:** Correlates multi-source operational telemetry to identify root-cause delivery bottlenecks.
6. **Action & Drafting Agent:** Prepares scheduled executive digests and drafts action cards with `require_confirmation=True`.

---

## 4. Key Workflows

### Workflow A: Asynchronous Daily Alignment Digest
* **Trigger:** Automated cron trigger at 08:00 AM local time.
* **Ingestion:** Sub-agents query status changes across Git, Jira, and Slack within the user's authorized organizational scope over the last 24 hours.
* **Synthesis:** Gemini identifies 3–5 high-impact delivery blockers requiring leadership attention.
* **Delivery:** Sends a formatted summary briefing with interactive action triggers to the lead's dashboard or inbox.

### Workflow B: Human-in-the-Loop Task Orchestration
* **Detection:** Synthesis agent identifies a stale dependency between squads.
* **Drafting:** Action agent prepares a contextual draft (e.g., *"Hi @Alex, PR #402 seems to be blocking the v2.1 deployment. Could you review it today or assign an alternate reviewer?"*).
* **Approval Checkpoint:** Workflow pauses in ADK session state presenting `[Send Message] | [Edit Draft] | [Discard]`.
* **Execution:** Dispatches external API mutation only upon explicit human confirmation.

---

## 5. Technology Stack & Directory Structure

### Stack Definition
* **Language & Runtime:** Python 3.11+
* **Foundation LLM:** Gemini 2.5 / 3.5 / 3.7 Flash via Google GenAI SDK (`google-genai` using `GEMINI_API_KEY`)
* **Orchestration Framework:** Google Agent Development Kit 2.0 (`google-adk`)
* **Security & Guardrails:** Custom ABAC Guard + Pydantic validation + Gemini Safety Filters + PII Sanitizer
* **State & Memory:** PostgreSQL (Neon / Supabase / Heroku Postgres / SQLite) with session checkpointing
* **Hosting:** Heroku (Procfile / Container), Azure App Service / Container Apps, Render, Railway, or local Docker
* **Observability:** OpenTelemetry traces and structured logging

### Target Repository Layout

```text
prometheus/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Gemini API key, model configurations & app settings
│   ├── main.py                   # Entrypoint & CLI / ADK web runner (FastAPI / Uvicorn)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router_agent.py       # ABAC & Guardrail security perimeter
│   │   ├── git_agent.py          # GitHub/CI ingestion agent
│   │   ├── jira_agent.py         # Jira/Linear project tracker agent
│   │   ├── workstream_agent.py   # Slack & calendar ingestion agent
│   │   ├── synthesis_agent.py    # Blocker correlation & dependency detector
│   │   └── action_agent.py       # Human-in-the-loop action drafter
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── github_tools.py       # Git PR & CI status tools (MCP / FunctionTool)
│   │   ├── jira_tools.py         # Project management tools
│   │   └── slack_tools.py        # Communication drafting tools
│   ├── security/
│   │   ├── __init__.py
│   │   ├── abac_guard.py         # Org scope validation (Scope_User ∩ Scope_Resource)
│   │   └── guardrails.py         # Inline prompt defense & PII sanitizer
│   ├── memory/
│   │   ├── __init__.py
│   │   └── state_store.py        # PostgreSQL / SQLite session checkpointing
│   └── workflows/
│       ├── __init__.py
│       └── prometheus_flow.py    # ADK Workflow DAG connecting all sub-agents
├── tests/
│   ├── mock_telemetry.py         # Mock PRs, Jira epics, and Slack data
│   └── test_workflow.py          # End-to-end multi-agent execution tests
├── Dockerfile                    # Multi-stage containerfile for Heroku / Azure / Render
├── Procfile                      # Heroku deployment process definition
├── requirements.txt              # Production dependencies
├── README.md                     # Setup, architecture & spin-up instructions
└── .env.example                  # Environment variables template (GEMINI_API_KEY, etc.)
```

---

## 6. Phased Implementation Plan for the SWE Agent

1. **Phase 1: Foundation & Baseline Smoke Test**
   * Initialize `config.py` with Gemini Developer API settings (`GEMINI_API_KEY`).
   * Define data schemas (`BlockerItem`, `AlignmentDigest`, `ActionDraft`).
   * Implement `smoke_test.py` to confirm ADK agent communication.

2. **Phase 2: Sub-Agents & Tooling Core**
   * Build standalone MCP/Python function tools with realistic mock datasets for Git, Jira, and Slack.
   * Construct individual ADK Agent instances with domain-specific system instructions.

3. **Phase 3: ADK Workflow & Human-in-the-Loop Integration**
   * Wire sub-agents into an ADK Workflow state DAG.
   * Configure mutating action tools with `require_confirmation=True`.
   * Implement session state persistence (PostgreSQL / SQLite).

4. **Phase 4: Security (Guardrails & ABAC) & Observability**
   * Wire prompt sanitization, safety filters, and PII masking into `router_agent.py`.
   * Enforce deterministic org-scope pre-filtering.
   * Instrument OpenTelemetry / structured traces for agent hops.

5. **Phase 5: Deployment & Packaging**
   * Write optimized multi-stage `Dockerfile` and Heroku `Procfile`.
   * Configure seamless local / Azure / Heroku / Render spin-up.
   * Generate a comprehensive `README.md` with visual ASCII architecture and reproducible local spin-up steps.

---

## 7. Mandatory SWE Agent Directives

* **Zero Unilateral Mutations:** All tools mutating external systems MUST enforce human confirmation pauses.
* **Clean Typing & Validation:** Use Pydantic models and explicit Python type hints.
* **Cloud & Free-Tier Portability:** Maintain zero GCP lock-in; support standard API keys (`GEMINI_API_KEY`), PostgreSQL/SQLite, and standard container/Heroku/Azure runtimes.
* **Rubric Alignment:** Optimize code structure for **Innovation & Operational Utility (40%)**, **Architectural Discipline (30%)**, and **Demo Readiness (30%)**.
