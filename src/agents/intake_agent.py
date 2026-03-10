"""Call Intake Agent — Validates input and extracts metadata"""

import os
import re
import json
import mimetypes
from typing import Dict, Any, Optional
from .base_agent import BaseClarityAgent


SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"}
SUPPORTED_TEXT_FORMATS = {".json", ".txt", ".csv"}


class IntakeAgent(BaseClarityAgent):
    """Validates input files and extracts call metadata."""

    name = "IntakeAgent"
    description = "Validates input formats and extracts call metadata"
    system_prompt = """You are the Call Intake Agent. Your responsibilities:
    - Validate that the input is a supported format (audio or transcript)
    - Extract metadata: duration, format, file size, language
    - Flag any issues with the input quality
    - Determine the processing path (audio vs text pipeline)
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        input_path = state.get("input_path", "")
        input_text = state.get("input_text", "")

        # Determine input type
        if input_text:
            return await self._process_text_input(input_text)
        elif input_path:
            return await self._process_file_input(input_path)
        else:
            raise ValueError("No input provided. Please upload an audio file or paste a transcript.")

    async def _process_text_input(self, text: str) -> Dict[str, Any]:
        """Process direct text/JSON input"""
        # Try to parse as JSON transcript
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "transcript" in data:
                transcript_text = self._extract_transcript_text(data["transcript"])
                agent_name = self._extract_agent_name_from_segments(data["transcript"])
                metadata = {
                    "format": "json",
                    "word_count": len(transcript_text.split()),
                    "has_speaker_labels": self._has_speaker_labels(data["transcript"]),
                    "source": "json_upload",
                }
                if agent_name:
                    metadata["agent_name"] = agent_name
                return {
                    "input_type": "transcript",
                    "call_metadata": metadata,
                    "transcript": transcript_text,
                    "speaker_segments": data.get("transcript", []),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # Treat as plain text transcript
        if len(text.strip()) < 50:
            raise ValueError(
                f"Text input too short ({len(text.strip())} chars). "
                "Minimum 50 characters required for analysis."
            )

        agent_name = self._extract_agent_name_from_text(text)
        metadata = {
            "format": "text",
            "word_count": len(text.split()),
            "has_speaker_labels": self._detect_speaker_labels_in_text(text),
            "source": "text_paste",
        }
        if agent_name:
            metadata["agent_name"] = agent_name

        return {
            "input_type": "text",
            "call_metadata": metadata,
            "transcript": text,
        }

    async def _process_file_input(self, file_path: str) -> Dict[str, Any]:
        """Process file upload (audio or text file)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        mime_type = mimetypes.guess_type(file_path)[0] or "unknown"

        # Audio file
        if ext in SUPPORTED_AUDIO_FORMATS:
            from src.config import config
            if file_size_mb > config.max_upload_size_mb:
                raise ValueError(
                    f"File too large ({file_size_mb:.1f}MB). "
                    f"Max: {config.max_upload_size_mb}MB."
                )
            return {
                "input_type": "audio",
                "call_metadata": {
                    "format": ext.lstrip("."),
                    "mime_type": mime_type,
                    "file_size_mb": round(file_size_mb, 2),
                    "file_path": file_path,
                    "source": "audio_upload",
                },
            }

        # Text/JSON file
        if ext in SUPPORTED_TEXT_FORMATS:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return await self._process_text_input(content)

        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported audio: {', '.join(SUPPORTED_AUDIO_FORMATS)}. "
            f"Supported text: {', '.join(SUPPORTED_TEXT_FORMATS)}."
        )

    def _extract_transcript_text(self, segments) -> str:
        """Extract full text from transcript segments"""
        if isinstance(segments, list):
            lines = []
            for seg in segments:
                if isinstance(seg, dict):
                    speaker = seg.get("speaker", "Unknown")
                    text = seg.get("text", "")
                    lines.append(f"{speaker}: {text}")
                elif isinstance(seg, str):
                    lines.append(seg)
            return "\n".join(lines)
        elif isinstance(segments, str):
            return segments
        return str(segments)

    def _has_speaker_labels(self, segments) -> bool:
        """Check if transcript has speaker labels"""
        if isinstance(segments, list) and segments:
            return isinstance(segments[0], dict) and "speaker" in segments[0]
        return False

    def _detect_speaker_labels_in_text(self, text: str) -> bool:
        """Detect speaker labels in plain text"""
        lines = text.strip().split("\n")
        labeled = sum(1 for line in lines if ":" in line[:30])
        return labeled > len(lines) * 0.3

    def _extract_agent_name_from_text(self, text: str) -> Optional[str]:
        """Extract agent name from plain text transcript.

        Handles common patterns:
          - 'Sarah (Agent): ...'
          - 'Agent Sarah: ...'
          - 'Agent: My name is Sarah, ...'
        """
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Pattern: "Name (Agent): ..."
            match = re.match(r'^([A-Z][a-z]+)\s*\(Agent\)\s*:', line)
            if match:
                return match.group(1)

            # Pattern: "Agent Name: ..."
            match = re.match(r'^Agent\s+([A-Z][a-z]+)\s*:', line)
            if match:
                return match.group(1)

            # Pattern: "Agent: ... My name is Name ..."
            match = re.match(r'^Agent\s*:', line, re.IGNORECASE)
            if match:
                name_match = re.search(
                    r'[Mm]y name is ([A-Z][a-z]+)', line
                )
                if name_match:
                    return name_match.group(1)

        return None

    def _extract_agent_name_from_segments(self, segments) -> Optional[str]:
        """Extract agent name from JSON transcript segments.

        Checks the 'speaker' field and the first agent line text for name.
        """
        if not isinstance(segments, list):
            return None

        for seg in segments:
            if not isinstance(seg, dict):
                continue
            speaker = seg.get("speaker", "")
            text = seg.get("text", "")

            # If speaker is a proper name (not just "Agent")
            if speaker and speaker not in ("Agent", "Customer", "System"):
                if speaker.replace(" ", "").isalpha():
                    return speaker

            # Check text for "My name is ..."
            if "agent" in speaker.lower():
                name_match = re.search(
                    r'[Mm]y name is ([A-Z][a-z]+)', text
                )
                if name_match:
                    return name_match.group(1)

        return None
