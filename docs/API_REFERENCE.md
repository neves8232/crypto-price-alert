# API Reference

Complete REST API reference for the Crypto Price Alert System.

**Base URL**: `http://localhost:52000`
**API Version**: v1
**Content-Type**: `application/json`

## Table of Contents

1. [Authentication](#authentication)
2. [Response Formats](#response-formats)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Cryptocurrencies API](#cryptocurrencies-api)
6. [Alerts API](#alerts-api)
7. [Prices API](#prices-api)
8. [Health Check API](#health-check-api)
9. [Metrics API](#metrics-api)

---

## Authentication

### Service-to-Service Authentication

Inter-service communication uses Bearer token authentication.

**Header**: `Authorization: Bearer {token}`

```bash
curl -H "Authorization: Bearer your_auth_token" \
     http://telegram-service:52001/api/v1/alerts/send
```

### Future: User Authentication

User authentication (JWT-based) is planned for future versions.

---

## Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested resource was not found",
  "details": {
    "resource": "alert",
    "alert_id": "abc123"
  },
  "request_id": "req_xyz789",
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### List Response

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "limit": 50
}
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | Description |
|-------------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Resource deleted successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVICE_UNAVAILABLE` | External service unavailable |
| `DATABASE_ERROR` | Database operation failed |
| `AUTHENTICATION_FAILED` | Invalid authentication credentials |

### Example Error Response

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "field": "threshold",
    "error": "threshold must be greater than 0"
  },
  "request_id": "req_abc123",
  "timestamp": "2025-11-07T10:30:00Z"
}
```

---

## Rate Limiting

### Rate Limits

| Endpoint Type | Rate Limit | Window |
|---------------|------------|--------|
| Read Operations | 100 requests | 1 minute |
| Write Operations | 20 requests | 1 minute |
| CoinGecko API | 30 calls | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699351800
```

### Rate Limit Exceeded Response

```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded, retry after delay",
  "retry_after_seconds": 30,
  "request_id": "req_abc123"
}
```

---

## Cryptocurrencies API

Manage cryptocurrencies on the watchlist.

### List Cryptocurrencies

Get a list of all monitored cryptocurrencies.

**Endpoint**: `GET /api/cryptocurrencies`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | - | Search by name or symbol |
| `limit` | integer | No | 50 | Results per page (1-100) |
| `offset` | integer | No | 0 | Results to skip |

**Example Request**:
```bash
curl -X GET "http://localhost:52000/api/cryptocurrencies?search=bitcoin&limit=10"
```

**Example Response** (200 OK):
```json
{
  "cryptocurrencies": [
    {
      "crypto_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "current_price": 45123.45,
      "market_cap": 882000000000,
      "volume_24h": 28500000000,
      "price_change_24h": 1234.56,
      "price_change_percentage_24h": 2.81,
      "last_updated": "2025-11-07T10:30:00Z",
      "is_active": true,
      "created_at": "2025-11-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### Add Cryptocurrency

Add a new cryptocurrency to the watchlist.

**Endpoint**: `POST /api/cryptocurrencies`

**Request Body**:
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "name": "Bitcoin"
}
```

**Field Descriptions**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crypto_id` | string | Yes | Unique cryptocurrency ID (use CoinGecko ID) |
| `symbol` | string | Yes | Symbol (e.g., "BTC", "ETH") |
| `name` | string | Yes | Full name (e.g., "Bitcoin", "Ethereum") |

**Example Request**:
```bash
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{
    "crypto_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin"
  }'
```

**Example Response** (201 Created):
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
  "created_at": "2025-11-07T10:30:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "error",
  "error_code": "DUPLICATE_RESOURCE",
  "message": "Cryptocurrency already exists",
  "details": {
    "crypto_id": "bitcoin"
  }
}
```

### Get Cryptocurrency

Get details of a specific cryptocurrency.

**Endpoint**: `GET /api/cryptocurrencies/{crypto_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `crypto_id` | string | Yes | Cryptocurrency ID |

**Example Request**:
```bash
curl -X GET "http://localhost:52000/api/cryptocurrencies/bitcoin"
```

**Example Response** (200 OK):
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "name": "Bitcoin",
  "current_price": 45123.45,
  "market_cap": 882000000000,
  "volume_24h": 28500000000,
  "price_change_24h": 1234.56,
  "price_change_percentage_24h": 2.81,
  "last_updated": "2025-11-07T10:30:00Z",
  "is_active": true,
  "created_at": "2025-11-01T00:00:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Cryptocurrency not found",
  "details": {
    "crypto_id": "unknown"
  }
}
```

### Remove Cryptocurrency

Remove a cryptocurrency from the watchlist (soft delete).

**Endpoint**: `DELETE /api/cryptocurrencies/{crypto_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `crypto_id` | string | Yes | Cryptocurrency ID to remove |

**Example Request**:
```bash
curl -X DELETE "http://localhost:52000/api/cryptocurrencies/bitcoin"
```

**Example Response** (204 No Content):
```
(empty response body)
```

**Error Response** (404 Not Found):
```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Cryptocurrency not found"
}
```

---

## Alerts API

Manage price alerts.

### List Alerts

Get a list of alerts with optional filters.

**Endpoint**: `GET /api/alerts`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | No | - | Filter by user ID |
| `crypto_id` | string | No | - | Filter by cryptocurrency ID |
| `enabled` | boolean | No | - | Filter by enabled status |

**Example Request**:
```bash
# Get all alerts for a user
curl -X GET "http://localhost:52000/api/alerts?user_id=user123"

# Get all enabled alerts for Bitcoin
curl -X GET "http://localhost:52000/api/alerts?crypto_id=bitcoin&enabled=true"
```

**Example Response** (200 OK):
```json
{
  "alerts": [
    {
      "alert_id": "alert_abc123",
      "user_id": "user123",
      "crypto_id": "bitcoin",
      "alert_type": "PRICE_ABOVE",
      "threshold": 50000.00,
      "telegram_chat_id": "123456789",
      "enabled": true,
      "last_triggered_at": "2025-11-07T09:15:00Z",
      "last_triggered_price": 50123.45,
      "trigger_count": 3,
      "metadata": {},
      "created_at": "2025-11-01T00:00:00Z",
      "updated_at": "2025-11-07T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Create Alert

Create a new price alert.

**Endpoint**: `POST /api/alerts`

**Request Body**:
```json
{
  "user_id": "user123",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00,
  "telegram_chat_id": "123456789",
  "enabled": true,
  "metadata": {
    "custom_message": "BTC is pumping! 🚀"
  }
}
```

**Field Descriptions**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User ID who owns the alert |
| `crypto_id` | string | Yes | Cryptocurrency ID to monitor |
| `alert_type` | string | Yes | Alert type (see below) |
| `threshold` | decimal | Yes | Price threshold (must be > 0) |
| `telegram_chat_id` | string | Yes | Telegram chat ID for notifications |
| `enabled` | boolean | No | Whether alert is enabled (default: true) |
| `metadata` | object | No | Additional alert configuration |

**Alert Types**:
- `PRICE_ABOVE`: Trigger when price is above threshold
- `PRICE_BELOW`: Trigger when price is below threshold
- `PRICE_CROSSES_UP`: Trigger when price crosses above threshold (once)
- `PRICE_CROSSES_DOWN`: Trigger when price crosses below threshold (once)
- `PRICE_CHANGE_PERCENT`: Trigger on percentage change

**Example Request**:
```bash
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": 50000.00,
    "telegram_chat_id": "123456789",
    "enabled": true
  }'
```

**Example Response** (201 Created):
```json
{
  "alert_id": "alert_abc123",
  "user_id": "user123",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00,
  "telegram_chat_id": "123456789",
  "enabled": true,
  "last_triggered_at": null,
  "last_triggered_price": null,
  "trigger_count": 0,
  "metadata": {},
  "created_at": "2025-11-07T10:30:00Z",
  "updated_at": "2025-11-07T10:30:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Cryptocurrency 'unknown' not found. Add it first.",
  "details": {
    "crypto_id": "unknown"
  }
}
```

**Error Response** (422 Unprocessable Entity):
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "field": "alert_type",
    "error": "alert_type must be one of {'PRICE_ABOVE', 'PRICE_BELOW', 'PRICE_CROSSES_UP', 'PRICE_CROSSES_DOWN', 'PRICE_CHANGE_PERCENT'}"
  }
}
```

### Get Alert

Get details of a specific alert.

**Endpoint**: `GET /api/alerts/{alert_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `alert_id` | string | Yes | Alert ID |

**Example Request**:
```bash
curl -X GET "http://localhost:52000/api/alerts/alert_abc123"
```

**Example Response** (200 OK):
```json
{
  "alert_id": "alert_abc123",
  "user_id": "user123",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00,
  "telegram_chat_id": "123456789",
  "enabled": true,
  "last_triggered_at": "2025-11-07T09:15:00Z",
  "last_triggered_price": 50123.45,
  "trigger_count": 3,
  "metadata": {},
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-11-07T10:30:00Z"
}
```

### Update Alert

Update an existing alert.

**Endpoint**: `PUT /api/alerts/{alert_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `alert_id` | string | Yes | Alert ID to update |

**Request Body** (partial update):
```json
{
  "threshold": 55000.00,
  "enabled": false
}
```

**Updatable Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `threshold` | decimal | New threshold value (must be > 0) |
| `enabled` | boolean | Enable/disable alert |
| `metadata` | object | Updated metadata |

**Example Request**:
```bash
curl -X PUT "http://localhost:52000/api/alerts/alert_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 55000.00,
    "enabled": false
  }'
```

**Example Response** (200 OK):
```json
{
  "alert_id": "alert_abc123",
  "user_id": "user123",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": 55000.00,
  "telegram_chat_id": "123456789",
  "enabled": false,
  "last_triggered_at": "2025-11-07T09:15:00Z",
  "last_triggered_price": 50123.45,
  "trigger_count": 3,
  "metadata": {},
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-11-07T10:35:00Z"
}
```

### Delete Alert

Delete an alert permanently.

**Endpoint**: `DELETE /api/alerts/{alert_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `alert_id` | string | Yes | Alert ID to delete |

**Example Request**:
```bash
curl -X DELETE "http://localhost:52000/api/alerts/alert_abc123"
```

**Example Response** (204 No Content):
```
(empty response body)
```

---

## Prices API

Get current and historical cryptocurrency prices.

### Get Current Prices

Get current prices for all monitored cryptocurrencies.

**Endpoint**: `GET /api/prices/current`

**Example Request**:
```bash
curl -X GET "http://localhost:52000/api/prices/current"
```

**Example Response** (200 OK):
```json
{
  "prices": [
    {
      "crypto_id": "bitcoin",
      "symbol": "BTC",
      "price": 45123.45,
      "timestamp": "2025-11-07T10:30:00Z"
    },
    {
      "crypto_id": "ethereum",
      "symbol": "ETH",
      "price": 3234.56,
      "timestamp": "2025-11-07T10:30:00Z"
    }
  ],
  "timestamp": "2025-11-07T10:30:00Z"
}
```

---

## Health Check API

Check service health and dependencies.

### Health Check

Get service health status.

**Endpoint**: `GET /health`

**Example Request**:
```bash
curl -X GET "http://localhost:52000/health"
```

**Example Response - Healthy** (200 OK):
```json
{
  "status": "healthy",
  "service": "crypto-price-alert",
  "version": "0.1.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "database": "connected",
    "crypto_api": "connected",
    "telegram_service": "connected",
    "active_monitors": 15,
    "alerts_triggered_last_hour": 42
  }
}
```

**Example Response - Unhealthy** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "service": "crypto-price-alert",
  "version": "0.1.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "database": "disconnected",
    "crypto_api": "connected",
    "telegram_service": "degraded",
    "active_monitors": 0,
    "alerts_triggered_last_hour": 0
  },
  "errors": [
    "Database connection failed: Connection refused"
  ]
}
```

---

## Metrics API

Get Prometheus metrics for monitoring.

### Get Metrics

Get service metrics in Prometheus format.

**Endpoint**: `GET /metrics`

**Example Request**:
```bash
curl -X GET "http://localhost:52002/metrics"
```

**Example Response** (200 OK):
```prometheus
# HELP crypto_api_requests_total Total API requests to crypto providers
# TYPE crypto_api_requests_total counter
crypto_api_requests_total{provider="coingecko",status="success"} 1234
crypto_api_requests_total{provider="coingecko",status="failed"} 12

# HELP alerts_triggered_total Total alerts triggered
# TYPE alerts_triggered_total counter
alerts_triggered_total{crypto="bitcoin",type="PRICE_ABOVE"} 42
alerts_triggered_total{crypto="ethereum",type="PRICE_BELOW"} 15

# HELP database_queries_total Total database queries
# TYPE database_queries_total counter
database_queries_total{operation="select"} 10000
database_queries_total{operation="insert"} 500

# HELP active_alerts_gauge Number of active alerts
# TYPE active_alerts_gauge gauge
active_alerts_gauge 45

# HELP active_crypto_monitors_gauge Number of monitored cryptocurrencies
# TYPE active_crypto_monitors_gauge gauge
active_crypto_monitors_gauge 15
```

---

## Telegram Service API

Internal API for Telegram message delivery (internal service only).

### Send Alert

Send an alert message via Telegram.

**Endpoint**: `POST http://telegram-service:52001/api/v1/alerts/send`

**Authentication**: Required (Bearer token)

**Request Headers**:
```
Authorization: Bearer {AUTH_TOKEN}
Content-Type: application/json
X-Request-ID: {uuid} (optional)
```

**Request Body**:
```json
{
  "chat_id": "123456789",
  "message": "🚨 BTC Alert: Price crossed above $45,000\nCurrent Price: $45,123.45\nTimestamp: 2025-11-07T10:30:00Z",
  "parse_mode": "HTML",
  "priority": "high",
  "metadata": {
    "alert_id": "alert_abc123",
    "user_id": "user_xyz789",
    "crypto_symbol": "BTC",
    "alert_type": "PRICE_CROSSES_UP"
  }
}
```

**Example Response - Success** (200 OK):
```json
{
  "status": "success",
  "message_id": 12345,
  "telegram_response": {
    "ok": true,
    "result": {
      "message_id": 12345,
      "date": 1699351800
    }
  },
  "delivery_time_ms": 234,
  "request_id": "req_abc123"
}
```

**Example Response - Queued** (202 Accepted):
```json
{
  "status": "queued",
  "queue_position": 5,
  "estimated_delay_seconds": 2,
  "request_id": "req_abc123"
}
```

**Example Response - Rate Limited** (429 Too Many Requests):
```json
{
  "status": "rate_limited",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded, retry after delay",
  "retry_after_seconds": 5,
  "request_id": "req_abc123"
}
```

---

## Code Examples

### Python Examples

#### Add Cryptocurrency and Create Alert

```python
import requests

BASE_URL = "http://localhost:52000"

# Add Bitcoin to watchlist
response = requests.post(
    f"{BASE_URL}/api/cryptocurrencies",
    json={
        "crypto_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin"
    }
)
print(f"Added Bitcoin: {response.status_code}")

# Create price alert
response = requests.post(
    f"{BASE_URL}/api/alerts",
    json={
        "user_id": "user123",
        "crypto_id": "bitcoin",
        "alert_type": "PRICE_ABOVE",
        "threshold": 50000.00,
        "telegram_chat_id": "123456789",
        "enabled": True
    }
)
alert = response.json()
print(f"Alert created: {alert['alert_id']}")
```

#### List All Enabled Alerts

```python
import requests

BASE_URL = "http://localhost:52000"

# Get all enabled alerts for a user
response = requests.get(
    f"{BASE_URL}/api/alerts",
    params={
        "user_id": "user123",
        "enabled": True
    }
)

alerts = response.json()
print(f"Found {alerts['total']} enabled alerts:")
for alert in alerts['alerts']:
    print(f"- {alert['crypto_id']}: {alert['alert_type']} @ {alert['threshold']}")
```

#### Update Alert Threshold

```python
import requests

BASE_URL = "http://localhost:52000"
ALERT_ID = "alert_abc123"

# Update alert threshold
response = requests.put(
    f"{BASE_URL}/api/alerts/{ALERT_ID}",
    json={
        "threshold": 55000.00
    }
)

updated_alert = response.json()
print(f"Alert updated: new threshold = {updated_alert['threshold']}")
```

### JavaScript Examples

#### Create Alert

```javascript
const BASE_URL = "http://localhost:52000";

async function createAlert() {
  const response = await fetch(`${BASE_URL}/api/alerts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: "user123",
      crypto_id: "bitcoin",
      alert_type: "PRICE_ABOVE",
      threshold: 50000.00,
      telegram_chat_id: "123456789",
      enabled: true
    })
  });

  const alert = await response.json();
  console.log(`Alert created: ${alert.alert_id}`);
}

createAlert();
```

#### Get Current Prices

```javascript
async function getCurrentPrices() {
  const response = await fetch('http://localhost:52000/api/prices/current');
  const data = await response.json();

  data.prices.forEach(price => {
    console.log(`${price.symbol}: $${price.price}`);
  });
}

getCurrentPrices();
```

### cURL Examples

#### Complete Workflow

```bash
# 1. Add cryptocurrency
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{
    "crypto_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin"
  }'

# 2. Get cryptocurrency details
curl -X GET "http://localhost:52000/api/cryptocurrencies/bitcoin"

# 3. Create alert
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": 50000.00,
    "telegram_chat_id": "123456789",
    "enabled": true
  }'

# 4. List all alerts
curl -X GET "http://localhost:52000/api/alerts?user_id=user123"

# 5. Get current prices
curl -X GET "http://localhost:52000/api/prices/current"

# 6. Check service health
curl -X GET "http://localhost:52000/health"
```

---

## Interactive API Documentation

The system provides interactive API documentation via Swagger UI:

**Swagger UI**: http://localhost:52000/docs
**ReDoc**: http://localhost:52000/redoc

These interfaces allow you to:
- Explore all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- Download OpenAPI specification

---

## Best Practices

### Error Handling

Always check HTTP status codes and handle errors appropriately:

```python
import requests

response = requests.post(url, json=data)

if response.status_code == 201:
    # Success
    result = response.json()
elif response.status_code == 400:
    # Bad request - check error details
    error = response.json()
    print(f"Error: {error['message']}")
elif response.status_code == 404:
    # Resource not found
    print("Resource not found")
elif response.status_code == 429:
    # Rate limited - wait and retry
    retry_after = response.headers.get('Retry-After', 60)
    time.sleep(int(retry_after))
    # Retry request
else:
    # Other error
    print(f"Unexpected error: {response.status_code}")
```

### Rate Limit Handling

Respect rate limits and implement retry logic:

```python
import time
import requests

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### Request IDs

Include request IDs for tracing:

```python
import uuid
import requests

request_id = str(uuid.uuid4())
response = requests.post(
    url,
    json=data,
    headers={"X-Request-ID": request_id}
)
```

---

## Changelog

### v0.1.0 (2025-11-07)
- Initial API release
- Cryptocurrencies management endpoints
- Alerts management endpoints
- Current prices endpoint
- Health check endpoint
- Prometheus metrics endpoint

---

## Support

For API questions and issues:
- **Documentation**: [API Reference](https://docs.crypto-price-alert.com/api)
- **Issues**: [GitHub Issues](https://github.com/yourusername/crypto-price-alert/issues)
- **Email**: api-support@crypto-price-alert.com
