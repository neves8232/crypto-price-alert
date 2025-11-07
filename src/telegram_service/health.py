"""
Health Check Logic

Performs health checks for:
- Telegram API connectivity
- Rate limiter status
- Message queue status
"""

from datetime import datetime
from typing import Dict, Any, Tuple

import structlog
from telegram.error import TelegramError

from .config import settings
from .models import HealthCheck

logger = structlog.get_logger(__name__)


async def check_telegram_api(telegram_client) -> Tuple[str, Dict[str, Any]]:
    """
    Check Telegram API connectivity.

    Args:
        telegram_client: TelegramClient instance

    Returns:
        Tuple of (status, details)
    """
    try:
        bot_info = await telegram_client.validate_token()
        return "connected", {
            "bot_username": bot_info.get("username"),
            "bot_id": bot_info.get("id"),
        }
    except TelegramError as e:
        logger.error("health_check_telegram_failed", error=str(e))
        return "disconnected", {
            "error": str(e),
            "error_type": type(e).__name__,
        }
    except Exception as e:
        logger.error("health_check_telegram_unexpected_error", error=str(e))
        return "error", {"error": str(e)}


async def check_rate_limiter(rate_limiter) -> Tuple[str, Dict[str, Any]]:
    """
    Check rate limiter status.

    Args:
        rate_limiter: RateLimiter instance

    Returns:
        Tuple of (status, details)
    """
    try:
        status = await rate_limiter.get_status()
        return "operational", status
    except Exception as e:
        logger.error("health_check_rate_limiter_failed", error=str(e))
        return "error", {"error": str(e)}


def check_queue(queue_size: int, queue_capacity: int) -> Tuple[str, Dict[str, Any]]:
    """
    Check message queue status.

    Args:
        queue_size: Current queue size
        queue_capacity: Maximum queue capacity

    Returns:
        Tuple of (status, details)
    """
    utilization = queue_size / queue_capacity if queue_capacity > 0 else 0

    if utilization >= 0.9:
        status = "critical"
    elif utilization >= 0.7:
        status = "warning"
    else:
        status = "normal"

    return status, {
        "size": queue_size,
        "capacity": queue_capacity,
        "utilization_percent": round(utilization * 100, 2),
    }


async def perform_health_check(
    telegram_client,
    rate_limiter,
    queue_size: int = 0,
) -> HealthCheck:
    """
    Perform comprehensive health check.

    Args:
        telegram_client: TelegramClient instance
        rate_limiter: RateLimiter instance
        queue_size: Current queue size

    Returns:
        HealthCheck model with results
    """
    checks = {}
    errors = []
    overall_status = "healthy"

    # Check Telegram API
    telegram_status, telegram_details = await check_telegram_api(telegram_client)
    checks["telegram_api"] = telegram_status
    checks["telegram_details"] = telegram_details

    if telegram_status == "disconnected":
        overall_status = "unhealthy"
        errors.append("Telegram API is unreachable")
    elif telegram_status == "error":
        overall_status = "degraded"
        errors.append("Telegram API check encountered an error")

    # Check rate limiter
    rate_limiter_status, rate_limiter_details = await check_rate_limiter(rate_limiter)
    checks["rate_limiter"] = rate_limiter_status
    checks["rate_limiter_details"] = rate_limiter_details

    if rate_limiter_status == "error":
        overall_status = "degraded"
        errors.append("Rate limiter check failed")

    # Check queue
    queue_status, queue_details = check_queue(queue_size, settings.queue_max_size)
    checks["queue_status"] = queue_status
    checks["queue"] = queue_details

    if queue_status == "critical":
        overall_status = "degraded"
        errors.append(f"Queue is {queue_details['utilization_percent']}% full")

    # Overall status logic:
    # - unhealthy: Telegram API down (critical dependency)
    # - degraded: Other issues but service can still function
    # - healthy: All checks passed

    return HealthCheck(
        status=overall_status,
        service=settings.app_name,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        checks=checks,
        errors=errors if errors else None,
    )
