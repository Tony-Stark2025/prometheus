param (
    [string]$ProjectId = "gen-lang-client-0942141479",
    [string]$Region = "us-central1",
    [switch]$VerifyOnly,
    [string]$EngineResourceName = "projects/135010851380/locations/us-central1/reasoningEngines/954065480874721280"
)

$ErrorActionPreference = "Stop"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " 🚀 Prometheus: Enterprise Google Cloud Fleet Deployment" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " Project ID : $ProjectId"
Write-Host " Region     : $Region"
Write-Host ""

if ($VerifyOnly) {
    Write-Host "🔍 Running Live Remote Verification Suite..." -ForegroundColor Yellow
    python deploy_agent_engine.py --verify-only $EngineResourceName
    python -c "import httpx; r = httpx.get('https://prometheus-chief-of-staff-135010851380.us-central1.run.app/health'); print('Cloud Run Health:', r.status_code, r.json())"
    exit 0
}

# 1. Vertex AI Agent Engine
Write-Host "1. Deploying Multi-Agent Fleet to Vertex AI Agent Engine..." -ForegroundColor Green
python deploy_agent_engine.py --project $ProjectId --location $Region

# 2. Cloud Run Service
Write-Host "2. Deploying FastAPI & MCP Platform to Google Cloud Run..." -ForegroundColor Green
gcloud run deploy prometheus-chief-of-staff --source . --region=$Region --allow-unauthenticated --port=8080 --set-env-vars="USE_VERTEX_AI=true,GCP_PROJECT_ID=$ProjectId,GCP_LOCATION=$Region,AGENT_ENGINE_APP_ID=$EngineResourceName,ENVIRONMENT=production,MCP_ENABLED=true" --quiet

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " ✨ Prometheus Google Cloud Deployment Complete & Operational!" -ForegroundColor Green
Write-Host " 🌐 Cloud Run URL: https://prometheus-chief-of-staff-135010851380.us-central1.run.app/dashboard"
Write-Host "==============================================================================" -ForegroundColor Cyan
