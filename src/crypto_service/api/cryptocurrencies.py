"""
Cryptocurrency management endpoints.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service.database import get_db
from crypto_service.models import Cryptocurrency
from crypto_service.schemas import (
    CryptocurrencyCreate,
    CryptocurrencyResponse,
    CryptocurrencyList,
)
from crypto_service.services.price_collector import PriceCollectorService
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import database_queries_total, active_crypto_monitors_gauge

logger = get_logger(__name__)

router = APIRouter(prefix="/api/cryptocurrencies", tags=["cryptocurrencies"])


@router.get("", response_model=CryptocurrencyList)
async def list_cryptocurrencies(
    search: str = Query(None, description="Search by name or symbol"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
) -> CryptocurrencyList:
    """
    List all monitored cryptocurrencies.

    Query Parameters:
        - search: Optional search term for name or symbol
        - limit: Maximum results to return (1-100)
        - offset: Number of results to skip
    """
    database_queries_total.labels(operation="select").inc()

    query = select(Cryptocurrency).where(Cryptocurrency.is_active == True)

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Cryptocurrency.name.ilike(search_term))
            | (Cryptocurrency.symbol.ilike(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()

    # Apply pagination
    query = query.order_by(Cryptocurrency.symbol).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    cryptocurrencies = result.scalars().all()

    # Update metrics
    active_crypto_monitors_gauge.set(total)

    return CryptocurrencyList(
        cryptocurrencies=[
            CryptocurrencyResponse.model_validate(crypto) for crypto in cryptocurrencies
        ],
        total=total,
    )


@router.post("", response_model=CryptocurrencyResponse, status_code=201)
async def add_cryptocurrency(
    crypto_data: CryptocurrencyCreate,
    db: AsyncSession = Depends(get_db),
) -> CryptocurrencyResponse:
    """
    Add a new cryptocurrency to the watchlist.

    Request Body:
        - crypto_id: Unique cryptocurrency ID (e.g., "bitcoin")
        - symbol: Symbol (e.g., "BTC")
        - name: Full name (e.g., "Bitcoin")
    """
    database_queries_total.labels(operation="insert").inc()

    logger.info(
        "adding_cryptocurrency",
        crypto_id=crypto_data.crypto_id,
        symbol=crypto_data.symbol,
    )

    # Use price collector service to add crypto
    collector = PriceCollectorService(db)
    crypto = await collector.add_cryptocurrency(
        crypto_id=crypto_data.crypto_id,
        symbol=crypto_data.symbol,
        name=crypto_data.name,
    )

    return CryptocurrencyResponse.model_validate(crypto)


@router.get("/{crypto_id}", response_model=CryptocurrencyResponse)
async def get_cryptocurrency(
    crypto_id: str,
    db: AsyncSession = Depends(get_db),
) -> CryptocurrencyResponse:
    """
    Get details of a specific cryptocurrency.

    Path Parameters:
        - crypto_id: Cryptocurrency ID (e.g., "bitcoin")
    """
    database_queries_total.labels(operation="select").inc()

    result = await db.execute(
        select(Cryptocurrency).where(Cryptocurrency.crypto_id == crypto_id)
    )
    crypto = result.scalar_one_or_none()

    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    return CryptocurrencyResponse.model_validate(crypto)


@router.delete("/{crypto_id}", status_code=204)
async def remove_cryptocurrency(
    crypto_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a cryptocurrency from the watchlist.

    Path Parameters:
        - crypto_id: Cryptocurrency ID to remove
    """
    database_queries_total.labels(operation="update").inc()

    result = await db.execute(
        select(Cryptocurrency).where(Cryptocurrency.crypto_id == crypto_id)
    )
    crypto = result.scalar_one_or_none()

    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    # Soft delete by setting is_active to False
    crypto.is_active = False
    await db.commit()

    logger.info("cryptocurrency_removed", crypto_id=crypto_id, symbol=crypto.symbol)
