"""
Unit tests for crypto service Pydantic schemas.

Tests request/response validation and serialization.
"""

import pytest
from pydantic import ValidationError
from decimal import Decimal
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from crypto_service.schemas import (
    CryptocurrencyCreate,
    CryptocurrencyResponse,
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    CurrentPrice,
    HealthCheck,
    ErrorResponse,
)


@pytest.mark.unit
class TestCryptocurrencySchemas:
    """Test cases for cryptocurrency schemas."""

    def test_create_cryptocurrency_valid(self):
        """Test creating valid cryptocurrency schema."""
        crypto = CryptocurrencyCreate(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin"
        )

        assert crypto.crypto_id == "bitcoin"
        assert crypto.symbol == "BTC"
        assert crypto.name == "Bitcoin"

    def test_create_cryptocurrency_missing_fields(self):
        """Test validation of missing required fields."""
        with pytest.raises(ValidationError):
            CryptocurrencyCreate(
                crypto_id="bitcoin",
                # Missing symbol and name
            )

    def test_create_cryptocurrency_empty_symbol(self):
        """Test that empty symbol is rejected."""
        with pytest.raises(ValidationError):
            CryptocurrencyCreate(
                crypto_id="bitcoin",
                symbol="",
                name="Bitcoin"
            )

    def test_cryptocurrency_response_serialization(self):
        """Test cryptocurrency response serialization."""
        crypto = CryptocurrencyResponse(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("50000.00"),
            market_cap=1000000000,
            volume_24h=50000000,
            price_change_24h=Decimal("500.00"),
            price_change_percentage_24h=Decimal("1.5"),
            last_updated=datetime.utcnow(),
            is_active=True,
            created_at=datetime.utcnow()
        )

        data = crypto.model_dump()
        assert data["symbol"] == "BTC"
        assert data["current_price"] == Decimal("50000.00")


@pytest.mark.unit
class TestAlertSchemas:
    """Test cases for alert schemas."""

    def test_create_alert_valid(self):
        """Test creating valid alert."""
        alert = AlertCreate(
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("60000.00"),
            telegram_chat_id="123456789"
        )

        assert alert.user_id == "user123"
        assert alert.crypto_id == "bitcoin"
        assert alert.alert_type == "PRICE_ABOVE"
        assert alert.threshold == Decimal("60000.00")
        assert alert.enabled is True  # Default value

    def test_create_alert_defaults(self):
        """Test default values for alert creation."""
        alert = AlertCreate(
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("60000.00"),
            telegram_chat_id="123456789"
        )

        assert alert.enabled is True
        assert alert.metadata == {}

    def test_create_alert_invalid_type(self):
        """Test that invalid alert type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AlertCreate(
                user_id="user123",
                crypto_id="bitcoin",
                alert_type="INVALID_TYPE",
                threshold=Decimal("60000.00"),
                telegram_chat_id="123456789"
            )

        errors = exc_info.value.errors()
        assert any("alert_type must be one of" in str(e["msg"]) for e in errors)

    def test_create_alert_valid_types(self):
        """Test all valid alert types."""
        valid_types = [
            "PRICE_ABOVE",
            "PRICE_BELOW",
            "PRICE_CHANGE_PERCENT",
            "PRICE_CROSSES_UP",
            "PRICE_CROSSES_DOWN",
        ]

        for alert_type in valid_types:
            alert = AlertCreate(
                user_id="user123",
                crypto_id="bitcoin",
                alert_type=alert_type,
                threshold=Decimal("60000.00"),
                telegram_chat_id="123456789"
            )
            assert alert.alert_type == alert_type

    def test_create_alert_negative_threshold(self):
        """Test that negative threshold is rejected."""
        with pytest.raises(ValidationError):
            AlertCreate(
                user_id="user123",
                crypto_id="bitcoin",
                alert_type="PRICE_ABOVE",
                threshold=Decimal("-1000.00"),  # Negative
                telegram_chat_id="123456789"
            )

    def test_create_alert_zero_threshold(self):
        """Test that zero threshold is rejected."""
        with pytest.raises(ValidationError):
            AlertCreate(
                user_id="user123",
                crypto_id="bitcoin",
                alert_type="PRICE_ABOVE",
                threshold=Decimal("0.00"),  # Zero
                telegram_chat_id="123456789"
            )

    def test_update_alert_partial(self):
        """Test partial alert update."""
        update = AlertUpdate(
            threshold=Decimal("70000.00")
        )

        assert update.threshold == Decimal("70000.00")
        assert update.enabled is None
        assert update.metadata is None

    def test_update_alert_all_fields(self):
        """Test updating all fields."""
        update = AlertUpdate(
            threshold=Decimal("70000.00"),
            enabled=False,
            metadata={"note": "Updated"}
        )

        assert update.threshold == Decimal("70000.00")
        assert update.enabled is False
        assert update.metadata == {"note": "Updated"}

    def test_alert_response_complete(self):
        """Test complete alert response."""
        alert = AlertResponse(
            alert_id="alert123",
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("60000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            metadata={},
            last_triggered_at=datetime.utcnow(),
            last_triggered_price=Decimal("61000.00"),
            trigger_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert alert.alert_id == "alert123"
        assert alert.trigger_count == 5


@pytest.mark.unit
class TestPriceSchemas:
    """Test cases for price schemas."""

    def test_current_price_valid(self):
        """Test creating valid current price."""
        price = CurrentPrice(
            crypto_id="bitcoin",
            symbol="BTC",
            price=Decimal("50000.00"),
            timestamp=datetime.utcnow()
        )

        assert price.crypto_id == "bitcoin"
        assert price.symbol == "BTC"
        assert price.price == Decimal("50000.00")

    def test_current_price_serialization(self):
        """Test price serialization."""
        now = datetime.utcnow()
        price = CurrentPrice(
            crypto_id="bitcoin",
            symbol="BTC",
            price=Decimal("50000.00"),
            timestamp=now
        )

        data = price.model_dump()
        assert data["crypto_id"] == "bitcoin"
        assert data["price"] == Decimal("50000.00")


@pytest.mark.unit
class TestHealthCheckSchema:
    """Test cases for health check schema."""

    def test_health_check_valid(self):
        """Test creating valid health check."""
        health = HealthCheck(
            status="healthy",
            service="crypto-service",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks={
                "database": "ok",
                "coingecko_api": "ok"
            }
        )

        assert health.status == "healthy"
        assert health.service == "crypto-service"
        assert health.checks["database"] == "ok"

    def test_health_check_invalid_status(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError):
            HealthCheck(
                status="broken",  # Invalid
                service="crypto-service",
                version="1.0.0",
                timestamp=datetime.utcnow(),
                checks={}
            )


@pytest.mark.unit
class TestErrorResponseSchema:
    """Test cases for error response schema."""

    def test_error_response_valid(self):
        """Test creating valid error response."""
        error = ErrorResponse(
            status="error",
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "threshold"},
            request_id="req-123"
        )

        assert error.status == "error"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"


@pytest.mark.unit
class TestSchemaValidation:
    """Test advanced validation scenarios."""

    def test_decimal_precision(self):
        """Test decimal precision handling."""
        alert = AlertCreate(
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("60000.12345678"),  # High precision
            telegram_chat_id="123456789"
        )

        assert alert.threshold == Decimal("60000.12345678")

    def test_very_large_threshold(self):
        """Test handling of very large threshold values."""
        alert = AlertCreate(
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("999999999999.99"),
            telegram_chat_id="123456789"
        )

        assert alert.threshold == Decimal("999999999999.99")

    def test_very_small_threshold(self):
        """Test handling of very small threshold values."""
        alert = AlertCreate(
            user_id="user123",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("0.00000001"),
            telegram_chat_id="123456789"
        )

        assert alert.threshold == Decimal("0.00000001")
