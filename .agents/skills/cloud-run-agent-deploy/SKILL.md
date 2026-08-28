---
name: cloud-run-agent-deploy
description: Fast, reliable packaging, deployment, URL resolution, and logging for FastAPI/Python agent apps on Google Cloud Run.
---

# Google Cloud Run Agent Deployment Guide

## 1. Fast Non-Interactive Deployment
Deploy source directly to Cloud Run using an environment variables YAML file to avoid Windows CLI escaping issues:

```powershell
gcloud run deploy <SERVICE_NAME> --source . --region=us-central1 --allow-unauthenticated --port=8080 --env-vars-file=env_cloud_run.yaml --quiet
```

## 2. Resolving the True Canonical URL
Cloud Run generates deterministic URLs. Never rely on the numeric project URL if the load balancer uses the hash domain:

```powershell
# Get canonical public URL
gcloud run services describe <SERVICE_NAME> --region=us-central1 --format="value(status.url)"
```

## 3. Viewing Logs without gcloud beta
Avoid gcloud beta run services logs which can prompt for interactive component installation on Windows:

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=<SERVICE_NAME>" --limit=25 --format="value(textPayload)"
```

## 4. Monitoring Cloud Build Progress
When gcloud run deploy --source . sends a build to Cloud Build, check the latest build status:

```powershell
gcloud builds list --region=us-central1 --limit=1
```
