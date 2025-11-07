# Changelog

All notable changes to the Crypto Price Alert System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v0.2.0
- Email notification support
- Mobile app (React Native)
- Multi-currency support (EUR, GBP, JPY)
- Advanced charting in Web UI
- Alert templates and presets
- Historical price data API
- Price history charts
- Alert scheduling (time-based rules)

### Planned for v0.3.0
- Machine learning price predictions
- Portfolio tracking
- Social trading features
- WhatsApp integration
- Desktop notifications
- Alert sharing
- Multi-user support with authentication

## [0.1.0] - 2025-11-07

### Added - Initial Release

#### Core Features
- Real-time cryptocurrency price monitoring
- Five alert types (PRICE_ABOVE, PRICE_BELOW, PRICE_CROSSES_UP, PRICE_CROSSES_DOWN, PRICE_CHANGE_PERCENT)
- Telegram notification delivery
- Web-based management UI
- RESTful API with OpenAPI documentation
- Docker-based deployment
- Microservices architecture (crypto-service + telegram-service)

#### Cryptocurrencies Management
- Add cryptocurrencies to watchlist
- Remove cryptocurrencies from watchlist
- Search cryptocurrencies by name or symbol
- View current prices and 24h change
- Support for 13M+ cryptocurrencies via CoinGecko API

#### Alerts Management
- Create price alerts with custom thresholds
- Update alert thresholds and status
- Enable/disable alerts
- Delete alerts
- Filter alerts by user, cryptocurrency, or status
- Alert debouncing (configurable, default 30 seconds)
- Custom alert messages via metadata

#### Notification System
- Dedicated Telegram service with rate limiting
- Token bucket rate limiter (25 messages/second)
- Message queue for high load handling
- Automatic retries with exponential backoff
- Delivery status tracking
- Support for HTML message formatting

#### Data Management
- PostgreSQL database for production
- SQLite support for development
- Database migrations with Alembic
- Soft delete for cryptocurrencies
- Alert trigger history tracking

#### Monitoring & Observability
- Prometheus metrics endpoints
- Structured JSON logging
- Health check endpoints
- Request ID tracing
- Database connection pooling

#### Developer Experience
- Interactive API documentation (Swagger UI)
- ReDoc API documentation
- Comprehensive error messages
- Request validation with Pydantic
- Type hints throughout codebase

#### Deployment
- Docker Compose orchestration
- Multi-stage Docker builds
- Development and production configurations
- Environment-based configuration
- Health checks for all services
- Automatic restart policies

#### Security
- Bearer token authentication for inter-service communication
- Environment variable-based secrets management
- Network isolation with Docker networks
- Input validation and sanitization
- SQL injection protection via ORM
- Secrets redaction in logs

#### Documentation
- Complete README with quick start
- API Reference with examples
- User Guide with Telegram setup instructions
- Developer Guide with code structure
- Operations Guide for production deployment
- Security documentation
- Troubleshooting guide
- Architecture Decision Records (ADRs)
- Quick Reference card
- Glossary of terms

### Technical Specifications
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0+ with async support
- PostgreSQL 14+ / SQLite 3.35+
- python-telegram-bot 20+
- httpx for async HTTP requests
- APScheduler for background tasks
- structlog for logging
- prometheus_client for metrics
- Docker 20.10+ & Docker Compose 2.0+

### API Endpoints
- `GET /api/cryptocurrencies` - List cryptocurrencies
- `POST /api/cryptocurrencies` - Add cryptocurrency
- `GET /api/cryptocurrencies/{crypto_id}` - Get cryptocurrency details
- `DELETE /api/cryptocurrencies/{crypto_id}` - Remove cryptocurrency
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `GET /api/alerts/{alert_id}` - Get alert details
- `PUT /api/alerts/{alert_id}` - Update alert
- `DELETE /api/alerts/{alert_id}` - Delete alert
- `GET /api/prices/current` - Get current prices
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Performance Metrics
- Price update interval: 15 seconds (configurable)
- Alert evaluation: < 100ms per alert
- API response time: < 200ms (p95)
- Telegram delivery: < 2s (p95)
- Database queries: < 50ms (p95)

### Resource Requirements
- crypto-service: 0.5 CPU cores, 512 MB RAM
- telegram-service: 0.25 CPU cores, 256 MB RAM
- PostgreSQL: 0.5 CPU cores, 256 MB RAM

### Known Issues
- Price history API not yet implemented (planned for v0.2.0)
- No user authentication (planned for v0.2.0)
- Web UI is basic (improvements planned for v0.2.0)
- Email notifications not yet supported (planned for v0.2.0)
- No mobile app (planned for v0.2.0)

### Dependencies
- CoinGecko API for cryptocurrency data (free tier: 30 calls/min)
- Telegram Bot API for notifications

---

## Version History

| Version | Release Date | Status | Highlights |
|---------|-------------|--------|------------|
| **0.1.0** | 2025-11-07 | **Current** | Initial production release |
| 0.2.0 | TBD | Planned | Email notifications, mobile app |
| 0.3.0 | TBD | Planned | ML predictions, portfolio tracking |

---

## Migration Guides

### Migrating to v0.2.0 (When Released)

Will include:
- Database schema changes
- API breaking changes
- Configuration updates
- Deprecation notices

---

## Deprecation Notices

None currently. This is the initial release.

---

## Security Updates

### v0.1.0
- Implemented bearer token authentication for inter-service communication
- Added secrets redaction in logs
- Enabled SQL injection protection via SQLAlchemy ORM
- Configured network isolation with Docker networks

---

## Breaking Changes

None currently. This is the initial release.

---

## Contributors

Special thanks to all contributors to v0.1.0:
- Backend Architecture Team
- Core Services Development Team
- Microservices Development Team
- Frontend Development Team
- DevOps & Infrastructure Team
- Quality Assurance Team
- Technical Documentation Team

---

## Links

- **Repository**: https://github.com/yourusername/crypto-price-alert
- **Documentation**: https://docs.crypto-price-alert.com
- **Issues**: https://github.com/yourusername/crypto-price-alert/issues
- **Releases**: https://github.com/yourusername/crypto-price-alert/releases

---

## Release Process

### Version Numbering

We follow Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

- [ ] Update version number in all files
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Update documentation
- [ ] Create git tag
- [ ] Build Docker images
- [ ] Publish release notes
- [ ] Notify users

---

**Maintained by the Crypto Price Alert Team**

For questions about this changelog, please [open an issue](https://github.com/yourusername/crypto-price-alert/issues).
