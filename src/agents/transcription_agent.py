"""Transcription Agent — Converts audio to text using Gemini or Whisper API"""

import mimetypes
from typing import Dict, Any
from .base_agent import BaseClarityAgent


class TranscriptionAgent(BaseClarityAgent):
    """Converts audio files to text transcripts using Gemini (default) or Whisper."""

    name = "TranscriptionAgent"
    description = "Converts audio to text with speaker diarization"
    system_prompt = """You are the Transcription Agent. Your responsibilities:
    - Convert audio files to text using the configured LLM
    - Provide timestamped transcript segments
    - Detect language and confidence scores
    - Identify different speakers when possible
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        input_type = state.get("input_type", "")

        # Skip transcription for text/transcript inputs
        if input_type in ("text", "transcript"):
            return {
                "transcript": state.get("transcript", ""),
                "speaker_segments": state.get("speaker_segments", []),
            }

        # Audio transcription
        if input_type == "audio":
            provider = state.get("llm_provider", "google")
            if provider == "google":
                return await self._transcribe_with_gemini(state)
            else:
                return await self._transcribe_with_whisper(state)

        raise ValueError(f"Unsupported input type for transcription: {input_type}")

    async def _transcribe_with_gemini(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio using Google Gemini (native audio support)"""
        from src.config import get_api_key

        metadata = state.get("call_metadata", {})
        file_path = metadata.get("file_path", "")

        if not file_path:
            raise ValueError("No audio file path in call metadata")

        try:
            import google.generativeai as genai

            genai.configure(api_key=get_api_key("google"))

            # Upload the audio file to Gemini
            mime_type = mimetypes.guess_type(file_path)[0] or "audio/mpeg"
            audio_file = genai.upload_file(file_path, mime_type=mime_type)

            model = genai.GenerativeModel("gemini-2.0-flash")

            prompt = """Transcribe this audio file into a detailed call transcript.

For each speaker turn, output in this exact format:
[MM:SS] Speaker Name: What they said

Rules:
- Identify distinct speakers (e.g., "Agent", "Customer", or their actual names if mentioned)
- Include timestamps for each turn
- Capture the full conversation accurately
- If a speaker introduces themselves by name, use that name going forward
- Keep the transcription verbatim — do not summarize

After the transcript, on a new line write:
LANGUAGE: <detected language code, e.g. en>
DURATION: <estimated duration in seconds>"""

            response = await model.generate_content_async([prompt, audio_file])
            transcript_text = response.text

            # Parse the structured response
            segments = self._parse_gemini_transcript(transcript_text)
            full_text = self._segments_to_text(segments) if segments else transcript_text

            # Extract metadata from response
            language = "en"
            duration = 0
            for line in transcript_text.split("\n"):
                line = line.strip()
                if line.startswith("LANGUAGE:"):
                    language = line.split(":", 1)[1].strip()
                elif line.startswith("DURATION:"):
                    try:
                        duration = int("".join(c for c in line.split(":", 1)[1] if c.isdigit()))
                    except ValueError:
                        pass

            # Clean up uploaded file
            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass

            updated_metadata = {
                **metadata,
                "duration_seconds": duration or (segments[-1].get("end", 0) if segments else 0),
                "word_count": len(full_text.split()),
                "language": language,
                "transcription_model": "gemini-2.0-flash",
            }

            return {
                "transcript": full_text,
                "speaker_segments": segments,
                "call_metadata": updated_metadata,
            }

        except ImportError:
            raise ImportError("google-generativeai package required. Run: pip install google-generativeai")
        except Exception as e:
            self.logger.warning(f"Gemini transcription failed: {e}, trying Whisper fallback...")
            # Fallback to Whisper
            try:
                return await self._transcribe_with_whisper(state)
            except Exception:
                raise RuntimeError(f"Audio transcription failed with both Gemini and Whisper: {str(e)}")

    def _parse_gemini_transcript(self, text: str) -> list:
        """Parse Gemini's transcript output into structured segments"""
        import re
        segments = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("LANGUAGE:") or line.startswith("DURATION:"):
                continue
            # Match [MM:SS] Speaker: Text
            match = re.match(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.*)', line)
            if match:
                timestamp = match.group(1)
                speaker = match.group(2).strip()
                text_content = match.group(3).strip()
                # Parse timestamp to seconds
                parts = timestamp.split(":")
                if len(parts) == 3:
                    secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    secs = int(parts[0]) * 60 + int(parts[1])
                segments.append({
                    "speaker": speaker,
                    "timestamp": timestamp,
                    "text": text_content,
                    "start": secs,
                    "end": secs,
                })
        return segments

    def _segments_to_text(self, segments: list) -> str:
        """Convert segments to plain text"""
        return "\n".join(f"{s['speaker']}: {s['text']}" for s in segments)

    async def _transcribe_with_whisper(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API (fallback)"""
        from src.config import config, get_api_key

        metadata = state.get("call_metadata", {})
        file_path = metadata.get("file_path", "")

        if not file_path:
            raise ValueError("No audio file path in call metadata")

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=get_api_key("openai"))

            with open(file_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model=config.whisper.model,
                    file=audio_file,
                    language=config.whisper.language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            # Build speaker segments from Whisper response
            segments = []
            if hasattr(response, "segments") and response.segments:
                for seg in response.segments:
                    segments.append({
                        "speaker": "Speaker",  # Whisper doesn't do diarization
                        "timestamp": self._format_timestamp(seg.start),
                        "text": seg.text.strip(),
                        "start": seg.start,
                        "end": seg.end,
                    })

            full_text = response.text if hasattr(response, "text") else ""

            updated_metadata = {
                **metadata,
                "duration_seconds": segments[-1]["end"] if segments else 0,
                "word_count": len(full_text.split()),
                "language": response.language if hasattr(response, "language") else "en",
                "transcription_model": config.whisper.model,
            }

            return {
                "transcript": full_text,
                "speaker_segments": segments,
                "call_metadata": updated_metadata,
            }

        except ImportError:
            raise ImportError("openai package required. Run: pip install openai")
        except Exception as e:
            self.logger.error(f"Whisper transcription failed: {e}")
            raise RuntimeError(f"Audio transcription failed: {str(e)}")

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
