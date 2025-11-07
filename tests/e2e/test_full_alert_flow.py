"""
End-to-end tests for complete alert flow.

Tests the full system from price fetch to alert delivery.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from crypto_service.services.price_collector import PriceCollectorService
from crypto_service.services.alert_engine import AlertEngine
from crypto_service.models import Alert


@pytest.mark.e2e
class TestFullAlertFlow:
    """End-to-end tests for complete alert flow."""

    @pytest.mark.asyncio
    async def test_complete_price_above_alert_flow(
        self, test_db, sample_user, sample_cryptocurrency, sample_alert
    ):
        """
        Test complete flow:
        1. Create cryptocurrency and alert
        2. Fetch price update
        3. Evaluate alert
        4. Send to Telegram
        5. Log in database
        """
        # 1. Setup: Create user, crypto, and alert
        user = await sample_user()
        crypto = await sample_cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            current_price=Decimal("45000.00")  # Below threshold
        )

        alert = await sample_alert(
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),  # Alert when price goes above 50k
            telegram_chat_id=user.telegram_chat_id,
            enabled=True,
        )

        # 2. Simulate price update
        price_collector = PriceCollectorService(test_db)

        mock_price_data = {
            "bitcoin": {
                "usd": 51000.00,  # Price now above threshold
                "usd_market_cap": 1000000000,
                "usd_24h_vol": 50000000,
                "usd_24h_change": 2.5,
            }
        }

        with patch.object(price_collector.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_price_data
            await price_collector.collect_prices()

        # Refresh crypto to get updated price
        await test_db.refresh(crypto)
        assert crypto.current_price == Decimal("51000.00")

        # 3. Evaluate alerts
        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, 12345, None)  # Success, message_id, no error

            await alert_engine.evaluate_alerts()

            # Verify Telegram send was called
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args.kwargs["chat_id"] == user.telegram_chat_id
            assert "51,000.00" in call_args.kwargs["message"]

        # 4. Verify alert state was updated
        await test_db.refresh(alert)
        assert alert.trigger_count == 1
        assert alert.last_triggered_at is not None
        assert alert.last_triggered_price == Decimal("51000.00")

        # 5. Verify alert log was created
        from crypto_service.models import AlertLog
        from sqlalchemy import select

        result = await test_db.execute(
            select(AlertLog).where(AlertLog.alert_id == alert.alert_id)
        )
        logs = result.scalars().all()

        assert len(logs) == 1
        assert logs[0].delivery_status == "sent"
        assert logs[0].telegram_message_id == 12345
        assert logs[0].trigger_price == Decimal("51000.00")

    @pytest.mark.asyncio
    async def test_alert_debouncing_prevents_spam(
        self, test_db, sample_user, sample_cryptocurrency, sample_alert
    ):
        """Test that debouncing prevents repeated alerts."""
        user = await sample_user()
        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        alert = await sample_alert(
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            enabled=True,
        )

        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, 12345, None)

            # First evaluation - should trigger
            await alert_engine.evaluate_alerts()
            assert mock_send.call_count == 1

            # Second evaluation immediately after - should NOT trigger (debouncing)
            await alert_engine.evaluate_alerts()
            assert mock_send.call_count == 1  # Still 1, not called again

    @pytest.mark.asyncio
    async def test_multiple_alerts_on_same_crypto(
        self, test_db, sample_cryptocurrency
    ):
        """Test multiple users with alerts on same cryptocurrency."""
        from crypto_service.models import User

        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        # Create multiple users with alerts
        users_and_alerts = []
        for i in range(3):
            user = User(
                user_id=f"user{i}",
                telegram_chat_id=f"chat{i}",
            )
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)

            alert = Alert(
                alert_id=f"alert{i}",
                user_id=user.user_id,
                crypto_id=crypto.crypto_id,
                alert_type="PRICE_ABOVE",
                threshold=Decimal("50000.00"),
                telegram_chat_id=user.telegram_chat_id,
                enabled=True,
                trigger_count=0,
            )
            test_db.add(alert)
            await test_db.commit()
            users_and_alerts.append((user, alert))

        # Evaluate alerts
        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, 12345, None)

            await alert_engine.evaluate_alerts()

            # All 3 alerts should trigger
            assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_price_crosses_down_flow(
        self, test_db, sample_user, sample_cryptocurrency
    ):
        """Test PRICE_CROSSES_DOWN alert flow."""
        user = await sample_user()
        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        # Create alert with last triggered price above threshold
        alert = Alert(
            alert_id="alert1",
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_CROSSES_DOWN",
            threshold=Decimal("50000.00"),
            telegram_chat_id=user.telegram_chat_id,
            enabled=True,
            trigger_count=0,
            last_triggered_price=Decimal("51000.00"),  # Was above
        )
        test_db.add(alert)
        await test_db.commit()

        # Update price to below threshold
        price_collector = PriceCollectorService(test_db)

        mock_price_data = {
            "bitcoin": {
                "usd": 49000.00,  # Now below threshold
                "usd_market_cap": 1000000000,
                "usd_24h_vol": 50000000,
            }
        }

        with patch.object(price_collector.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_price_data
            await price_collector.collect_prices()

        await test_db.refresh(crypto)

        # Evaluate alerts
        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, 12345, None)

            await alert_engine.evaluate_alerts()

            # Alert should trigger
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "crossed below" in call_args.kwargs["message"].lower()


@pytest.mark.e2e
@pytest.mark.slow
class TestAlertFlowErrorHandling:
    """Test error handling in alert flow."""

    @pytest.mark.asyncio
    async def test_telegram_send_failure_logged(
        self, test_db, sample_user, sample_cryptocurrency, sample_alert
    ):
        """Test that Telegram send failures are logged."""
        user = await sample_user()
        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        alert = await sample_alert(
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            enabled=True,
        )

        alert_engine = AlertEngine(test_db)

        # Mock Telegram send to fail
        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (False, None, "Network error")

            await alert_engine.evaluate_alerts()

        # Verify failure was logged
        from crypto_service.models import AlertLog
        from sqlalchemy import select

        result = await test_db.execute(
            select(AlertLog).where(AlertLog.alert_id == alert.alert_id)
        )
        logs = result.scalars().all()

        assert len(logs) == 1
        assert logs[0].delivery_status == "failed"
        assert logs[0].error_message == "Network error"

    @pytest.mark.asyncio
    async def test_disabled_alert_not_evaluated(
        self, test_db, sample_user, sample_cryptocurrency, sample_alert
    ):
        """Test that disabled alerts are not evaluated."""
        user = await sample_user()
        crypto = await sample_cryptocurrency(current_price=Decimal("51000.00"))

        alert = await sample_alert(
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            enabled=False,  # Disabled
        )

        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            await alert_engine.evaluate_alerts()

            # Should not send anything
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_inactive_crypto_alerts_not_evaluated(
        self, test_db, sample_user, sample_cryptocurrency, sample_alert
    ):
        """Test that alerts for inactive cryptocurrencies are not evaluated."""
        user = await sample_user()
        crypto = await sample_cryptocurrency(
            current_price=Decimal("51000.00"),
            is_active=False  # Inactive
        )

        alert = await sample_alert(
            user_id=user.user_id,
            crypto_id=crypto.crypto_id,
            alert_type="PRICE_ABOVE",
            threshold=Decimal("50000.00"),
            enabled=True,
        )

        alert_engine = AlertEngine(test_db)

        with patch.object(alert_engine.telegram_client, 'send_alert', new_callable=AsyncMock) as mock_send:
            await alert_engine.evaluate_alerts()

            # Should not send for inactive crypto
            mock_send.assert_not_called()
