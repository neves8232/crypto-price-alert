"""
Unit tests for the alert engine module.

Tests alert evaluation logic, debouncing, and triggering conditions.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from crypto_service.services.alert_engine import AlertEngine
from crypto_service.models import Alert, Cryptocurrency


@pytest.mark.unit
class TestAlertEngine:
    """Test cases for AlertEngine class."""

    @pytest.mark.asyncio
    async def test_price_above_alert_triggers(self, test_db):
        """Test that PRICE_ABOVE alert triggers when price exceeds threshold."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("51000.00"),
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True
        assert "above" in message.lower()
        assert "51,000.00" in message

    @pytest.mark.asyncio
    async def test_price_above_alert_does_not_trigger(self, test_db):
        """Test that PRICE_ABOVE alert doesn't trigger when price is below threshold."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("49000.00"),
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is False

    @pytest.mark.asyncio
    async def test_price_below_alert_triggers(self, test_db):
        """Test that PRICE_BELOW alert triggers when price is below threshold."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_BELOW",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("49000.00"),
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True
        assert "below" in message.lower()

    @pytest.mark.asyncio
    async def test_price_crosses_up_alert(self, test_db):
        """Test that PRICE_CROSSES_UP alert triggers on upward crossing."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_CROSSES_UP",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
            last_triggered_price=Decimal("49000.00"),  # Was below threshold
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("51000.00"),  # Now above threshold
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True
        assert "crossed above" in message.lower()

    @pytest.mark.asyncio
    async def test_price_crosses_down_alert(self, test_db):
        """Test that PRICE_CROSSES_DOWN alert triggers on downward crossing."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_CROSSES_DOWN",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
            last_triggered_price=Decimal("51000.00"),  # Was above threshold
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("49000.00"),  # Now below threshold
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True
        assert "crossed below" in message.lower()

    @pytest.mark.asyncio
    async def test_price_change_percent_alert(self, test_db):
        """Test that PRICE_CHANGE_PERCENT alert triggers on percentage change."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_CHANGE_PERCENT",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
            last_triggered_price=Decimal("50000.00"),
            metadata={"percentage": 5.0},  # 5% change
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("53000.00"),  # 6% increase
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True
        assert "6.00%" in message

    @pytest.mark.asyncio
    async def test_debouncing_prevents_trigger(self, test_db):
        """Test that alerts respect debounce period."""
        engine = AlertEngine(test_db)

        # Alert triggered 10 seconds ago (within debounce period of 30 seconds)
        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=1,
            last_triggered_at=datetime.utcnow() - timedelta(seconds=10),
        )

        can_trigger = engine._can_trigger(alert)

        assert can_trigger is False

    @pytest.mark.asyncio
    async def test_debouncing_allows_trigger_after_period(self, test_db):
        """Test that alerts can trigger after debounce period."""
        engine = AlertEngine(test_db)

        # Alert triggered 60 seconds ago (outside debounce period of 30 seconds)
        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=1,
            last_triggered_at=datetime.utcnow() - timedelta(seconds=60),
        )

        can_trigger = engine._can_trigger(alert)

        assert can_trigger is True

    @pytest.mark.asyncio
    async def test_first_trigger_allowed(self, test_db):
        """Test that alert with no previous trigger is allowed."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
            last_triggered_at=None,
        )

        can_trigger = engine._can_trigger(alert)

        assert can_trigger is True

    @pytest.mark.asyncio
    async def test_format_message(self, test_db):
        """Test alert message formatting."""
        engine = AlertEngine(test_db)

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("51000.00"),
            is_active=True,
        )

        message = engine._format_message(
            crypto=crypto,
            condition="Price is above $50,000.00",
            current_price=Decimal("51000.00"),
            comparison_price=Decimal("50000.00"),
        )

        assert "BTC Alert" in message
        assert "51,000.00" in message
        assert "+1,000.00" in message
        assert "+2.00%" in message
        assert "UTC" in message


@pytest.mark.unit
class TestAlertEngineEvaluation:
    """Test full alert evaluation flow."""

    @pytest.mark.asyncio
    async def test_evaluate_alerts_no_active_alerts(self, test_db):
        """Test evaluation when no alerts are active."""
        engine = AlertEngine(test_db)

        # Should not raise any errors
        await engine.evaluate_alerts()

    @pytest.mark.asyncio
    async def test_evaluate_alerts_with_disabled_alert(self, test_db, sample_cryptocurrency, sample_user, sample_alert):
        """Test that disabled alerts are not evaluated."""
        # Create cryptocurrency
        crypto = await sample_cryptocurrency()

        # Create user
        user = await sample_user()

        # Create disabled alert
        alert = await sample_alert(enabled=False)

        engine = AlertEngine(test_db)

        with patch.object(engine, '_trigger_alert') as mock_trigger:
            await engine.evaluate_alerts()
            mock_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_alert_updates_database(self, test_db, sample_cryptocurrency):
        """Test that triggering alert updates database correctly."""
        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )
        test_db.add(alert)
        await test_db.commit()

        engine = AlertEngine(test_db)

        # Mock telegram client
        with patch.object(engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, 12345, None)

            await engine._trigger_alert(alert, crypto, "Test message")

        await test_db.refresh(alert)

        assert alert.trigger_count == 1
        assert alert.last_triggered_at is not None
        assert alert.last_triggered_price == Decimal("51000.00")


@pytest.mark.unit
class TestAlertEngineEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_price_exactly_at_threshold(self, test_db):
        """Test alert behavior when price exactly equals threshold."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("50000.00"),  # Exactly at threshold
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        # PRICE_ABOVE should not trigger when price equals threshold
        assert should_trigger is False

    @pytest.mark.asyncio
    async def test_very_small_price_difference(self, test_db):
        """Test alert with very small price difference."""
        engine = AlertEngine(test_db)

        alert = Alert(
            alert_id="alert1",
            user_id="user1",
            crypto_id="bitcoin",
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            telegram_chat_id="123456789",
            enabled=True,
            trigger_count=0,
        )

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("50000.01"),  # Just 1 cent above
            is_active=True,
        )

        should_trigger, message = await engine._evaluate_condition(alert, crypto)

        assert should_trigger is True

    @pytest.mark.asyncio
    async def test_negative_price_change(self, test_db):
        """Test formatting of negative price changes."""
        engine = AlertEngine(test_db)

        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            current_price=Decimal("49000.00"),
            is_active=True,
        )

        message = engine._format_message(
            crypto=crypto,
            condition="Price dropped",
            current_price=Decimal("49000.00"),
            comparison_price=Decimal("50000.00"),
        )

        assert "-1,000.00" in message
        assert "-2.00%" in message
