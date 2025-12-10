"""Application Configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Loan System API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/loans_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Banking Providers (simulated URLs for MVP)
    BANKING_PROVIDER_ES_URL: str = "http://localhost:8001"
    BANKING_PROVIDER_ES_KEY: str = "es-api-key"
    BANKING_PROVIDER_MX_URL: str = "http://localhost:8002"
    BANKING_PROVIDER_MX_KEY: str = "mx-api-key"
    BANKING_PROVIDER_CO_URL: str = "http://localhost:8003"
    BANKING_PROVIDER_CO_KEY: str = "co-api-key"
    BANKING_PROVIDER_BR_URL: str = "http://localhost:8004"
    BANKING_PROVIDER_BR_KEY: str = "br-api-key"

    # Webhook
    WEBHOOK_SECRET: str = "webhook-secret-key"

    # Logging
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
