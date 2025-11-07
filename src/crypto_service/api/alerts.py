"""
Alert management endpoints.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service.database import get_db
from crypto_service.models import Alert, Cryptocurrency
from crypto_service.schemas import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertList,
)
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import database_queries_total, active_alerts_gauge

logger = get_logger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertList)
async def list_alerts(
    user_id: str = Query(None, description="Filter by user ID"),
    crypto_id: str = Query(None, description="Filter by cryptocurrency ID"),
    enabled: bool = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
) -> AlertList:
    """
    List alerts with optional filters.

    Query Parameters:
        - user_id: Filter by user ID
        - crypto_id: Filter by cryptocurrency ID
        - enabled: Filter by enabled status
    """
    database_queries_total.labels(operation="select").inc()

    query = select(Alert)

    # Apply filters
    if user_id:
        query = query.where(Alert.user_id == user_id)
    if crypto_id:
        query = query.where(Alert.crypto_id == crypto_id)
    if enabled is not None:
        query = query.where(Alert.enabled == enabled)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()

    # Execute query
    query = query.order_by(Alert.created_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()

    # Update metrics
    if enabled is None or enabled:
        active_alerts_gauge.set(
            sum(1 for alert in alerts if alert.enabled)
        )

    return AlertList(
        alerts=[AlertResponse.model_validate(alert) for alert in alerts],
        total=total,
    )


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """
    Create a new alert.

    Request Body:
        - user_id: User ID who owns the alert
        - crypto_id: Cryptocurrency ID to monitor
        - alert_type: Type of alert (PRICE_ABOVE, PRICE_BELOW, etc.)
        - threshold: Price threshold
        - telegram_chat_id: Telegram chat ID for notifications
        - enabled: Whether alert is enabled (default: true)
        - metadata: Additional alert configuration
    """
    database_queries_total.labels(operation="insert").inc()

    # Check if cryptocurrency exists
    result = await db.execute(
        select(Cryptocurrency).where(Cryptocurrency.crypto_id == alert_data.crypto_id)
    )
    crypto = result.scalar_one_or_none()

    if not crypto:
        raise HTTPException(
            status_code=404,
            detail=f"Cryptocurrency '{alert_data.crypto_id}' not found. Add it first.",
        )

    # Create alert
    alert = Alert(
        alert_id=str(uuid.uuid4()),
        user_id=alert_data.user_id,
        crypto_id=alert_data.crypto_id,
        alert_type=alert_data.alert_type,
        threshold=alert_data.threshold,
        telegram_chat_id=alert_data.telegram_chat_id,
        enabled=alert_data.enabled,
        metadata=alert_data.metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info(
        "alert_created",
        alert_id=alert.alert_id,
        user_id=alert.user_id,
        crypto_id=alert.crypto_id,
        alert_type=alert.alert_type,
    )

    return AlertResponse.model_validate(alert)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """
    Get details of a specific alert.

    Path Parameters:
        - alert_id: Alert ID
    """
    database_queries_total.labels(operation="select").inc()

    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """
    Update an existing alert.

    Path Parameters:
        - alert_id: Alert ID to update

    Request Body:
        - threshold: New threshold value (optional)
        - enabled: Enable/disable alert (optional)
        - metadata: Updated metadata (optional)
    """
    database_queries_total.labels(operation="update").inc()

    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields
    if alert_update.threshold is not None:
        alert.threshold = alert_update.threshold
    if alert_update.enabled is not None:
        alert.enabled = alert_update.enabled
    if alert_update.metadata is not None:
        alert.metadata = alert_update.metadata

    alert.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    logger.info("alert_updated", alert_id=alert_id)

    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an alert.

    Path Parameters:
        - alert_id: Alert ID to delete
    """
    database_queries_total.labels(operation="delete").inc()

    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    logger.info("alert_deleted", alert_id=alert_id)
