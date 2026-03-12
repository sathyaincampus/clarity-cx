# 📞 Clarity CX

### AI-Powered Call Center Intelligence Platform

> Transform call center recordings and transcripts into structured summaries, quality scores, and actionable insights.

![Backend Architecture](docs/images/backend_architecture.png)

---

## 🚀 Quick Start

```bash
# 1. Clone & install
git clone <repo-url> clarity-cx && cd clarity-cx
uv venv && source venv/bin/activate
uv pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env → add GOOGLE_API_KEY (minimum)

# 3. Seed sample data (optional)
python scripts/seed_database.py

# 4. Run
streamlit run src/ui/app.py
```

📖 **See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the full setup guide.**

---

## 🤖 Five Specialist Agents

| Agent | Role | Key Feature |
|-------|------|-------------|
| 📥 **Intake** | Input validation & metadata extraction | Auto-detects agent names |
| 🎙️ **Transcription** | Audio→Text conversion | Gemini 2.0 Flash + Whisper fallback |
| 📝 **Summarization** | LLM-powered call summaries | Key points, action items, intent |
| 📊 **Quality Scoring** | 5-dimension quality assessment | Empathy, Resolution, Professionalism, Compliance, Efficiency |
| 🔀 **Routing** | Report assembly & error recovery | Graceful degradation for partial failures |

All orchestrated via **LangGraph** state machine with parallel processing.

---

## 🖥️ Five-Tab UI

| Tab | Purpose |
|-----|---------|
| 📊 **Dashboard** | Live metrics, score distribution, recent calls with filter/sort |
| 🎙️ **Analyze Call** | Upload audio, paste transcript, or select from 20 samples |
| 📋 **Call History** | Browse all analyzed calls with search and score filtering |
| 📈 **Trends** | Quality trends over time, dimension averages, top topics |
| ⚙️ **Settings** | LLM provider and model configuration |

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| Frontend | Streamlit, Plotly, Custom CSS |
| Backend | FastAPI, LangGraph, MCP (7 tools) |
| LLMs | Gemini 2.0 Flash, GPT-4o, Claude |
| Transcription | Gemini 2.0 Flash (primary), Whisper (fallback) |
| Database | SQLite |
| Observability | Arize Phoenix + OpenTelemetry |
| Evaluations | Phoenix LLM-as-Judge (7 metrics) |
| Testing | pytest (26 tests) |
| Deployment | Google Cloud Run, Docker |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](docs/QUICKSTART.md) | 5-minute setup guide |
| [Architecture](docs/ARCHITECTURE.md) | System architecture with diagrams |
| [Code Walkthrough](docs/CODE_WALKTHROUGH.md) | Every module explained |
| [Deployment](docs/DEPLOYMENT.md) | Google Cloud Run guide |
| [Scoring](docs/SCORING.md) | Rubric assessment with evidence |
| [Technical Spec](SPEC_DEV.md) | Full technical specification |
| [Roadmap](ROADMAP.md) | Development timeline |

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
# 26 tests — agents, models, PII detection, compliance, database, samples
```

---

## 📦 Deployment

```bash
# Build & deploy to Google Cloud Run
docker build -t clarity-cx .
gcloud run deploy clarity-cx --image clarity-cx --port 8501
```

📖 **See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full deployment guide.**

---

## 📄 License

MIT
