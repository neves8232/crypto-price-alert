"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Cryptocurrency Schemas
class CryptocurrencyBase(BaseModel):
    """Base schema for cryptocurrency data."""
    symbol: str = Field(..., min_length=1, max_length=10, description="Cryptocurrency symbol (e.g., BTC)")
    name: str = Field(..., min_length=1, max_length=255, description="Cryptocurrency name (e.g., Bitcoin)")


class CryptocurrencyCreate(CryptocurrencyBase):
    """Schema for creating a new cryptocurrency."""
    crypto_id: str = Field(..., min_length=1, max_length=64, description="Unique cryptocurrency ID")


class CryptocurrencyResponse(CryptocurrencyBase):
    """Schema for cryptocurrency response."""
    crypto_id: str
    current_price: Optional[Decimal] = None
    market_cap: Optional[int] = None
    volume_24h: Optional[int] = None
    price_change_24h: Optional[Decimal] = None
    price_change_percentage_24h: Optional[Decimal] = None
    last_updated: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CryptocurrencyList(BaseModel):
    """Schema for list of cryptocurrencies."""
    cryptocurrencies: list[CryptocurrencyResponse]
    total: int


# Alert Schemas
class AlertBase(BaseModel):
    """Base schema for alert data."""
    crypto_id: str = Field(..., description="Cryptocurrency ID to monitor")
    alert_type: str = Field(
        ...,
        description="Alert type: PRICE_ABOVE, PRICE_BELOW, PRICE_CHANGE_PERCENT, PRICE_CROSSES_UP, PRICE_CROSSES_DOWN"
    )
    threshold: Decimal = Field(..., gt=0, description="Alert threshold value")
    telegram_chat_id: str = Field(..., description="Telegram chat ID for notifications")
    enabled: bool = Field(default=True, description="Whether alert is enabled")
    metadata: dict = Field(default_factory=dict, description="Additional alert metadata")

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        """Validate alert type is one of allowed values."""
        allowed_types = {
            "PRICE_ABOVE",
            "PRICE_BELOW",
            "PRICE_CHANGE_PERCENT",
            "PRICE_CROSSES_UP",
            "PRICE_CROSSES_DOWN",
        }
        if v not in allowed_types:
            raise ValueError(f"alert_type must be one of {allowed_types}")
        return v


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    user_id: str = Field(..., description="User ID who owns the alert")


class AlertUpdate(BaseModel):
    """Schema for updating an existing alert."""
    threshold: Optional[Decimal] = Field(None, gt=0)
    enabled: Optional[bool] = None
    metadata: Optional[dict] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    alert_id: str
    user_id: str
    last_triggered_at: Optional[datetime] = None
    last_triggered_price: Optional[Decimal] = None
    trigger_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertList(BaseModel):
    """Schema for list of alerts."""
    alerts: list[AlertResponse]
    total: int


# Price Schemas
class CurrentPrice(BaseModel):
    """Schema for current cryptocurrency price."""
    crypto_id: str
    symbol: str
    price: Decimal
    timestamp: datetime


class CurrentPriceList(BaseModel):
    """Schema for list of current prices."""
    prices: list[CurrentPrice]
    timestamp: datetime


class PriceHistoryPoint(BaseModel):
    """Schema for a single price history data point."""
    timestamp: datetime
    price: Decimal
    volume_24h: Optional[int] = None


class PriceHistoryResponse(BaseModel):
    """Schema for price history response."""
    crypto_id: str
    symbol: str
    interval: str
    data_points: list[PriceHistoryPoint]


# Health Check Schemas
class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")
    checks: dict = Field(..., description="Individual health check results")


# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None
