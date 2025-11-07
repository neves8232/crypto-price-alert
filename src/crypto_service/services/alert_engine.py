"""
Alert evaluation engine for monitoring price conditions and triggering alerts.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service.config import settings
from crypto_service.models import Alert, Cryptocurrency, AlertLog
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import (
    alerts_triggered_total,
    alerts_evaluated_total,
    alert_evaluation_duration_seconds,
)
from crypto_service.services.telegram_client import TelegramClient

logger = get_logger(__name__)


class AlertEngine:
    """
    Alert evaluation engine for checking price conditions and triggering alerts.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize alert engine.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.telegram_client = TelegramClient()

    async def evaluate_alerts(self) -> None:
        """
        Evaluate all active alerts against current prices.

        This method is called after each price update.
        """
        logger.info("evaluating_alerts")

        try:
            with alert_evaluation_duration_seconds.time():
                # Get all enabled alerts with their cryptocurrencies
                result = await self.db.execute(
                    select(Alert, Cryptocurrency)
                    .join(Cryptocurrency, Alert.crypto_id == Cryptocurrency.crypto_id)
                    .where(Alert.enabled == True)
                    .where(Cryptocurrency.is_active == True)
                    .where(Cryptocurrency.current_price != None)
                )
                alert_crypto_pairs = result.all()

                if not alert_crypto_pairs:
                    logger.info("no_active_alerts")
                    return

                logger.info("evaluating_alert_conditions", count=len(alert_crypto_pairs))

                triggered_count = 0
                for alert, crypto in alert_crypto_pairs:
                    alerts_evaluated_total.inc()

                    # Check debouncing
                    if not self._can_trigger(alert):
                        continue

                    # Evaluate alert condition
                    should_trigger, message = await self._evaluate_condition(
                        alert, crypto
                    )

                    if should_trigger:
                        await self._trigger_alert(alert, crypto, message)
                        triggered_count += 1

                logger.info("alerts_evaluated", total=len(alert_crypto_pairs), triggered=triggered_count)

        except Exception as e:
            logger.error("alert_evaluation_failed", error=str(e), exc_info=True)

    def _can_trigger(self, alert: Alert) -> bool:
        """
        Check if alert can be triggered based on debouncing rules.

        Args:
            alert: Alert instance

        Returns:
            True if alert can be triggered, False otherwise
        """
        if alert.last_triggered_at is None:
            return True

        time_since_last = datetime.utcnow() - alert.last_triggered_at
        debounce_delta = timedelta(seconds=settings.alert_debounce_seconds)

        return time_since_last >= debounce_delta

    async def _evaluate_condition(
        self, alert: Alert, crypto: Cryptocurrency
    ) -> tuple[bool, str]:
        """
        Evaluate if alert condition is met.

        Args:
            alert: Alert instance
            crypto: Cryptocurrency instance with current price

        Returns:
            Tuple of (should_trigger, message)
        """
        current_price = crypto.current_price
        threshold = alert.threshold
        last_price = alert.last_triggered_price or threshold

        alert_type = alert.alert_type
        should_trigger = False
        message = ""

        if alert_type == "PRICE_ABOVE":
            # Alert when price is above threshold
            should_trigger = current_price > threshold
            if should_trigger:
                message = self._format_message(
                    crypto,
                    f"Price is above ${threshold:,.2f}",
                    current_price,
                    threshold,
                )

        elif alert_type == "PRICE_BELOW":
            # Alert when price is below threshold
            should_trigger = current_price < threshold
            if should_trigger:
                message = self._format_message(
                    crypto,
                    f"Price is below ${threshold:,.2f}",
                    current_price,
                    threshold,
                )

        elif alert_type == "PRICE_CROSSES_UP":
            # Alert when price crosses threshold upward
            should_trigger = last_price < threshold <= current_price
            if should_trigger:
                message = self._format_message(
                    crypto,
                    f"Price crossed above ${threshold:,.2f}",
                    current_price,
                    threshold,
                )

        elif alert_type == "PRICE_CROSSES_DOWN":
            # Alert when price crosses threshold downward
            should_trigger = last_price > threshold >= current_price
            if should_trigger:
                message = self._format_message(
                    crypto,
                    f"Price crossed below ${threshold:,.2f}",
                    current_price,
                    threshold,
                )

        elif alert_type == "PRICE_CHANGE_PERCENT":
            # Alert on percentage change
            percentage = alert.metadata.get("percentage", 5.0)
            if alert.last_triggered_price:
                change_pct = abs(
                    float((current_price - last_price) / last_price * 100)
                )
                should_trigger = change_pct >= percentage
                if should_trigger:
                    direction = "increased" if current_price > last_price else "decreased"
                    message = self._format_message(
                        crypto,
                        f"Price {direction} by {change_pct:.2f}%",
                        current_price,
                        last_price,
                    )

        return should_trigger, message

    def _format_message(
        self,
        crypto: Cryptocurrency,
        condition: str,
        current_price: Decimal,
        comparison_price: Decimal,
    ) -> str:
        """
        Format alert message for Telegram.

        Args:
            crypto: Cryptocurrency instance
            condition: Alert condition description
            current_price: Current price
            comparison_price: Comparison price (threshold or last price)

        Returns:
            Formatted message string
        """
        change = current_price - comparison_price
        change_pct = float(change / comparison_price * 100) if comparison_price > 0 else 0

        message = f"""🚨 <b>{crypto.symbol} Alert</b>

{condition}

<b>Current Price:</b> ${float(current_price):,.2f}
<b>Change:</b> ${float(change):+,.2f} ({change_pct:+.2f}%)
<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        return message

    async def _trigger_alert(
        self, alert: Alert, crypto: Cryptocurrency, message: str
    ) -> None:
        """
        Trigger an alert by sending to Telegram service and updating database.

        Args:
            alert: Alert instance
            crypto: Cryptocurrency instance
            message: Alert message
        """
        logger.info(
            "triggering_alert",
            alert_id=alert.alert_id,
            crypto_id=crypto.crypto_id,
            alert_type=alert.alert_type,
            price=float(crypto.current_price),
        )

        # Send to Telegram service
        start_time = datetime.utcnow()
        success, telegram_msg_id, error_msg = await self.telegram_client.send_alert(
            chat_id=alert.telegram_chat_id,
            message=message,
            metadata={
                "alert_id": alert.alert_id,
                "user_id": alert.user_id,
                "crypto_symbol": crypto.symbol,
                "alert_type": alert.alert_type,
            },
        )
        delivery_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Update alert state
        alert.last_triggered_at = datetime.utcnow()
        alert.last_triggered_price = crypto.current_price
        alert.trigger_count += 1

        # Log alert trigger
        alert_log = AlertLog(
            alert_id=alert.alert_id,
            user_id=alert.user_id,
            crypto_id=crypto.crypto_id,
            trigger_price=crypto.current_price,
            threshold=alert.threshold,
            alert_type=alert.alert_type,
            message_sent=message,
            telegram_message_id=telegram_msg_id,
            delivery_status="sent" if success else "failed",
            delivery_time_ms=delivery_time_ms if success else None,
            error_message=error_msg,
            delivered_at=datetime.utcnow() if success else None,
        )
        self.db.add(alert_log)

        await self.db.commit()

        # Update metrics
        alerts_triggered_total.labels(
            crypto=crypto.symbol, type=alert.alert_type
        ).inc()

        if success:
            logger.info(
                "alert_triggered_successfully",
                alert_id=alert.alert_id,
                crypto=crypto.symbol,
                delivery_time_ms=delivery_time_ms,
            )
        else:
            logger.error(
                "alert_trigger_failed",
                alert_id=alert.alert_id,
                crypto=crypto.symbol,
                error=error_msg,
            )
