# E2E Test Infra: Prometheus AI Chief of Staff

## Test Philosophy
- Opaque-box & transparent-box hybrid verification: Derived from user requirements in `ORIGINAL_REQUEST.md`.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial + Real-World Workload Testing + Adversarial Red-Teaming.

## Feature Inventory & Test Coverage Mapping
| # | Feature | Source | Tier 1 (Unit) | Tier 2 (Live API) | Tier 3 (DAG/HITL) | Tier 4 (Remote) | Tier 5 (Adversarial) |
|---|---------|--------|:-------------:|:-----------------:|:-----------------:|:---------------:|:--------------------:|
| 1 | GitHub Live PR Ingestion | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 2 | GitHub Review Latency | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 3 | GitHub CI Failures | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 4 | Jira Sprint Issues | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 5 | Jira Blocker Dependencies | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 6 | Slack Ingestion | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 7 | Slack Action Card & DM Dispatch | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 8 | Rate Limiting & Auth Handling | ORIGINAL_REQUEST §R1 | ✓ | 5 | ✓ | ✓ | ✓ |
| 9 | Vertex AI Agent Engine Packaging | ORIGINAL_REQUEST §R2 | ✓ | - | ✓ | 5 | ✓ |
| 10 | Gemini 3.7 Flash & ADC | ORIGINAL_REQUEST §R2 | ✓ | - | ✓ | 5 | ✓ |
| 11 | Cloud Run FastAPI & MCP Server | ORIGINAL_REQUEST §R2 | ✓ | - | ✓ | 5 | ✓ |
| 12 | Secret Manager & Env Vars | ORIGINAL_REQUEST §R2 | ✓ | - | ✓ | 5 | ✓ |
| 13 | ABAC Scope Perimeter Isolation | ORIGINAL_REQUEST §R3 | 5 | - | ✓ | ✓ | 5 |
| 14 | Inline Prompt Defense & PII | ORIGINAL_REQUEST §R3 | 5 | - | ✓ | ✓ | 5 |
| 15 | HITL Draft & Approval Lifecycle | ORIGINAL_REQUEST §R3 | 5 | - | 5 | ✓ | 5 |

## Test Architecture
- **Runner**: `pytest` with `pytest.ini` configuration.
- **Directories**:
  - `tests/unit/`: Tier 1 Hermetic Unit & Component Tests
  - `tests/integration/`: Tier 2 Live API Integrations & Tier 3 Multi-Agent DAG Orchestration
  - `tests/e2e/`: Tier 4 Remote Cloud Endpoints (`test_vertex_agent_engine_remote.py`, `test_cloud_run_remote.py`)
  - `tests/adversarial/`: Tier 5 Prompt injection, ABAC boundary escalation, race condition fuzzing (`test_adversarial_matrix.py`)

## Coverage Thresholds
- **Tier 1 (Hermetic Unit)**: ≥15 test cases covering ABAC math, PII regex, MCP JSON-RPC, SQLite persistence.
- **Tier 2 (Live API Integration)**: ≥15 test cases covering GitHub, Jira Cloud, Slack with rate limiting and fallback.
- **Tier 3 (Multi-Agent DAG)**: ≥10 test cases covering 6-agent execution, correlation heuristics, HITL lifecycle & idempotency.
- **Tier 4 (Remote Cloud Endpoints)**: ≥5 test cases validating live Vertex AI Reasoning Engine and Cloud Run HTTP/SSE endpoints.
- **Tier 5 (Adversarial & Security)**: ≥10 test cases validating prompt injection defense, cross-tenant isolation, and race condition resistance.
- **Total Expected Tests**: ≥55 comprehensive test cases.
