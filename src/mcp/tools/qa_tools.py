"""QA MCP Tools — Quality scoring, PII detection, and compliance checking"""

import re
from typing import Dict, Any, List


async def score_quality(
    transcript: str,
    rubric: str = "standard",
) -> Dict[str, Any]:
    """Score call quality across 5 dimensions.

    Args:
        transcript: Full call transcript text
        rubric: standard | compliance | sales

    Returns:
        Quality scores with overall, per-dimension, and recommendations
    """
    from src.config import config, get_api_key
    from src.llm.adapter import get_llm_adapter

    llm = get_llm_adapter(config.llm.provider, config.llm.model, get_api_key(config.llm.provider))

    prompt = f"""Score this call using the '{rubric}' quality rubric.

Return JSON with scores 0-10 for each dimension:
{{
    "overall_score": 7.5,
    "empathy": {{"score": 8.0, "justification": "..."}},
    "resolution": {{"score": 7.0, "justification": "..."}},
    "professionalism": {{"score": 9.0, "justification": "..."}},
    "compliance": {{"score": 8.0, "justification": "..."}},
    "efficiency": {{"score": 7.0, "justification": "..."}},
    "flags": [],
    "recommendations": []
}}

Transcript:
{transcript}"""

    response = await llm.chat(
        [{"role": "user", "content": prompt}],
        system="You are a call center QA expert. Score precisely and return only valid JSON.",
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
        return {"overall_score": 0, "error": "Failed to parse quality scores"}


async def detect_pii(text: str) -> Dict[str, Any]:
    """Detect personally identifiable information in text.

    Checks for SSN, credit card numbers, phone numbers, emails, etc.

    Args:
        text: Text to scan for PII

    Returns:
        PII detection results with types, counts, and risk level
    """
    patterns = {
        "ssn": {
            "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
            "severity": "critical",
            "label": "Social Security Number",
        },
        "credit_card": {
            "pattern": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            "severity": "critical",
            "label": "Credit Card Number",
        },
        "phone": {
            "pattern": r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "severity": "medium",
            "label": "Phone Number",
        },
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "severity": "medium",
            "label": "Email Address",
        },
        "date_of_birth": {
            "pattern": r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b',
            "severity": "high",
            "label": "Date of Birth",
        },
    }

    detections = []
    for pii_type, config in patterns.items():
        matches = re.findall(config["pattern"], text)
        if matches:
            detections.append({
                "type": pii_type,
                "label": config["label"],
                "count": len(matches),
                "severity": config["severity"],
                "samples": [m[:4] + "***" for m in matches[:3]],  # Partially redacted
            })

    # Determine overall risk
    if any(d["severity"] == "critical" for d in detections):
        risk_level = "critical"
    elif any(d["severity"] == "high" for d in detections):
        risk_level = "high"
    elif detections:
        risk_level = "medium"
    else:
        risk_level = "none"

    return {
        "pii_found": len(detections) > 0,
        "detections": detections,
        "total_detections": sum(d["count"] for d in detections),
        "risk_level": risk_level,
    }


async def check_compliance(
    transcript: str,
    required_phrases: List[str] = None,
) -> Dict[str, Any]:
    """Verify script adherence and compliance requirements.

    Args:
        transcript: Full call transcript
        required_phrases: List of phrases that should appear in the call

    Returns:
        Compliance check results
    """
    if required_phrases is None:
        required_phrases = [
            "thank you for calling",
            "how may I help",
            "is there anything else",
            "have a great day",
        ]

    transcript_lower = transcript.lower()

    # Check required phrases
    phrase_results = []
    for phrase in required_phrases:
        found = phrase.lower() in transcript_lower
        phrase_results.append({
            "phrase": phrase,
            "found": found,
            "required": True,
        })

    # Check for prohibited content
    prohibited_phrases = [
        "i don't care",
        "that's not my problem",
        "you're wrong",
        "calm down",
        "whatever",
    ]

    violations = []
    for phrase in prohibited_phrases:
        if phrase.lower() in transcript_lower:
            violations.append({
                "type": "prohibited_language",
                "phrase": phrase,
                "severity": "warning",
            })

    # Calculate compliance score
    required_met = sum(1 for r in phrase_results if r["found"])
    compliance_rate = required_met / len(phrase_results) if phrase_results else 1.0

    return {
        "compliance_rate": round(compliance_rate, 2),
        "required_phrases": phrase_results,
        "violations": violations,
        "overall_status": "pass" if compliance_rate >= 0.75 and not violations else "review",
    }
