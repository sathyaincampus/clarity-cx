"""Analysis MCP Tools — Summary, action items, and sentiment analysis"""

from typing import Dict, Any, List


async def generate_summary(
    transcript: str,
    detail_level: str = "standard",
) -> Dict[str, Any]:
    """Generate structured summary from call transcript.

    Args:
        transcript: Full call transcript text
        detail_level: brief | standard | detailed

    Returns:
        Structured summary with key points and intent
    """
    from src.config import config, get_api_key
    from src.llm.adapter import get_llm_adapter

    llm = get_llm_adapter(config.llm.provider, config.llm.model, get_api_key(config.llm.provider))

    prompt = f"""Summarize this call transcript at '{detail_level}' detail level.

Return JSON:
{{
    "summary": "2-3 sentences",
    "key_points": ["point 1", "point 2"],
    "customer_intent": "reason for call",
    "resolution_status": "resolved|escalated|pending"
}}

Transcript:
{transcript}"""

    response = await llm.chat(
        [{"role": "user", "content": prompt}],
        system="You are a call center summarization expert. Return only valid JSON.",
    )

    import json
    try:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "summary": response[:500],
            "key_points": [],
            "customer_intent": "Unable to determine",
            "resolution_status": "pending",
        }


async def extract_action_items(
    transcript: str,
    summary: str = "",
) -> Dict[str, Any]:
    """Extract follow-up tasks and action items from the call.

    Args:
        transcript: Full transcript text
        summary: Optional pre-generated summary

    Returns:
        List of action items with priority and assignee
    """
    from src.config import config, get_api_key
    from src.llm.adapter import get_llm_adapter

    llm = get_llm_adapter(config.llm.provider, config.llm.model, get_api_key(config.llm.provider))

    context = f"Summary: {summary}\n\n" if summary else ""
    prompt = f"""{context}Extract all action items from this call transcript.

Return JSON:
{{
    "action_items": [
        {{"task": "description", "priority": "high|medium|low", "assignee": "agent|supervisor|system"}}
    ],
    "follow_up_needed": true/false
}}

Transcript:
{transcript}"""

    response = await llm.chat(
        [{"role": "user", "content": prompt}],
        system="You are an action item extraction specialist. Return only valid JSON.",
    )

    import json
    try:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"action_items": [], "follow_up_needed": False}


async def analyze_sentiment(
    transcript: str,
    granularity: str = "overall",
) -> Dict[str, Any]:
    """Analyze sentiment trajectory throughout the call.

    Args:
        transcript: Full transcript text
        granularity: overall | per_turn | per_minute

    Returns:
        Sentiment analysis with trajectory and scores
    """
    from src.config import config, get_api_key
    from src.llm.adapter import get_llm_adapter

    llm = get_llm_adapter(config.llm.provider, config.llm.model, get_api_key(config.llm.provider))

    prompt = f"""Analyze the sentiment trajectory of this call at '{granularity}' granularity.

Return JSON:
{{
    "overall_sentiment": "positive|negative|neutral|mixed",
    "overall_score": 0.5,
    "trajectory": "negative_to_positive|positive_throughout|negative_throughout|mixed",
    "phases": [
        {{"phase": "opening", "sentiment": "neutral", "score": 0.3, "key_moment": "description"}}
    ]
}}

Scores: -1.0 (very negative) to 1.0 (very positive)

Transcript:
{transcript}"""

    response = await llm.chat(
        [{"role": "user", "content": prompt}],
        system="You are a sentiment analysis expert. Return only valid JSON.",
    )

    import json
    try:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "overall_sentiment": "unknown",
            "overall_score": 0.0,
            "trajectory": "unknown",
            "phases": [],
        }
