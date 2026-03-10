"""Audio MCP Tools — Transcription and audio processing"""

from typing import Dict, Any


async def transcribe_audio(audio_path: str, language: str = "en") -> Dict[str, Any]:
    """Transcribe audio file using Whisper API.

    Args:
        audio_path: Path to audio file (WAV, MP3, FLAC, etc.)
        language: Language code (default: en)

    Returns:
        Transcript with segments, language, and duration
    """
    from src.config import get_api_key

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=get_api_key("openai"))

        with open(audio_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                })

        return {
            "transcript": response.text,
            "segments": segments,
            "language": getattr(response, "language", language),
            "duration": segments[-1]["end"] if segments else 0,
            "word_count": len(response.text.split()),
        }

    except FileNotFoundError:
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}")
