"""LangGraph Pipeline — Clarity CX Call Analysis Graph"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import ClarityState, create_initial_state
from .nodes import (
    intake_node,
    transcription_node,
    summarization_node,
    quality_scoring_node,
    routing_node,
    route_by_input_type,
)

logger = logging.getLogger(__name__)


def create_graph() -> StateGraph:
    """Create the Clarity CX analysis pipeline graph.

    Pipeline Flow:
    1. Intake Agent → validate & extract metadata
    2. Conditional: Audio → Transcribe, Text → Skip to Analysis
    3. Summarization Agent → structured summary (parallel with scoring)
    4. Quality Scoring Agent → 5-dimension rubric scores
    5. Routing Agent → assemble final report

    Returns:
        Compiled LangGraph state graph
    """
    workflow = StateGraph(ClarityState)

    # Add nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("transcribe", transcription_node)
    workflow.add_node("summarize", summarization_node)
    workflow.add_node("score_quality", quality_scoring_node)
    workflow.add_node("route", routing_node)

    # Set entry point
    workflow.set_entry_point("intake")

    # Conditional routing after intake
    workflow.add_conditional_edges(
        "intake",
        route_by_input_type,
        {
            "transcribe": "transcribe",  # Audio → transcribe first
            "analyze": "summarize",       # Text/JSON → skip transcription
            "error": "route",             # Errors → routing for fallback
        },
    )

    # After transcription → summarize
    workflow.add_edge("transcribe", "summarize")

    # After summarize → score quality
    workflow.add_edge("summarize", "score_quality")

    # After score quality → route and assemble report
    workflow.add_edge("score_quality", "route")

    # Routing is the final node
    workflow.add_edge("route", END)

    # Compile the graph
    compiled = workflow.compile()
    logger.info("Clarity CX pipeline graph compiled successfully")

    return compiled


# Singleton compiled graph
_pipeline = None


def get_pipeline():
    """Get or create the pipeline graph (singleton)"""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_graph()
    return _pipeline


async def analyze_call(
    input_path: str = "",
    input_text: str = "",
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    session_id: str = "",
) -> Dict[str, Any]:
    """Run the full call analysis pipeline.

    This is the main entry point for analyzing a call.

    Args:
        input_path: Path to audio file or transcript file
        input_text: Raw text or JSON transcript
        llm_provider: LLM provider to use
        llm_model: LLM model to use
        session_id: Optional session ID

    Returns:
        Final pipeline state including the report
    """
    pipeline = get_pipeline()

    # Create initial state
    initial_state = create_initial_state(
        input_path=input_path,
        input_text=input_text,
        session_id=session_id,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )

    logger.info(f"Starting analysis pipeline (session: {initial_state['session_id'][:8]}...)")

    # Run the pipeline
    final_state = await pipeline.ainvoke(initial_state)

    logger.info(
        f"Pipeline complete. Status: {final_state.get('final_report', {}).get('status', 'unknown')}"
    )

    return final_state
