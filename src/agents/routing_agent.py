"""Routing Agent — Handles fallback logic, error recovery, and report assembly"""

import json
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseClarityAgent


class RoutingAgent(BaseClarityAgent):
    """Handles routing, fallback logic, and final report assembly."""

    name = "RoutingAgent"
    description = "Manages fallback providers, error recovery, and final report formatting"
    system_prompt = """You are the Routing Agent. Your responsibilities:
    - Assemble the final report from all agent outputs
    - Handle errors by triggering fallback providers
    - Ensure all required fields are present
    - Format the output for display
    """

    # Fallback provider chain
    FALLBACK_CHAIN = [
        {"provider": "openai", "model": "gpt-4o"},
        {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        {"provider": "google", "model": "gemini-2.0-flash"},
    ]

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble the final report from all pipeline outputs"""

        # Check for errors in agent outputs
        agent_outputs = state.get("agent_outputs", [])
        errors = [o for o in agent_outputs if o.get("status") == "error"]
        successes = [o for o in agent_outputs if o.get("status") == "success"]

        # Assemble report
        report = self._assemble_report(state, errors)

        return {
            "final_report": report,
        }

    def _assemble_report(self, state: Dict[str, Any], errors: List[dict]) -> dict:
        """Build the final structured report"""
        metadata = state.get("call_metadata", {})
        summary = state.get("summary", {})
        quality = state.get("quality_scores", {})
        transcript = state.get("transcript", "")

        # Determine overall status
        if errors:
            status = "partial" if summary or quality else "failed"
        else:
            status = "complete"

        report = {
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "status": status,
            "generated_at": datetime.now().isoformat(),

            # Call Info
            "call_metadata": metadata,

            # Summary Section
            "summary": summary if summary else {
                "summary": "Summary generation failed or was not performed.",
                "key_points": [],
                "action_items": [],
                "customer_intent": "Unknown",
                "resolution_status": "pending",
                "topics": [],
                "sentiment_trajectory": "unknown",
            },

            # Quality Scores Section
            "quality_scores": quality if quality else {
                "overall_score": 0,
                "empathy": {"score": 0, "justification": "Not scored"},
                "resolution": {"score": 0, "justification": "Not scored"},
                "professionalism": {"score": 0, "justification": "Not scored"},
                "compliance": {"score": 0, "justification": "Not scored"},
                "efficiency": {"score": 0, "justification": "Not scored"},
                "flags": [],
                "recommendations": [],
                "band": {"label": "Not Scored", "emoji": "⚪", "action": "Retry analysis"},
            },

            # PII and Compliance
            "pii_detected": state.get("pii_detected", []),
            "compliance_flags": state.get("compliance_flags", []),

            # Transcript (truncated for report)
            "transcript_preview": transcript[:500] + "..." if len(transcript) > 500 else transcript,
            "transcript_word_count": len(transcript.split()) if transcript else 0,

            # Pipeline Info
            "errors": [e.get("error", "Unknown error") for e in errors],
            "agent_count": len(state.get("agent_outputs", [])),

            # Visualizations config
            "visualizations": self._build_visualizations(quality),
        }

        return report

    def _build_visualizations(self, quality: dict) -> List[dict]:
        """Build visualization configs for the UI"""
        vizs = []

        if quality and quality.get("overall_score", 0) > 0:
            # Radar chart for quality dimensions
            vizs.append({
                "type": "radar",
                "title": "Quality Score Dimensions",
                "data": {
                    "categories": [
                        "Empathy", "Resolution", "Professionalism",
                        "Compliance", "Efficiency"
                    ],
                    "values": [
                        quality.get("empathy", {}).get("score", 0),
                        quality.get("resolution", {}).get("score", 0),
                        quality.get("professionalism", {}).get("score", 0),
                        quality.get("compliance", {}).get("score", 0),
                        quality.get("efficiency", {}).get("score", 0),
                    ],
                },
            })

            # Gauge chart for overall score
            vizs.append({
                "type": "gauge",
                "title": "Overall Quality Score",
                "data": {
                    "value": quality.get("overall_score", 0),
                    "max": 10,
                },
            })

        return vizs

    async def retry_with_fallback(
        self,
        agent,
        state: Dict[str, Any],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Retry an agent with fallback LLM providers"""
        for i, fallback in enumerate(self.FALLBACK_CHAIN[:max_retries]):
            try:
                self.logger.info(
                    f"Retry {i + 1}/{max_retries}: "
                    f"Using {fallback['provider']}/{fallback['model']}"
                )
                state_copy = {
                    **state,
                    "llm_provider": fallback["provider"],
                    "llm_model": fallback["model"],
                }
                result = await agent.process(state_copy)
                return result
            except Exception as e:
                self.logger.warning(f"Fallback {i + 1} failed: {e}")
                continue

        # All fallbacks exhausted
        self.logger.error("All fallback providers exhausted")
        return {"error": "All providers failed"}
