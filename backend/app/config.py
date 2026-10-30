"""Central application configuration via pydantic-settings.

All settings are loaded from environment variables with sensible defaults.
Secrets (API keys, etc.) should be set via .env file or environment.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "APITestGen"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Server ───────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # ── Redis (optional cache) ───────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # ── LLM Provider Defaults ────────────────────────────────────
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai | anthropic | openai_compatible
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_REQUEST_TIMEOUT: int = 120  # seconds

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None

    # ── Test Generation ──────────────────────────────────────────
    MAX_TESTCASES_PER_ENDPOINT: int = 15
    GENERATED_TESTS_DIR: str = "./generated_tests"

    # ── Reports ──────────────────────────────────────────────────
    REPORTS_DIR: str = "./reports"
    REPORTS_RETENTION_DAYS: int = 90

    # ── Security ─────────────────────────────────────────────────
    API_KEY_ENCRYPTION_KEY: Optional[str] = None  # Fernet key; auto-generated if None

    # ── File Upload ──────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Paths (resolved relative to project root) ────────────────
    DATA_DIR: str = "./data"

    @property
    def generated_tests_path(self) -> Path:
        return Path(self.GENERATED_TESTS_DIR)

    @property
    def reports_path(self) -> Path:
        return Path(self.REPORTS_DIR)

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)


settings = Settings()
