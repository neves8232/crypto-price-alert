# Telegram Alert Service

A production-ready microservice for sending Telegram messages with rate limiting, queuing, retry logic, and comprehensive monitoring.

## Features

- **FastAPI-based REST API** - Modern async Python web framework
- **Rate Limiting** - Token bucket algorithm (30 msg/sec Telegram limit)
- **Message Queuing** - In-memory queue for high-load scenarios
- **Retry Logic** - Exponential backoff for failed deliveries
- **Bearer Token Auth** - Secure inter-service communication
- **Health Checks** - Comprehensive health monitoring
- **Prometheus Metrics** - Production-ready observability
- **Structured Logging** - JSON logs with correlation IDs
- **Docker Support** - Production-ready containerization

## Architecture

This service is designed to run as an independent microservice alongside the main crypto-price-alert application. It handles all Telegram message delivery with proper rate limiting and error handling.

### Component Overview

```
┌─────────────────────────────────────────┐
│        Telegram Alert Service           │
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │   FastAPI   │───▶│ Rate Limiter │  │
│  │   Server    │    │ (Token Bucket)│  │
│  └─────────────┘    └──────────────┘  │
│         │                    │          │
│         ▼                    ▼          │
│  ┌─────────────┐    ┌──────────────┐  │
│  │   Message   │    │  Telegram    │  │
│  │    Queue    │───▶│   Client     │  │
│  └─────────────┘    └──────────────┘  │
│                             │          │
└─────────────────────────────┼──────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Telegram Bot    │
                    │      API         │
                    └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Docker (optional, for containerized deployment)

### Installation

1. **Clone and navigate to the service directory:**
   ```bash
   cd src/telegram_service
   ```

2. **Create virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN and AUTH_TOKEN
   ```

5. **Run the service:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 52001 --reload
   ```

The service will be available at `http://localhost:52001`

## Configuration

### Environment Variables

All configuration is done via environment variables. See [`.env.example`](.env.example) for all available options.

**Required Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | `123456789:ABCdef...` |
| `AUTH_TOKEN` | Bearer token for authentication | Generate with `openssl rand -hex 32` |

**Optional Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment (development/staging/production) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SERVICE_PORT` | `52001` | HTTP server port |
| `RATE_LIMIT_MESSAGES_PER_SECOND` | `25.0` | Rate limit (Telegram max: 30) |
| `RATE_LIMIT_BURST_SIZE` | `50` | Burst capacity |
| `QUEUE_MAX_SIZE` | `1000` | Max queue size |
| `TELEGRAM_RETRY_ATTEMPTS` | `3` | Max retry attempts |

### Getting a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided
5. Add it to your `.env` file as `TELEGRAM_BOT_TOKEN`

### Generating Auth Token

Generate a secure random token for authentication:

```bash
openssl rand -hex 32
```

Use this token as `AUTH_TOKEN` in both:
- This service's `.env` file
- The crypto-price-alert service (as `TELEGRAM_SERVICE_AUTH_TOKEN`)

## API Documentation

### Base URL

```
http://localhost:52001
```

### Authentication

All API requests (except `/health` and `/metrics`) require Bearer token authentication:

```http
Authorization: Bearer <AUTH_TOKEN>
```

### Endpoints

#### 1. Send Alert Message

**POST** `/api/v1/alerts/send`

Send a Telegram message.

**Request Headers:**
```http
Content-Type: application/json
Authorization: Bearer <AUTH_TOKEN>
X-Request-ID: <optional-correlation-id>
```

**Request Body:**
```json
{
  "chat_id": "123456789",
  "message": "🚨 BTC Alert: Price crossed $45,000",
  "parse_mode": "HTML",
  "priority": "high",
  "metadata": {
    "alert_id": "alert_123",
    "crypto": "BTC"
  }
}
```

**Response (200 OK - Sent):**
```json
{
  "status": "success",
  "message_id": 12345,
  "telegram_response": {
    "ok": true,
    "result": {...}
  },
  "delivery_time_ms": 234,
  "request_id": "req_abc123"
}
```

**Response (202 Accepted - Queued):**
```json
{
  "status": "queued",
  "queue_position": 5,
  "estimated_delay_seconds": 2,
  "request_id": "req_abc123"
}
```

**Example with cURL:**
```bash
curl -X POST http://localhost:52001/api/v1/alerts/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_auth_token_here" \
  -d '{
    "chat_id": "123456789",
    "message": "Test alert message",
    "parse_mode": "HTML",
    "priority": "normal"
  }'
```

#### 2. Health Check

**GET** `/health`

Check service health.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "telegram-alert-service",
  "version": "1.0.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "telegram_api": "connected",
    "rate_limiter": "operational",
    "queue_status": "normal",
    "queue": {
      "size": 0,
      "capacity": 1000,
      "utilization_percent": 0.0
    }
  }
}
```

#### 3. Prometheus Metrics

**GET** `/metrics`

Get Prometheus metrics.

**Response:** Prometheus text format

## Docker Deployment

### Build Image

```bash
docker build -t telegram-alert-service:latest .
```

### Run Container

```bash
docker run -d \
  --name telegram-alert-service \
  -p 52001:52001 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e AUTH_TOKEN=your_auth_token \
  telegram-alert-service:latest
```

### Docker Compose

See the main project's `docker-compose.yml` for multi-service orchestration.

## Monitoring

### Health Checks

The service exposes a `/health` endpoint that checks:
- Telegram API connectivity
- Rate limiter operational status
- Message queue status

Use this endpoint for:
- Docker health checks
- Kubernetes liveness/readiness probes
- Monitoring systems

### Prometheus Metrics

Available metrics at `/metrics` endpoint:

**Message Metrics:**
- `telegram_messages_sent_total{status}` - Total messages sent
- `telegram_message_delivery_seconds` - Message delivery latency

**Rate Limiting:**
- `telegram_rate_limit_hits_total` - Rate limit hits
- `telegram_rate_limit_tokens_available` - Available tokens

**Queue Metrics:**
- `telegram_queue_size` - Current queue size
- `telegram_queue_max_size` - Maximum queue capacity

**Error Metrics:**
- `telegram_errors_total{error_type}` - Errors by type
- `telegram_retry_attempts_total{attempt}` - Retry attempts

### Structured Logging

All logs are output in JSON format with:
- Timestamp (ISO 8601)
- Log level
- Service name
- Request ID (correlation)
- Contextual data

Example log entry:
```json
{
  "timestamp": "2025-11-07T10:30:45.123Z",
  "level": "INFO",
  "event": "message_sent_successfully",
  "request_id": "req_abc123",
  "message_id": 12345,
  "delivery_time_ms": 234
}
```

## Testing

### Manual Testing

1. **Test health check:**
   ```bash
   curl http://localhost:52001/health
   ```

2. **Test message sending:**
   ```bash
   curl -X POST http://localhost:52001/api/v1/alerts/send \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_auth_token" \
     -d '{
       "chat_id": "your_telegram_chat_id",
       "message": "Test message from Telegram Alert Service",
       "parse_mode": "HTML"
     }'
   ```

3. **Test metrics:**
   ```bash
   curl http://localhost:52001/metrics
   ```

### Getting Your Chat ID

To get your Telegram chat ID:

1. Start a conversation with your bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}` in the response

## Troubleshooting

### Common Issues

**1. "Invalid Telegram bot token format"**
- Ensure token format is correct: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- Check for extra spaces or newlines in `.env` file

**2. "Failed to validate Telegram bot token"**
- Verify token is correct
- Check internet connectivity
- Ensure Telegram API is accessible

**3. "Missing authorization header"**
- Include `Authorization: Bearer <token>` header
- Verify AUTH_TOKEN matches between services

**4. "Message queue is full"**
- Increase `QUEUE_MAX_SIZE`
- Check if Telegram API is responding
- Review rate limiting settings

**5. "Bad Request: chat not found"**
- Verify chat_id is correct
- Ensure user has started conversation with bot

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload
```

## Security Best Practices

1. **Never commit secrets** - Use `.env` files (added to `.gitignore`)
2. **Use strong auth tokens** - Minimum 32 characters, randomly generated
3. **Run as non-root** - Docker image uses unprivileged user
4. **Validate inputs** - Pydantic models validate all requests
5. **Rate limiting** - Prevents abuse and respects Telegram limits
6. **Constant-time comparison** - Auth uses `secrets.compare_digest()`

## Performance

- **Throughput**: Up to 25 messages/second (configurable)
- **Latency**: ~200-500ms average delivery time
- **Queue**: Supports up to 1000 queued messages (configurable)
- **Burst handling**: 50 message burst capacity

## Integration

This service is designed to work with the main crypto-price-alert application. The main service sends HTTP POST requests to this service's `/api/v1/alerts/send` endpoint.

**Integration checklist:**
1. Both services use the same `AUTH_TOKEN`
2. Network connectivity between services (Docker network)
3. Health checks configured
4. Metrics scraped by Prometheus

## Contributing

When contributing to this service:

1. Follow PEP 8 style guide
2. Use type hints throughout
3. Add docstrings to all functions
4. Update this README for new features
5. Test with real Telegram API (no mocks in production code)

## License

Part of the crypto-price-alert project.

## Support

For issues or questions:
- Check the troubleshooting section
- Review logs for detailed error messages
- Ensure all environment variables are set correctly
- Test with `/health` endpoint first

## Version History

- **1.0.0** (2025-11-07) - Initial release
  - FastAPI-based REST API
  - Rate limiting with token bucket
  - Message queuing
  - Retry logic with exponential backoff
  - Health checks
  - Prometheus metrics
  - Structured logging
  - Docker support
