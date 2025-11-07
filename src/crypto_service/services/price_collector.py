"""
CoinGecko API client for fetching cryptocurrency prices.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_service.config import settings
from crypto_service.models import Cryptocurrency, PriceHistory
from crypto_service.utils.logging import get_logger
from crypto_service.utils.metrics import (
    api_requests_total,
    api_latency_seconds,
    price_updates_total,
)

logger = get_logger(__name__)


class CoinGeckoClient:
    """
    CoinGecko API client for fetching cryptocurrency prices.

    Handles rate limiting, retries, and error handling for CoinGecko API.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko client.

        Args:
            api_key: Optional CoinGecko API key for higher rate limits
        """
        self.api_key = api_key
        self.last_request_time = 0.0
        self.min_interval = 2.0  # 30 calls/min = 2 seconds between calls

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits."""
        if self.last_request_time > 0:
            elapsed = asyncio.get_event_loop().time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    async def fetch_prices(
        self, crypto_ids: list[str], vs_currency: str = "usd"
    ) -> dict[str, dict]:
        """
        Fetch current prices for multiple cryptocurrencies.

        Args:
            crypto_ids: List of cryptocurrency IDs (e.g., ["bitcoin", "ethereum"])
            vs_currency: Currency to get prices in (default: "usd")

        Returns:
            Dictionary mapping crypto_id to price data

        Raises:
            httpx.HTTPError: If API request fails after retries
        """
        await self._wait_for_rate_limit()

        # Build request parameters
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        }

        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key

        url = f"{self.BASE_URL}/simple/price"

        # Retry logic with exponential backoff
        for attempt in range(self.MAX_RETRIES):
            try:
                with api_latency_seconds.labels(provider="coingecko").time():
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url, params=params, headers=headers)

                        # Handle rate limiting
                        if response.status_code == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            logger.warning(
                                "rate_limit_exceeded",
                                retry_after=retry_after,
                                attempt=attempt + 1,
                            )
                            api_requests_total.labels(
                                provider="coingecko", status="rate_limited"
                            ).inc()
                            await asyncio.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        data = response.json()

                        api_requests_total.labels(
                            provider="coingecko", status="success"
                        ).inc()
                        logger.info(
                            "prices_fetched",
                            crypto_count=len(data),
                            cryptos=list(data.keys()),
                        )
                        return data

            except httpx.HTTPError as e:
                api_requests_total.labels(provider="coingecko", status="failed").inc()
                logger.error(
                    "api_request_failed",
                    error=str(e),
                    attempt=attempt + 1,
                    max_retries=self.MAX_RETRIES,
                )

                if attempt == self.MAX_RETRIES - 1:
                    raise

                # Exponential backoff
                await asyncio.sleep(self.RETRY_DELAY * (2**attempt))

        return {}

    async def fetch_crypto_info(self, crypto_id: str) -> Optional[dict]:
        """
        Fetch detailed information about a cryptocurrency.

        Args:
            crypto_id: Cryptocurrency ID (e.g., "bitcoin")

        Returns:
            Dictionary with cryptocurrency information or None if not found
        """
        await self._wait_for_rate_limit()

        url = f"{self.BASE_URL}/coins/{crypto_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }

        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("fetch_crypto_info_failed", crypto_id=crypto_id, error=str(e))
            return None


class PriceCollectorService:
    """
    Service for collecting and storing cryptocurrency prices.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize price collector service.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.client = CoinGeckoClient(api_key=settings.coingecko_api_key)

    async def collect_prices(self) -> None:
        """
        Collect current prices for all active cryptocurrencies.

        This method is called periodically by the scheduler.
        """
        logger.info("collecting_prices")

        try:
            # Get all active cryptocurrencies
            result = await self.db.execute(
                select(Cryptocurrency).where(Cryptocurrency.is_active == True)
            )
            cryptos = result.scalars().all()

            if not cryptos:
                logger.info("no_active_cryptocurrencies")
                return

            crypto_ids = [crypto.crypto_id for crypto in cryptos]
            logger.info("fetching_prices", crypto_count=len(crypto_ids))

            # Fetch prices from CoinGecko
            price_data = await self.client.fetch_prices(crypto_ids)

            if not price_data:
                logger.warning("no_price_data_received")
                return

            # Update database with new prices
            now = datetime.utcnow()
            for crypto in cryptos:
                if crypto.crypto_id not in price_data:
                    logger.warning(
                        "price_data_missing", crypto_id=crypto.crypto_id
                    )
                    continue

                data = price_data[crypto.crypto_id]
                price = Decimal(str(data.get("usd", 0)))

                if price <= 0:
                    continue

                # Update cryptocurrency current price
                crypto.current_price = price
                crypto.market_cap = data.get("usd_market_cap")
                crypto.volume_24h = data.get("usd_24h_vol")
                crypto.price_change_24h = (
                    Decimal(str(data["usd_24h_change"]))
                    if data.get("usd_24h_change")
                    else None
                )
                crypto.last_updated = now

                # Store in price history
                price_history = PriceHistory(
                    crypto_id=crypto.crypto_id,
                    price=price,
                    volume_24h=crypto.volume_24h,
                    timestamp=now,
                    source="coingecko",
                )
                self.db.add(price_history)

                # Update metrics
                price_updates_total.labels(crypto=crypto.symbol).inc()

                logger.info(
                    "price_updated",
                    crypto_id=crypto.crypto_id,
                    symbol=crypto.symbol,
                    price=float(price),
                )

            await self.db.commit()
            logger.info("prices_collected_successfully", count=len(price_data))

        except Exception as e:
            logger.error("price_collection_failed", error=str(e), exc_info=True)
            await self.db.rollback()
            raise

    async def add_cryptocurrency(
        self, crypto_id: str, symbol: str, name: str
    ) -> Cryptocurrency:
        """
        Add a new cryptocurrency to the watchlist.

        Args:
            crypto_id: Cryptocurrency ID (e.g., "bitcoin")
            symbol: Symbol (e.g., "BTC")
            name: Name (e.g., "Bitcoin")

        Returns:
            Created Cryptocurrency instance
        """
        # Check if already exists
        result = await self.db.execute(
            select(Cryptocurrency).where(Cryptocurrency.crypto_id == crypto_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                await self.db.commit()
            return existing

        # Create new cryptocurrency
        crypto = Cryptocurrency(
            crypto_id=crypto_id,
            symbol=symbol.upper(),
            name=name,
            is_active=True,
        )
        self.db.add(crypto)
        await self.db.commit()
        await self.db.refresh(crypto)

        logger.info(
            "cryptocurrency_added",
            crypto_id=crypto_id,
            symbol=symbol,
            name=name,
        )

        return crypto
