# 📞 Clarity CX — AI-Powered Call Center Intelligence

> **Codename:** "Contact Center Brain"  
> *Transform raw call data into structured summaries and QA insights*

## 🎯 What is Clarity CX?

Clarity CX is a **multi-agent AI system** that converts call center recordings and transcripts into:
- **Structured summaries** with key points and action items
- **Quality scores** across 5 dimensions (empathy, resolution, professionalism, compliance, efficiency)
- **PII detection** and compliance monitoring
- **Sentiment analysis** throughout the call trajectory
- **Actionable insights** for supervisors and QA managers

## 🏗️ Architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Streamlit | Upload, visualize, interact |
| API | FastAPI | REST endpoints |
| Orchestration | LangGraph | Pipeline state machine |
| Agents | 5 Specialists | Intake → Transcribe → Summarize → Score → Route |
| LLMs | Gemini 2.0 Flash / GPT-4o / Claude | Multi-provider with fallback |
| Tools | MCP (7 tools) | Whisper, Sentiment, PII, Compliance |
| Observability | Arize Phoenix | Tracing, eval workbench (localhost:6006) |
| Deployment | Docker + Cloud Run | Containerized |

## 🤖 Agent Roster

| Agent | Role | Key Output |
|-------|------|------------|
| 📥 **Call Intake** | Validate input, extract metadata | Format, duration, caller ID |
| 🎙️ **Transcription** | Whisper STT, speaker diarization | Timestamped transcript |
| 📝 **Summarization** | Key points, action items | Structured summary (Pydantic) |
| 📊 **Quality Scoring** | 5-dimension rubric evaluation | Scores + justifications |
| 🔀 **Routing** | Fallback logic, error recovery | Final assembled report |

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd clarity-cx

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
streamlit run src/ui/app.py
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [SPEC_DEV.md](./SPEC_DEV.md) | Technical Specification (14 sections) |
| [ROADMAP.md](./ROADMAP.md) | Execution Roadmap (5 phases) |
| [Architecture](./docs/ARCHITECTURE.md) | Architecture Diagrams |
| [Presentation](./docs/presentation.html) | Capstone Slide Deck |

## 📊 Evaluation Criteria

| Category | Weight | Target |
|----------|--------|--------|
| Functionality | 35% | 95% |
| Agent Design | 25% | 95% |
| User Experience | 15% | 90% |
| Routing & Fallback | 15% | 90% |
| Documentation | 10% | 95% |

## 📝 License

This project is part of the **Applied Agentic AI for SWEs** capstone program.
