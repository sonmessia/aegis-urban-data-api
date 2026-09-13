"""Application settings using pydantic-settings v2."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (12-factor app).
    In the Dev Tier, values come from Docker Compose / k3d pod env vars.
    Secrets (DB password) are injected by External Secrets Operator.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: Literal["dev", "demo", "production"] = Field(
        default="dev", alias="ENVIRONMENT"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    cors_origins: list[AnyHttpUrl] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    # Injected by External Secrets Operator from AWS Secrets Manager (Floci)
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    database_url: str = Field(alias="DATABASE_URL")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")

    # ── AWS / Floci ───────────────────────────────────────────────────────────
    # Endpoint URL: http://floci:4566 (in-cluster) or http://localhost:4566 (local dev)
    aws_endpoint_url: str | None = Field(default=None, alias="AWS_ENDPOINT_URL")
    aws_region: str = Field(default="ap-southeast-1", alias="AWS_DEFAULT_REGION")
    aws_access_key_id: str = Field(default="test", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="test", alias="AWS_SECRET_ACCESS_KEY")

    # ── Observability ─────────────────────────────────────────────────────────
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list:
        """Allow comma-separated string from env var."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of instantiating directly."""
    return Settings()
