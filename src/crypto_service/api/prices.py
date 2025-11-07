"""
Price data endpoints.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service.database import get_db
from crypto_service.models import Cryptocurrency, PriceHistory
from crypto_service.schemas import CurrentPrice, CurrentPriceList, PriceHistoryResponse, PriceHistoryPoint
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import database_queries_total

logger = get_logger(__name__)

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/current", response_model=CurrentPriceList)
async def get_current_prices(
    crypto_ids: str = Query(None, description="Comma-separated crypto IDs"),
    db: AsyncSession = Depends(get_db),
) -> CurrentPriceList:
    """
    Get current prices for cryptocurrencies.

    Query Parameters:
        - crypto_ids: Comma-separated list of crypto IDs (optional, returns all if not specified)
    """
    database_queries_total.labels(operation="select").inc()

    query = select(Cryptocurrency).where(
        Cryptocurrency.is_active == True,
        Cryptocurrency.current_price != None,
    )

    # Filter by specific crypto IDs if provided
    if crypto_ids:
        crypto_id_list = [cid.strip() for cid in crypto_ids.split(",")]
        query = query.where(Cryptocurrency.crypto_id.in_(crypto_id_list))

    result = await db.execute(query)
    cryptos = result.scalars().all()

    prices = [
        CurrentPrice(
            crypto_id=crypto.crypto_id,
            symbol=crypto.symbol,
            price=crypto.current_price,
            timestamp=crypto.last_updated or datetime.utcnow(),
        )
        for crypto in cryptos
    ]

    return CurrentPriceList(
        prices=prices,
        timestamp=datetime.utcnow(),
    )


@router.get("/{crypto_id}/history", response_model=PriceHistoryResponse)
async def get_price_history(
    crypto_id: str,
    interval: str = Query("15m", description="Time interval: 1m, 5m, 15m, 1h, 1d"),
    limit: int = Query(100, ge=1, le=1000, description="Number of data points"),
    db: AsyncSession = Depends(get_db),
) -> PriceHistoryResponse:
    """
    Get price history for a cryptocurrency.

    Path Parameters:
        - crypto_id: Cryptocurrency ID

    Query Parameters:
        - interval: Time interval (1m, 5m, 15m, 1h, 1d)
        - limit: Number of data points to return (1-1000)
    """
    database_queries_total.labels(operation="select").inc()

    # Check if cryptocurrency exists
    result = await db.execute(
        select(Cryptocurrency).where(Cryptocurrency.crypto_id == crypto_id)
    )
    crypto = result.scalar_one_or_none()

    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    # Calculate time range based on interval
    interval_map = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1),
    }

    if interval not in interval_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interval. Must be one of: {', '.join(interval_map.keys())}",
        )

    # Query price history
    query = (
        select(PriceHistory)
        .where(PriceHistory.crypto_id == crypto_id)
        .order_by(PriceHistory.timestamp.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    price_records = result.scalars().all()

    # Convert to response format
    data_points = [
        PriceHistoryPoint(
            timestamp=record.timestamp,
            price=record.price,
            volume_24h=record.volume_24h,
        )
        for record in reversed(price_records)  # Reverse to get chronological order
    ]

    return PriceHistoryResponse(
        crypto_id=crypto_id,
        symbol=crypto.symbol,
        interval=interval,
        data_points=data_points,
    )


@router.get("/{crypto_id}/current", response_model=CurrentPrice)
async def get_current_price(
    crypto_id: str,
    db: AsyncSession = Depends(get_db),
) -> CurrentPrice:
    """
    Get current price for a specific cryptocurrency.

    Path Parameters:
        - crypto_id: Cryptocurrency ID
    """
    database_queries_total.labels(operation="select").inc()

    result = await db.execute(
        select(Cryptocurrency).where(Cryptocurrency.crypto_id == crypto_id)
    )
    crypto = result.scalar_one_or_none()

    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    if not crypto.current_price:
        raise HTTPException(status_code=404, detail="Price data not available yet")

    return CurrentPrice(
        crypto_id=crypto.crypto_id,
        symbol=crypto.symbol,
        price=crypto.current_price,
        timestamp=crypto.last_updated or datetime.utcnow(),
    )
