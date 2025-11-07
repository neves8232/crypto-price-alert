# Testing Guide - Crypto Price Alert Service

## Manual Testing Procedure

### Prerequisites

1. **Setup environment:**
   ```bash
   cd /home/user/crypto-price-alert/src/crypto_service
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

### Test 1: Start Service

```bash
python -m uvicorn crypto_service.main:app --host 0.0.0.0 --port 52000
```

**Expected**: Service starts without errors, logs show:
- `application_started`
- `scheduler_started`
- `database_initialized`

### Test 2: Health Check

```bash
curl http://localhost:52000/health | jq
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "crypto-price-alert",
  "version": "1.0.0",
  "timestamp": "2025-11-07T...",
  "checks": {
    "database": "connected",
    "telegram_service": "disconnected",
    "active_monitors": 0,
    "alerts_triggered_last_hour": 0,
    "active_cryptocurrencies": 0,
    "price_updates": "no_data"
  }
}
```

### Test 3: Add Cryptocurrency

```bash
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{
    "crypto_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin"
  }' | jq
```

**Expected Response:**
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "name": "Bitcoin",
  "current_price": null,
  "market_cap": null,
  "volume_24h": null,
  "price_change_24h": null,
  "price_change_percentage_24h": null,
  "last_updated": null,
  "is_active": true,
  "created_at": "2025-11-07T..."
}
```

### Test 4: List Cryptocurrencies

```bash
curl "http://localhost:52000/api/cryptocurrencies" | jq
```

**Expected Response:**
```json
{
  "cryptocurrencies": [
    {
      "crypto_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      ...
    }
  ],
  "total": 1
}
```

### Test 5: Wait for Price Update

Wait 15-30 seconds for the price collector to run.

```bash
curl "http://localhost:52000/api/prices/current" | jq
```

**Expected Response:**
```json
{
  "prices": [
    {
      "crypto_id": "bitcoin",
      "symbol": "BTC",
      "price": "43250.50",
      "timestamp": "2025-11-07T..."
    }
  ],
  "timestamp": "2025-11-07T..."
}
```

### Test 6: Create Alert

```bash
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": 40000.00,
    "telegram_chat_id": "123456789",
    "enabled": true
  }' | jq
```

**Expected Response:**
```json
{
  "alert_id": "uuid-here",
  "user_id": "test_user",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": "40000.00",
  "telegram_chat_id": "123456789",
  "enabled": true,
  "last_triggered_at": null,
  "last_triggered_price": null,
  "trigger_count": 0,
  "created_at": "2025-11-07T...",
  "updated_at": "2025-11-07T...",
  "metadata": {}
}
```

### Test 7: List Alerts

```bash
curl "http://localhost:52000/api/alerts?user_id=test_user" | jq
```

**Expected Response:**
```json
{
  "alerts": [
    {
      "alert_id": "uuid-here",
      ...
    }
  ],
  "total": 1
}
```

### Test 8: Update Alert

```bash
ALERT_ID="your-alert-id-here"
curl -X PUT "http://localhost:52000/api/alerts/$ALERT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 45000.00,
    "enabled": false
  }' | jq
```

**Expected Response:**
```json
{
  "alert_id": "uuid-here",
  "threshold": "45000.00",
  "enabled": false,
  ...
}
```

### Test 9: Get Price History

```bash
curl "http://localhost:52000/api/prices/bitcoin/history?interval=15m&limit=10" | jq
```

**Expected Response:**
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "interval": "15m",
  "data_points": [
    {
      "timestamp": "2025-11-07T10:00:00Z",
      "price": "43200.00",
      "volume_24h": 28500000000
    },
    ...
  ]
}
```

### Test 10: Prometheus Metrics

```bash
curl http://localhost:52000/metrics
```

**Expected**: Prometheus metrics in text format:
```
# HELP crypto_api_requests_total Total API requests to crypto providers
# TYPE crypto_api_requests_total counter
crypto_api_requests_total{provider="coingecko",status="success"} 5.0
...
```

### Test 11: Delete Alert

```bash
ALERT_ID="your-alert-id-here"
curl -X DELETE "http://localhost:52000/api/alerts/$ALERT_ID"
```

**Expected**: HTTP 204 No Content

### Test 12: Remove Cryptocurrency

```bash
curl -X DELETE "http://localhost:52000/api/cryptocurrencies/bitcoin"
```

**Expected**: HTTP 204 No Content

## Common Test Scenarios

### Scenario 1: Multiple Cryptocurrencies

```bash
# Add Ethereum
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{"crypto_id": "ethereum", "symbol": "ETH", "name": "Ethereum"}'

# Add Cardano
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{"crypto_id": "cardano", "symbol": "ADA", "name": "Cardano"}'

# Get all current prices
curl "http://localhost:52000/api/prices/current" | jq
```

### Scenario 2: Different Alert Types

```bash
# PRICE_CROSSES_UP
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_CROSSES_UP",
    "threshold": 50000.00,
    "telegram_chat_id": "123456789"
  }'

# PRICE_BELOW
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_BELOW",
    "threshold": 30000.00,
    "telegram_chat_id": "123456789"
  }'

# PRICE_CHANGE_PERCENT
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_CHANGE_PERCENT",
    "threshold": 40000.00,
    "telegram_chat_id": "123456789",
    "metadata": {"percentage": 5.0}
  }'
```

### Scenario 3: Search and Filter

```bash
# Search cryptocurrencies
curl "http://localhost:52000/api/cryptocurrencies?search=bit" | jq

# Filter alerts by crypto
curl "http://localhost:52000/api/alerts?crypto_id=bitcoin" | jq

# Filter enabled alerts only
curl "http://localhost:52000/api/alerts?enabled=true" | jq
```

## Error Cases

### Test Invalid Cryptocurrency

```bash
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "invalid_crypto",
    "alert_type": "PRICE_ABOVE",
    "threshold": 40000.00,
    "telegram_chat_id": "123456789"
  }'
```

**Expected**: HTTP 404, error message about cryptocurrency not found

### Test Invalid Alert Type

```bash
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "INVALID_TYPE",
    "threshold": 40000.00,
    "telegram_chat_id": "123456789"
  }'
```

**Expected**: HTTP 422, validation error

### Test Negative Threshold

```bash
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": -40000.00,
    "telegram_chat_id": "123456789"
  }'
```

**Expected**: HTTP 422, validation error

## Logs Verification

Check logs for key events:

```bash
# Application startup
grep "application_started" logs.txt

# Price collection
grep "collecting_prices" logs.txt
grep "prices_collected_successfully" logs.txt

# Alert evaluation
grep "evaluating_alerts" logs.txt

# API requests
grep "cryptocurrency_added" logs.txt
grep "alert_created" logs.txt
```

## Performance Testing

### Load Test with Multiple Requests

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:52000/health

# Test list cryptocurrencies
ab -n 1000 -c 10 http://localhost:52000/api/cryptocurrencies

# Test current prices
ab -n 1000 -c 10 http://localhost:52000/api/prices/current
```

**Expected**:
- Response time: <100ms (average)
- Successful requests: 100%
- No 500 errors

## Integration Testing

### With Telegram Service

**Prerequisites**: Telegram service must be running

```bash
# Check Telegram service health
curl http://localhost:52001/health

# Test alert trigger (requires actual price crossing)
# 1. Add cryptocurrency
# 2. Create alert with threshold below/above current price
# 3. Wait for next price update (15 seconds)
# 4. Check alert logs and Telegram for message
```

## Database Verification

### Check Tables

```bash
sqlite3 crypto_alerts.db
```

```sql
-- List tables
.tables

-- Check cryptocurrencies
SELECT * FROM cryptocurrencies;

-- Check alerts
SELECT * FROM alerts;

-- Check price history
SELECT * FROM price_history ORDER BY timestamp DESC LIMIT 10;

-- Check alert logs
SELECT * FROM alert_logs;
```

## Troubleshooting

### Service Won't Start

1. Check Python version: `python --version` (should be 3.11+)
2. Check dependencies: `pip list`
3. Check environment: `cat .env`
4. Check logs for errors

### No Price Updates

1. Check CoinGecko rate limits
2. Verify cryptocurrencies are active: `SELECT * FROM cryptocurrencies WHERE is_active=1;`
3. Check scheduler logs: `grep "price_collection" logs.txt`
4. Test CoinGecko API manually: `curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"`

### Alerts Not Triggering

1. Verify alert is enabled: `SELECT * FROM alerts WHERE enabled=1;`
2. Check if threshold was crossed
3. Check debouncing (30 second minimum between triggers)
4. Verify Telegram service is running
5. Check alert evaluation logs: `grep "alert" logs.txt`

## Automated Testing (Future)

```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=crypto_service tests/
```

## Success Criteria

All tests pass when:
- ✅ Service starts without errors
- ✅ Health check returns 200
- ✅ Can add/list/delete cryptocurrencies
- ✅ Prices are collected within 30 seconds
- ✅ Can create/update/delete alerts
- ✅ Alerts evaluate without errors
- ✅ Metrics endpoint returns data
- ✅ No error logs (except expected validation errors)
- ✅ Database contains expected data
- ✅ API responses match schemas

## Notes

- Some tests require waiting for scheduled jobs (15-30 seconds)
- Telegram alerts require Telegram service to be running
- Rate limits apply to CoinGecko API (30 calls/minute)
- Use development environment for testing
