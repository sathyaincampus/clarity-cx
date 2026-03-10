"""MCP module — Model Context Protocol tools"""
from .tools.audio_tools import transcribe_audio
from .tools.analysis_tools import generate_summary, extract_action_items, analyze_sentiment
from .tools.qa_tools import score_quality, detect_pii, check_compliance

MCP_TOOLS = [
    {
        "name": "transcribe_audio",
        "description": "Convert audio file to text transcript with timestamps",
        "category": "audio",
        "function": transcribe_audio,
    },
    {
        "name": "generate_summary",
        "description": "Generate structured summary from call transcript",
        "category": "analysis",
        "function": generate_summary,
    },
    {
        "name": "extract_action_items",
        "description": "Extract follow-up tasks from the call",
        "category": "analysis",
        "function": extract_action_items,
    },
    {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment trajectory throughout the call",
        "category": "analysis",
        "function": analyze_sentiment,
    },
    {
        "name": "score_quality",
        "description": "Score call quality across empathy, resolution, tone dimensions",
        "category": "qa",
        "function": score_quality,
    },
    {
        "name": "detect_pii",
        "description": "Detect personally identifiable information in text",
        "category": "security",
        "function": detect_pii,
    },
    {
        "name": "check_compliance",
        "description": "Verify script adherence and compliance requirements",
        "category": "security",
        "function": check_compliance,
    },
]
