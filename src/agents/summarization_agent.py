"""Summarization Agent — Generates structured call summaries"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseClarityAgent


class CallSummary(BaseModel):
    """Structured call summary output"""
    summary: str = Field(description="2-3 sentence call overview")
    key_points: List[str] = Field(description="3-5 bullet-point highlights")
    action_items: List[str] = Field(description="Follow-up tasks required")
    customer_intent: str = Field(description="Primary reason for call")
    resolution_status: str = Field(description="resolved / escalated / pending")
    topics: List[str] = Field(description="Tags: billing, shipping, returns, technical")
    sentiment_trajectory: str = Field(
        description="e.g. negative_to_positive, neutral_throughout"
    )


class SummarizationAgent(BaseClarityAgent):
    """Generates structured summaries from call transcripts."""

    name = "SummarizationAgent"
    description = "Generates structured call summaries with key points and action items"
    system_prompt = """You are an expert call center summarization agent. Given a call transcript, produce a structured analysis.

Your output MUST be a valid JSON object matching this exact schema:
{
    "summary": "2-3 sentence overview of the call",
    "key_points": ["point 1", "point 2", "point 3"],
    "action_items": ["action 1", "action 2"],
    "customer_intent": "Primary reason the customer called",
    "resolution_status": "resolved | escalated | pending",
    "topics": ["billing", "shipping"],
    "sentiment_trajectory": "negative_to_positive | positive_throughout | negative_throughout | neutral | mixed"
}

Rules:
- summary: concise 2-3 sentences capturing the essence of the call
- key_points: 3-5 bullet points of important moments or decisions
- action_items: concrete follow-up tasks (empty list if none)
- resolution_status: must be one of: resolved, escalated, pending
- topics: relevant categories from: billing, shipping, returns, technical, account, complaint, inquiry, upgrade, cancellation, general
- sentiment_trajectory: describe how customer sentiment changed through the call
- Be factual — only include what's in the transcript
- Do NOT invent details not present in the transcript
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        transcript = state.get("transcript", "")
        if not transcript:
            raise ValueError("No transcript available for summarization")

        # Get LLM adapter
        from src.config import config, get_api_key
        from src.llm.adapter import get_llm_adapter

        provider = state.get("llm_provider", config.llm.provider)
        model = state.get("llm_model", config.llm.model)

        llm = get_llm_adapter(provider, model, get_api_key(provider))

        # Generate summary
        messages = [
            {
                "role": "user",
                "content": f"Analyze this call transcript and produce a structured JSON summary:\n\n{transcript}",
            }
        ]

        response = await llm.chat(messages, system=self.system_prompt)

        # Parse structured output
        summary = self._parse_summary(response)

        return {
            "summary": summary.model_dump(),
        }

    def _parse_summary(self, response: str) -> CallSummary:
        """Parse LLM response into CallSummary model"""
        # Try to extract JSON from response
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            return CallSummary(**data)
        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback: create a basic summary from the raw response
            return CallSummary(
                summary=text[:500] if len(text) > 500 else text,
                key_points=["Analysis completed but structured parsing failed"],
                action_items=[],
                customer_intent="Unable to determine",
                resolution_status="pending",
                topics=["general"],
                sentiment_trajectory="unknown",
            )
