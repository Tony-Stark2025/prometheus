# 🚀 Building Prometheus: How We Built an Autonomous AI Chief of Staff for Engineering Fleets with Gemini 3.7 & Google Cloud

**Subtitle:** *Connecting GitHub, Jira, and Slack into an autonomous multi-agent reasoning DAG that predicts delivery bottlenecks and drives 1-click human-in-the-loop resolutions.*

*By Bright Onwe*

---

![Prometheus Architecture Banner](https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1600&q=80)

---

## 🎯 The Hidden Tax on Modern Engineering Fleets

Every engineering leader and staff engineer knows the feeling:
- A high-priority milestone is scheduled for Friday.
- In Jira, tickets are marked `"In Progress"`.
- On GitHub, a critical pull request has been sitting unreviewed for 58 hours.
- In Slack, engineers are debating an API interface mismatch in a buried thread.

By the time anyone notices the blockage in a standup or retro, **days of velocity have already evaporated**. 

Modern engineering organizations don't suffer from a lack of tools — they suffer from **cross-domain fragmentation**. GitHub knows code latency. Jira knows sprint deadlines. Slack knows team sentiment. But **none of them talk to each other to diagnose root-cause delivery bottlenecks**.

To solve this, we built **Prometheus**: an enterprise-grade, autonomous **AI Chief of Staff** powered by **Google Cloud Vertex AI, Cloud Run, and Gemini 3.7 Flash**.

---

## 💡 What is Prometheus?

Prometheus is not just another chatbot or passive dashboard. It is an **asynchronous multi-agent intelligence platform** that continuously observes engineering workstreams across GitHub, Jira Cloud, and Slack. 

Instead of waiting for standups, Prometheus:
1. **Ingests real-time telemetry** concurrently across code reviews, CI builds, Jira epics, and team discussions.
2. **Correlates cross-domain evidence** using **Gemini 3.7 Flash** to identify the true root cause of delivery delays.
3. **Applies "Propose, Don't Impose"**: It drafts context-aware Slack action cards and direct messages, pausing safely for **1-click human-in-the-loop (HITL) approval** before taking any real-world action.

---

## 🏛️ The Multi-Agent Reasoning Fleet

Prometheus is architected as an asynchronous **Directed Acyclic Graph (DAG)** of 6 specialized autonomous agents:

```
[User / Scheduled Ingest]
           │
           ▼
 🛡️ Agent 1: Perimeter Router & ABAC Guard
           │ (Parallel Fan-Out)
 ┌─────────┼─────────┐
 ▼         ▼         ▼
🐙 Git    📋 Jira   💬 Workstream (Slack)
 └─────────┬─────────┘
           │ (Async Gather)
           ▼
 🧠 Agent 5: Synthesis & Root Cause (Gemini 3.7 Flash)
           │
           ▼
 📝 Agent 6: Action & Drafting Agent ("Propose, Don't Impose")
           │
     [State Store] ──► 🛑 HITL Human Gate (1-Click Approve / Reject)
                               │ (Approved)
                               ▼
                    🚀 Slack Web API Dispatcher
```

### The 6 Specialized Sub-Agents:

1. **🛡️ Perimeter Router Agent**: Authenticates requests via **Google OAuth 2.0**, enforces **Attribute-Based Access Control (ABAC)** perimeter scopes (`engineering`, `platform`, `security`), and sanitizes inputs using **Model Armor** prompt defense.
2. **🐙 Git & CI Ingestion Agent**: Analyzes live GitHub repositories, measuring PR review latency, unreviewed branch aging, and failed GitHub Actions CI runs.
3. **📋 Jira Agile Ingestion Agent**: Connects to Jira Cloud REST APIs, tracking active sprints, blocked epics, dependency linkages, and release milestones.
4. **💬 Workstream Discussion Agent**: Ingests public Slack channel chatter, inferring team context, sentiment, and technical roadblocks.
5. **🧠 Synthesis & Correlation Agent**: The brain of Prometheus. It feeds cross-domain telemetry into **Gemini 3.7 Flash** to perform root cause synthesis (e.g., *"PR #1's review delay directly stalls Jira Epic KAN-4 and causes downstream gateway CI failures"*).
6. **📝 Action & Drafting Agent**: Adheres strictly to the *Propose, Don't Impose* doctrine. It formulates targeted Slack Block Kit action cards and reviewer direct messages, persisting them to a state store with `require_confirmation = True`.

---

## 🔒 Enterprise Security: ABAC, OAuth 2.0 & Firestore Vault

Enterprise engineering data is sensitive. We designed Prometheus with four non-negotiable security layers:

- **Google OAuth 2.0 & Session Management**: Built-in enterprise authentication allowing new team leads and developers to authenticate frictionlessly.
- **ABAC Scope Perimeter**: Every user token is bound to specific organizational scopes (e.g., `engineering`, `platform`). Telemetry from unauthorized squads is pruned before reaching the LLM.
- **Multi-Tenant Firestore Vault**: API credentials for GitHub, Jira, and Slack are encrypted in Google Cloud Firestore with client-side key derivation, removing sensitive secrets from local disk and environment files.
- **Model Armor Prompt Defense**: Pre-execution filters detect prompt injection, jailbreak attempts, and redact PII/credentials before context is processed by Gemini.

---

## ⚡ Zero-Mock Live Telemetry & Resilient Integrations

One of our strictest project invariants was **Zero-Mock Production Safety**:

- **GitHub REST / GraphQL**: Direct ingestion of live pull requests, reviewer lists, commit timelines, and CI build status.
- **Jira Cloud API**: Built-in resilience against Atlassian Cloud's recent `/rest/api/3/search` HTTP 410 deprecations, falling back dynamically to `/rest/api/2/search` and `POST /rest/api/3/search/jql`.
- **Slack Web API**: Robust user resolution (`users.list` $\to$ `conversations.open` $\to$ `chat.postMessage`) ensuring direct messages and channel alerts reach verified user IDs (`im:write`, `chat:write`) even when channel listing scopes are restricted.

---

## 🎬 Real-World Walkthrough: From Blocker to 1-Click Resolution

Here is what Prometheus looks like in action on our live Google Cloud Run deployment:

### 1. Telemetry Ingestion & Autonomous Correlation
When the fleet triggers, Prometheus queries GitHub (`Tony-Stark2025/ecommerce-platform`), Jira (`KAN` project), and Slack (`my-first-workspace`).

Gemini 3.7 Flash correlates the data:
> **Root Cause Blocker Identified [BLK-01]:**  
> *"PR #1 ('feat(auth): Migrate auth service to OAuth 2.1 token exchange') has been waiting for review for 3.2 hours from reviewer @brightbutler7. It is directly blocking high-priority Jira Epic KAN-4. Downstream CI pipeline is failing due to interface mismatch."*

### 2. Action Card Drafting
Prometheus drafts a direct message tailored to the reviewer:
> *"Hi @brightbutler7! 👋 PR #1 (OAuth 2.1 token exchange) is awaiting your review and is currently stalling delivery on Epic KAN-4. Could you please take a look today to unblock the milestone? 🚀"*

### 3. Human-in-the-Loop 1-Click Sign-Off
On the Prometheus Executive Dashboard, the lead reviews the evidence graph and clicks **"Approve & Dispatch"**.

Within milliseconds, Prometheus calls Slack's `conversations.open` and `chat.postMessage`, delivering the interactive reminder directly into `@brightbutler7`'s Slack DM and recording an audit trail in SQLite.

---

## 🛠️ The Tech Stack

- **Reasoning Engine**: Google Vertex AI & Gemini 3.7 Flash
- **Deployment Platform**: Google Cloud Run (Serverless Container, us-central1)
- **Protocol**: Model Context Protocol (MCP) Server (SSE & REST)
- **Backend**: Python 3.14 / FastAPI / AsyncIO / Pydantic v2
- **Persistence**: SQLite (Local State & Audit Log) + Google Cloud Firestore (Credential Vault)
- **Integrations**: GitHub REST API, Atlassian Jira Cloud REST API, Slack Web API
- **Testing**: Hermetic Pytest matrix with 100% passing adversarial and namespace parity suites

---

## 📈 Key Learnings & Takeaways

1. **"Propose, Don't Impose" is the Golden Rule for Agentic AI**: Autonomous agents that take unconfirmed write actions in production destroy trust. Giving humans 1-click veto power transforms AI from a risky black box into an indispensable co-pilot.
2. **Correlation Beats Aggregation**: Simply aggregating data into another dashboard creates alert fatigue. The true unlock is **cross-domain reasoning** — linking a Git pull request to a Jira epic and a Slack discussion.
3. **Dual Namespace Parity Invariant**: Maintaining strict synchronization between mirrored package roots (`prometheus/` $\leftrightarrow$ `app/`) prevented circular imports and guaranteed zero drift between Cloud Run and local developer workflows.

---

## 🔗 Try Prometheus & Explore the Code

- **Live Dashboard**: [Prometheus on Cloud Run](https://prometheus-chief-of-staff-mbnra7rjha-uc.a.run.app/dashboard)
- **Documentation & Whitepaper**: [Prometheus Whitepaper](https://prometheus-chief-of-staff-mbnra7rjha-uc.a.run.app/documentation)
- **GitHub Repository**: [Tony-Stark2025/prometheus](https://github.com/Tony-Stark2025/prometheus)

---

*What delivery bottlenecks are hiding in your engineering fleet right now? Let's discuss in the comments below!* 💬
