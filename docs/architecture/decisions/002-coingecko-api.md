# ADR 002: Use CoinGecko API for Cryptocurrency Data

## Status

**Accepted** - November 7, 2025

## Context

We needed to choose a cryptocurrency data provider for real-time price monitoring. The API must provide:

- Current cryptocurrency prices
- Comprehensive cryptocurrency coverage
- Reliable service with good uptime
- Free tier suitable for initial deployment
- Commercial use permissions
- Reasonable rate limits

### Alternatives Considered

1. **CoinGecko API** - Comprehensive free API with commercial use
2. **Binance API** - Exchange API with real-time data
3. **Coinbase Advanced Trade API** - Coinbase exchange API
4. **CryptoCompare API** - Multi-exchange aggregated data

## Decision

We chose **CoinGecko API** as our primary cryptocurrency data provider.

## Rationale

### CoinGecko API Advantages

**1. Comprehensive Coverage**
- 13M+ tokens tracked
- 240+ blockchain networks
- 1,600+ exchanges
- Best coverage among alternatives

**2. Commercial Use Allowed**
- Free tier explicitly allows commercial use
- Simple attribution requirement: "Powered by CoinGecko API"
- No paid plan required for basic usage

**3. Stable Free Tier**
- 30 calls/minute (Demo plan with free registration)
- 10,000 calls/month quota
- More stable than public API (5-15 calls/min)
- Sufficient for monitoring 20+ cryptocurrencies

**4. No Regional Restrictions**
- Works worldwide, including United States
- Unlike Binance (blocks US IPs)
- Can deploy on any cloud provider

**5. Clear Rate Limits**
- Explicit documentation of limits
- Predictable rate limiting behavior
- Clear upgrade path if needed

**6. Continuous Improvements**
- 2025: Cache reduced from 60s to 10-30s
- Active development and improvements
- Reliable service track record

### Comparison with Alternatives

**Binance API**:
- ✅ Real-time data (millisecond precision)
- ✅ High rate limits (6,000 weight/min)
- ✅ Free WebSocket access
- ❌ **Critical**: Blocks US IP addresses
- ❌ Aggressive IP banning on violations
- ❌ Lower cryptocurrency coverage (439 vs 13M+)

**Coinbase Advanced Trade API**:
- ✅ High rate limits (30 req/sec)
- ✅ No regional restrictions
- ✅ Real-time WebSocket
- ❌ Limited cryptocurrency coverage (~550 markets)
- ❌ Major coins only, limited altcoins

**CryptoCompare API**:
- ✅ Comprehensive coverage (7,287 assets)
- ✅ Institutional-grade infrastructure
- ❌ Vague free tier limits (~5 calls/min average)
- ❌ Commercial use requires paid plans ($80-200/month)
- ❌ Free tier suitable for "prototypes" only

## Consequences

### Positive

1. **Best Coverage**: Access to 13M+ cryptocurrencies
2. **Cost Effective**: Free tier sufficient for MVP and beyond
3. **Deployment Flexibility**: No regional restrictions
4. **Clear Licensing**: Explicit commercial use permission
5. **Upgrade Path**: Can upgrade to paid tiers as needed

### Negative

1. **Rate Limits**: 30 calls/min may limit scaling
2. **Data Latency**: 10-30 second cache on free tier (vs real-time on Binance)
3. **No WebSocket**: Free tier uses REST polling (WebSocket requires paid plan)
4. **Monthly Quota**: 10,000 calls/month cap

### Neutral

1. **Attribution Required**: Must display "Powered by CoinGecko API"
2. **API Registration**: Requires account for stable rate limits

## Implementation Details

### API Configuration

```python
# Base configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
POLL_INTERVAL = 15  # seconds (30 calls/min rate limit)

# Optional API key for higher limits
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", None)
```

### Rate Limiting Strategy

```python
# Token bucket rate limiter
class CoinGeckoRateLimiter:
    def __init__(self):
        self.rate = 30 / 60  # 30 calls per minute
        self.capacity = 30
        self.tokens = self.capacity
        self.last_update = time.time()

    async def acquire(self):
        # Wait if no tokens available
        while self.tokens < 1:
            await asyncio.sleep(0.1)
            self._refill_tokens()

        self.tokens -= 1

    def _refill_tokens(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
```

### Fallback Strategy

```python
# Primary: CoinGecko
# Fallback: Coinbase (for major coins)
async def fetch_price(crypto_id: str) -> Decimal:
    try:
        return await coingecko_client.get_price(crypto_id)
    except RateLimitError:
        logger.warning("CoinGecko rate limited, using fallback")
        return await coinbase_client.get_price(crypto_id)
    except Exception as e:
        logger.error(f"Price fetch failed: {e}")
        raise
```

### Monitoring

```python
# Track API health
crypto_api_requests_total.labels(
    provider="coingecko",
    status="success"
).inc()

crypto_api_latency.labels(provider="coingecko").observe(duration)
```

## Scaling Considerations

### Free Tier Capacity

- **30 calls/minute** = monitoring up to 30 cryptocurrencies at 60-second intervals
- Or 15 cryptocurrencies at 30-second intervals (default: 15 seconds)
- **10,000 calls/month** = ~333 calls/day = sustainable for small user base

### Upgrade Triggers

Upgrade to paid plan if:
1. Monitoring > 30 cryptocurrencies regularly
2. Need update frequency < 15 seconds
3. Monthly calls exceed 10,000
4. Real-time data required

### Paid Tier Options

| Plan | Price | Rate Limit | Use Case |
|------|-------|------------|----------|
| Demo | Free | 30/min | Development, small production |
| Analyst | ~$50/mo | 500/min | Growing user base |
| Pro | ~$200/mo | 1000/min | Large-scale deployment |

## Risk Mitigation

### Risk 1: Rate Limit Exceeded

**Mitigation**:
- Implement robust rate limiting
- Monitor API usage with Prometheus
- Alert before hitting limits
- Graceful degradation (use cached prices)

### Risk 2: Service Downtime

**Mitigation**:
- Implement fallback to Coinbase API
- Cache last known prices
- Health check monitoring
- Retry with exponential backoff

### Risk 3: Data Quality Issues

**Mitigation**:
- Validate price data (sanity checks)
- Compare with multiple sources
- Alert on suspicious price movements
- Log all API responses

## Attribution Compliance

**Requirements** (per CoinGecko ToS):
```html
<!-- Web UI footer -->
<footer>
  Powered by <a href="https://www.coingecko.com/en/api">CoinGecko API</a>
</footer>
```

**API Response**:
```json
{
  "data": {...},
  "attribution": {
    "source": "CoinGecko API",
    "url": "https://www.coingecko.com/en/api"
  }
}
```

## Alternatives Reconsidered

We will reconsider this decision if:
- CoinGecko free tier becomes too restrictive
- Need real-time data (< 10 second latency)
- Rate limits prevent scaling
- Service reliability degrades
- Costs of paid tier become prohibitive

## Future Enhancements

**Version 0.2.0**:
- Add Coinbase API as fallback source
- Implement data aggregation from multiple sources
- Add WebSocket support (requires paid CoinGecko plan)

**Version 0.3.0**:
- Multi-source price comparison
- Automatic source switching based on reliability
- Custom data source plugins

## References

- **API Evaluation Report**: [CRYPTO_API_EVALUATION.md](../../api_research/CRYPTO_API_EVALUATION.md)
- **CoinGecko API Docs**: https://docs.coingecko.com/
- **CoinGecko API Terms**: https://www.coingecko.com/en/api_terms
- **Rate Limits**: https://docs.coingecko.com/reference/common-errors-rate-limit

## Related Decisions

- [ADR 001: Use FastAPI](001-use-fastapi.md) - FastAPI supports async HTTP clients
- [ADR 005: Rate Limiting Strategy](005-rate-limiting.md) - Rate limiting design

## Review Date

**Next Review**: February 2026 (3 months from decision)

**Review Triggers**:
- Rate limits preventing operation
- Service reliability < 95%
- Monthly costs exceed budget
- Alternative APIs offer better features

---

**Decision made by**: Research & API Evaluation Team
**Date**: November 7, 2025
**Approved by**: Technical Lead
