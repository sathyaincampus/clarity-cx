# Clarity CX — Quick Start Guide

> Get up and running in under 5 minutes.

---

## Prerequisites

| Requirement | Version | Check |
|------------|---------|-------|
| Python | 3.11+ | `python --version` |
| uv | latest | `uv --version` |
| Git | any | `git --version` |
| API Keys | At least one | Google, OpenAI, or Anthropic |

---

## 1. Clone & Install

```bash
git clone <your-repo-url> clarity-cx
cd clarity-cx

# Install dependencies with uv
uv venv
source venv/bin/activate   # macOS/Linux
uv pip install -r requirements.txt
```

> **Note:** If `chromadb` fails on Python 3.14, exclude it:
> ```bash
> grep -v chromadb requirements.txt | uv pip install -r /dev/stdin
> ```

---

## 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add at minimum one API key:

```env
# Required (at least one):
GOOGLE_API_KEY=your-gemini-key         # Recommended — used for transcription + analysis
OPENAI_API_KEY=your-openai-key         # Optional — Whisper fallback + GPT models
ANTHROPIC_API_KEY=your-anthropic-key   # Optional — Claude models

# Optional:
DATABASE_PATH=clarity_cx.db
PHOENIX_ENABLED=true
```

---

## 3. Seed the Database (Optional)

Load 20 pre-analyzed e-commerce call transcripts:

```bash
python scripts/seed_database.py
```

Expected output:
```
✅ Seeded 20 call records into clarity_cx.db
```

---

## 4. Run the Application

```bash
streamlit run src/ui/app.py
```

The app opens at **http://localhost:8501** with five tabs:

| Tab | Purpose |
|-----|---------|
| 📊 **Dashboard** | Overview metrics, score distribution, recent calls |
| 🎙️ **Analyze Call** | Upload audio, paste text, or pick a sample |
| 📋 **Call History** | Browse all analyzed calls with search & filter |
| 📈 **Trends** | Quality score trends, dimension averages, top topics |
| ⚙️ **Settings** | LLM provider/model configuration |

---

## 5. Analyze Your First Call

1. Go to the **Analyze Call** tab
2. Select **"Paste Transcript"** and paste any call transcript
3. Click **🚀 Analyze Call**
4. View the full analysis report: summary, quality scores, compliance flags
5. Check **Dashboard** and **Call History** — the call is saved automatically

### Audio Analysis

1. Select **"Upload Audio"** and upload a WAV/MP3 file
2. Gemini 2.0 Flash transcribes the audio with speaker identification
3. The full pipeline runs: Transcription → Summarization → Quality Scoring → Routing

---

## 6. Run Tests

```bash
python -m pytest tests/ -v
```

All 26 tests should pass.

---

## 7. Run the FastAPI Server (Optional)

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs at: **http://localhost:8000/docs**

---

## 8. Enable Observability & Evaluations (Optional)

```bash
# Terminal 1: Start Arize Phoenix
python -c "import phoenix as px; px.launch_app(); input('Phoenix running...')"

# Terminal 2: Run the app with tracing enabled
PHOENIX_ENABLED=true streamlit run src/ui/app.py
# → Analyze at least one call in the UI

# Terminal 3: Run LLM-as-Judge evaluations on the traces
python scripts/run_evals.py
```

Phoenix dashboard at: **http://localhost:6006** → click `clarity-cx` project → see spans and evaluation annotations

---

## Next Steps

- [Architecture Documentation](./ARCHITECTURE.md)
- [Code Walkthrough](./CODE_WALKTHROUGH.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Scoring Assessment](./SCORING.md)
