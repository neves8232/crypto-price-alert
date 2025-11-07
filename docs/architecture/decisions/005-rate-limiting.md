# ADR 005: Token Bucket Rate Limiting for Telegram API

## Status

**Accepted** - November 7, 2025

## Context

The Telegram Bot API has strict rate limits to prevent abuse and ensure service quality. Our system must respect these limits while providing reliable alert delivery.

**Telegram API Rate Limits**:
- **30 messages per second** to different users
- **1 message per second** to the same user
- Exceeding limits results in 429 (Too Many Requests) errors
- Repeated violations can lead to IP bans

**System Requirements**:
- Handle burst traffic during volatile price movements
- Prevent rate limit violations
- Ensure message delivery reliability
- Graceful degradation under high load
- Fair message distribution across users

### Alternatives Considered

1. **Token Bucket Algorithm** - Variable rate with burst capacity
2. **Fixed Window Counter** - Simple count per time window
3. **Sliding Window Log** - Precise rate limiting with history
4. **Leaky Bucket Algorithm** - Constant rate processing
5. **No Rate Limiting** - Rely on Telegram's errors (not recommended)

## Decision

We chose the **Token Bucket Algorithm** for rate limiting Telegram API requests.

## Rationale

### Token Bucket Algorithm Explained

**Concept**:
- Bucket holds tokens (capacity = max burst)
- Tokens refill at constant rate (30/second)
- Each message consumes 1 token
- If no tokens available, message queued
- Allows bursts up to bucket capacity

**Visual**:
```
Bucket Capacity: 30 tokens

Refill Rate: 30 tokens/second

┌─────────────────────────┐
│ 🪙 🪙 🪙 🪙 🪙 🪙 🪙 🪙 │  Tokens (8/30)
│                         │
│      [Empty Space]      │  Can burst up to 30
│                         │
└─────────────────────────┘
        ↑         ↓
    Refill    Consume
    (30/s)    (1 per msg)
```

### Why Token Bucket?

**1. Burst Handling**
- Accommodates sudden price movements
- Multiple alerts can trigger simultaneously
- Handles bursts up to 30 messages instantly
- Then throttles to 30/second

**2. Flexible Rate Control**
- Can adjust rate dynamically
- Can adjust capacity based on load
- Configurable parameters

**3. Simple Implementation**
- Easy to understand and maintain
- Stateless (no history needed)
- Low memory footprint
- Fast O(1) operations

**4. Industry Standard**
- Used by AWS, Google Cloud, etc.
- Well-tested algorithm
- Known behavior and characteristics

### Comparison with Alternatives

**Fixed Window Counter**:
- ❌ Burst problems at window boundaries
- ❌ Can send 60 messages in 1 second (30 end of window, 30 start of next)
- ✅ Simple to implement
- ❌ Not suitable for strict limits

**Sliding Window Log**:
- ✅ Precise rate limiting
- ❌ Memory intensive (stores all timestamps)
- ❌ More complex implementation
- ❌ Slower performance

**Leaky Bucket**:
- ✅ Constant rate processing
- ❌ No burst capacity
- ❌ Delays all messages
- ❌ Poor user experience during bursts

**No Rate Limiting**:
- ❌ Telegram returns 429 errors
- ❌ Risk of IP ban
- ❌ Poor reliability
- ❌ Unpredictable behavior

## Consequences

### Positive

1. **Reliable**: Prevents rate limit violations
2. **Responsive**: Handles bursts efficiently
3. **Simple**: Easy to implement and maintain
4. **Flexible**: Configurable parameters
5. **Fair**: Processes messages in order

### Negative

1. **Queue**: Messages delayed during high load
2. **Memory**: Queue consumes memory
3. **Complexity**: Adds component to system

### Neutral

1. **Stateful**: Rate limiter maintains state
2. **Single Point**: Centralized in Telegram service

## Implementation Details

### Token Bucket Implementation

```python
import asyncio
import time
from typing import Optional
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """
    Token bucket rate limiter.

    Args:
        rate: Tokens per second
        capacity: Maximum burst capacity
    """

    rate: float  # tokens per second
    capacity: int  # max tokens
    tokens: float  # current tokens
    last_update: float  # last refill time

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
        """
        while True:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            # Wait and retry
            await asyncio.sleep(wait_time)

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Returns:
            True if tokens acquired, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def available_tokens(self) -> int:
        """Get current available tokens"""
        self._refill()
        return int(self.tokens)

    def time_until_available(self, tokens: int = 1) -> float:
        """Get seconds until tokens available"""
        self._refill()

        if self.tokens >= tokens:
            return 0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.rate
```

### Telegram Service Integration

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Global rate limiter
telegram_rate_limiter = TokenBucket(
    rate=25.0,  # 25 messages/second (conservative)
    capacity=25  # Allow burst of 25
)

@app.post("/api/v1/alerts/send")
async def send_alert(
    alert_data: AlertMessage,
    auth: str = Depends(verify_auth_token)
):
    """
    Send alert message via Telegram.

    Rate limited to 25 messages/second with burst capacity of 25.
    """
    # Acquire token (wait if necessary)
    await telegram_rate_limiter.acquire(tokens=1)

    try:
        # Send message to Telegram
        result = await telegram_bot.send_message(
            chat_id=alert_data.chat_id,
            text=alert_data.message,
            parse_mode="HTML"
        )

        return {
            "status": "success",
            "message_id": result.message_id,
            "tokens_remaining": telegram_rate_limiter.available_tokens()
        }

    except Exception as e:
        # Return token on failure
        telegram_rate_limiter.tokens += 1
        raise HTTPException(status_code=500, detail=str(e))
```

### Message Queue

For reliability, combine rate limiting with message queue:

```python
import asyncio
from collections import deque
from typing import Deque

class TelegramMessageQueue:
    """
    Message queue with rate limiting.
    """

    def __init__(self, rate_limiter: TokenBucket):
        self.rate_limiter = rate_limiter
        self.queue: Deque[AlertMessage] = deque()
        self.processing = False

    async def enqueue(self, message: AlertMessage) -> None:
        """Add message to queue"""
        self.queue.append(message)

        if not self.processing:
            asyncio.create_task(self._process_queue())

    async def _process_queue(self) -> None:
        """Process messages from queue"""
        self.processing = True

        while self.queue:
            message = self.queue[0]

            # Wait for token
            await self.rate_limiter.acquire()

            try:
                # Send message
                await send_telegram_message(message)

                # Remove from queue on success
                self.queue.popleft()

            except Exception as e:
                logger.error(f"Failed to send message: {e}")

                # Retry after delay
                await asyncio.sleep(5)

        self.processing = False

    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)
```

### Configuration

**Environment Variables**:
```bash
# Telegram service configuration
TELEGRAM_RATE_LIMIT_PER_SECOND=25  # Conservative (vs 30 actual limit)
TELEGRAM_RATE_LIMIT_BURST=25       # Burst capacity
TELEGRAM_RATE_LIMIT_PER_USER=1     # Per-user limit
```

**Why 25/second instead of 30?**
- Safety margin for network delays
- Accounts for retry attempts
- Prevents edge cases near limit
- Better safe than sorry

### Monitoring

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Gauge, Histogram

# Message metrics
telegram_messages_sent_total = Counter(
    "telegram_messages_sent_total",
    "Total Telegram messages sent",
    ["status"]
)

telegram_messages_queued_total = Counter(
    "telegram_messages_queued_total",
    "Total messages queued"
)

# Rate limiter metrics
telegram_rate_limit_wait_seconds = Histogram(
    "telegram_rate_limit_wait_seconds",
    "Time waiting for rate limit tokens",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

telegram_queue_size_gauge = Gauge(
    "telegram_queue_size",
    "Current message queue size"
)

telegram_tokens_available_gauge = Gauge(
    "telegram_tokens_available",
    "Available rate limit tokens"
)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        unhealthy if queue size exceeds threshold
    """
    queue_size = message_queue.size()
    tokens_available = telegram_rate_limiter.available_tokens()

    status = "healthy"
    if queue_size > 100:
        status = "degraded"
    if queue_size > 1000:
        status = "unhealthy"

    return {
        "status": status,
        "queue_size": queue_size,
        "tokens_available": tokens_available,
        "rate_limit": {
            "rate": telegram_rate_limiter.rate,
            "capacity": telegram_rate_limiter.capacity
        }
    }
```

## Testing Strategy

### Unit Tests

```python
import pytest
import time

@pytest.mark.asyncio
async def test_token_bucket_basic():
    """Test basic token bucket functionality"""
    bucket = TokenBucket(rate=10, capacity=10)

    # Can acquire up to capacity
    for _ in range(10):
        assert bucket.try_acquire() == True

    # No more tokens available
    assert bucket.try_acquire() == False

    # Wait for refill
    await asyncio.sleep(0.5)  # 0.5s = 5 tokens

    # Can acquire 5 tokens
    for _ in range(5):
        assert bucket.try_acquire() == True

    # No more tokens
    assert bucket.try_acquire() == False

@pytest.mark.asyncio
async def test_token_bucket_wait():
    """Test waiting for tokens"""
    bucket = TokenBucket(rate=10, capacity=5)

    # Deplete bucket
    for _ in range(5):
        bucket.try_acquire()

    # Measure wait time
    start = time.time()
    await bucket.acquire()  # Should wait ~0.1s
    elapsed = time.time() - start

    assert 0.08 < elapsed < 0.15
```

### Load Tests

```python
@pytest.mark.load
async def test_high_volume_message_sending():
    """Test rate limiting under high load"""
    # Send 300 messages (10 seconds at 30/sec)
    messages = [create_test_message() for _ in range(300)]

    start = time.time()
    results = await asyncio.gather(*[
        send_message(msg) for msg in messages
    ])
    elapsed = time.time() - start

    # Should take ~12 seconds (300 / 25 per second)
    assert 11 < elapsed < 13

    # All messages should succeed
    assert all(r["status"] == "success" for r in results)
```

## Performance Considerations

### Memory Usage

**Token Bucket**:
- ~100 bytes per instance
- Minimal memory footprint

**Message Queue**:
- ~1KB per message (JSON serialized)
- 1000 messages = ~1MB
- Acceptable for most scenarios

### Latency

**Best Case** (tokens available):
- Latency: < 1ms
- Immediate processing

**Worst Case** (no tokens):
- Latency: 1/rate seconds
- Max wait: 40ms (1 token at 25/sec)

## Risk Mitigation

### Risk 1: Queue Growth

**Mitigation**:
- Monitor queue size
- Alert if queue > 100
- Reject messages if queue > 1000
- Scale Telegram service horizontally

### Risk 2: Rate Limit Changes

**Mitigation**:
- Configuration via environment variables
- Easy to adjust without code changes
- Monitor for 429 errors
- Automatic rate adjustment (future)

### Risk 3: Clock Skew

**Mitigation**:
- Use monotonic time (time.monotonic())
- Not affected by system clock changes
- Consistent behavior

## Future Enhancements

### Version 0.2.0
- **Distributed Rate Limiting**: Use Redis for shared state
- **Per-User Rate Limiting**: Separate limits per chat_id
- **Adaptive Rate Limiting**: Adjust based on 429 responses

### Version 0.3.0
- **Priority Queues**: High-priority messages first
- **Message Batching**: Combine messages where possible
- **Multi-Channel**: Support multiple Telegram bots

## References

- **Token Bucket Algorithm**: https://en.wikipedia.org/wiki/Token_bucket
- **Telegram API Limits**: https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
- **Rate Limiting Patterns**: https://blog.cloudflare.com/counting-things-a-lot-of-different-things/

## Related Decisions

- [ADR 004: Microservices Architecture](004-microservices.md) - Rate limiting in Telegram service
- [ADR 002: Choose CoinGecko API](002-coingecko-api.md) - Rate limiting for external API

## Review Date

**Next Review**: February 2026 (3 months from decision)

**Review Triggers**:
- Telegram rate limit violations
- Queue size growing unbounded
- Performance issues
- Telegram API limit changes

---

**Decision made by**: Microservices Development Team
**Date**: November 7, 2025
**Approved by**: Technical Lead
