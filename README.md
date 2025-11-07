# Crypto Price Alert System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/crypto-price-alert)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A production-ready cryptocurrency price monitoring and alert system with real-time price tracking, configurable alert conditions, and instant Telegram notifications.

## Features

- ✅ **Real-time Price Monitoring**: Track cryptocurrency prices with configurable polling intervals
- ✅ **Flexible Alert Types**: Price thresholds, percentage changes, and crossing alerts
- ✅ **Telegram Notifications**: Instant alerts delivered via Telegram Bot
- ✅ **Web-based Management UI**: Configure alerts and monitor prices through browser
- ✅ **RESTful API**: Complete API for programmatic access
- ✅ **Microservices Architecture**: Separate services for core logic and messaging
- ✅ **Production-Ready**: Docker-based deployment with PostgreSQL
- ✅ **Comprehensive Monitoring**: Prometheus metrics and Grafana dashboards
- ✅ **Secure by Design**: Token-based authentication, encrypted secrets
- ✅ **Scalable**: Stateless services, horizontal scaling ready

## Quick Start

Get the system running in under 5 minutes:

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crypto-price-alert.git
cd crypto-price-alert

# Copy environment template
cp .env.example .env

# Edit .env and set required values
nano .env
# Required: TELEGRAM_BOT_TOKEN, AUTH_TOKEN, POSTGRES_PASSWORD

# Generate secure tokens
openssl rand -hex 32  # For AUTH_TOKEN

# Start services (development mode with SQLite)
make dev

# Or start in production mode (with PostgreSQL)
make prod
```

### Access the System

- **Web UI**: http://localhost:52000
- **API Documentation**: http://localhost:52000/docs
- **Health Check**: http://localhost:52000/health
- **Metrics**: http://localhost:52002/metrics

### Create Your First Alert

1. Open http://localhost:52000 in your browser
2. Add a cryptocurrency to monitor (e.g., Bitcoin)
3. Create an alert:
   - Set price threshold
   - Choose alert type (above/below/cross)
   - Enter your Telegram chat ID
4. Wait for price to trigger alert
5. Receive notification in Telegram!

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│                                                              │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │  Crypto Service  │──────────▶│ Telegram Service │       │
│  │  Port: 52000     │  HTTP API │  Port: 52001     │       │
│  │                  │  Auth     │  (Internal)      │       │
│  │  • Price Polling │           │  • Rate Limiting │       │
│  │  • Alert Engine  │           │  • Message Queue │       │
│  │  • Web UI        │           │  • Delivery      │       │
│  │  • REST API      │           │                  │       │
│  └────────┬─────────┘           └──────────┬───────┘       │
│           │                                 │                │
│           │                                 │                │
│  ┌────────▼─────────┐           ┌──────────▼───────┐       │
│  │   PostgreSQL     │           │  External APIs   │       │
│  │   Port: 5432     │           │  • CoinGecko     │       │
│  │   (Internal)     │           │  • Telegram      │       │
│  └──────────────────┘           └──────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘

User → Web UI (52000) → Crypto Service → Alert Engine → Telegram Service → Telegram Bot API → User's Phone
```

### Key Components

- **crypto-service**: Main application service handling price monitoring, alert evaluation, and web UI
- **telegram-service**: Dedicated microservice for Telegram message delivery with rate limiting
- **PostgreSQL**: Production database for storing alerts, prices, and configurations
- **CoinGecko API**: External cryptocurrency data provider

## Documentation

### User Documentation
- **[User Guide](docs/USER_GUIDE.md)**: Setup Telegram bot, configure alerts, troubleshooting
- **[Quick Reference](docs/QUICK_REFERENCE.md)**: Essential commands and quick tips
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Glossary](docs/GLOSSARY.md)**: Technical terms and definitions

### Developer Documentation
- **[Developer Guide](docs/development/DEVELOPER_GUIDE.md)**: Development setup, code structure, testing
- **[API Reference](docs/API_REFERENCE.md)**: Complete REST API documentation
- **[System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)**: Detailed architecture overview
- **[Architecture Decisions](docs/architecture/decisions/)**: ADR records for key decisions
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

### Operations Documentation
- **[Operations Guide](docs/operations/OPERATIONS_GUIDE.md)**: Production deployment, monitoring, scaling
- **[Docker Guide](docs/deployment/DOCKER_GUIDE.md)**: Docker deployment instructions
- **[Security Documentation](docs/SECURITY.md)**: Security model and best practices

## Alert Types

The system supports multiple alert types:

| Alert Type | Description | Example |
|------------|-------------|---------|
| **PRICE_ABOVE** | Trigger when price goes above threshold | Alert when BTC > $50,000 |
| **PRICE_BELOW** | Trigger when price goes below threshold | Alert when ETH < $2,000 |
| **PRICE_CROSSES_UP** | Trigger when price crosses above (once) | Alert when BTC crosses $45,000 upward |
| **PRICE_CROSSES_DOWN** | Trigger when price crosses below (once) | Alert when ETH crosses $3,000 downward |
| **PRICE_CHANGE_PERCENT** | Trigger on percentage change | Alert on 5% price change |

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Application runtime |
| **Web Framework** | FastAPI | REST API and async operations |
| **Database** | PostgreSQL 14+ / SQLite | Data persistence |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Telegram** | python-telegram-bot | Telegram Bot API |
| **Scheduler** | APScheduler | Background price polling |
| **HTTP Client** | httpx | Async API requests |
| **Metrics** | Prometheus | Performance monitoring |
| **Logging** | structlog | Structured JSON logging |
| **Container** | Docker & Compose | Deployment |

## API Endpoints

### Cryptocurrencies

```bash
# List monitored cryptocurrencies
GET /api/cryptocurrencies

# Add cryptocurrency to watchlist
POST /api/cryptocurrencies
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "name": "Bitcoin"
}

# Get cryptocurrency details
GET /api/cryptocurrencies/{crypto_id}

# Remove cryptocurrency
DELETE /api/cryptocurrencies/{crypto_id}
```

### Alerts

```bash
# List all alerts (with optional filters)
GET /api/alerts?user_id={user_id}&enabled=true

# Create new alert
POST /api/alerts
{
  "user_id": "user123",
  "crypto_id": "bitcoin",
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00,
  "telegram_chat_id": "123456789",
  "enabled": true
}

# Get alert details
GET /api/alerts/{alert_id}

# Update alert
PUT /api/alerts/{alert_id}
{
  "threshold": 55000.00,
  "enabled": true
}

# Delete alert
DELETE /api/alerts/{alert_id}
```

### Current Prices

```bash
# Get current prices for all monitored cryptocurrencies
GET /api/prices/current
```

### Health Check

```bash
# Check service health
GET /health

# Response:
{
  "status": "healthy",
  "service": "crypto-price-alert",
  "version": "0.1.0",
  "timestamp": "2025-11-07T10:30:00Z",
  "checks": {
    "database": "connected",
    "crypto_api": "connected",
    "telegram_service": "connected"
  }
}
```

See [API Reference](docs/API_REFERENCE.md) for complete documentation.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token from @BotFather |
| `AUTH_TOKEN` | Yes | - | Inter-service authentication token |
| `POSTGRES_PASSWORD` | Yes (prod) | - | PostgreSQL database password |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CRYPTO_POLL_INTERVAL_SECONDS` | No | 15 | Price update frequency in seconds |
| `COINGECKO_API_KEY` | No | - | CoinGecko API key for higher rate limits |
| `ALERT_DEBOUNCE_SECONDS` | No | 30 | Minimum time between alert triggers |

### Alert Configuration

Alerts support metadata for advanced configuration:

```json
{
  "metadata": {
    "step_value": 500,         // For step-based alerts
    "percentage": 5.0,          // For percentage-based alerts
    "custom_message": "Custom notification text",
    "notification_channels": ["telegram", "email"]
  }
}
```

## Deployment

### Development

```bash
# Start with SQLite database (no PostgreSQL needed)
make dev

# View logs
make logs

# Stop services
make down
```

### Production

```bash
# Start with PostgreSQL
make prod

# Check health
make health

# View metrics
curl http://localhost:52002/metrics

# Backup database
make db-backup

# Scale services
docker-compose up -d --scale crypto-service=3
```

### Monitoring

```bash
# Start with monitoring stack (Prometheus + Grafana)
make monitoring-up

# Access Grafana: http://localhost:3000
# Access Prometheus: http://localhost:9090
```

See [Docker Guide](docs/deployment/DOCKER_GUIDE.md) for detailed deployment instructions.

## Security

- **Token-based authentication** between services
- **Encrypted secrets** via environment variables
- **Network isolation** with Docker networks
- **Rate limiting** on all external APIs
- **Input validation** with Pydantic schemas
- **SQL injection protection** via SQLAlchemy ORM
- **No credentials in logs** (automatic redaction)

See [Security Documentation](docs/SECURITY.md) for details.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_services/test_alert_engine.py -v

# Run integration tests
pytest tests/integration/ -v
```

## Monitoring and Metrics

The system exposes Prometheus metrics:

```bash
# Service metrics
curl http://localhost:52002/metrics

# Example metrics:
# - crypto_api_requests_total{provider="coingecko",status="success"}
# - alerts_triggered_total{crypto="bitcoin",type="PRICE_ABOVE"}
# - telegram_messages_sent_total{status="success"}
# - database_queries_total{operation="select"}
# - active_alerts_gauge
# - price_updates_total
```

## Performance

### Benchmarks

- **Price Updates**: 15-second intervals (configurable)
- **Alert Evaluation**: < 100ms per alert
- **API Response Time**: < 200ms (p95)
- **Telegram Delivery**: < 2s (p95)
- **Database Queries**: < 50ms (p95)

### Resource Usage

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| crypto-service | 0.5 cores | 512 MB | With 50 active alerts |
| telegram-service | 0.25 cores | 256 MB | Under normal load |
| PostgreSQL | 0.5 cores | 256 MB | With 90 days of data |

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port availability
sudo netstat -tulpn | grep 52000

# Validate environment
make validate-env
```

**Telegram bot not responding:**
```bash
# Verify token
curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe

# Check service logs
make logs-telegram
```

**Database connection errors:**
```bash
# Check PostgreSQL health
docker-compose ps postgres

# Restart database
docker-compose restart postgres crypto-service
```

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for more solutions.

## Roadmap

### Version 0.2.0 (Planned)
- [ ] Email notification support
- [ ] Mobile app (React Native)
- [ ] Multi-currency support (EUR, GBP, JPY)
- [ ] Advanced charting in Web UI
- [ ] Alert templates and presets

### Version 0.3.0 (Future)
- [ ] Machine learning price predictions
- [ ] Portfolio tracking
- [ ] Social trading features
- [ ] WhatsApp integration
- [ ] Desktop notifications

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **CoinGecko** for providing comprehensive cryptocurrency data API
- **Telegram** for the excellent Bot API platform
- **FastAPI** team for the outstanding web framework
- **SQLAlchemy** team for the powerful ORM
- **Docker** for simplifying deployment

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/neves8232/crypto-price-alert/issues)
- **Discussions**: [GitHub Discussions](https://github.com/neves8232/crypto-price-alert/discussions)
- **Email**: support@crypto-price-alert.com

## Project Status

**Current Version**: 0.1.0 (Initial Release)
**Status**: ✅ Production Ready
**Last Updated**: November 7, 2025

---

**Built with ❤️ by the Crypto Price Alert Team**

*Powered by [CoinGecko API](https://www.coingecko.com/en/api)*
