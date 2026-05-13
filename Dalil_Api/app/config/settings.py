"""
Application Configuration
=========================
Centralized settings loaded from environment variables using pydantic-settings.
The .env file is loaded automatically. NEVER hardcode secrets.

HOW TO SET UP YOUR API KEY:
1. Copy .env.example to .env in the project root
2. Replace 'your_google_api_key_here' with your real Gemini API key
3. Get your key from: https://aistudio.google.com/
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is loaded from environment variables.
    The .env file in the project root is auto-loaded.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "Dalil AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Security ─────────────────────────────────────────────
    API_SECRET_KEY: str = "change_this_to_a_random_secret_key"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ── Google Gemini API ────────────────────────────────────
    # THIS is where your API key is loaded from the .env file
    GOOGLE_API_KEY: str = ""

    # ── AI Model Settings ────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.1
    MAX_SAMPLE_ROWS: int = 10
    MAX_CONTEXT_TOKENS: int = 8000
    CONVERSATION_SUMMARY_THRESHOLD: int = 6

    # ── File Upload ──────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: str = ".csv,.xlsx,.xls"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_ext_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./dalil_ai.db"

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30
    GEMINI_RATE_LIMIT_RPM: int = 5

    # ── Caching ──────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 3600
    MAX_CACHE_SIZE: int = 100

    # ── Paths ────────────────────────────────────────────────
    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cache_path(self) -> Path:
        path = Path("data_cache")
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """
    Cached singleton for settings.
    Call this function to access settings anywhere in the app.
    """
    return Settings()
