# Clarity CX — Google Cloud Deployment Guide

> Deploy Clarity CX to Google Cloud Run in under 10 minutes.
> Cloud Build handles everything remotely.

---

## Prerequisites

| Requirement | Check |
|------------|-------|
| Google Cloud account | [console.cloud.google.com](https://console.cloud.google.com) |
| `gcloud` CLI installed | `gcloud --version` |
| API keys ready | `GOOGLE_API_KEY` minimum |

---

## Step 1: GCP Project Setup

```bash
# Login to GCP
gcloud auth login

# Create or select a project
gcloud projects create clarity-cx-app --name="Clarity CX"
gcloud config set project clarity-cx-app

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

---

## Step 2: Deploy to Cloud Run (Source-Based)

This uses Google Cloud Build to build and containerize the app remotely — nothing extra to install locally.

```bash
# From the project root
cd /path/to/clarity-cx

# Deploy in one command
gcloud run deploy clarity-cx \
    --source . \
    --region us-central1 \
    --port 8501 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=your-key-here" \
    --set-env-vars "DATABASE_PATH=/tmp/clarity_cx.db" \
    --set-env-vars "PHOENIX_ENABLED=false"
```

> **⚠️ Important:** Replace `your-key-here` with your actual API key. For production, use Secret Manager (see Step 4).

On first run, `gcloud` will prompt you to create an **Artifact Registry** repository — accept the defaults.

---

## Step 3: Verify Deployment

```bash
# Get the deployed URL
gcloud run services describe clarity-cx \
    --region us-central1 \
    --format='value(status.url)'
```

Open the URL in your browser. You should see the Clarity CX dashboard with **20 pre-loaded sample calls** — the app auto-seeds the database on first launch when it detects an empty DB.

> **Note:** Since Cloud Run uses ephemeral `/tmp` storage, the database reseeds automatically each time the container cold-starts. For persistent data across restarts, consider Cloud SQL.

### Check Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clarity-cx" \
    --limit 50 --format="table(timestamp,textPayload)"
```

Or view in the browser: [Cloud Run Logs Console](https://console.cloud.google.com/run/detail/us-central1/clarity-cx/logs?project=clarity-cx-app)

---

## Step 4: Secure API Keys with Secret Manager (Recommended)

```bash
# Create secrets
echo -n "your-google-api-key" | \
    gcloud secrets create GOOGLE_API_KEY --data-file=-

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Redeploy with secrets instead of plain env vars
gcloud run deploy clarity-cx \
    --source . \
    --region us-central1 \
    --port 8501 \
    --update-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
```

---

## Updating the Deployment

Just re-run the deploy command — Cloud Build rebuilds automatically:

```bash
gcloud run deploy clarity-cx \
    --source . \
    --region us-central1 \
    --port 8501
```

---

## Useful Commands

```bash
# Check which account is logged in
gcloud auth list

# Check which project is active
gcloud config get-value project

# List all your projects
gcloud projects list

# Fix quota project warning
gcloud auth application-default set-quota-project clarity-cx-app
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Permission denied` on deploy | Run `gcloud auth login` and ensure billing is enabled |
| App crashes on startup | Check logs in [Cloud Run Console](https://console.cloud.google.com/run/detail/us-central1/clarity-cx/logs?project=clarity-cx-app) |
| API key not found | Verify env vars: `gcloud run services describe clarity-cx --region us-central1` |
| Slow cold starts | Set `--min-instances 1` to keep one instance warm |
| Database resets | Expected — Cloud Run uses ephemeral `/tmp`. Use Cloud SQL for persistence |
| Quota project warning | Run `gcloud auth application-default set-quota-project clarity-cx-app` |

---

## Architecture on Cloud Run

```
┌─────────────┐     ┌─────────────────────────────────┐
│   Browser   │────▶│  Google Cloud Run                │
│  (Desktop/  │     │  ┌──────────────────────────┐    │
│   Mobile)   │     │  │  Streamlit (Port 8501)   │    │
└─────────────┘     │  │  ┌────────────────────┐  │    │
                    │  │  │  LangGraph Pipeline │  │    │
                    │  │  │  5 Agents           │  │    │
                    │  │  └────────┬───────────┘  │    │
                    │  │           │               │    │
                    │  │  ┌────────▼───────────┐  │    │
                    │  │  │  SQLite (/tmp)      │  │    │
                    │  │  └────────────────────┘  │    │
                    │  └──────────────────────────┘    │
                    └──────────┬───────────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  External AI Services         │
                    │  • Gemini 2.0 Flash           │
                    │  • OpenAI GPT-4o (optional)   │
                    │  • Anthropic Claude (optional) │
                    └──────────────────────────────┘
```
