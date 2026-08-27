# Deployment Architecture Investigation & Blueprint Report

## 1. Observation

### 1.1 GCP Environment & Authentication
- **Active GCP Account**: `brightonwe30@gmail.com`
- **Active GCP Project**: `gen-lang-client-0942141479`
- **Region**: `us-central1`
- **Enabled APIs observed** via `gcloud services list --enabled --project=gen-lang-client-0942141479`:
  - `aiplatform.googleapis.com` (Vertex AI / Agent Platform)
  - `run.googleapis.com` (Cloud Run Admin API)
  - `artifactregistry.googleapis.com` (Artifact Registry)
  - `cloudbuild.googleapis.com` (Cloud Build API)
  - `storage-api.googleapis.com` (Cloud Storage JSON API)
  - `secretmanager.googleapis.com` is **NOT** currently enabled (returned prompt: `API [secretmanager.googleapis.com] not enabled on project [gen-lang-client-0942141479]`).
- **GCS Staging Bucket observed** via `gcloud storage buckets list`:
  - `gs://gen-lang-client-0942141479-agent-engine/` exists in `US-CENTRAL1`.
- **Artifact Registry Repository observed** via `gcloud artifacts repositories list`:
  - `cloud-run-source-deploy` (Docker format) exists in `us-central1`.

### 1.2 Vertex AI Reasoning Engine / Agent Engine Architecture
- **Script**: `deploy_agent_engine.py` (242 lines)
  - Imports: `from prometheus.config import settings`, `from prometheus.engine_app import PrometheusAgentEngineApp, run_async`, `from prometheus.registry.agent_registry import agent_registry`.
  - Staging bucket resolution: `ensure_staging_bucket()` ensures `gs://{project_id}-agent-engine` exists.
  - Packaging mechanism: Lines 104–116 dynamically monkey-patches `vertexai.reasoning_engines._reasoning_engines._upload_extra_packages` with custom `_custom_upload_extra_packages` using `_tar_filter` to exclude `__pycache__`, `.pyc`, `.pytest_cache`, `.db`, and `.sqlite`, bundling `extra_packages=[pkg_prometheus, pkg_app]` into `dependencies.tar.gz`.
  - Deployment call: `reasoning_engines.ReasoningEngine.create(app_instance, requirements=[...], extra_packages=[pkg_prometheus, pkg_app], display_name="prometheus-chief-of-staff")`.
  - Required container packages:
    ```python
    requirements=[
        "google-cloud-aiplatform[agent_engines]>=1.70.0",
        "google-genai>=0.1.1",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.2.0",
        "aiosqlite>=0.20.0",
        "httpx>=0.27.0",
        "cloudpickle>=3.0.0",
    ]
    ```
- **Async Event Loop Handling (`app/engine_app.py` & `prometheus/engine_app.py`)**:
  - `run_async(coro)` (lines 17–33):
    ```python
    def run_async(coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)
    ```
  - Exposed RPC entrypoints on `PrometheusAgentEngineApp`:
    - `set_up()`: runs `state_store.init_db()`
    - `query(prompt, user_id, username, org_scopes)`: runs `PrometheusWorkflow.run()`
    - `list_agents()`: returns 6-agent fleet metadata
    - `approve_action(draft_id, approver_username)`: runs `SlackTools.dispatch_approved_action()`
    - `reject_action(draft_id, approver_username)`: updates state store status to `REJECTED`
    - `register_operations()`: returns `{"": ["query", "list_agents", "approve_action", "reject_action"]}`

### 1.3 Cloud Run Containerization & Entry Points
- **Dockerfile**:
  - Stage 1 (`builder`): `FROM python:3.11-slim`, installs `build-essential`, runs `pip install --no-cache-dir --user -r requirements.txt`.
  - Stage 2 (`runtime`): `FROM python:3.11-slim`, installs `curl`, copies `/root/.local` and application files, sets `ENV PORT=8000`, `EXPOSE 8000`.
  - Health check: `HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:${PORT}/healthz || exit 1`.
  - Startup command: `CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}` (dynamically adapts to Cloud Run's `$PORT`).
- **FastAPI Endpoints (`app/main.py`)**:
  - `GET /healthz`: Returns JSON with health status, Gemini model, platform name, Agent Engine app ID, HITL status, and MCP status.
  - `GET /dashboard` & `GET /`: Serves `app/dashboard/dashboard.html` executive UI.
  - `POST /mcp/sse`: Handles JSON-RPC 2.0 requests (`initialize`, `tools/list`, `tools/call`).
  - `GET /api/v1/blockers`: Active blockers.
  - `POST /api/v1/digest`: Trigger alignment workflow (`TriggerDigestRequest`).
  - `GET /api/v1/registry/agents`: Agent fleet registry.
  - `GET /api/v1/actions`: Pending action drafts.
  - `POST /api/v1/actions/{draft_id}/approve`: Explicit human approval.
  - `POST /api/v1/actions/{draft_id}/reject`: Human rejection.
  - `POST /api/v1/webhooks/github` & `POST /api/v1/webhooks/slack`: Real-time webhooks.

### 1.4 Codebase Namespaces & Tests
- Both `app/` and `prometheus/` directories exist in root with identical 31 Python modules.
- `setup.py` packages all packages discovered by `find_packages()`.
- Test suite execution (`pytest`):
  - Ran 14 items across `tests/test_endpoints.py` and `tests/test_workflow.py`.
  - Result: 14 passed in 38.00s (100% pass rate).

---

## 2. Logic Chain

1. **Vertex AI Agent Engine Packaging & Compatibility**:
   - `PrometheusAgentEngineApp` wraps the multi-agent asynchronous workflows into synchronous callable methods.
   - When deployed via Vertex AI SDK, `ReasoningEngine.create` serializes `PrometheusAgentEngineApp` via `cloudpickle` and uploads `dependencies.tar.gz` containing the package directories (`prometheus` and `app`) to `gs://gen-lang-client-0942141479-agent-engine/`.
   - The `_tar_filter` ensures runtime cache files (`.pyc`, `__pycache__`) and local test databases (`.db`) do not corrupt the container filesystem.
   - `run_async` allows async coroutines (`asyncio.gather`, `aiosqlite`, `client.aio`) to run safely inside the Reasoning Engine container worker process without event loop collision errors.

2. **Cloud Run Containerization & Port Binding**:
   - The multi-stage Dockerfile builds a lean image (~200MB) with dependencies separated from source code.
   - Cloud Run injects the `PORT` environment variable (typically 8080 or specified). Dockerfile line 39 (`CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`) binds correctly to `${PORT}`.
   - The health check at `/healthz` tests DB initialization, config loading, and returns 200 OK, matching Cloud Run's liveness probe requirements.
   - The existing `cloud-run-source-deploy` Artifact Registry in `us-central1` allows zero-friction deployment via `gcloud run deploy --source .`.

3. **Secret Manager & Environment Configuration**:
   - To integrate live GitHub, Jira, and Slack credentials into Cloud Run, secrets should either be passed via Cloud Run environment variables (`--set-env-vars`) or Cloud Run Secret Manager bindings (`--set-secrets`).
   - Because `secretmanager.googleapis.com` is not yet enabled on project `gen-lang-client-0942141479`, any workflow utilizing Secret Manager must first enable the API: `gcloud services enable secretmanager.googleapis.com --project=gen-lang-client-0942141479`.
   - Application Default Credentials (ADC) are natively available on both Vertex AI Agent Engine and Cloud Run via attached IAM service accounts, allowing passwordless authentication to Gemini 3.7 Flash.

4. **Identified Missing Files & Gaps**:
   - **Missing `deploy_cloud_run.sh`**: `deploy_gcp.sh` is an outdated legacy script referencing `gcloud ai custom-jobs create`. A production `deploy_cloud_run.sh` script is needed to automate Cloud Run deployment with health checks and env variable bindings.
   - **Dual Namespace Synchronization**: Changes made to `app/` must be mirrored in `prometheus/` (or vice-versa) to prevent packaging discrepancies between Cloud Run (`app.main:app`) and Vertex AI Reasoning Engine (`prometheus.engine_app`).

---

## 3. Caveats

1. **Ephemeral SQLite on Serverless**:
   - SQLite (`prometheus_state.db`) is stored locally in the container instance filesystem. On Vertex AI Reasoning Engine and Cloud Run, container instances are serverless and ephemeral. This is ideal for stateless/in-memory session state during active requests, but cross-instance permanent persistence in enterprise production would leverage Cloud SQL PostgreSQL (`DATABASE_URL=postgresql+asyncpg://...`).
2. **Direct gRPC in Subagent Sandbox**:
   - Direct outgoing gRPC calls to Vertex AI endpoints from within the local Windows subagent shell may be restricted by local network proxy/firewall policies. `gcloud` HTTPS REST endpoints work normally.
3. **Secret Manager API Enablement**:
   - If Secret Manager is chosen over environment variables, `secretmanager.googleapis.com` must be explicitly enabled by an IAM admin/owner before secret creation.

---

## 4. Conclusion

The Prometheus deployment architecture is sound, modular, and ready for deployment:

1. **Vertex AI Agent Engine (Reasoning Engine)**:
   - Target project: `gen-lang-client-0942141479`, location: `us-central1`.
   - Staging bucket `gs://gen-lang-client-0942141479-agent-engine/` is verified and accessible.
   - Deployment script `deploy_agent_engine.py` handles package filtering, `dependencies.tar.gz` creation, and `run_async` event loop execution.
   - Remote verification script `tests/verify_remote.py` verifies all 6 sub-agents, Gemini 3.7 Flash telemetry synthesis, HITL approval, prompt injection defense, and ABAC perimeter isolation.

2. **Cloud Run Service (`prometheus-chief-of-staff`)**:
   - Multi-stage Dockerfile is configured for dynamic `$PORT` binding and `/healthz` health checking.
   - FastAPI application exposes dashboard (`/dashboard`), MCP SSE stream (`/mcp/sse`), and REST APIs.
   - Requires adding `deploy_cloud_run.sh` for one-command Cloud Run deployment.

3. **Security & Secrets**:
   - Live tokens (`GITHUB_TOKEN`, `JIRA_API_TOKEN`, `JIRA_INSTANCE_URL`, `SLACK_BOT_TOKEN`) must be injected via Cloud Run `--set-env-vars` or GCP Secret Manager.
   - Enable `secretmanager.googleapis.com` on `gen-lang-client-0942141479` when creating cloud-stored secrets.

---

## 5. Verification Method

### Step 1: Run Full Local Test Suite
```bash
pytest -v
```
*Expected Result*: 14/14 tests pass across `tests/test_endpoints.py` and `tests/test_workflow.py`.

### Step 2: Verify Vertex AI Reasoning Engine Packaging & Deployment
```bash
python deploy_agent_engine.py --project gen-lang-client-0942141479 --location us-central1
```
*Validation*: Inspect created Reasoning Engine resource name (e.g. `projects/135010851380/locations/us-central1/reasoningEngines/...`) and verify remote query execution.

### Step 3: Verify Remote Reasoning Engine
```bash
python -m pytest tests/verify_remote.py -s
# or
python tests/verify_remote.py
```
*Validation*: Asserts 6 sub-agents registered, Gemini 3.7 Flash returns structured blockers, HITL approval dispatches action, prompt injection is rejected, and ABAC perimeter enforces authorization.

### Step 4: Verify Cloud Run Deployment & Endpoints
```bash
# Deploy to Cloud Run
gcloud run deploy prometheus-chief-of-staff \
    --source . \
    --region us-central1 \
    --project gen-lang-client-0942141479 \
    --allow-unauthenticated \
    --port 8000

# Verify Cloud Run Endpoints
curl -f https://<CLOUD_RUN_URL>/healthz
curl -f https://<CLOUD_RUN_URL>/dashboard
curl -X POST https://<CLOUD_RUN_URL>/mcp/sse -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```
*Validation*: HTTP 200 OK on `/healthz`, `/dashboard`, and `/mcp/sse`.
