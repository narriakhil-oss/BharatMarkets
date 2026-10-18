"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables."""

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://bharatmarkets:bharatmarkets_dev@localhost:5432/bharatmarkets",
        description="Async PostgreSQL connection URL",
    )

    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development / production)",
    )

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        description="Default rate limit per IP per minute",
    )

    # Gemini LLM (chat assistant)
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key for the AI assistant",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.8-flash",
        description="Gemini model name (set to current Flash model)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS_ORIGINS into a clean list of origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
