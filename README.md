# 🔥 Prometheus: Enterprise Workstream Observability & Asynchronous Orchestration Platform

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-Multi--Agent%20Fleet-orange.svg)]()
[![Security](https://img.shields.io/badge/security-ABAC%20%7C%20PII%20Sanitized-green.svg)]()
[![HITL](https://img.shields.io/badge/HITL-Propose%2C%20Don't%20Impose-purple.svg)]()

Prometheus is an enterprise-grade, asynchronous **AI Chief of Staff** multi-agent platform. It continuously ingests cross-functional developer telemetry (GitHub, Jira, Slack, CI/CD), correlates delivery blockers, isolates data strictly via ABAC/Row-Level Security, and proposes contextual remediation actions for human sign-off (**"Propose, Don't Impose"**).

---

## 🏛️ System Architecture & Sub-Agent Roster

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
                         ┌───────────────────────┼──────────────────────┐
                         ▼                       ▼                      ▼
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

### The 6 Specialized Sub-Agents

1. **Router & Guardrail Agent (`router_agent.py`):** Validates incoming user queries, verifies org token scopes, and runs prompt sanitization and PII redaction.
2. **Git & CI/CD Ingestion Agent (`git_agent.py`):** Scans PR review latency, stale branches (>48h unreviewed), and build pipeline failures.
3. **Project Tracker Agent (`jira_agent.py`):** Tracks issue statuses, blocked epics, and sprint burndown deviations.
4. **Workstream Ingestion Agent (`workstream_agent.py`):** Synthesizes public workstream chat context (Slack/Teams).
5. **Synthesis & Blocker Agent (`synthesis_agent.py`):** Correlates multi-source telemetry via Gemini 2.5 / 3.7 to pinpoint root-cause delivery bottlenecks.
6. **Action & Drafting Agent (`action_agent.py`):** Generates daily alignment digests and drafts action proposals (`require_confirmation=True`).

---

## 🔒 Security & Operational Principles

- **Zero Unilateral Mutations:** All tools mutating external systems require human sign-off.
- **Deterministic ABAC Isolation:** Guarantees agents only access data within the requester's authorized organizational scope:
  $$P(U, R) = \text{IsAuthenticated}(U) \land \text{WithinOrgScope}(U, R) \land \neg\text{IsRestricted}(R)$$
- **PII & Prompt Defense:** Automatic redaction of secrets, tokens, emails, and jailbreak attempts before multi-agent reasoning.
- **Cloud & Free-Tier Portability:** Zero proprietary cloud lock-in. Compatible with standard API keys (`GEMINI_API_KEY`), PostgreSQL/SQLite, Docker, Heroku, Azure, Render, and Railway.

---

## 📁 Repository Layout

```text
prometheus/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic settings & Gemini API configuration
│   ├── main.py                   # FastAPI REST API & Interactive CLI runner
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router_agent.py       # ABAC & Guardrail security perimeter
│   │   ├── git_agent.py          # GitHub/CI ingestion agent
│   │   ├── jira_agent.py         # Jira/Linear project tracker agent
│   │   ├── workstream_agent.py   # Slack & calendar ingestion agent
│   │   ├── synthesis_agent.py    # Blocker correlation & Gemini reasoning engine
│   │   └── action_agent.py       # Human-in-the-loop action drafter
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── github_tools.py       # Git PR & CI status tools
│   │   ├── jira_tools.py         # Project management tools
│   │   └── slack_tools.py        # Communication drafting & dispatch tools
│   ├── security/
│   │   ├── __init__.py
│   │   ├── abac_guard.py         # Attribute-Based Access Control (ABAC/RLS)
│   │   └── guardrails.py         # Inline prompt defense & PII sanitizer
│   ├── memory/
│   │   ├── __init__.py
│   │   └── state_store.py        # Durable session checkpointing & audit store
│   └── workflows/
│       ├── __init__.py
│       └── prometheus_flow.py    # Multi-agent asynchronous orchestration DAG
├── tests/
│   ├── mock_telemetry.py         # Test fixtures & telemetry generators
│   └── test_workflow.py          # End-to-end multi-agent execution & security tests
├── Dockerfile                    # Multi-stage containerfile
├── Procfile                      # Heroku / PaaS process definition
├── requirements.txt              # Production & test dependencies
├── PROJECT_SPEC.md               # Detailed system design specification
└── .env.example                  # Environment variables template
```

---

## 🚀 Quickstart & Usage

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Tony-Stark2025/prometheus.git
cd prometheus

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Set your GEMINI_API_KEY in .env
```

### 3. Run the Interactive CLI Demo

```bash
python app/main.py --cli
```

### 4. Run the REST API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🧪 Testing

Run unit tests and end-to-end integration workflows:

```bash
pytest tests/ -v
```

---

## 🚢 Deployment

### Docker
```bash
docker build -t prometheus:latest .
docker run -p 8000:8000 -e GEMINI_API_KEY="your_api_key" prometheus:latest
```

### Heroku / Render / Railway
Deploy directly using the provided `Dockerfile` or `Procfile`.
