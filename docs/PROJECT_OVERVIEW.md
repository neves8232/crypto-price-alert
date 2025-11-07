# Crypto Price Alert System - Project Overview

**Project Name**: crypto-price-alert
**Status**: In Development
**Last Updated**: 2025-11-07

## Executive Summary

A Dockerized cryptocurrency price monitoring system that tracks real-time crypto prices and sends intelligent alerts via Telegram. Built with Python following microservices architecture principles.

## Core Objectives

1. **Real Data Only**: No mock data or simulations in price logic
2. **Microservices Design**: Separate containers for core logic and alert delivery
3. **Scalable Architecture**: Designed to support multiple alert channels and users
4. **Pythonic & Simple**: Clean, maintainable Python code following best practices
5. **Fully Documented**: Every technical decision backed by research and sources

## System Components

### 1. Crypto Price Alert Service (Main Container)
- **Responsibilities**:
  - Fetch real-time cryptocurrency prices from public APIs
  - Process user-defined alert rules
  - Trigger alerts when conditions are met
  - Provide web UI for configuration
  - Store user preferences and historical data

### 2. Telegram Alert Service (Separate Container)
- **Responsibilities**:
  - Receive alert requests via HTTP API
  - Send messages to Telegram Bot API
  - Handle rate limiting and retries
  - Provide health check endpoints
  - Log all message deliveries

## Technical Requirements

### Language & Framework
- **Primary**: Python 3.11+
- **Web Framework**: Flask or FastAPI (to be decided)
- **Database**: SQLite (dev) / PostgreSQL (prod)

### Deployment
- **Containerization**: Docker
- **Orchestration**: docker-compose
- **Networking**: Internal Docker network with auth tokens
- **Port Policy**: Random non-default ports (avoid 80, 443, 8080)

### Data Sources
Must evaluate and select from:
- CoinGecko (free tier)
- Binance Public API
- Coinbase Exchange API
- CryptoCompare

**Selection Criteria**: Latency, rate limits, data completeness, cost, reliability

### Security
- Environment variables for secrets
- Auth tokens for inter-service communication
- No sensitive data in logs
- Secure Telegram token handling

## Functional Requirements

### Cryptocurrency Selection
- User can select multiple cryptocurrencies (default: BTC, ETH)
- Maximum watchlist: 25 assets
- Easy add/remove via web UI

### Alert Conditions
1. **Price Crosses Up**: Alert when price rises above threshold
2. **Price Crosses Down**: Alert when price falls below threshold
3. **Absolute Dollar Steps**: Alert every $X change (e.g., every $500 for BTC)
4. **Percentage Steps**: Alert on Y% change (e.g., every 5%)
5. **Custom Price Points**: Alert at specific price levels

### Alert Intelligence
- **Debouncing**: Minimum 30-second interval per asset
- **Suggestions Engine**: Recommend sensible step values per crypto
- **User Override**: Accept, modify, or ignore suggestions

### Data Refresh
- Minimum poll interval: 5 seconds
- Recommended default: 15 seconds
- Respect API rate limits
- Graceful degradation on API errors

## Non-Functional Requirements

### Performance
- Sub-second alert delivery after price trigger
- Support up to 25 simultaneous crypto monitors
- Handle API rate limits gracefully

### Reliability
- Auto-reconnect on API failures
- Health check endpoints
- Structured logging for debugging
- Graceful container restarts

### Observability
- `/health` endpoint on both services
- `/metrics` endpoint (Prometheus-compatible)
- Structured JSON logs to stdout
- Request/response logging with timestamps

### Testing
- Unit tests for core logic (pytest)
- Integration tests with real API calls (dev environment)
- End-to-end validation with live Telegram delivery
- CI pipeline to run tests on PR

## Architecture Principles

1. **Separation of Concerns**: Core logic separate from alert delivery
2. **Stateless Services**: Enable horizontal scaling
3. **API-First Design**: Well-defined interfaces between components
4. **Configuration as Code**: docker-compose for deployment
5. **Fail-Fast**: Clear error messages, no silent failures

## Development Workflow

### Phase 1: Research & Design (Current)
- [ ] Evaluate cryptocurrency data APIs
- [ ] Design system architecture
- [ ] Define inter-service API contracts
- [ ] Create technical documentation

### Phase 2: Core Development
- [ ] Implement Telegram Alert Service
- [ ] Implement Crypto Price Service
- [ ] Build Web UI
- [ ] Create Docker setup

### Phase 3: Testing & Validation
- [ ] Unit tests for all modules
- [ ] Integration tests with real APIs
- [ ] End-to-end alert delivery test
- [ ] Load testing

### Phase 4: Documentation & Deployment
- [ ] API documentation
- [ ] Deployment guide
- [ ] Operational runbook
- [ ] User guide

## Success Criteria

✅ **MVP Acceptance**:
1. Two containers running via docker-compose
2. Real crypto prices fetched from selected API
3. Web UI for configuring alerts
4. Alert triggered on price condition
5. Telegram message delivered successfully
6. All major decisions documented with sources

## Team Structure

- **Research Lead**: API evaluation and documentation
- **Backend Architect**: System design and interfaces
- **Core Services Developer**: Main crypto alert logic
- **Microservices Developer**: Telegram service
- **Frontend Developer**: Web UI
- **DevOps Engineer**: Docker and deployment
- **QA Engineer**: Testing strategy and implementation
- **Documentation Specialist**: Technical writing

## Constraints

- ❌ No default ports (80, 443, 8080)
- ❌ No mock data in production logic
- ❌ No undocumented technical decisions
- ❌ No hardcoded secrets
- ✅ Must use real cryptocurrency data
- ✅ Must document API terms and rate limits
- ✅ Must implement proper error handling
- ✅ Must follow Python best practices (PEP8, type hints)

## References

- Full requirements: See repository root
- Architecture decisions: `/docs/architecture/`
- API research: `/docs/api_research/`
- Development guides: `/docs/development/`
