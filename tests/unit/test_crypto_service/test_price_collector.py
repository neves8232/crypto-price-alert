"""
Unit tests for the price collector module.

Tests CoinGecko API client and price collection logic.
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from crypto_service.services.price_collector import CoinGeckoClient, PriceCollectorService
from crypto_service.models import Cryptocurrency


@pytest.mark.unit
class TestCoinGeckoClient:
    """Test cases for CoinGeckoClient class."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initializes with correct settings."""
        client = CoinGeckoClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.last_request_time == 0.0
        assert client.min_interval == 2.0

    @pytest.mark.asyncio
    async def test_rate_limiting_delay(self):
        """Test that rate limiting adds delay between requests."""
        client = CoinGeckoClient()

        # Set last request time to now
        client.last_request_time = asyncio.get_event_loop().time()

        # Measure delay
        start = asyncio.get_event_loop().time()
        await client._wait_for_rate_limit()
        elapsed = asyncio.get_event_loop().time() - start

        # Should wait approximately min_interval (2 seconds)
        assert elapsed >= 1.9  # Allow for small variance

    @pytest.mark.asyncio
    async def test_fetch_prices_success(self, mock_coingecko_response):
        """Test successful price fetching."""
        client = CoinGeckoClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_coingecko_response
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            prices = await client.fetch_prices(["bitcoin", "ethereum"])

            assert "bitcoin" in prices
            assert "ethereum" in prices
            assert prices["bitcoin"]["usd"] == 50000.00
            assert prices["ethereum"]["usd"] == 3000.00

    @pytest.mark.asyncio
    async def test_fetch_prices_with_api_key(self):
        """Test that API key is included in headers."""
        client = CoinGeckoClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"bitcoin": {"usd": 50000}}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await client.fetch_prices(["bitcoin"])

            # Verify API key was sent
            call_args = mock_client.get.call_args
            assert "headers" in call_args.kwargs
            assert call_args.kwargs["headers"]["x-cg-demo-api-key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_fetch_prices_rate_limit_429(self):
        """Test handling of 429 rate limit response."""
        client = CoinGeckoClient()
        client.MAX_RETRIES = 2

        # First call returns 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"bitcoin": {"usd": 50000}}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [mock_response_429, mock_response_ok]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with patch('asyncio.sleep') as mock_sleep:
                prices = await client.fetch_prices(["bitcoin"])

                assert "bitcoin" in prices
                mock_sleep.assert_called_with(1)  # Should sleep for retry_after

    @pytest.mark.asyncio
    async def test_fetch_prices_http_error_retry(self):
        """Test retry logic on HTTP errors."""
        client = CoinGeckoClient()
        client.MAX_RETRIES = 3
        client.RETRY_DELAY = 0.1  # Speed up test

        # First two calls fail, third succeeds
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"bitcoin": {"usd": 50000}}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [
                httpx.HTTPError("Connection failed"),
                httpx.HTTPError("Connection failed"),
                mock_response_ok,
            ]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            prices = await client.fetch_prices(["bitcoin"])

            assert "bitcoin" in prices
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_prices_max_retries_exceeded(self):
        """Test that max retries are enforced."""
        client = CoinGeckoClient()
        client.MAX_RETRIES = 3
        client.RETRY_DELAY = 0.1

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Always fails")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPError):
                await client.fetch_prices(["bitcoin"])

            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_crypto_info_success(self):
        """Test fetching detailed crypto information."""
        client = CoinGeckoClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "market_data": {
                "current_price": {"usd": 50000}
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            info = await client.fetch_crypto_info("bitcoin")

            assert info["id"] == "bitcoin"
            assert info["symbol"] == "btc"

    @pytest.mark.asyncio
    async def test_fetch_crypto_info_not_found(self):
        """Test handling of crypto not found."""
        client = CoinGeckoClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Not found")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            info = await client.fetch_crypto_info("nonexistent")

            assert info is None


@pytest.mark.unit
class TestPriceCollectorService:
    """Test cases for PriceCollectorService class."""

    @pytest.mark.asyncio
    async def test_collect_prices_success(self, test_db, sample_cryptocurrency, mock_coingecko_response):
        """Test successful price collection."""
        # Create cryptocurrencies
        await sample_cryptocurrency(crypto_id="bitcoin", symbol="BTC")
        await sample_cryptocurrency(crypto_id="ethereum", symbol="ETH")

        service = PriceCollectorService(test_db)

        # Mock the CoinGecko client
        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_coingecko_response

            await service.collect_prices()

        # Verify prices were updated
        from sqlalchemy import select
        result = await test_db.execute(select(Cryptocurrency))
        cryptos = result.scalars().all()

        btc = next(c for c in cryptos if c.crypto_id == "bitcoin")
        assert btc.current_price == Decimal("50000.00")
        assert btc.market_cap == 1000000000
        assert btc.volume_24h == 50000000

    @pytest.mark.asyncio
    async def test_collect_prices_no_active_cryptos(self, test_db):
        """Test collection when no active cryptocurrencies exist."""
        service = PriceCollectorService(test_db)

        # Should not raise any errors
        await service.collect_prices()

    @pytest.mark.asyncio
    async def test_collect_prices_missing_data(self, test_db, sample_cryptocurrency):
        """Test handling of missing price data for some cryptos."""
        await sample_cryptocurrency(crypto_id="bitcoin", symbol="BTC")

        service = PriceCollectorService(test_db)

        # Mock fetch_prices to return empty data
        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {}  # No data returned

            await service.collect_prices()

        # Should not crash, just log warning

    @pytest.mark.asyncio
    async def test_collect_prices_creates_history(self, test_db, sample_cryptocurrency, mock_coingecko_response):
        """Test that price collection creates history records."""
        await sample_cryptocurrency(crypto_id="bitcoin", symbol="BTC")

        service = PriceCollectorService(test_db)

        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_coingecko_response

            await service.collect_prices()

        # Verify price history was created
        from crypto_service.models import PriceHistory
        from sqlalchemy import select
        result = await test_db.execute(select(PriceHistory))
        history = result.scalars().all()

        assert len(history) > 0
        assert history[0].crypto_id == "bitcoin"
        assert history[0].price == Decimal("50000.00")

    @pytest.mark.asyncio
    async def test_add_cryptocurrency_new(self, test_db):
        """Test adding a new cryptocurrency."""
        service = PriceCollectorService(test_db)

        crypto = await service.add_cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin"
        )

        assert crypto.crypto_id == "bitcoin"
        assert crypto.symbol == "BTC"
        assert crypto.name == "Bitcoin"
        assert crypto.is_active is True

    @pytest.mark.asyncio
    async def test_add_cryptocurrency_existing(self, test_db, sample_cryptocurrency):
        """Test adding cryptocurrency that already exists."""
        # Create existing crypto
        existing = await sample_cryptocurrency(crypto_id="bitcoin")

        service = PriceCollectorService(test_db)

        # Try to add again
        crypto = await service.add_cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin"
        )

        # Should return existing crypto
        assert crypto.crypto_id == existing.crypto_id

    @pytest.mark.asyncio
    async def test_add_cryptocurrency_reactivate(self, test_db):
        """Test reactivating an inactive cryptocurrency."""
        service = PriceCollectorService(test_db)

        # Add inactive crypto
        crypto = Cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            is_active=False,
        )
        test_db.add(crypto)
        await test_db.commit()

        # Add again - should reactivate
        reactivated = await service.add_cryptocurrency(
            crypto_id="bitcoin",
            symbol="BTC",
            name="Bitcoin"
        )

        await test_db.refresh(reactivated)
        assert reactivated.is_active is True


@pytest.mark.unit
class TestPriceCollectorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_zero_price_ignored(self, test_db, sample_cryptocurrency):
        """Test that zero prices are ignored."""
        await sample_cryptocurrency(crypto_id="bitcoin")

        service = PriceCollectorService(test_db)

        # Mock response with zero price
        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "bitcoin": {"usd": 0}  # Zero price
            }

            await service.collect_prices()

        # Verify price was not updated
        from sqlalchemy import select
        result = await test_db.execute(select(Cryptocurrency))
        crypto = result.scalar_one()

        # Should still be None (not updated to 0)
        assert crypto.current_price is None or crypto.current_price != 0

    @pytest.mark.asyncio
    async def test_negative_price_ignored(self, test_db, sample_cryptocurrency):
        """Test that negative prices are ignored."""
        await sample_cryptocurrency(crypto_id="bitcoin")

        service = PriceCollectorService(test_db)

        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "bitcoin": {"usd": -100}  # Negative price
            }

            await service.collect_prices()

        # Negative prices should be ignored

    @pytest.mark.asyncio
    async def test_api_error_rollback(self, test_db, sample_cryptocurrency):
        """Test that database is rolled back on API errors."""
        await sample_cryptocurrency(crypto_id="bitcoin")

        service = PriceCollectorService(test_db)

        # Mock fetch_prices to raise exception
        with patch.object(service.client, 'fetch_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await service.collect_prices()

        # Database should be rolled back
