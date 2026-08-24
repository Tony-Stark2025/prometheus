#!/usr/bin/env bash
# ==============================================================================
# Prometheus: 1-Click Deployment to Google Cloud Run
# For All Things Agentic Hackathon: The Fortified Enterprise Fleet Track
# ==============================================================================

set -euo pipefail

# Configuration
SERVICE_NAME="prometheus-chief-of-staff"
REGION="${GCP_REGION:-us-central1}"
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"

echo "=============================================================================="
echo " 🚀 Deploying Prometheus Multi-Agent Fleet to Google Cloud Run"
echo "=============================================================================="

if [ -z "$PROJECT_ID" ]; then
    echo "⚠️ Error: GCP Project ID not set. Please run 'gcloud config set project <PROJECT_ID>'"
    exit 1
fi

echo "Project ID : $PROJECT_ID"
echo "Region     : $REGION"
echo "Service    : $SERVICE_NAME"
echo ""

# Enable required Google Cloud APIs
echo "1. Enabling Google Cloud APIs (Cloud Run, Artifact Registry)..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com --project="$PROJECT_ID"

# Build and Deploy to Cloud Run
echo "2. Building container and deploying to Cloud Run (scales to zero when idle)..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3 \
    --memory 1Gi \
    --cpu 1 \
    --port 8000 \
    --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO,MCP_ENABLED=true"

# Fetch Service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')

echo ""
echo "=============================================================================="
echo " ✨ Prometheus Successfully Deployed to Google Cloud Run!"
echo " 🔗 Service URL  : $SERVICE_URL"
echo " 📚 OpenAPI Docs : $SERVICE_URL/docs"
echo " 🏥 Healthcheck  : $SERVICE_URL/healthz"
echo " 📡 MCP Stream   : $SERVICE_URL/mcp/sse"
echo "=============================================================================="
