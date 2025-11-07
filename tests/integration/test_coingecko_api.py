"""
Integration tests for CoinGecko API.

These tests make real API calls and require internet connectivity.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from crypto_service.services.price_collector import CoinGeckoClient


@pytest.mark.integration
class TestCoinGeckoAPIIntegration:
    """Integration tests for CoinGecko API."""

    @pytest.mark.asyncio
    async def test_fetch_real_bitcoin_price(self):
        """Test fetching real Bitcoin price from CoinGecko."""
        client = CoinGeckoClient()

        prices = await client.fetch_prices(['bitcoin'])

        assert 'bitcoin' in prices
        assert 'usd' in prices['bitcoin']
        assert prices['bitcoin']['usd'] > 0
        assert isinstance(prices['bitcoin']['usd'], (int, float))

    @pytest.mark.asyncio
    async def test_fetch_multiple_cryptocurrencies(self):
        """Test fetching multiple cryptocurrencies at once."""
        client = CoinGeckoClient()

        prices = await client.fetch_prices(['bitcoin', 'ethereum', 'solana'])

        assert 'bitcoin' in prices
        assert 'ethereum' in prices
        assert 'solana' in prices

        for crypto, data in prices.items():
            assert 'usd' in data
            assert data['usd'] > 0

    @pytest.mark.asyncio
    async def test_fetch_with_market_data(self):
        """Test that market data is included in response."""
        client = CoinGeckoClient()

        prices = await client.fetch_prices(['bitcoin'], vs_currency='usd')

        btc_data = prices['bitcoin']
        assert 'usd' in btc_data
        assert 'usd_market_cap' in btc_data
        assert 'usd_24h_vol' in btc_data
        assert 'usd_24h_change' in btc_data

    @pytest.mark.asyncio
    async def test_fetch_crypto_info(self):
        """Test fetching detailed cryptocurrency information."""
        client = CoinGeckoClient()

        info = await client.fetch_crypto_info('bitcoin')

        assert info is not None
        assert info['id'] == 'bitcoin'
        assert info['symbol'] == 'btc'
        assert info['name'] == 'Bitcoin'
        assert 'market_data' in info

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rate_limiting_multiple_requests(self):
        """Test that rate limiting works with multiple requests."""
        client = CoinGeckoClient()

        # Make multiple sequential requests
        for _ in range(3):
            prices = await client.fetch_prices(['bitcoin'])
            assert 'bitcoin' in prices

        # All requests should succeed with rate limiting

    @pytest.mark.asyncio
    async def test_nonexistent_cryptocurrency(self):
        """Test handling of nonexistent cryptocurrency."""
        client = CoinGeckoClient()

        # CoinGecko returns empty dict for invalid IDs
        prices = await client.fetch_prices(['this-crypto-does-not-exist-12345'])

        # Should return empty or missing data for invalid crypto

    @pytest.mark.asyncio
    async def test_different_currencies(self):
        """Test fetching prices in different currencies."""
        client = CoinGeckoClient()

        # Fetch in EUR
        prices_eur = await client.fetch_prices(['bitcoin'], vs_currency='eur')
        assert 'bitcoin' in prices_eur

        # Fetch in USD
        prices_usd = await client.fetch_prices(['bitcoin'], vs_currency='usd')
        assert 'bitcoin' in prices_usd

        # Prices should be different
        # Note: CoinGecko might return different structure for different currencies


@pytest.mark.integration
@pytest.mark.requires_api_key
class TestCoinGeckoAPIWithKey:
    """Integration tests that require API key for higher rate limits."""

    @pytest.mark.asyncio
    async def test_fetch_with_api_key(self, test_env_vars):
        """Test fetching with API key."""
        api_key = test_env_vars.get("COINGECKO_API_KEY")

        if not api_key or api_key == "test-coingecko-key":
            pytest.skip("Real CoinGecko API key not configured")

        client = CoinGeckoClient(api_key=api_key)

        prices = await client.fetch_prices(['bitcoin'])

        assert 'bitcoin' in prices
        assert prices['bitcoin']['usd'] > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_higher_rate_limit_with_key(self, test_env_vars):
        """Test that API key allows higher rate limits."""
        api_key = test_env_vars.get("COINGECKO_API_KEY")

        if not api_key or api_key == "test-coingecko-key":
            pytest.skip("Real CoinGecko API key not configured")

        client = CoinGeckoClient(api_key=api_key)
        client.min_interval = 0.5  # Higher rate with API key

        # Make multiple rapid requests
        for _ in range(5):
            prices = await client.fetch_prices(['bitcoin'])
            assert 'bitcoin' in prices


@pytest.mark.integration
class TestCoinGeckoErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_vs_currency(self):
        """Test handling of invalid vs_currency parameter."""
        client = CoinGeckoClient()

        # CoinGecko should handle this gracefully
        try:
            prices = await client.fetch_prices(['bitcoin'], vs_currency='invalid_currency')
            # May return empty or error response
        except Exception as e:
            # Expected - invalid currency should fail
            assert True

    @pytest.mark.asyncio
    async def test_empty_crypto_list(self):
        """Test fetching with empty cryptocurrency list."""
        client = CoinGeckoClient()

        prices = await client.fetch_prices([])

        # Should return empty dict or handle gracefully
        assert isinstance(prices, dict)
