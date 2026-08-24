# 🔥 Prometheus: Enterprise Workstream Observability & Asynchronous Orchestration Platform

[![All Things Agentic Hackathon](https://img.shields.io/badge/All_Things_Agentic_Hackathon-The_Fortified_Enterprise_Fleet-blueviolet.svg)](https://allthingsagentichackathon.devpost.com/)
[![Google GenAI SDK](https://img.shields.io/badge/Google_GenAI-Gemini_3.7_Flash-4285F4.svg)](https://ai.google.dev/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-stdio_%7C_SSE-00C7B7.svg)]()
[![Google Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Ready-34A853.svg)](https://cloud.google.com/run)
[![Security](https://img.shields.io/badge/security-ABAC_%7C_Model_Armor-critical.svg)]()
[![HITL](https://img.shields.io/badge/HITL-Propose%2C_Don't_Impose-FF6F00.svg)]()

> **Submission for All Things Agentic Hackathon: The Fortified Enterprise Fleet Track**  
> *Autonomous AI Chief of Staff correlating cross-functional engineering telemetry (GitHub, Jira, Slack, CI/CD), isolating data via ABAC/RLS, and proposing contextual remediation actions for human sign-off ("Propose, Don't Impose").*

---

## 🏛️ System Architecture & Sub-Agent Fleet

```text
                          [ User Query / 08:00 AM Cron / Webhook / MCP ]
                                                │
                                                ▼
                                ┌───────────────────────────────────┐
                                │    Router & Guardrail Agent       │
                                │   - ABAC & Scope Perimeter Check  │
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
                                                │ (Aggregated Telemetry via MCP)
                                                ▼
                                ┌───────────────────────────────────┐
                                │    Synthesis & Blocker Agent      │
                                │    - Gemini 3.7 Flash Engine      │
                                │    - Multi-Model Quota Cascade    │
                                │    - Root-Cause Bottleneck Finder │
                                └────────────────┬──────────────────┘
                                                 │
                                                 ▼
                                ┌───────────────────────────────────┐
                                │     Action & Drafting Agent       │
                                │     - "Propose, Don't Impose"     │
                                │     - Slack Block Kit Action Cards│
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

---

## 🌟 Enterprise Fleet Architectural Pillars

| Pillar | Platform Implementation | Capabilities |
| :--- | :--- | :--- |
| **Discovery & Lifecycle** | **Agent Registry** (`app/registry/`) | Central cataloging, schema validation, tool binding, and versioning for all 6 sub-agents. |
| **Core Execution & State** | **Async DAG + Memory Bank** (`app/memory/`) | Checkpointing, multi-week blocker lifecycles, and human approval state machines. |
| **Security & Governance** | **ABAC Perimeter & Model Armor** (`app/security/`) | Deterministic scope validation $P(U,R)$, PII redaction (tokens, emails, phone numbers), and prompt injection filters. |
| **Observability & Protocols** | **Hybrid MCP + Structured Traces** (`app/mcp/`) | Dual `stdio` & `SSE` Model Context Protocol transports + OpenTelemetry trace headers. |

---

## ⚡ Multi-Model Rate-Limit Quota Cascade

To bypass Gemini free-tier rate limits and maximize continuous execution, Prometheus implements a **5-tier dynamic model cascade**:

$$\text{gemini-3.7-flash} \xrightarrow{429} \text{gemini-3.6-flash} \xrightarrow{429} \text{gemini-3.5-flash} \xrightarrow{429} \text{gemini-3.5-flash-lite} \xrightarrow{429} \text{gemini-3.1-flash-lite} \xrightarrow{} \text{Heuristic Fallback}$$

- **Zero-Downtime Failover**: If any model returns `429 (ResourceExhausted)`, Prometheus immediately retries with the next tier.
- **Telemetry Delta Caching**: Inputs are hashed (`SHA-256`) to return cached digests for unchanged telemetry, saving token quota.

---

## 📁 Repository Layout

```text
prometheus/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Gemini 3.x cascade, MCP & Cloud Run settings
│   ├── main.py                   # FastAPI REST API, MCP SSE Stream & CLI runner
│   ├── scheduler.py              # Background 08:00 AM async cron scheduler
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router_agent.py       # ABAC & Guardrail security perimeter
│   │   ├── git_agent.py          # GitHub/CI ingestion agent
│   │   ├── jira_agent.py         # Jira/Linear project tracker agent
│   │   ├── workstream_agent.py   # Slack & calendar ingestion agent
│   │   ├── synthesis_agent.py    # Multi-domain correlation (Gemini 3.7 Pool)
│   │   └── action_agent.py       # HITL action drafter with Slack Block Kit
│   ├── llm/
│   │   ├── __init__.py
│   │   └── gemini_pool.py        # Gemini 3.x multi-model cascade & keyring pool
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── protocol.py           # MCP JSON-RPC 2.0 schemas
│   │   ├── server.py             # Prometheus MCP Server (stdio & SSE)
│   │   └── client.py             # MCP Client adapter for external tools
│   ├── registry/
│   │   ├── __init__.py
│   │   └── agent_registry.py     # Sub-Agent cataloging & discovery
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
│   └── test_workflow.py          # Hermetic multi-agent & security test suite
├── .github/
│   └── workflows/ci.yml          # GitHub Actions automated CI pipeline
├── deploy_gcp.sh                 # 1-Click Google Cloud Run deployment script
├── Dockerfile                    # Multi-stage production containerfile
├── Procfile                      # PaaS process definition
├── requirements.txt              # Production & test dependencies
├── PROJECT_SPEC.md               # Detailed system design specification
└── .env.example                  # Environment variables template
```

---

## 🚀 Quickstart & Setup

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

### 4. Run the REST API & MCP Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **OpenAPI Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MCP Server-Sent Events Endpoint**: `http://localhost:8000/mcp/sse`
- **Agent Registry Discovery**: `http://localhost:8000/api/v1/registry/agents`

---

## 🔌 Connecting to Claude Desktop / Antigravity via MCP

Add Prometheus to your MCP client configuration (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "python",
      "args": ["-m", "app.mcp.server"]
    }
  }
}
```

---

## ☁️ 1-Click Google Cloud Run Deployment

Deploy Prometheus to Google Cloud Run (automatically scales to zero when idle):

```bash
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

---

## 🧪 Testing

Run hermetic test suite:

```bash
pytest tests/ -v
```
