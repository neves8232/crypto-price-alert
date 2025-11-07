"""
Configuration management using Pydantic Settings.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="crypto-price-alert", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")

    # Web Server
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=52000, description="API port")
    service_port: int = Field(default=52000, description="Service port (alias for api_port)")

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./crypto_alerts.db",
        description="Database connection URL"
    )

    # Crypto API Settings
    crypto_api_provider: str = Field(default="coingecko", description="Crypto API provider")
    coingecko_api_key: Optional[str] = Field(default=None, description="CoinGecko API key (optional)")
    crypto_poll_interval_seconds: int = Field(default=15, description="Price polling interval in seconds")
    poll_interval_seconds: int = Field(default=15, description="Poll interval (alias)")
    max_watchlist_size: int = Field(default=25, description="Maximum cryptocurrencies to monitor")

    # Alert Settings
    alert_debounce_seconds: int = Field(default=30, description="Minimum seconds between alert triggers")
    alert_batch_size: int = Field(default=10, description="Maximum alerts to process in batch")

    # Telegram Service Integration
    telegram_service_url: str = Field(
        default="http://telegram-alert-service:52001",
        description="Telegram service base URL"
    )
    telegram_service_auth_token: Optional[str] = Field(
        default=None,
        alias="auth_token",
        description="Auth token for telegram service"
    )
    telegram_service_timeout_seconds: int = Field(default=10, description="Telegram service timeout")

    # Security
    internal_auth_token: Optional[str] = Field(default=None, description="Internal API auth token")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:52000",
        description="Comma-separated CORS origins"
    )

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=52002, description="Metrics endpoint port")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()
