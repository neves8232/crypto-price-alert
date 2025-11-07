"""
Unit tests for the rate limiter module.

Tests the token bucket algorithm and rate limiting logic.
"""

import asyncio
import time
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from telegram_service.rate_limiter import TokenBucket, RateLimiter


@pytest.mark.unit
class TestTokenBucket:
    """Test cases for TokenBucket class."""

    @pytest.mark.asyncio
    async def test_bucket_initialization(self):
        """Test that token bucket initializes with correct values."""
        bucket = TokenBucket(rate=25.0, capacity=30)

        assert bucket.rate == 25.0
        assert bucket.capacity == 30
        assert bucket.tokens == 30.0
        assert bucket.last_update > 0

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful token acquisition."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        result = await bucket.acquire(1)

        assert result is True
        assert bucket.tokens == 9.0

    @pytest.mark.asyncio
    async def test_acquire_insufficient_tokens(self):
        """Test token acquisition fails when insufficient tokens available."""
        bucket = TokenBucket(rate=10.0, capacity=5)

        # Consume all tokens
        for _ in range(5):
            await bucket.acquire(1)

        # Should fail now
        result = await bucket.acquire(1)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        result = await bucket.acquire(5)

        assert result is True
        assert bucket.tokens == 5.0

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        # Consume all tokens
        await bucket.acquire(10)
        assert bucket.tokens == 0.0

        # Wait for refill (0.5 seconds should add 5 tokens at 10/sec rate)
        await asyncio.sleep(0.5)

        available = await bucket.get_available_tokens()
        assert available >= 4.5  # Allow for timing variance
        assert available <= 5.5

    @pytest.mark.asyncio
    async def test_refill_does_not_exceed_capacity(self):
        """Test that refill doesn't exceed bucket capacity."""
        bucket = TokenBucket(rate=100.0, capacity=10)

        # Wait for a long time
        await asyncio.sleep(0.5)

        available = await bucket.get_available_tokens()
        assert available == 10.0  # Should not exceed capacity

    @pytest.mark.asyncio
    async def test_wait_for_token_success(self):
        """Test waiting for token availability."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        # Consume all tokens
        await bucket.acquire(10)

        # Wait for tokens to refill
        start = time.monotonic()
        result = await bucket.wait_for_token(1, timeout=2.0)
        elapsed = time.monotonic() - start

        assert result is True
        assert elapsed < 0.5  # Should get token within 0.2 seconds

    @pytest.mark.asyncio
    async def test_wait_for_token_timeout(self):
        """Test waiting for token times out."""
        bucket = TokenBucket(rate=1.0, capacity=1)

        # Consume all tokens
        await bucket.acquire(1)

        # Try to wait but timeout quickly
        result = await bucket.wait_for_token(1, timeout=0.2)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_wait_time(self):
        """Test estimating wait time for tokens."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        # Consume all tokens
        await bucket.acquire(10)

        # Need 5 tokens at 10/sec rate = 0.5 seconds
        wait_time = await bucket.get_wait_time(5)

        assert 0.4 <= wait_time <= 0.6  # Allow for small variance

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test thread safety with concurrent access."""
        bucket = TokenBucket(rate=20.0, capacity=20)

        async def acquire_token():
            return await bucket.acquire(1)

        # Try to acquire 25 tokens concurrently (20 capacity)
        tasks = [acquire_token() for _ in range(25)]
        results = await asyncio.gather(*tasks)

        # Exactly 20 should succeed
        successful = sum(1 for r in results if r is True)
        assert successful == 20


@pytest.mark.unit
class TestRateLimiter:
    """Test cases for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(messages_per_second=25.0, burst_size=30)

        assert limiter.messages_per_second == 25.0
        assert limiter.burst_size == 30
        assert limiter.total_hits == 0

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful rate limit acquisition."""
        limiter = RateLimiter(messages_per_second=10.0, burst_size=10)

        result = await limiter.acquire()

        assert result is True
        assert limiter.total_hits == 0  # No hits when successful

    @pytest.mark.asyncio
    async def test_acquire_tracks_hits(self):
        """Test that rate limiter tracks rate limit hits."""
        limiter = RateLimiter(messages_per_second=5.0, burst_size=5)

        # Consume all capacity
        for _ in range(5):
            await limiter.acquire()

        # Next acquisition should fail and increment hits
        result = await limiter.acquire()

        assert result is False
        assert limiter.total_hits == 1

    @pytest.mark.asyncio
    async def test_wait_for_capacity(self):
        """Test waiting for capacity to become available."""
        limiter = RateLimiter(messages_per_second=10.0, burst_size=5)

        # Consume all capacity
        for _ in range(5):
            await limiter.acquire()

        # Wait for capacity
        start = time.monotonic()
        result = await limiter.wait_for_capacity(timeout=2.0)
        elapsed = time.monotonic() - start

        assert result is True
        assert elapsed < 0.5  # Should get capacity within ~0.1 seconds

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting rate limiter status."""
        limiter = RateLimiter(messages_per_second=25.0, burst_size=30)

        # Consume some tokens
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        status = await limiter.get_status()

        assert status["messages_per_second"] == 25.0
        assert status["burst_size"] == 30
        assert status["available_tokens"] == 27.0
        assert status["total_rate_limit_hits"] == 0

    @pytest.mark.asyncio
    async def test_realistic_telegram_limits(self):
        """Test with realistic Telegram rate limits (25 msg/sec)."""
        limiter = RateLimiter(messages_per_second=25.0, burst_size=30)

        # Should be able to send 30 messages immediately (burst)
        results = []
        for _ in range(30):
            results.append(await limiter.acquire())

        assert all(results)

        # 31st message should fail
        result = await limiter.acquire()
        assert result is False
        assert limiter.total_hits == 1


@pytest.mark.unit
class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_zero_tokens_requested(self):
        """Test requesting zero tokens."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        result = await bucket.acquire(0)

        # Should succeed as no tokens are needed
        assert result is True

    @pytest.mark.asyncio
    async def test_very_high_rate(self):
        """Test with very high refill rate."""
        bucket = TokenBucket(rate=1000.0, capacity=100)

        # Consume all
        await bucket.acquire(100)

        # Wait just 0.1 seconds
        await asyncio.sleep(0.1)

        # Should have refilled completely (1000 * 0.1 = 100)
        available = await bucket.get_available_tokens()
        assert available >= 99.0  # Allow for small timing variance

    @pytest.mark.asyncio
    async def test_very_low_rate(self):
        """Test with very low refill rate."""
        bucket = TokenBucket(rate=0.1, capacity=1)

        await bucket.acquire(1)

        # Wait 0.5 seconds
        await asyncio.sleep(0.5)

        # Should only have refilled 0.05 tokens
        available = await bucket.get_available_tokens()
        assert available < 0.1
