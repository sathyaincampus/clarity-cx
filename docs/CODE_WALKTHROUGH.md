# Clarity CX — Code Walkthrough

> Complete source tree guide with every module explained.

---

## Project Structure

```
clarity-cx/
├── src/                          # Application source code
│   ├── __init__.py               # Package init
│   ├── config.py                 # Configuration management (env vars, defaults)
│   ├── database.py               # SQLite persistence layer
│   ├── evals.py                  # Phoenix LLM-as-judge evaluation pipeline
│   ├── observability.py          # Arize Phoenix + OpenTelemetry integration
│   │
│   ├── agents/                   # 🤖 The Five Specialist Agents
│   │   ├── base_agent.py         # Abstract base class for all agents
│   │   ├── intake_agent.py       # Input validation & metadata extraction
│   │   ├── transcription_agent.py # Audio→Text (Gemini/Whisper)
│   │   ├── summarization_agent.py # LLM-powered call summarization
│   │   ├── quality_scoring_agent.py # 5-dimension quality assessment
│   │   └── routing_agent.py      # Report assembly & error recovery
│   │
│   ├── orchestration/            # 🔀 LangGraph Pipeline
│   │   ├── graph.py              # State machine definition & analyze_call()
│   │   └── state.py              # Pipeline state schema (TypedDict)
│   │
│   ├── llm/                      # 🧠 LLM Adapter Layer
│   │   └── adapter.py            # Unified interface for OpenAI/Anthropic/Google
│   │
│   ├── mcp/                      # 🔧 MCP Tool Integration
│   │   ├── __init__.py           # MCP client initialization
│   │   └── tools/                # 7 individual MCP tools
│   │       ├── analysis_tools.py # Sentiment, PII, compliance tools
│   │       ├── audio_tools.py    # Audio processing tools
│   │       └── qa_tools.py       # Quality assessment tools
│   │
│   ├── api/                      # 🌐 FastAPI REST API
│   │   └── main.py               # API routes and server
│   │
│   ├── eval/                     # 📊 Evaluation Framework
│   │   └── dataset_loader.py     # Test dataset management
│   │
│   └── ui/                       # 🖥️ Streamlit Frontend
│       └── app.py                # Main UI application (all tabs)
│
├── data/                         # Data files
│   └── sample_transcripts/
│       └── samples.json          # 20 e-commerce call transcripts
│
├── scripts/                      # Utility scripts
│   ├── seed_database.py          # Populate DB with sample data
│   └── generate_audio.py         # Generate sample audio via TTS
│
├── tests/                        # Test suite
│   └── test_clarity.py           # 26 pytest tests
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # Architecture documentation
│   ├── QUICKSTART.md             # Quick start guide
│   ├── CODE_WALKTHROUGH.md       # This file
│   ├── DEPLOYMENT.md             # Google Cloud deployment
│   ├── presentation.html         # Presentation slides
│   └── images/                   # Architecture diagrams
│
├── .env.example                  # Environment variable template
├── Dockerfile                    # Container definition
├── .gcloudignore                 # Cloud Build upload exclusions
├── pyproject.toml                # Project metadata & dependencies
├── requirements.txt              # Pip-compatible dependency list
├── SPEC_DEV.md                   # Full technical specification
└── ROADMAP.md                    # Development roadmap
```

---

## The Five Agents

Clarity CX uses a **sequential pipeline** of five specialist agents, orchestrated by LangGraph:

### 1. 📥 Intake Agent (`intake_agent.py`)
**Role:** Validates input and extracts metadata.

- Detects input type: audio file, JSON transcript, or plain text
- Validates file formats and size limits
- Extracts metadata: word count, speaker labels, language
- **Extracts agent name** from transcript patterns (`Sarah (Agent):`, `Agent Sarah:`, `My name is Sarah`)

### 2. 🎙️ Transcription Agent (`transcription_agent.py`)
**Role:** Converts audio to text with speaker identification.

- **Primary:** Gemini 2.0 Flash (native audio support, speaker diarization)
- **Fallback:** OpenAI Whisper (if Gemini fails or OpenAI provider selected)
- Produces timestamped segments with speaker labels
- Skips automatically for text/transcript inputs

### 3. 📝 Summarization Agent (`summarization_agent.py`)
**Role:** Generates structured call summaries using LLM.

- Produces: summary, key points, action items, customer intent
- Detects: resolution status, sentiment trajectory, topics
- Uses Pydantic models for structured output
- Supports all three LLM providers

### 4. 📊 Quality Scoring Agent (`quality_scoring_agent.py`)
**Role:** Evaluates call quality on five dimensions.

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Empathy | 25% | Active listening, acknowledgment, tone |
| Resolution | 25% | Problem-solving effectiveness |
| Professionalism | 20% | Language, courtesy, protocol adherence |
| Compliance | 15% | PII handling, script adherence, regulations |
| Efficiency | 15% | Call duration, unnecessary transfers |

- Generates: overall score (1-10), dimension scores, justifications
- Classifies into bands: 🟢 Excellent (8+), 🟡 Good (6-8), 🟠 Needs Work (4-6), 🔴 Critical (<4)
- Flags compliance issues and provides recommendations

### 5. 🔀 Routing Agent (`routing_agent.py`)
**Role:** Assembles the final report with error recovery.

- Aggregates outputs from all upstream agents
- Handles partial failures gracefully (partial reports)
- Builds visualization configs for the dashboard
- Determines final status: complete, partial, or failed

---

## Pipeline Flow (LangGraph)

```
analyze_call(input_text, llm_provider, llm_model)
    │
    ▼
┌─────────────┐
│ Intake Agent │ ← Validate input, extract metadata
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Transcription    │ ← Audio→Text (Gemini/Whisper) or skip
│ Agent            │
└──────┬───────────┘
       │
       ├─────────────────────┐
       ▼                     ▼
┌─────────────────┐  ┌───────────────────┐
│ Summarization   │  │ Quality Scoring   │  ← Run in parallel
│ Agent           │  │ Agent             │
└────────┬────────┘  └────────┬──────────┘
         │                    │
         └──────┬─────────────┘
                ▼
        ┌───────────────┐
        │ Routing Agent │ ← Assemble report, handle errors
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Final Report  │ → Save to DB → Display in UI
        └───────────────┘
```

The pipeline is defined in `src/orchestration/graph.py` using LangGraph's `StateGraph`.

---

## Database Schema (SQLite)

Four tables in `clarity_cx.db`:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `calls` | Call records | id, case_id (CX-YYYYMMDD-XXXX), order_id, agent_name, call_date |
| `transcripts` | Full text | call_id, full_text, word_count |
| `analyses` | Summaries | call_id, summary, intent, topics, resolution |
| `quality_scores` | Scores | call_id, overall + 5 dimension scores |

Methods on `Database` class:
- `save_analysis(report)` — persists a full pipeline report, auto-generates case ID (CX-YYYYMMDD-XXXX), extracts order ID from transcript via regex
- `get_call_history(limit)` — fetches recent calls with all dimension scores + transcript
- `get_call_detail(call_id)` — full data for a single call across all 4 tables
- `get_dashboard_stats()` — aggregate metrics for dashboard
- `get_trends_data()` — daily scores, dimension averages, top topics
- `get_agent_leaderboard(limit)` — agents ranked by average quality score

---

## MCP Tools (7 Tools)

| Tool | Module | Purpose |
|------|--------|---------|
| Sentiment Analyzer | `analysis_tools.py` | Detect call sentiment polarity |
| PII Detector | `analysis_tools.py` | Find SSN, credit cards, emails |
| Compliance Checker | `analysis_tools.py` | Flag script deviations |
| Text Formatter | `analysis_tools.py` | Format output reports |
| Audio Processor | `audio_tools.py` | Pre-process audio files |
| Transcript Parser | `qa_tools.py` | Parse transcript formats |
| Report Generator | `qa_tools.py` | Build structured reports |

---

## Evaluation Pipeline (`src/evals.py`)

Runs **automatically** after each call analysis when `PHOENIX_ENABLED=true`. Uses Gemini Flash as LLM-as-judge. Evaluations execute in a background thread so the UI doesn't block.

| Metric | What It Evaluates |
|--------|-------------------|
| Relevance | Summary matches transcript content |
| Hallucination | No fabricated information |
| QA Correctness | Quality scores are justified |
| Toxicity | No inappropriate language |
| Summarization | Summary quality and completeness |

For batch evaluation of existing traces: `python scripts/run_evals.py`

---

## UI Tabs (`app.py`)

| Tab | Key Features |
|-----|-------------|
| **Dashboard** | Metrics row, score distribution chart, resolution pie chart, **drilldown with radar charts**, dimension breakdowns, transcript preview, **agent leaderboard** with medals |
| **Analyze Call** | Audio upload + Gemini transcription, text paste with **clear button**, sample selection, LLM provider config, real-time pipeline status |
| **Call History** | Full history from DB, search by topic/agent, filter by score band, expandable details, **CSV export** |
| **Trends** | Quality score trend by date, dimension averages bar chart, top topics frequency chart |
| **Settings** | LLM provider selection, model config, API key status |

---

## Configuration (`config.py`)

Key environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOOGLE_API_KEY` | — | Gemini API access (primary LLM + transcription) |
| `OPENAI_API_KEY` | — | GPT models + Whisper fallback |
| `ANTHROPIC_API_KEY` | — | Claude models |
| `DATABASE_PATH` | `clarity_cx.db` | SQLite database location |
| `PHOENIX_ENABLED` | `false` | Enable Arize Phoenix tracing |
| `WHISPER_MODEL` | `whisper-1` | Whisper model name |
| `MAX_UPLOAD_SIZE_MB` | `200` | Max audio file size |
