from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Union
import json


class Settings(BaseSettings):
    # AI Provider (free tier first)
    llm7_api_key: str = Field(default="", validation_alias="LLM7_API_KEY")
    llm7_model: str = Field(default="gpt-4o-mini", validation_alias="LLM7_MODEL")

    # OpenAI (optional, fallback)
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL")

    # Anthropic (alternative)
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-haiku-20240307", validation_alias="ANTHROPIC_MODEL")

    # Backend
    backend_host: str = Field(default="0.0.0.0", validation_alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, validation_alias="PORT")
    cors_origins: Union[str, List[str]] = Field(default="http://localhost:3000,http://127.0.0.1:3000", validation_alias="BACKEND_CORS_ORIGINS")

    # Frontend
    next_public_api_url: str = Field(default="http://localhost:8000", validation_alias="NEXT_PUBLIC_API_URL")
    next_public_app_name: str = Field(default="LegalAid AI", validation_alias="NEXT_PUBLIC_APP_NAME")
    next_public_app_url: str = Field(default="http://localhost:3000", validation_alias="NEXT_PUBLIC_APP_URL")

    # Security
    secret_key: str = Field(default="", validation_alias="SECRET_KEY")
    rate_limit_requests: int = Field(default=30, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")

    # Database
    database_url: str = Field(default="sqlite:///./legal_aid.db", validation_alias="DATABASE_URL")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("openai_api_key", "anthropic_api_key", mode="before")
    @classmethod
    def normalize_api_key(cls, v):
        if not isinstance(v, str):
            return v
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            v = v[1:-1].strip()
        return v.strip('"').strip("'").strip()


settings = Settings()

# Validate required settings (warn instead of crash to allow MockProvider fallback)
import warnings

if not settings.openai_api_key and not settings.anthropic_api_key:
    warnings.warn("No AI provider API key configured. Using mock provider for testing.")

if not settings.secret_key or len(settings.secret_key) < 32:
    warnings.warn("SECRET_KEY not configured or too short. Using default for testing.")