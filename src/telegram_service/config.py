"""
Configuration Management

Loads and validates environment variables using Pydantic Settings.
Follows 12-factor app principles for configuration management.
"""

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All sensitive values (tokens, secrets) must be provided via environment variables.
    Never hardcode secrets in code or configuration files.
    """

    # Application metadata
    app_name: str = Field(default="telegram-alert-service", description="Service name")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # Web server configuration
    service_port: int = Field(default=52001, ge=1024, le=65535, description="HTTP port")
    host: str = Field(default="0.0.0.0", description="Bind host")

    # Telegram Bot configuration
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_api_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Telegram API request timeout"
    )
    telegram_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retry attempts for failed requests"
    )
    telegram_retry_delay_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        description="Initial retry delay (exponential backoff)"
    )

    # Rate limiting configuration
    # Telegram allows 30 msg/sec, we set to 25 to be safe
    rate_limit_messages_per_second: float = Field(
        default=25.0,
        ge=1.0,
        le=30.0,
        description="Messages per second limit"
    )
    rate_limit_burst_size: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Burst capacity"
    )

    # Message queue configuration
    queue_max_size: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Maximum queue size"
    )

    # Security
    auth_token: str = Field(..., description="Bearer token for API authentication")

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        if not v:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        # Basic format validation: should be like "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid Telegram bot token format")

        if not parts[0].isdigit():
            raise ValueError("Invalid Telegram bot token format")

        if len(parts[1]) < 30:
            raise ValueError("Invalid Telegram bot token format")

        return v

    @field_validator("auth_token")
    @classmethod
    def validate_auth_token(cls, v: str) -> str:
        """Validate auth token is not empty."""
        if not v:
            raise ValueError("AUTH_TOKEN is required")

        if len(v) < 32:
            raise ValueError("AUTH_TOKEN should be at least 32 characters for security")

        return v

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


# Global settings instance
settings = Settings()
