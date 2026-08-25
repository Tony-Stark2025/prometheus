# 🏆 DEVPOST SUBMISSION DRAFT: PROMETHEUS
## Track: The Fortified Enterprise Fleet Track (All Things Agentic Hackathon)

---

## 📌 Project Header
- **Project Title:** Prometheus: Autonomous AI Chief of Staff & Workstream Observability Platform
- **Tagline:** Correlating multi-domain engineering telemetry across GitHub, Jira, and Slack on Vertex AI Gemini 3.7 Flash with zero unilateral mutation ("Propose, Don't Impose").
- **Track:** The Fortified Enterprise Fleet Track
- **Tech Stack:** Google Cloud Vertex AI, Gemini 3.7 Flash, Gemini Enterprise Agent Platform (Agent Engine), Model Context Protocol (MCP stdio & SSE), Python 3.11+, FastAPI, aiosqlite.
- **GitHub Repository:** [https://github.com/Tony-Stark2025/prometheus](https://github.com/Tony-Stark2025/prometheus)

---

## 💡 Inspiration & The Problem
In modern decentralized engineering organizations, delivery velocity suffers not from lack of effort, but from **invisible delivery bottlenecks** across disconnected tool silos:
1. **Tool Silos:** Code reviews live in GitHub, sprint tickets live in Jira/Linear, and blocker context is buried in fragmented Slack threads.
2. **Review Latency & Cascade Failures:** A Pull Request waiting on review for 48+ hours silently blocks downstream Jira Epics and breaks staging CI builds without proactive cross-system alerts.
3. **Status Overhead:** Engineering leads spend hours manually chasing updates, organizing status standups, and piecing together fractured workstreams.
4. **The "Autonomous Agent" Risk:** Traditional autonomous agents often make unilateral destructive mutations across production systems without human verification.

---

## 🚀 What Prometheus Does
**Prometheus** is an enterprise-grade, asynchronous **AI Chief of Staff** that acts as the connective tissue across software engineering fleets. 

Operating under the guiding philosophy of **"Propose, Don't Impose"**, Prometheus:
- **Passively Ingests & Correlates:** Ingests objective developer work artifacts across GitHub PRs, Jira Epics, Slack communications, and CI/CD pipelines.
- **Identifies Delivery Blockers:** Uses **Gemini 3.7 Flash** on Google Cloud Vertex AI to correlate root causes (e.g., *PR-402 awaiting alex-lead's review is blocking Epic PROJ-108 and breaking CI build #184*).
- **Drafts Interactive Action Cards:** Generates contextual Slack Block Kit action drafts (e.g., Slack DM, blocker channel alert, reviewer reassignment).
- **Enforces Human-in-the-Loop Sign-Off:** Halts before external mutation, requiring explicit human approval (`[Approve & Dispatch]`, `[Edit]`, `[Discard]`) to ensure zero rogue actions.
- **Governs with Zero-Trust ABAC & Model Armor:** Enforces deterministic Attribute-Based Access Control $P(U,R)$, inline prompt injection filters, and automatic PII sanitization.

---

## 🏛️ How We Built It: Alignment with the 7 Fortified Enterprise Fleet Pillars

Prometheus was purpose-built to embody all 7 core pillars of the Fortified Enterprise Fleet architecture:

### 1. Agent Discovery & Lifecycle (Agent Registry)
- Central cataloging in `app/registry/agent_registry.py` registering all 6 specialized sub-agents (`Router`, `Git`, `Jira`, `Workstream`, `Synthesis`, `Action Drafter`).
- Inspects versioning, roles, capabilities, model requirements (`gemini-3.7-flash`), and security bounds.

### 2. Core Execution & State (Async DAG Engine)
- Asynchronous orchestration engine in `app/workflows/prometheus_flow.py` coordinating sub-agent ingestion in parallel and piping aggregated telemetry into the reasoning core.
- Configured for deployment on the **Gemini Enterprise Agent Platform (Agent Engine)**.

### 3. Memory Bank & Session Checkpointing
- Durable session memory and multi-week blocker tracking via asynchronous SQLite (`aiosqlite`) in `app/memory/state_store.py`.
- Persists blocker lifecycles, human approval decisions, and audit trails across runs.

### 4. Agent Identity & Security (Google Cloud IAM & ABAC Perimeter)
- Enterprise authentication using Google Cloud Application Default Credentials (ADC) and IAM service accounts with zero raw API keys exposed.
- Deterministic Attribute-Based Access Control (`ABACGuard`) ensuring users and agents only access authorized organizational telemetry scopes:
  $$P(U,R) = \text{IsAuthenticated}(U) \land \text{WithinOrgScope}(U, R) \land \neg\text{IsRestricted}$$

### 5. Gateway & External Interoperability (Dual Model Context Protocol)
- Implements standard **Model Context Protocol (MCP)** supporting both `stdio` (for Claude Desktop / Antigravity IDE) and `SSE` (Server-Sent Events for web agents) in `app/mcp/server.py`.
- Exposes tools: `get_daily_digest`, `list_active_blockers`, `approve_action`, and `get_agent_registry`.

### 6. Model Armor & Safety
- Inline prompt injection defense detecting jailbreaks, instruction overrides, and system prompt extractors in `app/security/guardrails.py`.
- Automatic PII redaction sanitizing GitHub tokens (`ghp_...`), email addresses, and API credentials before LLM invocation.

### 7. Observability & Telemetry Caching
- Full trajectory tracing across sub-agent hops.
- SHA-256 telemetry delta caching (`TelemetryCache`) to deduplicate LLM reasoning for identical telemetry states, saving token consumption and reducing latency.

---

## 🛠️ Architecture & Multi-Agent Topology

```text
                          [ User Query / 08:00 AM Cron / MCP SSE Stream ]
                                                 │
                                                 ▼
                                 ┌───────────────────────────────────┐
                                 │     Router & Guardrail Agent      │
                                 │   - ABAC & Scope Perimeter Check  │
                                 │   - Model Armor & PII Filter      │
                                 └─────────────────┬─────────────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                        ▼                        ▼
              ┌───────────────────────┐ ┌────────────────────┐ ┌───────────────────────┐
              │ Git & CI/CD Ingestion │ │  Project Tracker   │ │ Workstream Ingestion  │
              │ - GitHub PR Latency   │ │  - Jira Sprint Epics│ │ - Slack Channels      │
              │ - CI Build Failures   │ │  - Blocked Tickets │ │ - Discussion Sentiment│
              └───────────┬───────────┘ └──────────┬─────────┘ └───────────┬───────────┘
                          │                        │                       │
                          └────────────────────────┼───────────────────────┘
                                                   │ (Aggregated Telemetry via MCP)
                                                   ▼
                                 ┌───────────────────────────────────┐
                                 │     Synthesis & Blocker Agent     │
                                 │     - Gemini 3.7 Flash Engine     │
                                 │     - Cross-Domain Correlation    │
                                 │     - Root-Cause Bottleneck Finder│
                                 └─────────────────┬─────────────────┘
                                                   │
                                                   ▼
                                 ┌───────────────────────────────────┐
                                 │      Action & Drafting Agent      │
                                 │      - "Propose, Don't Impose"    │
                                 │      - Slack Block Kit Drafter    │
                                 └─────────────────┬─────────────────┘
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

## 🎬 3-Minute Video Demonstration Script

| Timestamp | Scene / Visual | Script / Voiceover |
| :--- | :--- | :--- |
| **0:00 - 0:30** | **The Hook & Problem**<br/>Show disconnected tabs (GitHub PRs, Jira board, Slack messages). | *"In fast-moving engineering teams, delivery bottlenecks don't happen because engineers aren't working — they happen because critical work gets stuck across tool silos. A pull request waits 58 hours for review, silently blocking a tier-1 Jira epic and failing downstream CI builds. Meet Prometheus: the autonomous AI Chief of Staff built on Google Cloud Vertex AI and Gemini 3.7 Flash."* |
| **0:30 - 1:15** | **Live Ingestion & Correlation**<br/>Click "Run Fleet Ingest" on the Prometheus Web Dashboard (`/dashboard`). Show live progress bar animating across the 4 stages. | *"With one click or via scheduled 08:00 AM cron, Prometheus triggers its asynchronous multi-agent fleet. Agent 1 validates ABAC security scopes. Agents 2, 3, and 4 ingest Git PR latencies, Jira sprint statuses, and Slack threads in parallel. Agent 5, powered by Gemini 3.7 Flash on Vertex AI, correlates this telemetry to discover the root cause: PR-402 is stalling the v2.1 Gateway milestone."* |
| **1:15 - 2:00** | **"Propose, Don't Impose" (HITL Action Cards)**<br/>Switch to the "Action Cards" tab. Show Slack Block Kit preview cards. Click **[Approve & Dispatch]**. | *"Instead of making rogue changes, Prometheus adheres to 'Propose, Don't Impose'. Agent 6 drafts precise, contextual Slack Block Kit action cards. As an engineering lead, I can review the drafted Slack DM to Alex, edit it, or click 'Approve & Dispatch'. The action is dispatched with full audit provenance stored durably in our SQLite state store."* |
| **2:00 - 2:30** | **Security & Model Armor Sandbox**<br/>Switch to "Security & Model Armor" tab. Test ABAC simulator and PII redaction. | *"Security is foundational. Our deterministic ABAC guard ensures strict multi-tenant isolation so sales or external guests cannot access backend engineering repositories. Model Armor filters prompt injection attempts and automatically masks GitHub tokens and employee PII before LLM invocation."* |
| **2:30 - 3:00** | **MCP Integration & Deployment**<br/>Show MCP SSE endpoint (`/mcp/sse`) and OpenAPI docs. | *"Prometheus is fully interoperable via standard Model Context Protocol (MCP) with stdio and SSE transports, and is packaged for the Gemini Enterprise Agent Platform. Prometheus transforms engineering operations from reactive chaos into proactive, human-governed velocity."* |

---

## 🌟 What We Learned & What's Next
- **Gemini 3.7 Flash Performance:** Standardizing on Gemini 3.7 Flash via Vertex AI provided fast structured JSON reasoning and correlated cross-domain data with precision.
- **Human-in-the-Loop Value:** The "Propose, Don't Impose" paradigm establishes trust for enterprise adoption.
- **Roadmap:**
  - Automated pull request rebalancing based on reviewer calendar bandwidth.
  - Native bidirectional Slack Bolt interactive socket integrations.
  - Deep Jira Automation and GitLab merge request support.
