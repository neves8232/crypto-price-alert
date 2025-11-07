"""
Pydantic Models

Request and response models for API endpoints.
Provides automatic validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AlertRequest(BaseModel):
    """
    Request model for sending Telegram alerts.

    Based on the architecture spec:
    POST /api/v1/alerts/send
    """

    chat_id: str = Field(
        ...,
        description="Telegram chat ID",
        min_length=1,
        max_length=64,
        examples=["123456789", "-1001234567890"]
    )

    message: str = Field(
        ...,
        description="Message text to send",
        min_length=1,
        max_length=4096  # Telegram's limit
    )

    parse_mode: Optional[Literal["HTML", "Markdown"]] = Field(
        default=None,
        description="Message parsing mode"
    )

    priority: Literal["low", "normal", "high"] = Field(
        default="normal",
        description="Message priority (affects queue processing)"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for logging"
    )

    @field_validator("message")
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        """Validate message content doesn't contain malicious content."""
        # Basic XSS prevention
        dangerous_patterns = ["<script>", "javascript:", "onerror=", "onclick="]
        message_lower = v.lower()

        for pattern in dangerous_patterns:
            if pattern in message_lower:
                raise ValueError(f"Message contains forbidden pattern: {pattern}")

        return v


class AlertResponse(BaseModel):
    """
    Response model for successful alert delivery.
    """

    status: Literal["success", "queued", "error", "rate_limited"] = Field(
        ...,
        description="Request status"
    )

    message_id: Optional[int] = Field(
        default=None,
        description="Telegram message ID (if sent immediately)"
    )

    telegram_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw Telegram API response"
    )

    delivery_time_ms: Optional[int] = Field(
        default=None,
        description="Message delivery time in milliseconds"
    )

    request_id: str = Field(
        ...,
        description="Unique request ID for tracking"
    )

    queue_position: Optional[int] = Field(
        default=None,
        description="Position in queue (if queued)"
    )

    estimated_delay_seconds: Optional[int] = Field(
        default=None,
        description="Estimated delay before delivery (if queued)"
    )


class ErrorResponse(BaseModel):
    """
    Response model for errors.
    """

    status: Literal["error", "rate_limited"] = Field(
        ...,
        description="Error status"
    )

    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    details: Optional[str] = Field(
        default=None,
        description="Additional error details"
    )

    retry_after_seconds: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retrying (for rate limits)"
    )

    request_id: str = Field(
        ...,
        description="Request ID for tracking"
    )


class HealthCheck(BaseModel):
    """
    Health check response model.
    """

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall health status"
    )

    service: str = Field(
        ...,
        description="Service name"
    )

    version: str = Field(
        ...,
        description="Service version"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )

    checks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Individual health check results"
    )

    errors: Optional[list[str]] = Field(
        default=None,
        description="List of errors (if unhealthy)"
    )
