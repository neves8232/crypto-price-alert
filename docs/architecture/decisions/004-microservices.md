# ADR 004: Adopt Microservices Architecture with Separate Telegram Service

## Status

**Accepted** - November 7, 2025

## Context

We needed to decide on the overall system architecture for the Crypto Price Alert System. The key decision was whether to build a monolithic application or separate concerns into distinct services.

**Key Considerations**:
- Telegram API has strict rate limits (30 messages/second)
- Price monitoring needs to run continuously in the background
- Different components have different scaling requirements
- Alert delivery must be reliable and fault-tolerant
- Development teams may work on different components independently

### Alternatives Considered

1. **Microservices** - Separate crypto service and Telegram service
2. **Monolithic** - Single application handling all functionality
3. **Modular Monolith** - Single deployment with clear module boundaries
4. **Serverless** - Function-based architecture (Lambda, Cloud Functions)

## Decision

We chose a **microservices architecture** with two primary services:

1. **crypto-service**: Core application (price monitoring, alert logic, API, web UI)
2. **telegram-service**: Dedicated messaging service (rate limiting, delivery, retry logic)

## Rationale

### Why Microservices?

**1. Independent Scaling**
- Telegram service can scale independently based on message volume
- Crypto service scales based on number of monitored cryptocurrencies
- Different resource requirements:
  - Crypto service: CPU-intensive (price polling, alert evaluation)
  - Telegram service: I/O-intensive (message delivery, HTTP requests)

**2. Fault Isolation**
- Telegram service failure doesn't crash price monitoring
- Price monitoring continues even if message delivery is down
- Easier to identify and debug issues
- Better system resilience

**3. Rate Limiting Isolation**
- Telegram API rate limits (30 msg/sec) isolated to one service
- Token bucket algorithm managed in dedicated service
- Message queue prevents overwhelming Telegram API
- Crypto service doesn't need to handle Telegram limits

**4. Technology Independence**
- Each service can use optimal technology stack
- Easier to swap out Telegram for other notification services
- Future: Email service, SMS service, etc.

**5. Development Velocity**
- Teams can work independently on each service
- Faster iteration and deployment cycles
- Clear service boundaries and responsibilities
- Better code organization

**6. Security**
- Telegram bot token isolated to one service
- Network-level isolation via Docker networks
- Token-based inter-service authentication
- Principle of least privilege

### Service Responsibilities

**Crypto Service**:
```
┌─────────────────────────────┐
│     Crypto Service          │
├─────────────────────────────┤
│ • Price Monitoring          │
│ • Alert Evaluation          │
│ • Cryptocurrency Management │
│ • Alert Configuration       │
│ • Web UI                    │
│ • REST API                  │
│ • Database Management       │
│ • Health Checks             │
└─────────────────────────────┘
```

**Telegram Service**:
```
┌─────────────────────────────┐
│    Telegram Service         │
├─────────────────────────────┤
│ • Message Delivery          │
│ • Rate Limiting             │
│ • Message Queue             │
│ • Retry Logic               │
│ • Delivery Tracking         │
│ • Token Management          │
│ • Health Checks             │
└─────────────────────────────┘
```

### Why Not Monolithic?

**Monolithic Drawbacks**:
- All components scale together (inefficient)
- Single failure point
- Harder to isolate rate limiting concerns
- Deployment requires full application restart
- Tighter coupling between components

### Why Not Modular Monolith?

**Modular Monolith Drawbacks**:
- Still requires full restart for any change
- Can't scale components independently
- Rate limiting complexity in shared runtime
- Harder to enforce module boundaries

### Why Not Serverless?

**Serverless Drawbacks**:
- Cold start latency for price monitoring
- Cost for continuous polling (24/7 operation)
- State management complexity
- Harder to debug and monitor
- Vendor lock-in concerns

## Consequences

### Positive

1. **Scalability**: Independent scaling of services
2. **Resilience**: Fault isolation between services
3. **Maintainability**: Clear service boundaries
4. **Development**: Parallel development possible
5. **Deployment**: Independent deployment cycles
6. **Security**: Service-level isolation

### Negative

1. **Complexity**: More moving parts to manage
2. **Network Latency**: Inter-service communication overhead
3. **Distributed Debugging**: Harder to trace issues across services
4. **Deployment**: More complex deployment process
5. **Testing**: Need integration tests across services

### Neutral

1. **Container Orchestration**: Requires Docker Compose (or Kubernetes later)
2. **Service Discovery**: Services must know how to reach each other
3. **Monitoring**: Need to monitor multiple services

## Implementation Details

### Service Communication

**HTTP REST API**:
```python
# Crypto service -> Telegram service
async def send_telegram_alert(alert: Alert, price: Decimal):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://telegram-service:52001/api/v1/alerts/send",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={
                "chat_id": alert.telegram_chat_id,
                "message": format_alert_message(alert, price),
                "priority": "high"
            },
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()
```

**Authentication**:
```python
# Bearer token authentication
async def verify_auth_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)

    token = authorization.split()[1]
    if not secrets.compare_digest(token, os.getenv("AUTH_TOKEN")):
        raise HTTPException(status_code=401)

    return token
```

### Service Configuration

**Docker Compose**:
```yaml
version: '3.8'

services:
  crypto-service:
    build: ./src/crypto_service
    ports:
      - "52000:52000"  # Public API
    environment:
      - TELEGRAM_SERVICE_URL=http://telegram-service:52001
      - AUTH_TOKEN=${AUTH_TOKEN}
    depends_on:
      - postgres
      - telegram-service
    networks:
      - crypto-alert-net

  telegram-service:
    build: ./src/telegram_service
    ports:
      - "52001:52001"  # Internal only (no external exposure)
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - AUTH_TOKEN=${AUTH_TOKEN}
    networks:
      - crypto-alert-net

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - crypto-alert-net

networks:
  crypto-alert-net:
    driver: bridge

volumes:
  postgres_data:
```

### Network Isolation

**Security Design**:
- Only crypto-service exposed to external network (port 52000)
- telegram-service internal only (no external access)
- postgres internal only (no external access)
- Inter-service communication via Docker network
- Bearer token authentication required

### Health Checks

**Crypto Service**:
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "telegram_service": await check_telegram_service(),
        "crypto_api": await check_coingecko_api(),
    }

    status = "healthy" if all(checks.values()) else "unhealthy"
    return {
        "status": status,
        "service": "crypto-price-alert",
        "version": "0.1.0",
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

**Telegram Service**:
```python
@app.get("/health")
async def health_check():
    checks = {
        "telegram_api": await check_telegram_api(),
        "rate_limiter": check_rate_limiter_status(),
        "message_queue": get_queue_size(),
    }

    status = "healthy" if all(checks.values()) else "unhealthy"
    return {
        "status": status,
        "service": "telegram-alert-service",
        "version": "0.1.0",
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

## Service Responsibilities Matrix

| Responsibility | Crypto Service | Telegram Service |
|----------------|----------------|------------------|
| Price Monitoring | ✅ Owns | ❌ None |
| Alert Evaluation | ✅ Owns | ❌ None |
| Database Access | ✅ Owns | ❌ None |
| Web UI | ✅ Owns | ❌ None |
| REST API | ✅ Owns | ⚠️ Internal API only |
| Telegram Messaging | ⚠️ Client | ✅ Owns |
| Rate Limiting | ❌ None | ✅ Owns |
| Message Queue | ❌ None | ✅ Owns |
| Retry Logic | ⚠️ Basic | ✅ Advanced |

## Scaling Strategy

### Horizontal Scaling

**Crypto Service**:
```bash
# Scale to 3 instances
docker-compose up -d --scale crypto-service=3

# Load balancer (nginx) distributes requests
```

**Telegram Service**:
```bash
# Scale to 2 instances for high message volume
docker-compose up -d --scale telegram-service=2

# Shared rate limiter state (via Redis in future)
```

### Resource Allocation

**Production Deployment**:
```yaml
services:
  crypto-service:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  telegram-service:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Testing Strategy

### Unit Tests
- Each service tested independently
- Mock inter-service communication
- Fast, isolated tests

### Integration Tests
```python
@pytest.mark.integration
async def test_alert_delivery_flow():
    """Test full flow from alert trigger to Telegram delivery"""
    # 1. Create alert in crypto service
    alert = await crypto_client.create_alert(...)

    # 2. Trigger alert condition
    await crypto_client.update_price("bitcoin", 51000)

    # 3. Verify Telegram message sent
    messages = await telegram_client.get_sent_messages()
    assert len(messages) == 1
    assert "Bitcoin" in messages[0]["text"]
```

### End-to-End Tests
- Full Docker Compose deployment
- Real Telegram API (test bot)
- Verify complete workflow

## Future Enhancements

### Version 0.2.0
- Add email service (similar microservice pattern)
- Add SMS service
- Implement service mesh (Istio/Linkerd)

### Version 0.3.0
- Migrate to Kubernetes for orchestration
- Implement event-driven architecture (message bus)
- Add notification orchestrator service

## Migration Path

If microservices prove too complex:

1. **Merge Services**: Combine into modular monolith
2. **Keep Modules**: Maintain clear module boundaries
3. **Extract Later**: Can re-extract when needed

**Rollback Plan**:
```python
# Import Telegram module directly
from telegram_service.telegram_client import TelegramClient

# Use as internal module
telegram = TelegramClient(bot_token=BOT_TOKEN)
await telegram.send_message(chat_id, message)
```

## Monitoring and Observability

**Prometheus Metrics**:
```python
# Crypto Service
crypto_api_requests_total
alerts_triggered_total
alerts_evaluated_total

# Telegram Service
telegram_messages_sent_total
telegram_rate_limit_hits_total
telegram_queue_size_gauge
```

**Distributed Tracing** (Future):
- Add request ID to all inter-service calls
- Implement OpenTelemetry
- Trace alert flow across services

## Security Considerations

**Network Security**:
- Docker network isolation
- No external access to Telegram service
- Firewall rules block internal ports

**Authentication**:
- Bearer token for inter-service auth
- Tokens in environment variables only
- Secrets never in logs

**Failure Modes**:
- Telegram service down: Crypto service continues monitoring
- Crypto service down: Telegram service idle (no impact)
- Database down: Both services degraded gracefully

## Alternatives Reconsidered

We will reconsider this decision if:
- Operational complexity becomes overwhelming
- Inter-service latency impacts performance
- Team size shrinks (harder to maintain multiple services)
- Cost of infrastructure exceeds benefits

## References

- **Microservices Pattern**: https://microservices.io/patterns/microservices.html
- **Docker Networking**: https://docs.docker.com/network/
- **Service Discovery**: https://www.nginx.com/blog/service-discovery-in-a-microservices-architecture/

## Related Decisions

- [ADR 001: Use FastAPI](001-use-fastapi.md) - FastAPI supports microservices well
- [ADR 005: Rate Limiting Strategy](005-rate-limiting.md) - Rate limiting in Telegram service

## Review Date

**Next Review**: May 2026 (6 months from decision)

**Review Triggers**:
- Operational issues with multiple services
- Team requests consolidation
- Performance problems from network latency
- Deployment complexity impacts velocity

---

**Decision made by**: Backend Architecture Team
**Date**: November 7, 2025
**Approved by**: Technical Lead
