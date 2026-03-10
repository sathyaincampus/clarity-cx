"""LangGraph Node functions for Clarity CX Pipeline"""

from typing import Dict, Any
from .state import ClarityState
from src.agents import (
    IntakeAgent,
    TranscriptionAgent,
    SummarizationAgent,
    QualityScoringAgent,
    RoutingAgent,
)

# Agent instances (singleton)
_intake = IntakeAgent()
_transcription = TranscriptionAgent()
_summarization = SummarizationAgent()
_quality_scorer = QualityScoringAgent()
_router = RoutingAgent()


async def intake_node(state: ClarityState) -> Dict[str, Any]:
    """Validate input and extract metadata"""
    return await _intake.safe_process(state)


async def transcription_node(state: ClarityState) -> Dict[str, Any]:
    """Transcribe audio or pass through text"""
    return await _transcription.safe_process(state)


async def summarization_node(state: ClarityState) -> Dict[str, Any]:
    """Generate structured summary"""
    return await _summarization.safe_process(state)


async def quality_scoring_node(state: ClarityState) -> Dict[str, Any]:
    """Score quality across 5 dimensions"""
    return await _quality_scorer.safe_process(state)


async def routing_node(state: ClarityState) -> Dict[str, Any]:
    """Assemble final report with fallback handling"""
    return await _router.safe_process(state)


def route_by_input_type(state: ClarityState) -> str:
    """Conditional routing based on input type.

    Audio inputs go through transcription first.
    Text/JSON inputs skip directly to analysis.
    """
    input_type = state.get("input_type", "")

    if input_type == "audio":
        return "transcribe"
    elif input_type in ("text", "transcript"):
        return "analyze"
    else:
        return "error"
