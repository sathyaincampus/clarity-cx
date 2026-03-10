"""Clarity CX Configuration Management"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class LLMConfig(BaseModel):
    """LLM provider configuration"""
    provider: str = Field(default="google", description="LLM provider: google, openai, anthropic")
    model: str = Field(default="gemini-2.0-flash", description="Model identifier")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=100, le=16384)


class WhisperConfig(BaseModel):
    """Whisper transcription configuration"""
    model: str = Field(default="whisper-1")
    language: str = Field(default="en")
    response_format: str = Field(default="verbose_json")


class AppConfig(BaseModel):
    """Main application configuration"""
    # App
    app_name: str = "Clarity CX"
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # LLM
    llm: LLMConfig = Field(default_factory=LLMConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Observability (Arize Phoenix)
    phoenix_enabled: bool = Field(default=True, description="Enable Arize Phoenix tracing")
    phoenix_port: int = 6006
    phoenix_collector_endpoint: str = "http://localhost:6006/v1/traces"

    # Limits
    max_audio_duration_seconds: int = 1800  # 30 minutes
    max_upload_size_mb: int = 25

    # Database
    database_path: str = str(PROJECT_ROOT / "clarity_cx.db")

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501


def load_config() -> AppConfig:
    """Load configuration from environment variables"""
    return AppConfig(
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("APP_ENV", "development") == "development",
        llm=LLMConfig(
            provider=os.getenv("DEFAULT_LLM_PROVIDER", "google"),
            model=os.getenv("DEFAULT_LLM_MODEL", "gemini-2.0-flash"),
        ),
        whisper=WhisperConfig(
            model=os.getenv("WHISPER_MODEL", "whisper-1"),
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        phoenix_enabled=os.getenv("PHOENIX_ENABLED", "true").lower() == "true",
        phoenix_port=int(os.getenv("PHOENIX_PORT", "6006")),
        phoenix_collector_endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
        max_audio_duration_seconds=int(os.getenv("MAX_AUDIO_DURATION_SECONDS", "1800")),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "25")),
        database_path=os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "clarity_cx.db")),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
    )


# Singleton config instance
config = load_config()


def get_api_key(provider: str) -> str:
    """Get API key for a given LLM provider"""
    key_map = {
        "openai": config.openai_api_key,
        "anthropic": config.anthropic_api_key,
        "google": config.google_api_key,
    }
    key = key_map.get(provider)
    if not key:
        raise ValueError(
            f"No API key configured for provider '{provider}'. "
            f"Set {provider.upper()}_API_KEY in your .env file."
        )
    return key
