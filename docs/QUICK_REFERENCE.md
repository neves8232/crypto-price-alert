# Quick Reference

Essential commands and information for the Crypto Price Alert System.

## Essential Commands

### Service Management

```bash
# Start development mode (SQLite)
make dev

# Start production mode (PostgreSQL)
make prod

# Stop all services
make down

# Restart services
make restart

# Check service status
make status

# View logs
make logs

# View specific service logs
make logs-crypto
make logs-telegram
make logs-postgres
```

### Health Checks

```bash
# Check all services
make health

# Individual health checks
curl http://localhost:52000/health    # Crypto service
curl http://localhost:52001/health    # Telegram service (internal)
curl http://localhost:52002/metrics   # Prometheus metrics
```

### Database

```bash
# Run migrations
make db-migrate

# Backup database
make db-backup

# Restore database
make db-restore

# Access database shell
make db-shell

# Reset database (⚠️ DATA LOSS!)
make clean
```

---

## Common API Calls

### Cryptocurrencies

```bash
# List all
curl "http://localhost:52000/api/cryptocurrencies"

# Add Bitcoin
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{"crypto_id":"bitcoin","symbol":"BTC","name":"Bitcoin"}'

# Get details
curl "http://localhost:52000/api/cryptocurrencies/bitcoin"

# Remove
curl -X DELETE "http://localhost:52000/api/cryptocurrencies/bitcoin"
```

### Alerts

```bash
# List all alerts
curl "http://localhost:52000/api/alerts"

# List user's alerts
curl "http://localhost:52000/api/alerts?user_id=user123"

# Create alert
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

# Update alert
curl -X PUT "http://localhost:52000/api/alerts/ALERT_ID" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 55000.00}'

# Delete alert
curl -X DELETE "http://localhost:52000/api/alerts/ALERT_ID"
```

### Prices

```bash
# Get current prices
curl "http://localhost:52000/api/prices/current"

# Get with formatting
curl "http://localhost:52000/api/prices/current" | jq '.'
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456789:ABCdef...` |
| `AUTH_TOKEN` | Inter-service auth token | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Database password (prod) | Strong password |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | DEBUG, INFO, WARNING, ERROR |
| `CRYPTO_POLL_INTERVAL_SECONDS` | 15 | Price update frequency |
| `ALERT_DEBOUNCE_SECONDS` | 30 | Min time between alerts |
| `COINGECKO_API_KEY` | - | For higher rate limits |

### Generate Secure Tokens

```bash
# 32-byte hex (64 characters)
openssl rand -hex 32

# 32-byte base64
openssl rand -base64 32

# UUID
python3 -c "import uuid; print(uuid.uuid4())"
```

---

## Port Numbers

| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| 52000 | crypto-service | Public | Web UI & API |
| 52001 | telegram-service | Internal | Alert delivery |
| 52002 | crypto-service | Optional | Prometheus metrics |
| 52003 | telegram-service | Optional | Prometheus metrics |
| 5432 | PostgreSQL | Internal | Database |
| 9090 | Prometheus | Optional | Metrics collection |
| 3000 | Grafana | Optional | Dashboards |

---

## URLs

### Web Interfaces

| URL | Description |
|-----|-------------|
| http://localhost:52000 | Main Web UI |
| http://localhost:52000/docs | API Documentation (Swagger) |
| http://localhost:52000/redoc | API Documentation (ReDoc) |
| http://localhost:3000 | Grafana Dashboards |
| http://localhost:9090 | Prometheus Metrics |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/cryptocurrencies` | GET | List cryptocurrencies |
| `/api/cryptocurrencies` | POST | Add cryptocurrency |
| `/api/cryptocurrencies/{id}` | GET | Get cryptocurrency |
| `/api/cryptocurrencies/{id}` | DELETE | Remove cryptocurrency |
| `/api/alerts` | GET | List alerts |
| `/api/alerts` | POST | Create alert |
| `/api/alerts/{id}` | GET | Get alert |
| `/api/alerts/{id}` | PUT | Update alert |
| `/api/alerts/{id}` | DELETE | Delete alert |
| `/api/prices/current` | GET | Get current prices |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

---

## Alert Types

| Type | Behavior | Example |
|------|----------|---------|
| `PRICE_ABOVE` | Continuous above threshold | Alert while BTC > $50k |
| `PRICE_BELOW` | Continuous below threshold | Alert while ETH < $2k |
| `PRICE_CROSSES_UP` | One-time crossing up | Alert once when BTC crosses $45k upward |
| `PRICE_CROSSES_DOWN` | One-time crossing down | Alert once when ETH crosses $3k downward |
| `PRICE_CHANGE_PERCENT` | Percentage change | Alert on 5% price change |

---

## Troubleshooting Shortcuts

### Services Won't Start

```bash
# Check Docker
sudo systemctl status docker

# Check ports
sudo netstat -tulpn | grep -E "52000|52001"

# Validate environment
ls -la .env
```

### Telegram Not Working

```bash
# Verify token
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Check service
make logs-telegram
```

### Alert Not Triggering

```bash
# Check alert status
curl "http://localhost:52000/api/alerts/ALERT_ID"

# Check current price
curl "http://localhost:52000/api/prices/current"

# Check logs
make logs-crypto | grep alert_engine
```

### Database Issues

```bash
# Check PostgreSQL
docker-compose ps postgres

# Check connection
docker exec crypto-postgres pg_isready

# Restart database
docker-compose restart postgres crypto-service
```

---

## Docker Quick Reference

### Container Management

```bash
# List containers
docker-compose ps

# Stop container
docker-compose stop crypto-service

# Start container
docker-compose start crypto-service

# Restart container
docker-compose restart crypto-service

# View logs
docker-compose logs -f crypto-service

# Access shell
docker exec -it crypto-price-alert /bin/bash
```

### Image Management

```bash
# Build images
docker-compose build

# Build without cache
docker-compose build --no-cache

# Pull base images
docker-compose pull

# List images
docker images | grep crypto
```

### Volume Management

```bash
# List volumes
docker volume ls | grep crypto

# Inspect volume
docker volume inspect crypto-postgres-data

# Remove volume (⚠️ DATA LOSS!)
docker volume rm crypto-postgres-data
```

### Network Management

```bash
# List networks
docker network ls

# Inspect network
docker network inspect crypto-alert-net

# Remove network
docker network rm crypto-alert-net
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Prune unused resources
docker system prune

# Prune everything (⚠️ DATA LOSS!)
docker system prune -a --volumes
```

---

## Python Quick Reference

### Run Python in Container

```bash
# Interactive Python
docker exec -it crypto-price-alert python3

# Run script
docker exec crypto-price-alert python3 /app/scripts/script.py

# Install package (temporary)
docker exec crypto-price-alert pip install package_name
```

### Common Python Commands

```python
# Import database
from crypto_service.database import get_db

# Import models
from crypto_service.models import Alert, Cryptocurrency

# Import schemas
from crypto_service.schemas import AlertCreate

# Query database
from sqlalchemy import select
result = await db.execute(select(Alert))
alerts = result.scalars().all()
```

---

## Telegram Quick Reference

### Get Chat ID

**Method 1**: Use @userinfobot
1. Search for @userinfobot on Telegram
2. Click "Start"
3. Bot replies with your ID

**Method 2**: Check logs
```bash
# Send message to your bot
# Then check logs
make logs-telegram | grep "chat_id"
```

### Test Bot

```bash
# Verify token
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Send test message
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=YOUR_CHAT_ID" \
  -d "text=Test message"
```

---

## Monitoring Commands

### View Metrics

```bash
# All metrics
curl http://localhost:52002/metrics

# Specific metrics
curl http://localhost:52002/metrics | grep crypto_api_requests_total
curl http://localhost:52002/metrics | grep alerts_triggered_total
curl http://localhost:52002/metrics | grep database_queries_total
```

### Resource Usage

```bash
# Monitor resources
docker stats

# Monitor specific container
docker stats crypto-price-alert

# Single snapshot
docker stats --no-stream
```

### Health Monitoring

```bash
# Watch health status
watch -n 5 'curl -s http://localhost:52000/health | jq ".status"'

# Alert on unhealthy
while true; do
  status=$(curl -s http://localhost:52000/health | jq -r ".status")
  if [ "$status" != "healthy" ]; then
    echo "ALERT: Service unhealthy!"
  fi
  sleep 30
done
```

---

## Configuration Files

### Key Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `docker-compose.yml` | Service orchestration |
| `docker-compose.dev.yml` | Development overrides |
| `docker-compose.prod.yml` | Production overrides |
| `Makefile` | Common commands |
| `requirements.txt` | Python dependencies |
| `alembic.ini` | Database migrations config |

### Important Directories

| Directory | Purpose |
|-----------|---------|
| `/src/crypto_service/` | Main application code |
| `/src/telegram_service/` | Telegram service code |
| `/docs/` | Documentation |
| `/tests/` | Test files |
| `/config/` | Configuration files |
| `/scripts/` | Utility scripts |
| `/data/` | SQLite database (dev) |
| `/backups/` | Database backups |

---

## Cheat Sheet

### First-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/crypto-price-alert.git
cd crypto-price-alert

# 2. Setup environment
cp .env.example .env
nano .env  # Add your tokens

# 3. Generate tokens
openssl rand -hex 32  # For AUTH_TOKEN

# 4. Start services
make dev  # or make prod

# 5. Verify
make health
```

### Daily Operations

```bash
# Check status
make status

# View logs
make logs

# Backup database
make db-backup

# Monitor resources
docker stats
```

### Common Tasks

```bash
# Add cryptocurrency
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{"crypto_id":"bitcoin","symbol":"BTC","name":"Bitcoin"}'

# Create alert
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"user123",
    "crypto_id":"bitcoin",
    "alert_type":"PRICE_ABOVE",
    "threshold":50000,
    "telegram_chat_id":"YOUR_CHAT_ID"
  }'

# Check prices
curl "http://localhost:52000/api/prices/current" | jq '.'
```

---

## Support

- **Documentation**: [docs/](.)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/crypto-price-alert/issues)

---

**Last Updated**: November 7, 2025
