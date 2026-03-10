"""LangGraph State Definition for Clarity CX Pipeline"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from operator import add


class ClarityState(TypedDict):
    """State definition for the Clarity CX analysis pipeline.

    This state flows through the LangGraph pipeline, accumulating
    results from each agent.
    """

    # === Input ===
    input_type: str              # 'audio', 'transcript', 'text'
    input_path: str              # File path (for audio uploads)
    input_text: str              # Raw text/JSON (for paste/upload)
    session_id: str              # Unique session identifier

    # === LLM Config ===
    llm_provider: str            # 'openai', 'anthropic', 'google'
    llm_model: str               # Model identifier

    # === Pipeline Outputs (Accumulated) ===
    agent_outputs: Annotated[List[dict], add]  # Accumulated agent results

    # === Call Metadata ===
    call_metadata: Optional[dict]  # Format, duration, file info

    # === Transcript ===
    transcript: Optional[str]              # Full text transcript
    speaker_segments: Optional[List[dict]]  # Speaker-labeled segments

    # === Analysis ===
    summary: Optional[dict]            # Structured summary (CallSummary)
    quality_scores: Optional[dict]     # Quality scores (QualityScore)

    # === Compliance ===
    pii_detected: List[str]            # PII types found
    compliance_flags: List[str]        # Compliance issues

    # === Output ===
    final_report: Optional[dict]       # Assembled final report
    visualizations: List[dict]         # Chart configs for UI

    # === Observability ===
    trace_id: str                      # Trace identifier
    error_log: Annotated[List[str], add]  # Accumulated errors


def create_initial_state(
    input_path: str = "",
    input_text: str = "",
    session_id: str = "",
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
) -> dict:
    """Create initial state for the pipeline"""
    import uuid

    return {
        "input_type": "",
        "input_path": input_path,
        "input_text": input_text,
        "session_id": session_id or str(uuid.uuid4()),
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "agent_outputs": [],
        "call_metadata": None,
        "transcript": None,
        "speaker_segments": None,
        "summary": None,
        "quality_scores": None,
        "pii_detected": [],
        "compliance_flags": [],
        "final_report": None,
        "visualizations": [],
        "trace_id": str(uuid.uuid4()),
        "error_log": [],
    }
