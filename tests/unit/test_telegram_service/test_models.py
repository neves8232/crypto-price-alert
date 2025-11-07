"""
Unit tests for Pydantic models.

Tests request/response validation and serialization.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from telegram_service.models import (
    AlertRequest,
    AlertResponse,
    ErrorResponse,
    HealthCheck,
)


@pytest.mark.unit
class TestAlertRequest:
    """Test cases for AlertRequest model."""

    def test_valid_alert_request(self):
        """Test creating valid alert request."""
        request = AlertRequest(
            chat_id="123456789",
            message="Test alert message",
            parse_mode="HTML",
            priority="high",
            metadata={"crypto": "BTC"}
        )

        assert request.chat_id == "123456789"
        assert request.message == "Test alert message"
        assert request.parse_mode == "HTML"
        assert request.priority == "high"
        assert request.metadata == {"crypto": "BTC"}

    def test_alert_request_defaults(self):
        """Test default values for optional fields."""
        request = AlertRequest(
            chat_id="123456789",
            message="Test message"
        )

        assert request.parse_mode is None
        assert request.priority == "normal"
        assert request.metadata == {}

    def test_alert_request_missing_chat_id(self):
        """Test that missing chat_id raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AlertRequest(message="Test message")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("chat_id",) for e in errors)

    def test_alert_request_missing_message(self):
        """Test that missing message raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AlertRequest(chat_id="123456789")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)

    def test_alert_request_empty_chat_id(self):
        """Test that empty chat_id is rejected."""
        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="",
                message="Test message"
            )

    def test_alert_request_empty_message(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="123456789",
                message=""
            )

    def test_alert_request_message_too_long(self):
        """Test that message exceeding 4096 chars is rejected."""
        long_message = "a" * 4097

        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="123456789",
                message=long_message
            )

    def test_alert_request_invalid_parse_mode(self):
        """Test that invalid parse_mode is rejected."""
        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="123456789",
                message="Test",
                parse_mode="Invalid"
            )

    def test_alert_request_invalid_priority(self):
        """Test that invalid priority is rejected."""
        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="123456789",
                message="Test",
                priority="urgent"  # Only low/normal/high allowed
            )

    def test_alert_request_xss_validation(self):
        """Test XSS prevention in message validation."""
        dangerous_messages = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onerror='alert(1)'>",
            "<div onclick='malicious()'>",
        ]

        for msg in dangerous_messages:
            with pytest.raises(ValidationError) as exc_info:
                AlertRequest(
                    chat_id="123456789",
                    message=msg
                )

            errors = exc_info.value.errors()
            assert any("forbidden pattern" in str(e["msg"]).lower() for e in errors)

    def test_alert_request_case_sensitivity_xss(self):
        """Test that XSS validation is case-insensitive."""
        with pytest.raises(ValidationError):
            AlertRequest(
                chat_id="123456789",
                message="<SCRIPT>alert('xss')</SCRIPT>"
            )

    def test_alert_request_valid_html(self):
        """Test that valid HTML markup is allowed."""
        request = AlertRequest(
            chat_id="123456789",
            message="<b>Bold</b> and <i>italic</i> text",
            parse_mode="HTML"
        )

        assert "<b>Bold</b>" in request.message


@pytest.mark.unit
class TestAlertResponse:
    """Test cases for AlertResponse model."""

    def test_valid_success_response(self):
        """Test creating valid success response."""
        response = AlertResponse(
            status="success",
            message_id=12345,
            telegram_response={"ok": True},
            delivery_time_ms=150,
            request_id="req-123"
        )

        assert response.status == "success"
        assert response.message_id == 12345
        assert response.delivery_time_ms == 150
        assert response.request_id == "req-123"

    def test_valid_queued_response(self):
        """Test creating valid queued response."""
        response = AlertResponse(
            status="queued",
            request_id="req-123",
            queue_position=5,
            estimated_delay_seconds=10
        )

        assert response.status == "queued"
        assert response.message_id is None
        assert response.queue_position == 5
        assert response.estimated_delay_seconds == 10

    def test_response_invalid_status(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError):
            AlertResponse(
                status="invalid_status",
                request_id="req-123"
            )


@pytest.mark.unit
class TestErrorResponse:
    """Test cases for ErrorResponse model."""

    def test_valid_error_response(self):
        """Test creating valid error response."""
        error = ErrorResponse(
            status="error",
            error_code="TELEGRAM_API_ERROR",
            message="Failed to send message",
            details="Connection timeout",
            request_id="req-123"
        )

        assert error.status == "error"
        assert error.error_code == "TELEGRAM_API_ERROR"
        assert error.message == "Failed to send message"
        assert error.details == "Connection timeout"

    def test_rate_limited_response(self):
        """Test creating rate limited response."""
        error = ErrorResponse(
            status="rate_limited",
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            retry_after_seconds=60,
            request_id="req-123"
        )

        assert error.status == "rate_limited"
        assert error.retry_after_seconds == 60


@pytest.mark.unit
class TestHealthCheck:
    """Test cases for HealthCheck model."""

    def test_valid_healthy_response(self):
        """Test creating valid healthy response."""
        health = HealthCheck(
            status="healthy",
            service="telegram-service",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks={
                "telegram_api": "ok",
                "rate_limiter": "ok"
            }
        )

        assert health.status == "healthy"
        assert health.service == "telegram-service"
        assert health.version == "1.0.0"
        assert health.checks["telegram_api"] == "ok"

    def test_valid_unhealthy_response(self):
        """Test creating valid unhealthy response."""
        health = HealthCheck(
            status="unhealthy",
            service="telegram-service",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks={
                "telegram_api": "failed"
            },
            errors=["Telegram API unreachable"]
        )

        assert health.status == "unhealthy"
        assert health.errors == ["Telegram API unreachable"]

    def test_health_check_invalid_status(self):
        """Test that invalid health status is rejected."""
        with pytest.raises(ValidationError):
            HealthCheck(
                status="broken",  # Only healthy/degraded/unhealthy allowed
                service="telegram-service",
                version="1.0.0",
                timestamp=datetime.utcnow(),
                checks={}
            )


@pytest.mark.unit
class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_alert_request_to_dict(self):
        """Test converting AlertRequest to dictionary."""
        request = AlertRequest(
            chat_id="123456789",
            message="Test message",
            priority="high"
        )

        data = request.model_dump()

        assert data["chat_id"] == "123456789"
        assert data["message"] == "Test message"
        assert data["priority"] == "high"

    def test_alert_request_to_json(self):
        """Test converting AlertRequest to JSON."""
        request = AlertRequest(
            chat_id="123456789",
            message="Test message"
        )

        json_str = request.model_dump_json()

        assert "123456789" in json_str
        assert "Test message" in json_str

    def test_alert_request_from_dict(self):
        """Test creating AlertRequest from dictionary."""
        data = {
            "chat_id": "123456789",
            "message": "Test message",
            "parse_mode": "HTML",
            "priority": "normal",
            "metadata": {"key": "value"}
        }

        request = AlertRequest(**data)

        assert request.chat_id == "123456789"
        assert request.metadata == {"key": "value"}

    def test_health_check_timestamp_default(self):
        """Test that timestamp has default value."""
        health = HealthCheck(
            status="healthy",
            service="test-service",
            version="1.0.0",
            checks={}
        )

        assert isinstance(health.timestamp, datetime)
        assert health.timestamp is not None
