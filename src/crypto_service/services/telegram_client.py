"""
HTTP client for sending alerts to the Telegram service.
"""

from typing import Optional, Tuple
import httpx

from crypto_service.config import settings
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import (
    alert_dispatch_requests_total,
    alert_dispatch_latency_seconds,
)

logger = get_logger(__name__)


class TelegramClient:
    """
    HTTP client for communicating with the Telegram alert service.
    """

    def __init__(self):
        """Initialize Telegram client."""
        self.base_url = settings.telegram_service_url
        self.auth_token = settings.telegram_service_auth_token
        self.timeout = settings.telegram_service_timeout_seconds

    async def send_alert(
        self,
        chat_id: str,
        message: str,
        metadata: Optional[dict] = None,
        priority: str = "high",
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Send an alert message to the Telegram service.

        Args:
            chat_id: Telegram chat ID
            message: Alert message text
            metadata: Optional metadata for logging
            priority: Message priority (low, normal, high)

        Returns:
            Tuple of (success, telegram_message_id, error_message)
        """
        if not self.auth_token:
            logger.error("telegram_auth_token_not_configured")
            return False, None, "Telegram auth token not configured"

        url = f"{self.base_url}/api/v1/alerts/send"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "chat_id": chat_id,
            "message": message,
            "parse_mode": "HTML",
            "priority": priority,
            "metadata": metadata or {},
        }

        try:
            with alert_dispatch_latency_seconds.time():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        telegram_msg_id = data.get("message_id")
                        alert_dispatch_requests_total.labels(status="success").inc()
                        logger.info(
                            "telegram_alert_sent",
                            chat_id=chat_id[:6] + "***",  # Redact for privacy
                            message_id=telegram_msg_id,
                            delivery_time_ms=data.get("delivery_time_ms"),
                        )
                        return True, telegram_msg_id, None

                    elif response.status_code == 202:
                        # Alert queued
                        data = response.json()
                        alert_dispatch_requests_total.labels(status="queued").inc()
                        logger.info(
                            "telegram_alert_queued",
                            chat_id=chat_id[:6] + "***",
                            queue_position=data.get("queue_position"),
                        )
                        return True, None, None

                    elif response.status_code == 429:
                        # Rate limited
                        data = response.json()
                        retry_after = data.get("retry_after_seconds", 5)
                        alert_dispatch_requests_total.labels(status="rate_limited").inc()
                        logger.warning(
                            "telegram_rate_limited",
                            retry_after_seconds=retry_after,
                        )
                        return False, None, f"Rate limited, retry after {retry_after}s"

                    else:
                        # Other error
                        alert_dispatch_requests_total.labels(status="failed").inc()
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("message", "Unknown error")
                        except Exception:
                            error_msg = response.text or f"HTTP {response.status_code}"

                        logger.error(
                            "telegram_request_failed",
                            status_code=response.status_code,
                            error=error_msg,
                        )
                        return False, None, error_msg

        except httpx.TimeoutException:
            alert_dispatch_requests_total.labels(status="timeout").inc()
            logger.error("telegram_request_timeout", timeout=self.timeout)
            return False, None, f"Request timeout after {self.timeout}s"

        except httpx.RequestError as e:
            alert_dispatch_requests_total.labels(status="error").inc()
            logger.error("telegram_request_error", error=str(e))
            return False, None, str(e)

        except Exception as e:
            alert_dispatch_requests_total.labels(status="error").inc()
            logger.error("telegram_unexpected_error", error=str(e), exc_info=True)
            return False, None, str(e)

    async def health_check(self) -> bool:
        """
        Check if Telegram service is reachable.

        Returns:
            True if service is healthy, False otherwise
        """
        if not self.auth_token:
            return False

        try:
            url = f"{self.base_url}/health"
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200

        except Exception as e:
            logger.error("telegram_health_check_failed", error=str(e))
            return False
