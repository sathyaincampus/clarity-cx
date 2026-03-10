"""
Generate Audio — Creates WAV files from sample transcripts using OpenAI TTS.

Usage:
    python scripts/generate_audio.py

Generates 2-3 audio WAV files from selected transcripts using OpenAI TTS API.
Uses different voices for Agent (alloy) vs Customer (nova) to simulate real calls.

Requirements:
    - OPENAI_API_KEY environment variable set
    - openai package installed
"""

import sys
import json
import io
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Samples to generate audio for
SAMPLES_TO_GENERATE = [
    "SAMPLE-001",  # Order Delay Inquiry (good call)
    "SAMPLE-005",  # Complaint Escalation (bad call)
    "SAMPLE-008",  # Wrong Item Received (e-commerce)
]

VOICE_MAP = {
    "Agent": "alloy",
    "Customer": "nova",
}

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sample_audio"


def generate_audio_for_sample(client, sample: dict) -> bytes:
    """Generate a combined audio file from a transcript sample."""
    from pydub import AudioSegment

    combined = AudioSegment.silent(duration=500)  # 500ms leading silence

    for segment in sample["transcript"]:
        speaker = segment["speaker"]
        text = segment["text"]
        voice = VOICE_MAP.get(speaker, "alloy")

        print(f"    🎤 {speaker} ({voice}): {text[:60]}...")

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3",
        )

        # Convert response to AudioSegment
        audio_data = io.BytesIO(response.content)
        segment_audio = AudioSegment.from_mp3(audio_data)

        # Add pause between speakers (300ms for same speaker, 600ms for different)
        combined += AudioSegment.silent(duration=400)
        combined += segment_audio

    # Add trailing silence
    combined += AudioSegment.silent(duration=500)

    return combined


def main():
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ openai package required. Run: pip install openai")
        sys.exit(1)

    try:
        from pydub import AudioSegment  # noqa: F401
    except ImportError:
        print("❌ pydub package required. Run: pip install pydub")
        print("   Also needs ffmpeg: brew install ffmpeg")
        sys.exit(1)

    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Load samples
    samples_path = Path(__file__).parent.parent / "data" / "sample_transcripts" / "samples.json"
    with open(samples_path) as f:
        samples = json.load(f)

    samples_by_id = {s["call_id"]: s for s in samples}

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for sample_id in SAMPLES_TO_GENERATE:
        sample = samples_by_id.get(sample_id)
        if not sample:
            print(f"⚠ Sample {sample_id} not found, skipping")
            continue

        scenario_slug = sample["scenario"].lower().replace(" ", "_").replace("-", "_")
        output_file = OUTPUT_DIR / f"{scenario_slug}.wav"

        print(f"\n🎙️ Generating: {sample['scenario']} ({sample_id})")
        print(f"   Output: {output_file}")

        try:
            combined_audio = generate_audio_for_sample(client, sample)
            combined_audio.export(str(output_file), format="wav")
            duration_sec = len(combined_audio) / 1000
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"   ✅ Done! Duration: {duration_sec:.1f}s, Size: {size_mb:.1f}MB")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print(f"\n🎉 Audio files saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    print("🎙️ Generating audio files from sample transcripts...\n")
    main()
