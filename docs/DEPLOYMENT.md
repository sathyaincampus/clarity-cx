# Clarity CX — Google Cloud Deployment Guide

> Deploy Clarity CX to Google Cloud Run in under 15 minutes.

---

## Prerequisites

| Requirement | Check |
|------------|-------|
| Google Cloud account | [console.cloud.google.com](https://console.cloud.google.com) |
| `gcloud` CLI installed | `gcloud --version` |
| Docker installed | `docker --version` |
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
    artifactregistry.googleapis.com

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

---

## Step 2: Configure Docker for GCP

```bash
# Configure Docker to use Google Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Create an Artifact Registry repository
gcloud artifacts repositories create clarity-cx \
    --repository-format=docker \
    --location=us-central1 \
    --description="Clarity CX container images"
```

---

## Step 3: Build & Push the Docker Image

```bash
# From the project root
cd /path/to/clarity-cx

# Build the Docker image
docker build -t clarity-cx .

# Tag for Artifact Registry
docker tag clarity-cx \
    us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest

# Push to Artifact Registry
docker push \
    us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest
```

> **Tip:** You can also use Cloud Build to build directly on GCP:
> ```bash
> gcloud builds submit --tag us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest
> ```

---

## Step 4: Deploy to Cloud Run

```bash
gcloud run deploy clarity-cx \
    --image us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest \
    --platform managed \
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

> **⚠️ Important:** Replace `your-key-here` with your actual API keys. For production, use Cloud Run Secrets instead.

---

## Step 5: Set Environment Variables (Secure Method)

For sensitive API keys, use Google Secret Manager:

```bash
# Create secrets
echo -n "your-google-api-key" | \
    gcloud secrets create GOOGLE_API_KEY --data-file=-

echo -n "your-openai-api-key" | \
    gcloud secrets create OPENAI_API_KEY --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:$(gcloud iam service-accounts list --format='value(email)' --filter='Cloud Run')" \
    --role="roles/secretmanager.secretAccessor"

# Deploy with secrets
gcloud run deploy clarity-cx \
    --image us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest \
    --update-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
    --update-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

---

## Step 6: Verify Deployment

```bash
# Get the deployed URL
gcloud run services describe clarity-cx \
    --region us-central1 \
    --format='value(status.url)'
```

Open the URL in your browser. You should see the Clarity CX dashboard.

### Seed the Database (Post-Deploy)

Since Cloud Run uses ephemeral `/tmp` storage, seed the DB on first load:

```bash
# Option 1: SSH into the container and run the seed script
gcloud run services proxy clarity-cx --region us-central1

# Option 2: The app auto-shows "No data" message with instructions
# Users can analyze calls which persist for the session
```

> **Note:** For persistent data across deployments, consider using Cloud SQL (SQLite is session-only on Cloud Run). For demo purposes, the seed script or live analysis is sufficient.

---

## Updating the Deployment

```bash
# Rebuild and push
docker build -t clarity-cx .
docker tag clarity-cx us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest
docker push us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest

# Redeploy (Cloud Run auto-detects new image)
gcloud run deploy clarity-cx \
    --image us-central1-docker.pkg.dev/clarity-cx-app/clarity-cx/clarity-cx:latest \
    --region us-central1
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Permission denied` on deploy | Run `gcloud auth login` and ensure billing is enabled |
| App crashes on startup | Check logs: `gcloud run logs read clarity-cx --region us-central1` |
| API key not found | Verify env vars: `gcloud run services describe clarity-cx --region us-central1` |
| Slow cold starts | Set `--min-instances 1` to keep one instance warm |
| Database resets | Expected on Cloud Run — use Cloud SQL for persistence |

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
