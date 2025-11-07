"""
Rate Limiter

Token bucket implementation for rate limiting Telegram API requests.
Telegram limits: 30 messages/second per bot.

Algorithm:
- Tokens are added to bucket at a constant rate
- Each message consumes one token
- If no tokens available, request is queued or delayed
"""

import asyncio
import time
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class TokenBucket:
    """
    Thread-safe token bucket rate limiter.

    The token bucket algorithm allows for burst traffic while maintaining
    an average rate limit over time.

    Attributes:
        rate: Tokens added per second
        capacity: Maximum tokens in bucket
        tokens: Current tokens available
        last_update: Last time tokens were added
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second (e.g., 25.0 for 25 msg/sec)
            capacity: Maximum bucket capacity (burst size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

        logger.info(
            "token_bucket_initialized",
            rate=rate,
            capacity=capacity
        )

    async def _refill(self) -> None:
        """
        Refill tokens based on elapsed time.

        Internal method called before token acquisition.
        """
        now = time.monotonic()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_update = now

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self._lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    "tokens_acquired",
                    tokens_requested=tokens,
                    tokens_remaining=self.tokens
                )
                return True

            logger.debug(
                "tokens_unavailable",
                tokens_requested=tokens,
                tokens_available=self.tokens
            )
            return False

    async def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until tokens are available.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if tokens were acquired, False if timeout occurred
        """
        start_time = time.monotonic()

        while True:
            if await self.acquire(tokens):
                wait_time = time.monotonic() - start_time
                if wait_time > 0.1:  # Log if we had to wait
                    logger.info(
                        "tokens_acquired_after_wait",
                        wait_time_ms=int(wait_time * 1000),
                        tokens=tokens
                    )
                return True

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        "token_acquisition_timeout",
                        timeout_seconds=timeout,
                        tokens_requested=tokens
                    )
                    return False

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    async def get_available_tokens(self) -> float:
        """
        Get current number of available tokens.

        Returns:
            Number of tokens currently available
        """
        async with self._lock:
            await self._refill()
            return self.tokens

    async def get_wait_time(self, tokens: int = 1) -> float:
        """
        Estimate time to wait for tokens to be available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Estimated wait time in seconds
        """
        async with self._lock:
            await self._refill()

            if self.tokens >= tokens:
                return 0.0

            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            return wait_time


class RateLimiter:
    """
    High-level rate limiter for the Telegram service.

    Manages rate limiting with metrics and monitoring.
    """

    def __init__(self, messages_per_second: float, burst_size: int):
        """
        Initialize rate limiter.

        Args:
            messages_per_second: Maximum messages per second
            burst_size: Maximum burst capacity
        """
        self.bucket = TokenBucket(rate=messages_per_second, capacity=burst_size)
        self.messages_per_second = messages_per_second
        self.burst_size = burst_size
        self.total_hits = 0

        logger.info(
            "rate_limiter_initialized",
            messages_per_second=messages_per_second,
            burst_size=burst_size
        )

    async def acquire(self) -> bool:
        """
        Attempt to acquire a token for sending a message.

        Returns:
            True if allowed, False if rate limited
        """
        acquired = await self.bucket.acquire(1)

        if not acquired:
            self.total_hits += 1
            logger.warning(
                "rate_limit_hit",
                total_hits=self.total_hits
            )

        return acquired

    async def wait_for_capacity(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until capacity is available.

        Args:
            timeout: Maximum time to wait

        Returns:
            True if capacity acquired, False if timeout
        """
        return await self.bucket.wait_for_token(1, timeout)

    async def get_status(self) -> dict:
        """
        Get rate limiter status for monitoring.

        Returns:
            Status dictionary with metrics
        """
        available = await self.bucket.get_available_tokens()

        return {
            "messages_per_second": self.messages_per_second,
            "burst_size": self.burst_size,
            "available_tokens": round(available, 2),
            "total_rate_limit_hits": self.total_hits,
        }
