"""Quality Scoring Agent — Evaluates call quality across 5 dimensions"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseClarityAgent


class ScoreDimension(BaseModel):
    """Individual scoring dimension"""
    score: float = Field(ge=0, le=10, description="Score from 0-10")
    justification: str = Field(description="Brief explanation for the score")


class QualityScore(BaseModel):
    """Complete quality scoring output"""
    overall_score: float = Field(ge=0, le=10, description="Weighted average score")
    empathy: ScoreDimension = Field(description="Active listening, acknowledgment (25%)")
    resolution: ScoreDimension = Field(description="Problem solved, clear next steps (25%)")
    professionalism: ScoreDimension = Field(description="Tone, language, script adherence (20%)")
    compliance: ScoreDimension = Field(description="PII handling, disclaimer delivery (15%)")
    efficiency: ScoreDimension = Field(description="Handle time, talk-to-listen ratio (15%)")
    flags: List[str] = Field(default_factory=list, description="Issues detected")
    recommendations: List[str] = Field(default_factory=list, description="Coaching suggestions")


def get_score_band(score: float) -> Dict[str, str]:
    """Get score band label and color"""
    if score >= 8.0:
        return {"label": "Excellent", "emoji": "🟢", "action": "Recognize & reward"}
    elif score >= 6.0:
        return {"label": "Good", "emoji": "🟡", "action": "Minor coaching"}
    elif score >= 4.0:
        return {"label": "Needs Improvement", "emoji": "🟠", "action": "Targeted training"}
    else:
        return {"label": "Critical", "emoji": "🔴", "action": "Immediate review"}


class QualityScoringAgent(BaseClarityAgent):
    """Evaluates call quality using a structured 5-dimension rubric."""

    name = "QualityScoringAgent"
    description = "Scores call quality across empathy, resolution, tone, compliance, efficiency"
    system_prompt = """You are a call center quality assurance expert. Evaluate the call transcript using this 5-dimension rubric.

Your output MUST be a valid JSON object matching this exact schema:
{
    "overall_score": 7.5,
    "empathy": {
        "score": 8.0,
        "justification": "Agent acknowledged customer frustration early"
    },
    "resolution": {
        "score": 7.0,
        "justification": "Issue was addressed but follow-up needed"
    },
    "professionalism": {
        "score": 9.0,
        "justification": "Maintained professional tone throughout"
    },
    "compliance": {
        "score": 8.0,
        "justification": "No PII exposed, proper verification done"
    },
    "efficiency": {
        "score": 7.0,
        "justification": "Call handled in reasonable time"
    },
    "flags": ["long_hold_time", "script_deviation"],
    "recommendations": ["Reduce hold times", "Follow opening script"]
}

SCORING DIMENSIONS:
1. Empathy (25% weight): Active listening, acknowledgment of feelings, genuine concern
   - 9-10: Exceptional emotional intelligence, proactive reassurance
   - 7-8: Good acknowledgment, appropriate responses
   - 5-6: Basic acknowledgment but lacks warmth
   - 1-4: Dismissive, robotic, or insensitive

2. Resolution (25% weight): Problem solved, clear next steps, customer satisfied
   - 9-10: Issue fully resolved, customer delighted
   - 7-8: Issue resolved with clear next steps
   - 5-6: Partial resolution, some ambiguity
   - 1-4: Unresolved, customer still frustrated

3. Professionalism (20% weight): Tone, language, courtesy, script adherence
   - 9-10: Perfect tone, professional throughout
   - 7-8: Mostly professional with minor lapses
   - 5-6: Noticeable unprofessional moments
   - 1-4: Rude, inappropriate, or hostile

4. Compliance (15% weight): PII handling, required disclosures, proper verification
   - 9-10: Perfect compliance, proper verification
   - 7-8: Good compliance, minor gaps
   - 5-6: Some compliance issues
   - 1-4: Major compliance violations

5. Efficiency (15% weight): Average handle time, unnecessary holds, repetition
   - 9-10: Swift resolution, no wasted time
   - 7-8: Efficient with minor delays
   - 5-6: Some unnecessary delays or repetition
   - 1-4: Very long holds, excessive transfers

overall_score = (empathy * 0.25) + (resolution * 0.25) + (professionalism * 0.20) + (compliance * 0.15) + (efficiency * 0.15)

COMMON FLAGS (include if detected):
- pii_detected: Customer or agent shared sensitive info
- long_hold: Hold time exceeded 2 minutes
- script_deviation: Agent deviated from required script
- escalation_needed: Issue requires supervisor attention
- repeat_caller: Customer mentions previous calls
- customer_frustration: Elevated frustration detected
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        transcript = state.get("transcript", "")
        if not transcript:
            raise ValueError("No transcript available for quality scoring")

        # Get LLM adapter
        from src.config import config, get_api_key
        from src.llm.adapter import get_llm_adapter

        provider = state.get("llm_provider", config.llm.provider)
        model = state.get("llm_model", config.llm.model)

        llm = get_llm_adapter(provider, model, get_api_key(provider))

        # Score quality
        messages = [
            {
                "role": "user",
                "content": (
                    f"Score this call transcript using the quality rubric. "
                    f"Return ONLY a valid JSON object.\n\n"
                    f"Transcript:\n{transcript}"
                ),
            }
        ]

        response = await llm.chat(messages, system=self.system_prompt)

        # Parse quality scores
        quality = self._parse_quality_score(response)

        # Add score band info
        band = get_score_band(quality.overall_score)

        return {
            "quality_scores": {
                **quality.model_dump(),
                "band": band,
            },
        }

    def _parse_quality_score(self, response: str) -> QualityScore:
        """Parse LLM response into QualityScore model"""
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            return QualityScore(**data)
        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(f"Failed to parse quality score JSON: {e}")
            # Fallback scores
            default_dim = ScoreDimension(score=5.0, justification="Unable to parse scoring response")
            return QualityScore(
                overall_score=5.0,
                empathy=default_dim,
                resolution=default_dim,
                professionalism=default_dim,
                compliance=default_dim,
                efficiency=default_dim,
                flags=["parsing_error"],
                recommendations=["Manual review recommended — automated scoring failed"],
            )
