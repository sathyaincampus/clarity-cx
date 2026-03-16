# Clarity CX — Capstone Submission Guide

> **Project:** Clarity CX — AI-Powered Call Center Intelligence Platform
> **Author:** Sathya Narayanan Srinivasan
> **Submission Date:** March 15, 2026

---

## Quick Links

| Item | Link / Location |
|------|----------------|
| **Git Repository** | [github.com/sathyaincampus/clarity-cx](https://github.com/sathyaincampus/clarity-cx) |
| **Git Branch** | `main` |
| **Live App (Cloud Run)** | [clarity-cx-6p5vb63myq-uc.a.run.app](https://clarity-cx-6p5vb63myq-uc.a.run.app) |
| **README** | [`README.md`](./README.md) |
| **Architecture** | [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) |
| **Technical Spec** | [`SPEC_DEV.md`](./SPEC_DEV.md) |
| **Roadmap** | [`ROADMAP.md`](./ROADMAP.md) |
| **Code Walkthrough** | [`docs/CODE_WALKTHROUGH.md`](./docs/CODE_WALKTHROUGH.md) |
| **Deployment Guide** | [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) |
| **Presentation** | [`docs/presentation.html`](./docs/presentation.html) |
| **Problem Statement** | [`Call Center Summarization App_ Agentic AI Problem Statement.pdf`](./Call%20Center%20Summarization%20App_%20Agentic%20AI%20Problem%20Statement.pdf) |

---

## How to Run Locally

```bash
git clone git@github.com:sathyaincampus/clarity-cx.git
cd clarity-cx
uv venv && source venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # Add your GOOGLE_API_KEY (minimum)
streamlit run src/ui/app.py
# Open http://localhost:8501
```

> The app **auto-seeds 20 sample calls** into the database on first launch.

---

## Try It Out — Evaluator Quick Test

### Option 1: Paste a Transcript
1. Open app → **Analyze Call** tab → **📝 Paste Transcript**
2. Copy contents of [`data/sample_transcripts/demo_transcript.txt`](./data/sample_transcripts/demo_transcript.txt)
3. Click **🚀 Analyze Call**

### Option 2: Upload Audio
1. Open app → **Analyze Call** tab → **📤 Upload Audio**
2. Upload [`data/sample_audio/demo_call.mp3`](./data/sample_audio/demo_call.mp3)
3. Click **🚀 Analyze Call** — Gemini transcribes and runs full pipeline

### Option 3: Use Pre-Loaded Samples
1. Open app → **Analyze Call** tab → **📁 Sample Transcript**
2. Choose any of 20 scenarios → **🚀 Analyze Call**

---

## Rubric Alignment — Where to Find Everything

### 1. Functionality (35%)

#### Multi-Agent System — 5 Specialized Agents

| Agent | File | Purpose |
|-------|------|---------|
| 📥 Intake | [`src/agents/intake_agent.py`](./src/agents/intake_agent.py) | Input validation, metadata extraction, agent name detection |
| 🎙️ Transcription | [`src/agents/transcription_agent.py`](./src/agents/transcription_agent.py) | Audio→Text via Gemini 2.0 Flash + Whisper fallback |
| 📝 Summarization | [`src/agents/summarization_agent.py`](./src/agents/summarization_agent.py) | LLM-powered structured summaries (Pydantic output) |
| 📊 Quality Scoring | [`src/agents/quality_scoring_agent.py`](./src/agents/quality_scoring_agent.py) | 5-dimension quality assessment with justifications |
| 🔀 Routing | [`src/agents/routing_agent.py`](./src/agents/routing_agent.py) | Report assembly, error recovery, graceful degradation |
| — Base class | [`src/agents/base_agent.py`](./src/agents/base_agent.py) | `BaseAgent` ABC with `safe_process()` error wrapping |

#### LangGraph Orchestration (State Machine)

| File | Purpose |
|------|---------|
| [`src/orchestration/state.py`](./src/orchestration/state.py) | `ClarityState` TypedDict with pipeline fields |
| [`src/orchestration/graph.py`](./src/orchestration/graph.py) | `StateGraph`: intake → transcribe → summarize ∥ score → route |

#### MCP Tool Integration (7 Tools)

| File | Tools |
|------|-------|
| [`src/mcp/tools/analysis_tools.py`](./src/mcp/tools/analysis_tools.py) | Sentiment analysis, PII detection, compliance checker, text formatter |
| [`src/mcp/tools/audio_tools.py`](./src/mcp/tools/audio_tools.py) | Audio pre-processing |
| [`src/mcp/tools/qa_tools.py`](./src/mcp/tools/qa_tools.py) | Transcript parser, report generator |

#### LLM Gateway (Multi-Provider)

| File | Purpose |
|------|---------|
| [`src/llm/adapter.py`](./src/llm/adapter.py) | Unified adapter for OpenAI, Anthropic, Google Gemini |

#### Database Persistence

| File | Purpose |
|------|---------|
| [`src/database.py`](./src/database.py) | SQLite — 4 tables (calls, transcripts, analyses, quality_scores) |
| [`scripts/seed_database.py`](./scripts/seed_database.py) | 20 pre-computed sample analyses for demo seeding |

#### Observability & Evaluations

| File | Purpose |
|------|---------|
| [`src/observability.py`](./src/observability.py) | Arize Phoenix + OpenTelemetry tracing (auto-connects to running Phoenix) |
| [`src/evals.py`](./src/evals.py) | Inline LLM-as-Judge — 5 eval metrics run automatically after each analysis |
| [`scripts/run_evals.py`](./scripts/run_evals.py) | Batch evaluations on existing traces (optional, for manual runs) |

**Evaluations run automatically** when `PHOENIX_ENABLED=true`. After each call analysis, Gemini Flash runs 5 LLM-as-judge metrics (Relevance, QA Quality, Toxicity, Hallucination, Summarization) in a background thread and logs results to Phoenix.

```bash
# Terminal 1: Start Phoenix
python -c "import phoenix as px; px.launch_app(); input('Phoenix running...')"
# Terminal 2: Run app with tracing + auto-evals
PHOENIX_ENABLED=true streamlit run src/ui/app.py
# → Analyze a call → evals run automatically → view at http://localhost:6006
```

#### Testing — 26 Tests

| Test Area | File |
|-----------|------|
| All tests | [`tests/test_clarity.py`](./tests/test_clarity.py) |

Covers: intake validation, transcription skip logic, base agent error handling, quality score bands, summarization models, PII detection (SSN, credit card, email), compliance checking, orchestration state, database CRUD, sample data integrity.

```bash
pytest tests/ -v   # 26 passed
```

---

### 2. Agent Design (25%)

| Criterion | Evidence |
|-----------|----------|
| **Multi-agent system** | 5 agents in [`src/agents/`](./src/agents/) |
| **LangGraph orchestration** | [`graph.py`](./src/orchestration/graph.py) — StateGraph with conditional edges |
| **MCP tools** | 7 tools in [`src/mcp/tools/`](./src/mcp/tools/) |
| **Multi-provider LLM** | 3 providers via [`adapter.py`](./src/llm/adapter.py) |
| **Pydantic structured output** | `CallSummary`, `QualityScores`, `ScoreBand` models |
| **Parallel processing** | Summarization + Quality Scoring run in parallel |
| **Error recovery** | Routing agent produces partial reports on upstream failures |

---

### 3. User Experience (15%)

#### UI — 5 Tabs (Streamlit + Custom CSS)

| Tab | Key Features |
|-----|-------------|
| 📊 **Dashboard** | Metrics, score distribution, resolution pie chart, drilldown with radar charts, agent leaderboard |
| 🎙️ **Analyze Call** | Audio upload (Gemini), text paste with clear button, 20 sample transcripts, LLM provider config |
| 📋 **Call History** | Search, filter by score band/status, sort, expandable details, **CSV export** |
| 📈 **Trends** | Quality score trends by date, dimension averages, top topics frequency |
| ⚙️ **Settings** | LLM provider/model selection, API key status |

---

### 4. Routing & Fallback (15%)

| Feature | Evidence |
|---------|----------|
| **Transcription fallback** | Gemini 2.0 Flash → Whisper automatic failover |
| **Multi-provider LLM** | Switch between Google, OpenAI, Anthropic in UI |
| **Error recovery** | Routing agent handles partial failures gracefully |
| **Input validation** | Type checking, size limits, format detection |

---

### 5. Documentation (10%)

| Document | Purpose |
|----------|---------|
| [`README.md`](./README.md) | Overview, quick start, evaluator guide |
| [`SPEC_DEV.md`](./SPEC_DEV.md) | Full technical specification (1170 lines) |
| [`ROADMAP.md`](./ROADMAP.md) | Development timeline |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | Architecture diagrams |
| [`docs/CODE_WALKTHROUGH.md`](./docs/CODE_WALKTHROUGH.md) | Every module explained |
| [`docs/QUICKSTART.md`](./docs/QUICKSTART.md) | 5-minute setup guide |
| [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) | Google Cloud Run deployment |
| [`docs/presentation.html`](./docs/presentation.html) | Presentation slides |

---

## Project Structure

```
clarity-cx/
├── src/
│   ├── config.py                     # Configuration management
│   ├── database.py                   # SQLite persistence (4 tables)
│   ├── observability.py              # Arize Phoenix + OpenTelemetry (auto-connects)
│   ├── agents/                       # 5 specialized agents
│   │   ├── base_agent.py             #   BaseAgent ABC
│   │   ├── intake_agent.py           #   📥 Input validation
│   │   ├── transcription_agent.py    #   🎙️ Audio→Text (Gemini/Whisper)
│   │   ├── summarization_agent.py    #   📝 LLM summarization
│   │   ├── quality_scoring_agent.py  #   📊 5-dimension scoring
│   │   └── routing_agent.py          #   🔀 Report assembly
│   ├── orchestration/                # LangGraph pipeline
│   │   ├── state.py                  #   ClarityState TypedDict
│   │   └── graph.py                  #   StateGraph workflow
│   ├── llm/
│   │   └── adapter.py                # Multi-provider LLM adapter
│   ├── mcp/tools/                    # 7 MCP tools
│   │   ├── analysis_tools.py         #   Sentiment, PII, compliance
│   │   ├── audio_tools.py            #   Audio processing
│   │   └── qa_tools.py               #   QA and report tools
│   ├── api/
│   │   └── main.py                   # FastAPI REST API
│   └── ui/
│       └── app.py                    # Streamlit UI (5 tabs)
├── data/
│   ├── sample_transcripts/
│   │   ├── samples.json              # 20 e-commerce call transcripts
│   │   └── demo_transcript.txt       # Evaluator test transcript
│   └── sample_audio/
│       └── demo_call.mp3             # Evaluator test audio
├── scripts/
│   ├── seed_database.py              # DB seed script (auto-runs on startup)
│   ├── run_evals.py                  # Phoenix LLM-as-Judge evaluations (5 metrics)
│   └── generate_audio.py             # TTS audio generation
├── tests/
│   └── test_clarity.py               # 26 pytest tests
├── docs/                             # 9 documentation files
├── .env.example                      # Environment template
├── Dockerfile                        # Container definition
├── .gcloudignore                     # Cloud Build exclusions
├── pyproject.toml                    # Project metadata
├── requirements.txt                  # Dependencies
├── SPEC_DEV.md                       # Technical specification
└── ROADMAP.md                        # Development roadmap
```

---

## Technology Stack

| Category | Technology |
|----------|-----------|
| **Frontend** | Streamlit, Plotly, Custom CSS (dark mode) |
| **Backend** | FastAPI, LangGraph, MCP |
| **LLM Gateway** | Multi-provider: OpenAI, Anthropic, Google Gemini |
| **Agents** | 5 specialists with LangGraph state machine |
| **Transcription** | Gemini 2.0 Flash (primary), OpenAI Whisper (fallback) |
| **Database** | SQLite (4 tables, auto-seeding) |
| **Observability** | Arize Phoenix + OpenTelemetry |
| **Evaluations** | Phoenix LLM-as-Judge (5 metrics: Relevance, QA, Toxicity, Hallucination, Summarization) |
| **Testing** | pytest (26 tests) |
| **Deployment** | Google Cloud Run (source deploy, Secret Manager) |

---

## Key Metrics

| Metric | Count |
|--------|-------|
| Agents | 5 |
| MCP Tools | 7 |
| UI Tabs | 5 |
| Sample Transcripts | 20 |
| Test Cases | 26 |
| LLM Providers | 3 (OpenAI, Anthropic, Google) |
| Quality Dimensions | 5 (Empathy, Resolution, Professionalism, Compliance, Efficiency) |
| Evaluation Metrics | 5 |
| Documentation Files | 9 |
