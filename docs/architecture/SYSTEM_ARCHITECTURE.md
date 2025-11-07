# System Architecture - Crypto Price Alert System

**Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: Design Complete - Ready for Implementation

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Container Specifications](#container-specifications)
3. [API Contracts](#api-contracts)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Security Model](#security-model)
7. [Observability](#observability)
8. [Technology Stack](#technology-stack)
9. [Deployment Considerations](#deployment-considerations)
10. [Development Workflow](#development-workflow)

---

## Architecture Overview

### High-Level System Diagram

```mermaid
graph TB
    subgraph "External Services"
        CryptoAPI[Crypto API<br/>CoinGecko/Binance]
        TelegramAPI[Telegram Bot API]
    end

    subgraph "Docker Network: crypto-alert-net"
        subgraph "Container 1: crypto-price-alert"
            WebUI[Web UI<br/>FastAPI Static Files]
            APIEndpoints[REST API<br/>Port 52000]
            DataCollector[Data Collector<br/>Background Task]
            PriceMonitor[Price Monitor<br/>Alert Evaluator]
            AlertDispatcher[Alert Dispatcher<br/>HTTP Client]
            DB[(Database<br/>SQLite/PostgreSQL)]

            WebUI --> APIEndpoints
            APIEndpoints --> DataCollector
            APIEndpoints --> PriceMonitor
            PriceMonitor --> AlertDispatcher
            DataCollector --> DB
            PriceMonitor --> DB
            APIEndpoints --> DB
        end

        subgraph "Container 2: telegram-alert-service"
            TelegramAPI_Server[HTTP API Server<br/>Port 52001]
            RateLimiter[Rate Limiter<br/>Token Bucket]
            MessageQueue[Message Queue<br/>In-Memory Deque]
            TelegramClient[Telegram Client<br/>python-telegram-bot]

            TelegramAPI_Server --> RateLimiter
            RateLimiter --> MessageQueue
            MessageQueue --> TelegramClient
        end

        AlertDispatcher -->|HTTP POST| TelegramAPI_Server
    end

    DataCollector -->|HTTPS| CryptoAPI
    TelegramClient -->|HTTPS| TelegramAPI

    User[User Browser] -->|HTTPS| WebUI
    TelegramUser[Telegram User] -.->|Receives Messages| TelegramAPI

    style CryptoAPI fill:#e1f5ff
    style TelegramAPI fill:#e1f5ff
    style DB fill:#ffe1e1
    style WebUI fill:#e1ffe1
```

### Architecture Principles

1. **Microservices Separation**: Core business logic isolated from messaging infrastructure
2. **API-First Design**: All inter-service communication via well-defined REST APIs
3. **Stateless Components**: Services can be restarted/scaled without data loss
4. **Async Operations**: Non-blocking I/O for price polling and alert dispatch
5. **Fail-Fast**: Clear error boundaries with proper exception handling
6. **Real Data Only**: No mocks in production code paths

### Component Responsibilities

#### crypto-price-alert Container
- **Primary Purpose**: Business logic for price monitoring and user management
- **Key Responsibilities**:
  - Fetch cryptocurrency prices from external APIs
  - Evaluate user-defined alert conditions
  - Manage user configurations via web UI
  - Persist data (users, alerts, price history)
  - Dispatch alert requests to telegram service
  - Expose health/metrics endpoints

#### telegram-alert-service Container
- **Primary Purpose**: Dedicated messaging infrastructure
- **Key Responsibilities**:
  - Receive alert requests via HTTP API
  - Rate limit outgoing messages (Telegram limits: 30 msg/sec)
  - Queue messages during high load
  - Retry failed deliveries with exponential backoff
  - Log all message attempts and outcomes
  - Expose health/metrics endpoints

---

## Container Specifications

### Container 1: crypto-price-alert

#### Image Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY config/ ./config/
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "52000"]
```

#### Environment Variables
```bash
# Application Settings
APP_NAME=crypto-price-alert
APP_ENV=production  # development, staging, production
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR

# Web Server
API_HOST=0.0.0.0
API_PORT=52000
API_WORKERS=2

# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/crypto_alerts
# For development: DATABASE_URL=sqlite:///data/alerts.db

# Crypto API Settings
CRYPTO_API_PROVIDER=coingecko  # coingecko, binance
CRYPTO_API_KEY=optional_api_key
CRYPTO_POLL_INTERVAL_SECONDS=15
MAX_WATCHLIST_SIZE=25

# Alert Settings
ALERT_DEBOUNCE_SECONDS=30
ALERT_BATCH_SIZE=10

# Telegram Service Integration
TELEGRAM_SERVICE_URL=http://telegram-alert-service:52001
TELEGRAM_SERVICE_AUTH_TOKEN=secure_random_token_here
TELEGRAM_SERVICE_TIMEOUT_SECONDS=10

# Security
INTERNAL_AUTH_TOKEN=another_secure_random_token
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Observability
ENABLE_METRICS=true
METRICS_PORT=52002
```

#### Port Assignments
- **52000**: Main HTTP API and Web UI (TCP)
- **52002**: Metrics endpoint (TCP)

#### Volume Mounts
```yaml
volumes:
  - ./data:/app/data              # Database and logs (dev mode)
  - ./config:/app/config:ro       # Configuration files (read-only)
```

#### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:52000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 10s
```

#### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 128M
```

---

### Container 2: telegram-alert-service

#### Image Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY telegram-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY telegram-service/ ./
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "52001"]
```

#### Environment Variables
```bash
# Application Settings
APP_NAME=telegram-alert-service
APP_ENV=production
LOG_LEVEL=INFO

# Web Server
API_HOST=0.0.0.0
API_PORT=52001

# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_API_TIMEOUT_SECONDS=30
TELEGRAM_RETRY_ATTEMPTS=3
TELEGRAM_RETRY_DELAY_SECONDS=2

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_SECOND=25  # Below Telegram's 30/sec limit
RATE_LIMIT_BURST_SIZE=50

# Message Queue
QUEUE_MAX_SIZE=1000
QUEUE_WORKER_COUNT=2

# Security
AUTH_TOKEN=secure_random_token_here  # Must match TELEGRAM_SERVICE_AUTH_TOKEN

# Observability
ENABLE_METRICS=true
METRICS_PORT=52003
```

#### Port Assignments
- **52001**: HTTP API for receiving alert requests (TCP)
- **52003**: Metrics endpoint (TCP)

#### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:52001/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 5s
```

#### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
    reservations:
      cpus: '0.1'
      memory: 64M
```

---

### Port Assignment Policy

**Port Range**: 52000-52999 (randomly selected high ports)

**Rationale**:
- Avoids common ports (80, 443, 8080, 3000, 5000)
- High enough to avoid system port conflicts
- Sequential numbering for logical grouping
- Leaves room for additional services (52004+)

**Port Registry**:
| Port  | Service                          | Protocol |
|-------|----------------------------------|----------|
| 52000 | crypto-price-alert API/UI        | HTTP     |
| 52001 | telegram-alert-service API       | HTTP     |
| 52002 | crypto-price-alert metrics       | HTTP     |
| 52003 | telegram-alert-service metrics   | HTTP     |
| 52004-52099 | Reserved for future services | -        |

---

## API Contracts

### 1. Inter-Service API: Telegram Alert Service

#### Base URL
```
http://telegram-alert-service:52001
```

#### Authentication
All requests require `Authorization` header:
```
Authorization: Bearer <AUTH_TOKEN>
```

#### Endpoint: Send Alert

**POST** `/api/v1/alerts/send`

**Request Headers**:
```http
Content-Type: application/json
Authorization: Bearer <AUTH_TOKEN>
X-Request-ID: <uuid>  # Optional correlation ID
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
    "alert_type": "price_cross_up"
  }
}
```

**Field Descriptions**:
- `chat_id` (string, required): Telegram chat ID
- `message` (string, required): Message text (max 4096 chars)
- `parse_mode` (string, optional): "HTML" or "Markdown" (default: null)
- `priority` (string, optional): "low", "normal", "high" (default: "normal")
- `metadata` (object, optional): Additional context for logging

**Response - Success (200)**:
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

**Response - Queued (202)**:
```json
{
  "status": "queued",
  "queue_position": 5,
  "estimated_delay_seconds": 2,
  "request_id": "req_abc123"
}
```

**Response - Error (400)**:
```json
{
  "status": "error",
  "error_code": "INVALID_CHAT_ID",
  "message": "The provided chat_id is invalid",
  "request_id": "req_abc123"
}
```

**Response - Rate Limited (429)**:
```json
{
  "status": "rate_limited",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded, retry after delay",
  "retry_after_seconds": 5,
  "request_id": "req_abc123"
}
```

**Response - Service Error (500)**:
```json
{
  "status": "error",
  "error_code": "TELEGRAM_API_ERROR",
  "message": "Failed to deliver message to Telegram API",
  "details": "Connection timeout after 30 seconds",
  "request_id": "req_abc123"
}
```

#### Endpoint: Health Check

**GET** `/health`

**Response (200)**:
```json
{
  "status": "healthy",
  "service": "telegram-alert-service",
  "version": "1.0.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "telegram_api": "connected",
    "rate_limiter": "operational",
    "queue_size": 3,
    "queue_capacity": 1000
  }
}
```

**Response - Unhealthy (503)**:
```json
{
  "status": "unhealthy",
  "service": "telegram-alert-service",
  "version": "1.0.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "telegram_api": "disconnected",
    "rate_limiter": "operational",
    "queue_size": 1000,
    "queue_capacity": 1000
  },
  "errors": ["Telegram API unreachable for 60 seconds"]
}
```

#### Endpoint: Metrics

**GET** `/metrics`

**Response (200)** - Prometheus format:
```
# HELP telegram_messages_sent_total Total number of messages sent
# TYPE telegram_messages_sent_total counter
telegram_messages_sent_total{status="success"} 1234
telegram_messages_sent_total{status="failed"} 12

# HELP telegram_message_delivery_seconds Message delivery latency
# TYPE telegram_message_delivery_seconds histogram
telegram_message_delivery_seconds_bucket{le="0.1"} 100
telegram_message_delivery_seconds_bucket{le="0.5"} 450
telegram_message_delivery_seconds_bucket{le="1.0"} 890
telegram_message_delivery_seconds_bucket{le="+Inf"} 1234

# HELP telegram_queue_size Current queue size
# TYPE telegram_queue_size gauge
telegram_queue_size 5

# HELP telegram_rate_limit_hits_total Rate limit hits
# TYPE telegram_rate_limit_hits_total counter
telegram_rate_limit_hits_total 23
```

---

### 2. Web UI API: Crypto Price Alert Service

#### Base URL
```
http://localhost:52000
```

#### Authentication
Session-based (future: JWT tokens)

#### Endpoint: List Cryptocurrencies

**GET** `/api/v1/cryptocurrencies`

**Query Parameters**:
- `search` (string, optional): Search by name or symbol
- `limit` (int, optional): Results per page (default: 50, max: 100)

**Response (200)**:
```json
{
  "cryptocurrencies": [
    {
      "id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "current_price": 45123.45,
      "price_change_24h": 1234.56,
      "price_change_percentage_24h": 2.81,
      "last_updated": "2025-11-07T10:30:00Z"
    }
  ],
  "total": 100,
  "page": 1
}
```

#### Endpoint: Create Alert

**POST** `/api/v1/alerts`

**Request Body**:
```json
{
  "user_id": "user_xyz789",
  "crypto_id": "bitcoin",
  "alert_type": "price_cross_up",
  "threshold": 45000.00,
  "telegram_chat_id": "123456789",
  "enabled": true,
  "metadata": {
    "step_value": 500,
    "percentage": 5.0,
    "custom_message": "BTC is pumping!"
  }
}
```

**Alert Types**:
- `price_cross_up`: Trigger when price crosses above threshold
- `price_cross_down`: Trigger when price crosses below threshold
- `absolute_step`: Trigger every $X change (use metadata.step_value)
- `percentage_step`: Trigger every Y% change (use metadata.percentage)
- `custom_price`: Trigger at specific price point

**Response (201)**:
```json
{
  "alert_id": "alert_abc123",
  "user_id": "user_xyz789",
  "crypto_id": "bitcoin",
  "alert_type": "price_cross_up",
  "threshold": 45000.00,
  "telegram_chat_id": "123456789",
  "enabled": true,
  "created_at": "2025-11-07T10:30:00Z",
  "last_triggered_at": null,
  "trigger_count": 0
}
```

#### Endpoint: List User Alerts

**GET** `/api/v1/alerts?user_id={user_id}`

**Response (200)**:
```json
{
  "alerts": [
    {
      "alert_id": "alert_abc123",
      "crypto_symbol": "BTC",
      "alert_type": "price_cross_up",
      "threshold": 45000.00,
      "enabled": true,
      "last_triggered_at": "2025-11-07T09:15:00Z",
      "trigger_count": 3
    }
  ],
  "total": 5
}
```

#### Endpoint: Update Alert

**PATCH** `/api/v1/alerts/{alert_id}`

**Request Body** (partial update):
```json
{
  "threshold": 46000.00,
  "enabled": false
}
```

**Response (200)**: Returns updated alert object

#### Endpoint: Delete Alert

**DELETE** `/api/v1/alerts/{alert_id}`

**Response (204)**: No content

#### Endpoint: Get Price History

**GET** `/api/v1/prices/{crypto_id}/history`

**Query Parameters**:
- `interval` (string): "1m", "5m", "15m", "1h", "1d" (default: "15m")
- `limit` (int): Number of data points (default: 100, max: 1000)

**Response (200)**:
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "interval": "15m",
  "data_points": [
    {
      "timestamp": "2025-11-07T10:30:00Z",
      "price": 45123.45,
      "volume_24h": 28500000000
    }
  ]
}
```

#### Endpoint: Health Check

**GET** `/health`

**Response (200)**:
```json
{
  "status": "healthy",
  "service": "crypto-price-alert",
  "version": "1.0.0",
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

---

## Data Flow

### 1. Price Data Collection Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Scheduled Task (Every 15 seconds)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Data Collector                                             │
│    - Get list of tracked cryptocurrencies from DB             │
│    - Batch request to Crypto API (max 25 assets)              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Crypto API (CoinGecko/Binance)                             │
│    - HTTPS GET request                                         │
│    - Response: JSON with price data                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Data Validation & Parsing                                  │
│    - Validate response structure                               │
│    - Extract price, timestamp, volume                          │
│    - Handle API errors (rate limit, timeout)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Database Persistence                                        │
│    - INSERT INTO price_history (crypto_id, price, timestamp)   │
│    - UPDATE cryptocurrencies SET current_price, last_updated   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Trigger Price Monitor                                       │
│    - Emit event: PriceUpdated(crypto_id, new_price)            │
└─────────────────────────────────────────────────────────────┘
```

**Error Handling**:
- API timeout: Retry up to 3 times with exponential backoff
- Rate limit: Wait for retry-after period, skip this cycle
- Invalid data: Log error, continue with next cryptocurrency
- Database error: Raise alert, attempt reconnection

---

### 2. Alert Evaluation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Receive PriceUpdated Event                                 │
│    - crypto_id: "bitcoin"                                      │
│    - new_price: 45123.45                                       │
│    - old_price: 44999.00                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Query Active Alerts                                         │
│    SELECT * FROM alerts                                        │
│    WHERE crypto_id = 'bitcoin'                                 │
│      AND enabled = true                                        │
│      AND (last_triggered_at IS NULL                            │
│           OR last_triggered_at < NOW() - INTERVAL '30 seconds')│
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Evaluate Each Alert Condition                              │
│    For alert_type = "price_cross_up":                          │
│      IF old_price < threshold AND new_price >= threshold:     │
│        TRIGGER ALERT                                           │
│                                                                │
│    For alert_type = "absolute_step":                           │
│      IF abs(new_price - last_step_price) >= step_value:       │
│        TRIGGER ALERT                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Build Alert Message                                         │
│    message = f"""                                              │
│    🚨 {crypto_symbol} Alert                                   │
│    Type: {alert_type}                                          │
│    Current Price: ${new_price:,.2f}                           │
│    Threshold: ${threshold:,.2f}                               │
│    Change: {change_pct:+.2f}%                                 │
│    Timestamp: {now_iso}                                        │
│    """                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Dispatch to Alert Queue                                     │
│    alert_queue.put({                                           │
│      "alert_id": alert.id,                                     │
│      "chat_id": alert.telegram_chat_id,                        │
│      "message": message,                                       │
│      "priority": "high",                                       │
│      "metadata": {...}                                         │
│    })                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Update Alert State                                          │
│    UPDATE alerts                                               │
│    SET last_triggered_at = NOW(),                              │
│        trigger_count = trigger_count + 1                       │
│    WHERE alert_id = ?                                          │
└─────────────────────────────────────────────────────────────┘
```

**Debouncing Logic**:
- Track `last_triggered_at` per alert
- Minimum 30-second interval between triggers
- Prevents spam during volatile price swings

---

### 3. Message Delivery Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Alert Dispatcher (Background Worker)                       │
│    - Monitors alert_queue                                      │
│    - Processes alerts in batches (up to 10)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. HTTP POST to Telegram Service                              │
│    POST http://telegram-alert-service:52001/api/v1/alerts/send│
│    Headers:                                                    │
│      Authorization: Bearer <token>                             │
│      Content-Type: application/json                            │
│    Body: { "chat_id": "...", "message": "...", ... }          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Telegram Service: Rate Limiter                             │
│    - Check token bucket (25 tokens/sec, burst 50)             │
│    - If tokens available: Process immediately                 │
│    - If exhausted: Queue message (return 202 Accepted)         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Telegram Service: Message Queue Worker                     │
│    - Dequeue message from in-memory deque                      │
│    - Prepare Telegram API request                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Telegram Bot API                                            │
│    POST https://api.telegram.org/bot<token>/sendMessage       │
│    Body: { "chat_id": "...", "text": "...", "parse_mode": ... }│
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Handle Response                                             │
│    Success (200): Return message_id                            │
│    Rate Limited (429): Retry after delay                       │
│    Client Error (4xx): Log and fail permanently                │
│    Server Error (5xx): Retry up to 3 times                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Log Result                                                  │
│    INFO: Message delivered successfully                        │
│    {                                                           │
│      "message_id": 12345,                                      │
│      "delivery_time_ms": 234,                                  │
│      "request_id": "req_abc123"                                │
│    }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Retry Strategy**:
- Max attempts: 3
- Delay: 2s, 4s, 8s (exponential backoff)
- Permanent failures logged and reported via metrics

---

### 4. Configuration Update Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Action in Web UI                                      │
│    - Create new alert                                          │
│    - Update threshold                                          │
│    - Enable/disable alert                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Frontend Validation                                         │
│    - Check required fields                                     │
│    - Validate numeric ranges                                   │
│    - Confirm watchlist size < 25                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. POST /api/v1/alerts                                         │
│    Request body with alert configuration                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Backend Validation                                          │
│    - Authenticate user session                                 │
│    - Validate crypto_id exists                                 │
│    - Check alert limits per user                               │
│    - Validate threshold is positive                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Database Transaction                                        │
│    BEGIN TRANSACTION;                                          │
│      INSERT INTO alerts (user_id, crypto_id, ...);            │
│      UPDATE users SET alert_count = alert_count + 1;          │
│    COMMIT;                                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Cache Invalidation (if using cache)                        │
│    - Invalidate user's alert list cache                        │
│    - Refresh active monitors set                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Response to Client                                          │
│    201 Created                                                 │
│    Body: { "alert_id": "...", ... }                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Technology Choice
- **Development**: SQLite 3.35+ (file-based, zero-config)
- **Production**: PostgreSQL 14+ (ACID, concurrent access, JSON support)

### Schema Definition

#### Table: users
```sql
CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    telegram_chat_id VARCHAR(64) NOT NULL UNIQUE,
    telegram_username VARCHAR(64),
    email VARCHAR(255),
    alert_count INTEGER DEFAULT 0,
    watchlist_size INTEGER DEFAULT 0,
    max_watchlist_size INTEGER DEFAULT 25,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_telegram_chat_id ON users(telegram_chat_id);
CREATE INDEX idx_users_last_activity ON users(last_activity_at);
```

#### Table: cryptocurrencies
```sql
CREATE TABLE cryptocurrencies (
    crypto_id VARCHAR(64) PRIMARY KEY,  -- e.g., "bitcoin"
    symbol VARCHAR(10) NOT NULL,        -- e.g., "BTC"
    name VARCHAR(255) NOT NULL,         -- e.g., "Bitcoin"
    current_price DECIMAL(20, 8),
    market_cap BIGINT,
    volume_24h BIGINT,
    price_change_24h DECIMAL(20, 8),
    price_change_percentage_24h DECIMAL(10, 4),
    last_updated TIMESTAMP WITH TIME ZONE,
    api_data JSONB DEFAULT '{}',        -- Raw API response
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crypto_symbol ON cryptocurrencies(symbol);
CREATE INDEX idx_crypto_active ON cryptocurrencies(is_active);
CREATE INDEX idx_crypto_last_updated ON cryptocurrencies(last_updated);
```

#### Table: alerts
```sql
CREATE TABLE alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    crypto_id VARCHAR(64) NOT NULL REFERENCES cryptocurrencies(crypto_id),
    alert_type VARCHAR(32) NOT NULL,  -- price_cross_up, price_cross_down, absolute_step, percentage_step, custom_price
    threshold DECIMAL(20, 8) NOT NULL,
    telegram_chat_id VARCHAR(64) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    last_triggered_price DECIMAL(20, 8),
    trigger_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',  -- step_value, percentage, custom_message, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_threshold_positive CHECK (threshold > 0),
    CONSTRAINT check_alert_type CHECK (alert_type IN (
        'price_cross_up', 'price_cross_down', 'absolute_step',
        'percentage_step', 'custom_price'
    ))
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_crypto_id ON alerts(crypto_id);
CREATE INDEX idx_alerts_enabled ON alerts(enabled) WHERE enabled = true;
CREATE INDEX idx_alerts_last_triggered ON alerts(last_triggered_at);
CREATE INDEX idx_alerts_active_monitors ON alerts(crypto_id, enabled) WHERE enabled = true;
```

#### Table: price_history
```sql
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    crypto_id VARCHAR(64) NOT NULL REFERENCES cryptocurrencies(crypto_id),
    price DECIMAL(20, 8) NOT NULL,
    volume_24h BIGINT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(32) DEFAULT 'api',  -- api, manual, calculated

    CONSTRAINT check_price_positive CHECK (price > 0)
);

CREATE INDEX idx_price_history_crypto_time ON price_history(crypto_id, timestamp DESC);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp DESC);

-- Partition by month for better query performance (PostgreSQL only)
-- ALTER TABLE price_history PARTITION BY RANGE (timestamp);
```

#### Table: alert_logs
```sql
CREATE TABLE alert_logs (
    log_id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(64) NOT NULL REFERENCES alerts(alert_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    crypto_id VARCHAR(64) NOT NULL,
    trigger_price DECIMAL(20, 8) NOT NULL,
    threshold DECIMAL(20, 8) NOT NULL,
    alert_type VARCHAR(32) NOT NULL,
    message_sent TEXT,
    telegram_message_id BIGINT,
    delivery_status VARCHAR(32) NOT NULL,  -- sent, failed, queued, rate_limited
    delivery_time_ms INTEGER,
    error_message TEXT,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_alert_logs_alert_id ON alert_logs(alert_id);
CREATE INDEX idx_alert_logs_user_id ON alert_logs(user_id);
CREATE INDEX idx_alert_logs_triggered_at ON alert_logs(triggered_at DESC);
CREATE INDEX idx_alert_logs_delivery_status ON alert_logs(delivery_status);
```

#### Table: system_metrics
```sql
CREATE TABLE system_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(64) NOT NULL,
    metric_value DECIMAL(20, 4) NOT NULL,
    metric_type VARCHAR(32) NOT NULL,  -- counter, gauge, histogram
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, timestamp DESC);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
```

### Database Relationships

```
users (1) ----< (N) alerts
cryptocurrencies (1) ----< (N) alerts
cryptocurrencies (1) ----< (N) price_history
alerts (1) ----< (N) alert_logs
```

### Data Retention Policies

1. **price_history**: Retain 90 days (TTL cleanup job)
   ```sql
   DELETE FROM price_history WHERE timestamp < NOW() - INTERVAL '90 days';
   ```

2. **alert_logs**: Retain 30 days
   ```sql
   DELETE FROM alert_logs WHERE triggered_at < NOW() - INTERVAL '30 days';
   ```

3. **system_metrics**: Retain 7 days (high-resolution) + aggregated monthly summaries
   ```sql
   DELETE FROM system_metrics WHERE timestamp < NOW() - INTERVAL '7 days';
   ```

### Database Migrations

Use **Alembic** (SQLAlchemy migration tool):
```bash
# Generate migration
alembic revision --autogenerate -m "Add alerts table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Security Model

### 1. Secret Management

#### Environment Variables (12-Factor App)
All secrets stored in environment variables, never in code or configuration files.

**Required Secrets**:
```bash
# Crypto API credentials
CRYPTO_API_KEY=your_api_key_here

# Telegram Bot token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Inter-service authentication
TELEGRAM_SERVICE_AUTH_TOKEN=$(openssl rand -hex 32)
INTERNAL_AUTH_TOKEN=$(openssl rand -hex 32)

# Database credentials (production)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Session secret (web UI)
SESSION_SECRET_KEY=$(openssl rand -hex 32)
```

**Docker Compose Secrets**:
```yaml
services:
  crypto-price-alert:
    environment:
      - TELEGRAM_SERVICE_AUTH_TOKEN=${TELEGRAM_SERVICE_AUTH_TOKEN}
    secrets:
      - database_password
      - api_key

secrets:
  database_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
```

#### Secret Rotation Policy
- Rotate inter-service tokens quarterly
- Rotate Telegram bot token on suspected compromise
- Log all authentication failures for monitoring

---

### 2. Inter-Service Authentication

#### Bearer Token Authentication

**Request Flow**:
```http
POST /api/v1/alerts/send HTTP/1.1
Host: telegram-alert-service:52001
Authorization: Bearer <TELEGRAM_SERVICE_AUTH_TOKEN>
Content-Type: application/json

{...}
```

**Validation Logic** (FastAPI):
```python
from fastapi import Header, HTTPException, status

async def verify_auth_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )

    expected_token = os.getenv("AUTH_TOKEN")
    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    return token
```

**Security Properties**:
- Constant-time comparison (`secrets.compare_digest`)
- No token in logs (redacted in structured logging)
- Single token per service pair (simplicity over complexity)

---

### 3. Network Isolation

#### Docker Network Configuration

```yaml
networks:
  crypto-alert-net:
    driver: bridge
    internal: false  # Needs external access for APIs
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Access Control**:
- `crypto-price-alert`: Exposed port 52000 (public web UI)
- `telegram-alert-service`: Internal only (no exposed ports)
- Both containers can reach external HTTPS endpoints
- No direct database access from outside Docker network

#### Firewall Rules (Host Level)
```bash
# Allow only necessary ports
iptables -A INPUT -p tcp --dport 52000 -j ACCEPT  # Web UI
iptables -A INPUT -p tcp --dport 52002 -j ACCEPT  # Metrics (internal monitoring only)
iptables -A INPUT -p tcp --dport 52003 -j ACCEPT  # Metrics (internal monitoring only)
iptables -A INPUT -j DROP  # Deny all other inbound
```

---

### 4. Telegram Token Protection

#### Best Practices
1. **Never log the token**: Redact in all log statements
2. **Environment variable only**: Never in code, config files, or database
3. **Validate bot ownership**: Check bot info on startup
4. **Rate limit validation**: Prevent token abuse via rate limiting

**Token Validation on Startup**:
```python
import httpx

async def validate_telegram_token():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{token}/getMe"
        )
        if response.status_code != 200:
            raise ValueError("Invalid Telegram bot token")

        bot_info = response.json()
        logger.info(f"Telegram bot validated: {bot_info['result']['username']}")
```

---

### 5. Input Validation

#### Request Validation (Pydantic Models)
```python
from pydantic import BaseModel, Field, validator

class AlertRequest(BaseModel):
    chat_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=4096)
    parse_mode: Optional[str] = Field(None, regex="^(HTML|Markdown)$")
    priority: str = Field("normal", regex="^(low|normal|high)$")

    @validator("message")
    def validate_message_content(cls, v):
        # Prevent injection attacks
        if "<script>" in v.lower():
            raise ValueError("Message contains forbidden content")
        return v
```

#### SQL Injection Prevention
- Use **parameterized queries** only (SQLAlchemy ORM)
- Never construct SQL with string concatenation
- Enable SQL query logging in development

#### XSS Prevention (Web UI)
- Escape all user input in HTML templates
- Use Content Security Policy (CSP) headers
- Sanitize Markdown/HTML in alert messages

---

### 6. Logging Security

#### Redact Sensitive Data
```python
import re

def redact_sensitive_data(log_message: dict) -> dict:
    """Redact sensitive information from logs"""
    sensitive_keys = [
        "authorization", "token", "password", "api_key",
        "telegram_bot_token", "session_id"
    ]

    for key in sensitive_keys:
        if key in log_message:
            log_message[key] = "***REDACTED***"

    # Redact chat IDs (privacy)
    if "chat_id" in log_message:
        chat_id = str(log_message["chat_id"])
        log_message["chat_id"] = f"{chat_id[:3]}***{chat_id[-3:]}"

    return log_message
```

---

## Observability

### 1. Logging Strategy

#### Structured JSON Logging

**Log Format**:
```json
{
  "timestamp": "2025-11-07T10:30:45.123Z",
  "level": "INFO",
  "service": "crypto-price-alert",
  "logger": "price_monitor",
  "message": "Alert triggered for BTC",
  "context": {
    "alert_id": "alert_abc123",
    "crypto_id": "bitcoin",
    "trigger_price": 45123.45,
    "threshold": 45000.00,
    "user_id": "user_xyz789"
  },
  "request_id": "req_abc123",
  "trace_id": "trace_def456",
  "duration_ms": 234,
  "error": null
}
```

#### Log Configuration (Python)
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": os.getenv("APP_NAME", "unknown"),
            "logger": record.name,
            "message": record.getMessage(),
            "context": getattr(record, "context", {}),
            "request_id": getattr(record, "request_id", None),
        }

        if record.exc_info:
            log_data["error"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_data)

# Configure root logger
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logging.root.handlers[0].setFormatter(JSONFormatter())
```

#### Log Levels
- **DEBUG**: Detailed debugging information (disabled in production)
- **INFO**: Normal operational events (API calls, alerts triggered)
- **WARNING**: Unexpected but recoverable issues (API rate limit, queue full)
- **ERROR**: Error events that don't stop the application (failed message delivery)
- **CRITICAL**: Severe errors requiring immediate attention (database down)

#### Request ID Propagation
```python
import uuid
from fastapi import Request

async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

### 2. Metrics (Prometheus Format)

#### Metrics Exposed

**Crypto Price Alert Service** (`/metrics` on port 52002):
```
# Price collection metrics
crypto_api_requests_total{provider="coingecko",status="success"} 1234
crypto_api_requests_total{provider="coingecko",status="failed"} 12
crypto_api_latency_seconds{provider="coingecko",quantile="0.5"} 0.234
crypto_api_latency_seconds{provider="coingecko",quantile="0.95"} 0.891
crypto_api_latency_seconds{provider="coingecko",quantile="0.99"} 1.234

# Price monitoring metrics
price_updates_total{crypto="bitcoin"} 5678
alerts_triggered_total{crypto="bitcoin",type="price_cross_up"} 42
alerts_evaluated_total 15000
alert_evaluation_duration_seconds 0.012

# Alert dispatch metrics
alert_dispatch_requests_total{status="success"} 987
alert_dispatch_requests_total{status="failed"} 3
alert_dispatch_latency_seconds{quantile="0.95"} 0.456

# Database metrics
database_queries_total{operation="select"} 10000
database_queries_total{operation="insert"} 500
database_connection_pool_size 10
database_connection_pool_active 3

# System metrics
active_alerts_gauge 45
active_crypto_monitors_gauge 15
watchlist_total_size_gauge 375
```

**Telegram Alert Service** (`/metrics` on port 52003):
```
# Message delivery metrics
telegram_messages_sent_total{status="success"} 987
telegram_messages_sent_total{status="failed"} 3
telegram_message_delivery_seconds{quantile="0.5"} 0.234
telegram_message_delivery_seconds{quantile="0.95"} 0.891
telegram_message_delivery_seconds{quantile="0.99"} 1.234

# Rate limiting metrics
telegram_rate_limit_hits_total 23
telegram_rate_limit_tokens_available 25

# Queue metrics
telegram_queue_size_gauge 5
telegram_queue_max_size_gauge 1000
telegram_queue_processing_duration_seconds 0.012

# Retry metrics
telegram_retry_attempts_total{attempt="1"} 10
telegram_retry_attempts_total{attempt="2"} 3
telegram_retry_attempts_total{attempt="3"} 1
```

#### Metrics Implementation (Prometheus Client)
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
api_requests_total = Counter(
    "crypto_api_requests_total",
    "Total API requests to crypto providers",
    ["provider", "status"]
)

api_latency = Histogram(
    "crypto_api_latency_seconds",
    "API request latency in seconds",
    ["provider"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

active_alerts = Gauge(
    "active_alerts_gauge",
    "Number of active alerts"
)

# Usage
api_requests_total.labels(provider="coingecko", status="success").inc()

with api_latency.labels(provider="coingecko").time():
    response = await fetch_prices()

active_alerts.set(len(get_active_alerts()))
```

---

### 3. Health Check Implementation

#### Crypto Price Alert Service

**Endpoint**: `GET /health`

**Health Check Logic**:
```python
from fastapi import FastAPI
from datetime import datetime, timedelta
import httpx

app = FastAPI()

@app.get("/health")
async def health_check():
    checks = {}
    overall_status = "healthy"

    # Check database connection
    try:
        await database.execute("SELECT 1")
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = "disconnected"
        overall_status = "unhealthy"

    # Check crypto API connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{CRYPTO_API_BASE_URL}/ping"
            )
            if response.status_code == 200:
                checks["crypto_api"] = "connected"
            else:
                checks["crypto_api"] = "degraded"
                overall_status = "degraded"
    except Exception:
        checks["crypto_api"] = "disconnected"
        overall_status = "unhealthy"

    # Check telegram service connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{TELEGRAM_SERVICE_URL}/health",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code == 200:
                checks["telegram_service"] = "connected"
            else:
                checks["telegram_service"] = "degraded"
    except Exception:
        checks["telegram_service"] = "disconnected"
        overall_status = "degraded"  # Not critical

    # Check last price update time
    last_update = await get_last_price_update_time()
    if last_update and (datetime.utcnow() - last_update) > timedelta(minutes=5):
        checks["price_updates"] = "stale"
        overall_status = "degraded"
    else:
        checks["price_updates"] = "current"

    # System stats
    checks["active_monitors"] = await count_active_monitors()
    checks["alerts_triggered_last_hour"] = await count_recent_alerts()

    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "service": "crypto-price-alert",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks
        }
    )
```

#### Telegram Alert Service

**Endpoint**: `GET /health`

**Health Check Logic**:
```python
@app.get("/health")
async def health_check():
    checks = {}
    overall_status = "healthy"

    # Check Telegram API connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            )
            if response.status_code == 200:
                checks["telegram_api"] = "connected"
            else:
                checks["telegram_api"] = "degraded"
                overall_status = "degraded"
    except Exception:
        checks["telegram_api"] = "disconnected"
        overall_status = "unhealthy"

    # Check rate limiter
    checks["rate_limiter"] = "operational"

    # Check message queue
    queue_size = message_queue.qsize()
    queue_capacity = MAX_QUEUE_SIZE
    checks["queue_size"] = queue_size
    checks["queue_capacity"] = queue_capacity

    if queue_size >= queue_capacity * 0.9:
        checks["queue_status"] = "near_full"
        overall_status = "degraded"
    else:
        checks["queue_status"] = "normal"

    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "service": "telegram-alert-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks
        }
    )
```

---

### 4. Distributed Tracing

#### Correlation IDs

**Request ID Propagation**:
```python
# In crypto-price-alert service
async def dispatch_alert(alert_data: dict, request_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_SERVICE_URL}/api/v1/alerts/send",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "X-Request-ID": request_id,
                "X-Trace-ID": generate_trace_id()
            },
            json=alert_data
        )
    return response

# In telegram-alert-service
@app.post("/api/v1/alerts/send")
async def send_alert(
    request: Request,
    alert: AlertRequest,
    auth: str = Depends(verify_auth_token)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    trace_id = request.headers.get("X-Trace-ID", request_id)

    logger.info(
        "Received alert request",
        extra={
            "request_id": request_id,
            "trace_id": trace_id,
            "context": {"chat_id": alert.chat_id}
        }
    )
    # ... process alert
```

---

### 5. Alerting Rules

#### Prometheus Alertmanager Rules
```yaml
groups:
  - name: crypto_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighAPIErrorRate
        expr: |
          rate(crypto_api_requests_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High crypto API error rate"
          description: "API error rate is {{ $value }} errors/sec"

      # Stale price data
      - alert: StalePriceData
        expr: |
          time() - crypto_last_update_timestamp > 300
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Price data is stale"
          description: "No price updates for 5+ minutes"

      # Queue near full
      - alert: TelegramQueueNearFull
        expr: |
          telegram_queue_size_gauge / telegram_queue_max_size_gauge > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Telegram queue near full"
          description: "Queue is {{ $value | humanizePercentage }} full"

      # Service down
      - alert: ServiceDown
        expr: |
          up{job="crypto-price-alert"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.job }} has been down for 1+ minute"
```

---

## Technology Stack

### Technology Decisions & Rationale

#### 1. Web Framework: **FastAPI** ✅

**Chosen**: FastAPI
**Rejected**: Flask

**Rationale**:
- **Async/Await Support**: Native async for concurrent price polling and API calls
- **Automatic API Documentation**: OpenAPI/Swagger generated automatically
- **Type Hints & Validation**: Pydantic models for request/response validation
- **Performance**: Built on Starlette (ASGI) - significantly faster than Flask (WSGI)
- **Modern Python**: Embraces Python 3.7+ features (type hints, async)
- **Dependency Injection**: Clean pattern for managing dependencies
- **WebSocket Support**: Future-proof for real-time price updates to Web UI

**Trade-offs**:
- Steeper learning curve than Flask
- Smaller ecosystem (but growing rapidly)
- Less mature (but stable and well-maintained)

**Decision**: FastAPI's async capabilities and automatic validation make it ideal for I/O-bound operations like API polling and inter-service communication.

---

#### 2. Database: **SQLite (Dev) + PostgreSQL (Prod)** ✅

**Chosen**: SQLite for development, PostgreSQL for production

**Rationale**:

**SQLite (Development)**:
- Zero configuration (no separate database server)
- Single-file database (easy to reset/backup)
- Fast for single-user development
- Built into Python standard library

**PostgreSQL (Production)**:
- **ACID Compliance**: Reliable transactions for alert state
- **Concurrent Access**: Multiple workers can query simultaneously
- **JSONB Support**: Efficient storage for metadata and API responses
- **Advanced Features**: Partial indexes, CTEs, window functions
- **Scalability**: Can handle production load (hundreds of alerts)
- **Mature Ecosystem**: Well-supported by SQLAlchemy

**Trade-offs**:
- Need separate database server in production
- More complex deployment (but manageable with Docker)

**Decision**: SQLite for rapid development, PostgreSQL for production reliability.

---

#### 3. ORM: **SQLAlchemy 2.0** ✅

**Chosen**: SQLAlchemy 2.0
**Alternatives**: Raw SQL, Django ORM, Peewee

**Rationale**:
- **Database Agnostic**: Same code works with SQLite and PostgreSQL
- **Type Safety**: Full type hint support in 2.0
- **Async Support**: Native async with `asyncpg` driver
- **Migration Tool**: Alembic for schema versioning
- **Flexibility**: Can drop to raw SQL when needed
- **Industry Standard**: Most widely used Python ORM

**Example**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(index=True)
    threshold: Mapped[Decimal] = mapped_column()
    enabled: Mapped[bool] = mapped_column(default=True)
```

---

#### 4. HTTP Client: **httpx** ✅

**Chosen**: httpx
**Alternatives**: requests, aiohttp

**Rationale**:
- **Async Support**: Native async/await (compatible with FastAPI)
- **Sync API Available**: Can use synchronously if needed
- **HTTP/2 Support**: Better performance for repeated API calls
- **Requests-like API**: Familiar interface for developers
- **Type Hints**: Full type hint support
- **Active Development**: Modern, well-maintained

**Example**:
```python
import httpx

async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd"}
    )
    data = response.json()
```

**Decision**: httpx's async support and modern API make it the best choice for both crypto API calls and inter-service communication.

---

#### 5. Telegram Library: **python-telegram-bot** ✅

**Chosen**: python-telegram-bot v20+
**Alternatives**: aiogram, telethon

**Rationale**:
- **Official Wrapper**: Endorsed by Telegram
- **Async Support**: Native async in v20+
- **Comprehensive**: Covers entire Telegram Bot API
- **Well-Documented**: Extensive docs and examples
- **Active Community**: Large user base, frequent updates
- **Type Hints**: Full type safety

**Example**:
```python
from telegram import Bot
from telegram.error import TelegramError

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_message(chat_id: str, text: str):
    try:
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )
        return message.message_id
    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        raise
```

**Decision**: python-telegram-bot is the most mature and feature-complete library for Telegram bot development.

---

#### 6. Rate Limiter: **Custom Token Bucket** ✅

**Chosen**: Custom implementation
**Alternatives**: slowapi, limits

**Rationale**:
- **Simple Algorithm**: Token bucket is easy to understand and implement
- **No External Dependencies**: Lightweight, no Redis required
- **In-Memory State**: Fast, suitable for single-instance service
- **Telegram-Specific**: Tuned to Telegram's 30 msg/sec limit
- **Configurable**: Easy to adjust for different rate limits

**Implementation**:
```python
import asyncio
from time import time

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time()

    async def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire tokens, returns True if successful"""
        now = time()
        elapsed = now - self.last_update

        # Refill tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    async def wait_for_token(self):
        """Wait until a token is available"""
        while not await self.acquire():
            await asyncio.sleep(0.1)

# Usage
rate_limiter = TokenBucket(rate=25.0, capacity=50)
await rate_limiter.wait_for_token()
await send_telegram_message(...)
```

**Decision**: Custom token bucket provides precise control over Telegram rate limits without external dependencies.

---

#### 7. Task Scheduler: **APScheduler** ✅

**Chosen**: APScheduler (AsyncIO scheduler)
**Alternatives**: Celery, built-in asyncio

**Rationale**:
- **Lightweight**: No message broker required (unlike Celery)
- **Async Support**: Native asyncio support
- **Flexible Scheduling**: Interval, cron, and date-based triggers
- **In-Process**: Runs within the application process
- **Persistent Jobs**: Can persist jobs to database
- **Easy to Use**: Simple API for background tasks

**Example**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def poll_crypto_prices():
    logger.info("Polling crypto prices...")
    await data_collector.fetch_prices()

# Schedule every 15 seconds
scheduler.add_job(
    poll_crypto_prices,
    trigger="interval",
    seconds=15,
    id="price_poller",
    max_instances=1
)

scheduler.start()
```

**Decision**: APScheduler provides the right balance of features and simplicity for periodic price polling.

---

#### 8. Testing Framework: **pytest + pytest-asyncio** ✅

**Chosen**: pytest with async support
**Alternatives**: unittest, nose2

**Rationale**:
- **Async Testing**: pytest-asyncio for testing async code
- **Fixtures**: Powerful fixture system for test setup
- **Parametrization**: Easy to run tests with multiple inputs
- **Rich Ecosystem**: Extensive plugin ecosystem
- **Readable Output**: Clear test failure messages
- **Industry Standard**: Most popular Python testing framework

**Example**:
```python
import pytest
from httpx import AsyncClient

@pytest.fixture
async def client():
    """Test client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_alert(client):
    response = await client.post(
        "/api/v1/alerts",
        json={
            "user_id": "test_user",
            "crypto_id": "bitcoin",
            "alert_type": "price_cross_up",
            "threshold": 45000.00,
            "telegram_chat_id": "123456"
        }
    )
    assert response.status_code == 201
    assert "alert_id" in response.json()
```

**Additional Testing Tools**:
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Mocking support
- **respx**: Mock httpx requests
- **faker**: Generate test data

---

#### 9. Logging: **structlog** ✅

**Chosen**: structlog
**Alternatives**: loguru, standard logging

**Rationale**:
- **Structured Logging**: Native JSON output
- **Context Binding**: Attach context to all log statements
- **Processor Pipeline**: Transform logs before output
- **Thread-Safe**: Safe for concurrent operations
- **Standard Library Compatible**: Works with Python logging

**Example**:
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

# Bind context
logger = logger.bind(
    request_id="req_abc123",
    user_id="user_xyz789"
)

# All subsequent logs include bound context
logger.info("alert_triggered", alert_id="alert_123", price=45123.45)
```

**Decision**: structlog provides production-ready structured logging with excellent async support.

---

#### 10. Metrics: **prometheus_client** ✅

**Chosen**: prometheus_client
**Alternatives**: statsd, custom metrics

**Rationale**:
- **Industry Standard**: Prometheus is de facto standard for metrics
- **Rich Metric Types**: Counter, Gauge, Histogram, Summary
- **Pull Model**: Prometheus scrapes /metrics endpoint
- **Easy Integration**: Simple Python library
- **Grafana Support**: Visualize with Grafana dashboards

**Example**:
```python
from prometheus_client import Counter, Histogram, start_http_server

alert_counter = Counter(
    "alerts_triggered_total",
    "Total alerts triggered",
    ["crypto", "type"]
)

api_latency = Histogram(
    "api_latency_seconds",
    "API request latency",
    ["provider"]
)

# Usage
alert_counter.labels(crypto="bitcoin", type="price_cross_up").inc()

with api_latency.labels(provider="coingecko").time():
    await fetch_prices()

# Expose metrics on separate port
start_http_server(52002)
```

---

### Complete Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.11+ | Application runtime |
| **Web Framework** | FastAPI | 0.104+ | REST API and Web UI |
| **ASGI Server** | Uvicorn | 0.24+ | Production web server |
| **Database (Dev)** | SQLite | 3.35+ | Development database |
| **Database (Prod)** | PostgreSQL | 14+ | Production database |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Migrations** | Alembic | 1.12+ | Schema versioning |
| **HTTP Client** | httpx | 0.25+ | Async HTTP requests |
| **Telegram** | python-telegram-bot | 20+ | Telegram Bot API |
| **Scheduler** | APScheduler | 3.10+ | Background tasks |
| **Validation** | Pydantic | 2.4+ | Data validation |
| **Logging** | structlog | 23.2+ | Structured logging |
| **Metrics** | prometheus_client | 0.19+ | Prometheus metrics |
| **Testing** | pytest | 7.4+ | Test framework |
| **Async Testing** | pytest-asyncio | 0.21+ | Async test support |
| **HTTP Mocking** | respx | 0.20+ | Mock HTTP requests |
| **Coverage** | pytest-cov | 4.1+ | Code coverage |
| **Linting** | ruff | 0.1+ | Fast Python linter |
| **Formatting** | black | 23.11+ | Code formatting |
| **Type Checking** | mypy | 1.7+ | Static type checking |
| **Container** | Docker | 24+ | Containerization |
| **Orchestration** | docker-compose | 2.23+ | Multi-container apps |

---

## Deployment Considerations

### Docker Compose Configuration

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL database (production)
  postgres:
    image: postgres:14-alpine
    container_name: crypto-db
    environment:
      POSTGRES_DB: crypto_alerts
      POSTGRES_USER: crypto_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - crypto-alert-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crypto_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Main crypto price alert service
  crypto-price-alert:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: crypto-price-alert
    ports:
      - "52000:52000"  # API/Web UI
      - "52002:52002"  # Metrics
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://crypto_user:${DB_PASSWORD}@postgres:5432/crypto_alerts
      - CRYPTO_API_PROVIDER=coingecko
      - CRYPTO_API_KEY=${CRYPTO_API_KEY}
      - TELEGRAM_SERVICE_URL=http://telegram-alert-service:52001
      - TELEGRAM_SERVICE_AUTH_TOKEN=${TELEGRAM_SERVICE_AUTH_TOKEN}
      - INTERNAL_AUTH_TOKEN=${INTERNAL_AUTH_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - alert_logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      telegram-alert-service:
        condition: service_healthy
    networks:
      - crypto-alert-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:52000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  # Telegram alert service
  telegram-alert-service:
    build:
      context: ./telegram-service
      dockerfile: Dockerfile
    container_name: telegram-alert-service
    environment:
      - APP_ENV=production
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - AUTH_TOKEN=${TELEGRAM_SERVICE_AUTH_TOKEN}
      - LOG_LEVEL=INFO
    expose:
      - "52001"  # Internal only
      - "52003"  # Metrics (internal)
    networks:
      - crypto-alert-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:52001/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
    restart: unless-stopped

  # Prometheus (monitoring)
  prometheus:
    image: prom/prometheus:latest
    container_name: crypto-prometheus
    ports:
      - "52090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - crypto-alert-net
    restart: unless-stopped

  # Grafana (dashboards)
  grafana:
    image: grafana/grafana:latest
    container_name: crypto-grafana
    ports:
      - "52091:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
      - grafana_data:/var/lib/grafana
    networks:
      - crypto-alert-net
    depends_on:
      - prometheus
    restart: unless-stopped

networks:
  crypto-alert-net:
    driver: bridge

volumes:
  postgres_data:
  alert_logs:
  prometheus_data:
  grafana_data:
```

---

### Environment Variables

**File**: `.env` (not committed to git)

```bash
# Database
DB_PASSWORD=your_secure_password_here

# Crypto API
CRYPTO_API_KEY=optional_coingecko_api_key

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Inter-Service Auth
TELEGRAM_SERVICE_AUTH_TOKEN=$(openssl rand -hex 32)
INTERNAL_AUTH_TOKEN=$(openssl rand -hex 32)

# Monitoring
GRAFANA_PASSWORD=admin_password
```

**File**: `.env.example` (committed to git)

```bash
# Database
DB_PASSWORD=changeme

# Crypto API
CRYPTO_API_KEY=

# Telegram
TELEGRAM_BOT_TOKEN=

# Inter-Service Auth (generate with: openssl rand -hex 32)
TELEGRAM_SERVICE_AUTH_TOKEN=
INTERNAL_AUTH_TOKEN=

# Monitoring
GRAFANA_PASSWORD=changeme
```

---

### Deployment Commands

```bash
# Generate auth tokens
export TELEGRAM_SERVICE_AUTH_TOKEN=$(openssl rand -hex 32)
export INTERNAL_AUTH_TOKEN=$(openssl rand -hex 32)

# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f crypto-price-alert
docker-compose logs -f telegram-alert-service

# Check health
curl http://localhost:52000/health
curl http://localhost:52001/health  # Internal network only

# View metrics
curl http://localhost:52002/metrics
curl http://localhost:52003/metrics

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

### Production Checklist

- [ ] Set strong passwords for DB, Grafana
- [ ] Generate secure random tokens for inter-service auth
- [ ] Configure HTTPS/TLS (use reverse proxy like nginx or Caddy)
- [ ] Set up log aggregation (ELK, Loki, or cloud provider)
- [ ] Configure backup for PostgreSQL database
- [ ] Set up monitoring alerts (Alertmanager)
- [ ] Configure rate limiting at reverse proxy level
- [ ] Enable Docker container resource limits
- [ ] Set up health check monitoring (UptimeRobot, Pingdom)
- [ ] Document runbook for common issues
- [ ] Test disaster recovery procedure
- [ ] Configure log rotation
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Review security settings (firewall, SSH keys)

---

## Development Workflow

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/crypto-price-alert.git
cd crypto-price-alert

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env and add your Telegram bot token

# Run database migrations
alembic upgrade head

# Start development server (auto-reload enabled)
uvicorn src.main:app --reload --port 52000

# In another terminal, start Telegram service
cd telegram-service
uvicorn main:app --reload --port 52001
```

---

### Project Structure

```
crypto-price-alert/
├── .env                          # Environment variables (not committed)
├── .env.example                  # Environment template
├── .gitignore
├── README.md
├── docker-compose.yml            # Multi-container orchestration
├── Dockerfile                    # Main service image
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── alembic.ini                   # Database migration config
├── pyproject.toml                # Project metadata and tool config
│
├── config/
│   ├── logging.yaml              # Logging configuration
│   └── settings.yaml             # Application settings
│
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── architecture/
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   └── diagrams/
│   ├── api_research/
│   │   └── crypto_apis.md
│   └── development/
│       └── DEVELOPER_GUIDE.md
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database setup and connection
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── alert.py
│   │   ├── cryptocurrency.py
│   │   └── price_history.py
│   │
│   ├── schemas/                  # Pydantic models for validation
│   │   ├── __init__.py
│   │   ├── alert.py
│   │   ├── cryptocurrency.py
│   │   └── api.py
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── alerts.py
│   │   │   ├── cryptocurrencies.py
│   │   │   └── users.py
│   │   └── health.py
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── data_collector.py    # Fetch prices from crypto APIs
│   │   ├── price_monitor.py     # Evaluate alert conditions
│   │   ├── alert_dispatcher.py  # Send alerts to Telegram service
│   │   └── crypto_api_client.py # Crypto API abstraction
│   │
│   ├── background/               # Background tasks
│   │   ├── __init__.py
│   │   ├── scheduler.py          # APScheduler setup
│   │   └── tasks.py              # Scheduled jobs
│   │
│   ├── middleware/               # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── logging.py
│   │   └── error_handler.py
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── security.py
│   │
│   └── static/                   # Web UI assets
│       ├── index.html
│       ├── css/
│       └── js/
│
├── telegram-service/             # Separate microservice
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app
│   ├── telegram_client.py        # Telegram Bot API wrapper
│   ├── rate_limiter.py           # Token bucket implementation
│   ├── message_queue.py          # In-memory queue
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_api/
│   │   ├── test_alerts.py
│   │   └── test_health.py
│   ├── test_services/
│   │   ├── test_data_collector.py
│   │   └── test_price_monitor.py
│   └── test_telegram_service/
│       └── test_rate_limiter.py
│
├── monitoring/
│   ├── prometheus.yml            # Prometheus config
│   ├── grafana-datasources.yml   # Grafana datasources
│   └── dashboards/
│       └── crypto-alerts.json    # Grafana dashboard
│
├── alembic/                      # Database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── env.py
│
└── scripts/
    ├── generate_tokens.sh        # Generate auth tokens
    ├── backup_db.sh              # Backup database
    └── load_test.py              # Load testing script
```

---

### Development Commands

```bash
# Code formatting
black src/ telegram-service/ tests/

# Linting
ruff src/ telegram-service/ tests/

# Type checking
mypy src/ telegram-service/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov=telegram-service --cov-report=html

# Run specific test
pytest tests/test_services/test_price_monitor.py -v

# Create database migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Start local development
docker-compose -f docker-compose.dev.yml up
```

---

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/alert-suggestions

# Make changes and commit
git add .
git commit -m "Add alert suggestion engine"

# Push to remote
git push origin feature/alert-suggestions

# Create pull request on GitHub

# After review, merge to main
git checkout main
git merge feature/alert-suggestions
git push origin main
```

---

### CI/CD Pipeline (GitHub Actions Example)

**File**: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14-alpine
        env:
          POSTGRES_DB: crypto_alerts_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run linters
        run: |
          ruff src/ telegram-service/ tests/
          black --check src/ telegram-service/ tests/

      - name: Run type checking
        run: |
          mypy src/ telegram-service/

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/crypto_alerts_test
        run: |
          pytest --cov=src --cov=telegram-service --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose build

      - name: Test Docker services
        run: |
          docker-compose up -d
          sleep 10
          curl -f http://localhost:52000/health
          docker-compose down
```

---

## Conclusion

This architecture document provides a complete, implementation-ready design for the cryptocurrency price alert system. Key highlights:

### Design Strengths
1. **Clear Separation of Concerns**: Two-container architecture isolates business logic from messaging infrastructure
2. **Scalability**: Stateless services can be horizontally scaled
3. **Observability**: Comprehensive logging, metrics, and health checks
4. **Security**: Token-based auth, network isolation, secret management
5. **Technology Choices**: Modern Python stack with async support
6. **Real Data**: No mocks in production code paths
7. **Testability**: Comprehensive testing strategy with pytest

### Implementation Phases

**Phase 1 - Core Infrastructure** (Week 1-2):
- Database schema and migrations
- FastAPI application skeleton
- Docker configuration
- Health check endpoints

**Phase 2 - Data Collection** (Week 2-3):
- Crypto API client implementation
- Data collector service
- Background task scheduler
- Price history persistence

**Phase 3 - Alert Logic** (Week 3-4):
- Alert evaluation engine
- Alert types implementation (cross up/down, steps, custom)
- Debouncing logic
- Alert state management

**Phase 4 - Telegram Integration** (Week 4-5):
- Telegram service implementation
- Rate limiter (token bucket)
- Message queue
- Inter-service API

**Phase 5 - Web UI** (Week 5-6):
- REST API endpoints
- Frontend implementation
- User configuration interface
- Alert management

**Phase 6 - Observability** (Week 6-7):
- Structured logging
- Prometheus metrics
- Grafana dashboards
- Alerting rules

**Phase 7 - Testing & Documentation** (Week 7-8):
- Unit tests
- Integration tests
- End-to-end tests
- API documentation
- Deployment guide

### Next Steps

1. **Review & Approval**: Review this architecture with team
2. **API Research**: Complete crypto API evaluation (separate document)
3. **Prototyping**: Build proof-of-concept for critical components
4. **Implementation**: Begin Phase 1 development
5. **Iteration**: Refine based on implementation learnings

---

**Document Status**: ✅ **Complete and Ready for Implementation**

**Feedback Welcome**: Please review and provide feedback before development begins.

---

**References**:
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Telegram Bot API: https://core.telegram.org/bots/api
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/
- Prometheus Best Practices: https://prometheus.io/docs/practices/
- 12-Factor App: https://12factor.net/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
