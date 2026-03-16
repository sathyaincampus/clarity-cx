# Clarity CX — Architecture Documentation

> **Version:** 2.0.0
> **Last Updated:** March 9, 2026

---

## Backend Architecture

![Backend Architecture](images/backend_architecture.png)

The Clarity CX backend follows a layered pipeline architecture with clear separation of concerns.

### Layers

| Layer | Components | Purpose |
|-------|------------|------------|
| **Input Layer** | Audio Upload, Transcript Upload, Text Paste | Entry points for call data |
| **Orchestration** | LangGraph StateGraph, Pipeline State Machine | Sequential + parallel agent execution |
| **Agent Layer** | 5 specialized agents | Process, analyze, and score calls |
| **AI Services** | Gemini 2.0 Flash, GPT-4o, Claude | Multi-provider LLM support |
| **MCP Tools** | 7 tools: Sentiment, PII, Compliance, etc. | Modular tool integrations |
| **Storage** | SQLite (`clarity_cx.db`) | Call records, analyses, quality scores |
| **Observability** | Arize Phoenix + OpenTelemetry | Tracing and LLM evaluations |
| **API Gateway** | FastAPI (Port 8000) | REST endpoints for external access |

---

## Frontend Architecture

![Frontend Architecture](images/frontend_architecture.png)

The Clarity CX frontend is built with Streamlit for rapid development and responsive design.

### Layers

| Layer | Components | Purpose |
|-------|------------|------------|
| **User Layer** | Supervisors, QA Managers, Analysts | Cross-platform browser access |
| **Pages/Tabs** | Dashboard, Analyze, History, Trends, Settings | 5-tab navigation |
| **Components** | Score Cards, Plotly Charts, Transcript Viewer | Reusable UI elements |
| **Features** | Audio Transcription, Quality Scoring, PII Detection | Core capabilities |
| **Data Layer** | SQLite queries, Session State, LangGraph calls | Backend communication |

---

## Pipeline Architecture

```mermaid
flowchart TB
    subgraph Input["📁 INPUT LAYER"]
        Audio["🎙️ Audio Files<br/>(WAV/MP3/FLAC)"]
        JSON["📄 JSON Transcripts"]
        Text["📝 Plain Text"]
    end

    subgraph Validation["📥 VALIDATION"]
        Intake["Call Intake Agent<br/>Format Detection<br/>Metadata + Agent Name Extraction"]
    end

    subgraph Transcription["🎙️ TRANSCRIPTION"]
        STT["Transcription Agent<br/>Gemini 2.0 Flash (primary)<br/>Whisper API (fallback)"]
    end

    subgraph Analysis["🧠 PARALLEL ANALYSIS"]
        Summary["📝 Summarization Agent<br/>Key Points + Action Items"]
        Quality["📊 Quality Scoring Agent<br/>5-Dimension Rubric"]
    end

    subgraph Control["🔀 CONTROL & OUTPUT"]
        Router["Routing Agent<br/>Report Assembly + Error Recovery"]
        Report["📋 Final Report<br/>Summary + Scores + Flags"]
    end

    Input --> Validation
    Validation -->|Audio| Transcription
    Validation -->|Text/JSON| Analysis
    Transcription --> Analysis
    Analysis --> Control
```

---

## Data Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    participant U as Supervisor
    participant UI as Streamlit
    participant LG as LangGraph
    participant IA as Intake Agent
    participant TA as Transcription Agent
    participant SA as Summarization Agent
    participant QA as Quality Scoring Agent
    participant RA as Routing Agent
    participant LLM as Gemini 2.0 Flash
    participant DB as SQLite

    U->>UI: Upload audio / paste transcript
    UI->>LG: analyze_call(input, provider, model)

    LG->>IA: Validate input
    IA-->>LG: Metadata + agent_name extracted

    alt Audio Input
        LG->>TA: Transcribe audio
        TA->>LLM: Send audio to Gemini
        LLM-->>TA: Transcript + speakers + timestamps
        TA-->>LG: Structured transcript
    end

    par Parallel Analysis
        LG->>SA: Generate summary
        SA->>LLM: Summarize transcript
        LLM-->>SA: Summary, key points, intent, topics
    and
        LG->>QA: Score quality
        QA->>LLM: 5-dimension scoring rubric
        LLM-->>QA: Scores + justifications + flags
    end

    LG->>RA: Assemble report
    RA-->>UI: Final report (JSON)
    UI->>DB: save_analysis(report)
    DB-->>UI: call_id
    UI->>UI: st.rerun() → Dashboard updates
    UI-->>U: Display report + updated dashboard
```

---

## Agent Interaction Diagram

```mermaid
flowchart LR
    subgraph Pipeline["Call Analysis Pipeline"]
        direction LR
        I["📥 Intake"] --> T["🎙️ Transcribe"]
        T --> S["📝 Summarize"]
        T --> Q["📊 Score"]
        S --> R["🔀 Route"]
        Q --> R
    end

    subgraph Tools["MCP Tools (7)"]
        ST["Sentiment"]
        PII["PII Detect"]
        CC["Compliance"]
        TF["Text Format"]
        AP["Audio Process"]
        TP["Transcript Parse"]
        RG["Report Gen"]
    end

    subgraph LLMs["LLM Providers"]
        G["Google Gemini"]
        O["OpenAI GPT"]
        A["Anthropic Claude"]
    end

    T -.-> AP
    Q -.-> ST
    Q -.-> PII
    Q -.-> CC
    R -.-> TF
    R -.-> RG
    S --> G
    Q --> G
```

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Streamlit, Plotly, Custom CSS |
| **Backend** | FastAPI, LangGraph, MCP |
| **Primary LLM** | Gemini 2.0 Flash (transcription + analysis) |
| **Additional LLMs** | GPT-4o, GPT-4o-mini, Claude Sonnet, Claude Haiku |
| **Agents** | 5 specialists (Intake, Transcription, Summarization, Quality Scoring, Routing) |
| **Transcription** | Gemini 2.0 Flash (primary), OpenAI Whisper (fallback) |
| **MCP Tools** | 7 tools (Sentiment, PII, Compliance, Format, Audio, Parse, Report) |
| **Database** | SQLite (call records, analyses, quality scores) |
| **Structured Output** | Pydantic v2 |
| **Observability** | Arize Phoenix + OpenTelemetry |
| **Evaluations** | Phoenix LLM-as-Judge (5 metrics) |
| **Testing** | pytest (26 tests) |
| **Deployment** | Google Cloud Run, Docker |

---

*See [CODE_WALKTHROUGH.md](./CODE_WALKTHROUGH.md) for detailed module documentation.*
*See [DEPLOYMENT.md](./DEPLOYMENT.md) for cloud deployment instructions.*
