"""
Health check and metrics endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service import __version__
from crypto_service.config import settings
from crypto_service.database import get_db
from crypto_service.models import Alert, Cryptocurrency, AlertLog
from crypto_service.schemas import HealthCheck
from crypto_service.services.telegram_client import TelegramClient
from crypto_service.utils.metrics import metrics_endpoint
from crypto_service.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    """
    Health check endpoint.

    Returns service health status and component checks.
    """
    checks = {}
    overall_status = "healthy"

    # Check database connection
    try:
        await db.execute(select(1))
        checks["database"] = "connected"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["database"] = "disconnected"
        overall_status = "unhealthy"

    # Check Telegram service
    telegram_client = TelegramClient()
    telegram_healthy = await telegram_client.health_check()
    checks["telegram_service"] = "connected" if telegram_healthy else "disconnected"
    if not telegram_healthy:
        overall_status = "degraded"  # Not critical for main service

    # Get active monitors count
    try:
        result = await db.execute(
            select(func.count(Alert.alert_id)).where(Alert.enabled == True)
        )
        checks["active_monitors"] = result.scalar_one()
    except Exception:
        checks["active_monitors"] = 0

    # Get alerts triggered in last hour
    try:
        one_hour_ago = datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        )
        result = await db.execute(
            select(func.count(AlertLog.log_id)).where(
                AlertLog.triggered_at >= one_hour_ago
            )
        )
        checks["alerts_triggered_last_hour"] = result.scalar_one()
    except Exception:
        checks["alerts_triggered_last_hour"] = 0

    # Get active cryptocurrencies count
    try:
        result = await db.execute(
            select(func.count(Cryptocurrency.crypto_id)).where(
                Cryptocurrency.is_active == True
            )
        )
        checks["active_cryptocurrencies"] = result.scalar_one()
    except Exception:
        checks["active_cryptocurrencies"] = 0

    # Check if prices are stale (no update in 5 minutes)
    try:
        result = await db.execute(
            select(func.max(Cryptocurrency.last_updated)).where(
                Cryptocurrency.is_active == True
            )
        )
        last_update = result.scalar_one_or_none()
        if last_update:
            time_since_update = (datetime.utcnow() - last_update).total_seconds()
            if time_since_update > 300:  # 5 minutes
                checks["price_updates"] = "stale"
                overall_status = "degraded"
            else:
                checks["price_updates"] = "current"
        else:
            checks["price_updates"] = "no_data"
    except Exception:
        checks["price_updates"] = "unknown"

    return HealthCheck(
        status=overall_status,
        service=settings.app_name,
        version=__version__,
        timestamp=datetime.utcnow(),
        checks=checks,
    )


@router.get("/metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    return metrics_endpoint()
