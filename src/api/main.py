"""Clarity CX — FastAPI REST API"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = FastAPI(
    title="Clarity CX API",
    description="AI-Powered Call Center Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ──────────────────────────────────────────────
class AnalyzeTextRequest(BaseModel):
    transcript: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"


class HealthResponse(BaseModel):
    status: str
    version: str
    agents: List[str]
    tools: int


# ─── Routes ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": "Clarity CX API", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        agents=["IntakeAgent", "TranscriptionAgent", "SummarizationAgent",
                "QualityScoringAgent", "RoutingAgent"],
        tools=7,
    )


@app.post("/api/v1/analyze/text", tags=["Analysis"])
async def analyze_text(request: AnalyzeTextRequest):
    """Analyze a text transcript through the full pipeline"""
    try:
        from src.orchestration.graph import analyze_call

        result = await analyze_call(
            input_text=request.transcript,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
        )

        report = result.get("final_report", {})
        return {
            "status": "success",
            "report": report,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze/audio", tags=["Analysis"])
async def analyze_audio(
    file: UploadFile = File(...),
    llm_provider: str = Form("openai"),
    llm_model: str = Form("gpt-4o"),
):
    """Analyze an audio file through the full pipeline (transcription + analysis)"""
    # Validate file type
    allowed = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}. Use: {', '.join(allowed)}")

    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        from src.orchestration.graph import analyze_call

        result = await analyze_call(
            input_path=tmp_path,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        report = result.get("final_report", {})
        return {
            "status": "success",
            "report": report,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/api/v1/history", tags=["History"])
async def get_history(limit: int = 50):
    """Get recent call analysis history"""
    try:
        from src.database import get_db
        db = get_db()
        records = db.get_call_history(limit=limit)
        return {"status": "success", "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/dashboard", tags=["Dashboard"])
async def get_dashboard():
    """Get dashboard statistics"""
    try:
        from src.database import get_db
        db = get_db()
        stats = db.get_dashboard_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tools", tags=["MCP"])
async def list_tools():
    """List available MCP tools"""
    from src.mcp import MCP_TOOLS
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
            }
            for t in MCP_TOOLS
        ]
    }


@app.get("/api/v1/samples", tags=["Samples"])
async def get_samples():
    """Get sample transcripts"""
    samples_path = Path(__file__).parent.parent.parent / "data" / "sample_transcripts" / "samples.json"
    if samples_path.exists():
        with open(samples_path) as f:
            return {"samples": json.load(f)}
    return {"samples": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
