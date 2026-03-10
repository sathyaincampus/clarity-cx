# Clarity CX — Architecture Documentation

> **Version:** 1.0.0  
> **Last Updated:** February 22, 2026

---

## Backend Architecture

The Clarity CX backend follows a layered pipeline architecture with clear separation of concerns.

### Layers

| Layer | Components | Purpose |
|-------|------------|---------|
| **Input Layer** | Audio Upload, Transcript Upload, Text Paste | Entry points for call data |
| **API Gateway** | FastAPI (Port 8000) | REST endpoints, file handling |
| **Orchestration** | LangGraph, State Machine, MCP Client | Pipeline orchestration, tool coordination |
| **Agent Layer** | 5 specialized agents | Sequential + parallel processing |
| **MCP Tools** | Whisper, Sentiment, PII Detector, Formatter | External integrations |
| **Storage** | SQLite, ChromaDB | Persistence layer |
| **Observability** | Arize Phoenix | Tracing and monitoring (localhost:6006) |
| **AI Services** | OpenAI, Anthropic, Google | Multi-provider LLM support |

---

## Pipeline Architecture

```mermaid
flowchart TB
    subgraph Input["📁 INPUT LAYER"]
        Audio["🎙️ Audio Files<br/>(WAV/MP3)"]
        JSON["📄 JSON Transcripts"]
        Text["📝 Plain Text"]
    end

    subgraph Validation["📥 VALIDATION"]
        Intake["Call Intake Agent<br/>Format Detection<br/>Metadata Extraction"]
    end

    subgraph Transcription["🎙️ TRANSCRIPTION"]
        STT["Transcription Agent<br/>Whisper API<br/>Speaker Diarization"]
    end

    subgraph Analysis["🧠 PARALLEL ANALYSIS"]
        Summary["📝 Summarization Agent<br/>Key Points + Action Items"]
        Quality["📊 Quality Scoring Agent<br/>5-Dimension Rubric"]
    end

    subgraph Control["🔀 CONTROL & OUTPUT"]
        Router["Routing Agent<br/>Fallback + Error Recovery"]
        Report["📋 Final Report<br/>Summary + Scores + Flags"]
    end

    Input --> Validation
    Validation -->|Audio| Transcription
    Validation -->|Text/JSON| Analysis
    Transcription --> Analysis
    Analysis --> Control

    classDef input fill:#3498db,stroke:#2980b9,color:white
    classDef agent fill:#2ecc71,stroke:#27ae60,color:white
    classDef output fill:#9b59b6,stroke:#8e44ad,color:white
```

---

## Frontend Architecture

The Clarity CX frontend is built with Streamlit for rapid development and responsive design.

### Layers

| Layer | Components | Purpose |
|-------|------------|---------|
| **User Layer** | Desktop, Mobile browsers | Cross-platform access |
| **Navigation** | Streamlit Tabs | Tab-based 5-section layout |
| **Pages** | Dashboard, Analyze, History, Trends, Settings | Feature screens |
| **Components** | Score Cards, Charts, Transcript Viewer | Reusable UI elements |
| **State** | Session State | User settings, analysis cache |
| **Services** | HTTP Client, File Upload | Backend communication |

---

## Data Flow

```mermaid
sequenceDiagram
    participant U as Supervisor
    participant UI as Streamlit
    participant API as FastAPI
    participant LG as LangGraph
    participant A as Agents
    participant T as MCP Tools
    participant LLM as LLM Provider
    participant DB as SQLite

    U->>UI: Upload call recording
    UI->>API: POST /api/v1/analyze
    API->>LG: Initialize pipeline state

    LG->>A: Intake Agent (validate)
    A-->>LG: Metadata extracted

    LG->>A: Transcription Agent
    A->>T: Whisper API
    T-->>A: Transcript + timestamps
    A-->>LG: Structured transcript

    par Parallel Analysis
        LG->>A: Summarization Agent
        A->>LLM: Generate summary
        LLM-->>A: Structured summary
    and
        LG->>A: Quality Scoring Agent
        A->>LLM: Score with rubric
        LLM-->>A: 5-dimension scores
    end

    LG->>A: Routing Agent (assemble)
    A-->>API: Final report
    API->>DB: Store results
    API-->>UI: Stream response
    UI-->>U: Display report
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

    subgraph Tools["MCP Tools"]
        W["Whisper API"]
        SE["Sentiment"]
        PII["PII Detect"]
        FMT["Formatter"]
    end

    subgraph LLMs["LLM Providers"]
        O["OpenAI"]
        A["Anthropic"]
        G["Google"]
    end

    T --> W
    Q --> SE
    Q --> PII
    R --> FMT
    S --> O
    Q --> O
```

---

## Technology Stack Summary

| Category | Technology |
|----------|------------|
| Frontend | Streamlit, Plotly, Custom CSS |
| Backend | FastAPI, LangGraph, MCP |
| LLMs | Gemini 2.0 Flash, GPT-4o, Claude |
| Agents | 5 specialists (Intake, Transcription, Summarization, Quality Scoring, Routing) |
| Transcription | OpenAI Whisper |
| Databases | SQLite (records), ChromaDB (vectors) |
| Structured Output | Pydantic v2 |
| Observability | Arize Phoenix |
| Evaluations | DeepEval (Relevance, Faithfulness, Hallucination) |
| Deployment | Google Cloud Run, Docker |

---

*See [SPEC_DEV.md](../SPEC_DEV.md) for complete technical specifications.*
