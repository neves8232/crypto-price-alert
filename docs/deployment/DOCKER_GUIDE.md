# Docker Deployment Guide

Complete guide for deploying the Crypto Price Alert System using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Environment Configuration](#environment-configuration)
5. [Development Deployment](#development-deployment)
6. [Production Deployment](#production-deployment)
7. [Monitoring Stack](#monitoring-stack)
8. [Common Operations](#common-operations)
9. [Database Management](#database-management)
10. [Troubleshooting](#troubleshooting)
11. [Security Best Practices](#security-best-practices)
12. [Backup and Restore](#backup-and-restore)
13. [Performance Tuning](#performance-tuning)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Make**: For convenience commands (optional but recommended)
- **curl**: For health checks

### Verify Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.0.0 or higher

# Check Make
make --version
```

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2 GB
- Disk: 10 GB free space

**Recommended (Production):**
- CPU: 4 cores
- RAM: 4 GB
- Disk: 20 GB free space (more for long-term data storage)

---

## Architecture Overview

### Services

The system consists of the following Docker services:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                   (crypto-network)                       │
│                                                          │
│  ┌─────────────────┐        ┌──────────────────┐       │
│  │  Crypto Service │───────▶│ Telegram Service │       │
│  │  Port: 52000    │        │  Port: 52001     │       │
│  └────────┬────────┘        └──────────────────┘       │
│           │                                              │
│           │                                              │
│  ┌────────▼────────┐        ┌──────────────────┐       │
│  │   PostgreSQL    │        │   Prometheus     │       │
│  │   Port: 5432    │        │   Port: 9090     │       │
│  └─────────────────┘        └────────┬─────────┘       │
│                                       │                  │
│                              ┌────────▼─────────┐       │
│                              │     Grafana      │       │
│                              │    Port: 3000    │       │
│                              └──────────────────┘       │
└─────────────────────────────────────────────────────────┘

External Access:
- Port 52000: Crypto Service Web UI (Public)
- Port 3000: Grafana Dashboard (Optional)
- Port 9090: Prometheus (Optional)
```

### Service Descriptions

| Service | Description | Port | Public Access |
|---------|-------------|------|---------------|
| **crypto-service** | Main API and price monitoring service | 52000 | Yes |
| **telegram-service** | Alert delivery via Telegram | 52001 | No (Internal) |
| **postgres** | PostgreSQL database | 5432 | No (Internal) |
| **prometheus** | Metrics collection (optional) | 9090 | Optional |
| **grafana** | Metrics visualization (optional) | 3000 | Optional |

---

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /home/user/crypto-price-alert

# Initialize project (creates directories and .env)
make init
```

### 2. Configure Environment

```bash
# Edit .env file with your values
nano .env

# Required fields:
# - TELEGRAM_BOT_TOKEN (from @BotFather)
# - AUTH_TOKEN (generate with: openssl rand -hex 32)
# - POSTGRES_PASSWORD (strong password)
```

### 3. Start Services

**Development Mode (SQLite database):**
```bash
make dev
```

**Production Mode (PostgreSQL database):**
```bash
make prod
```

### 4. Verify Deployment

```bash
# Check service status
make status

# Check health endpoints
make health

# View logs
make logs
```

### 5. Access Services

- **Web UI**: http://localhost:52000
- **Health Check**: http://localhost:52000/health
- **API Docs**: http://localhost:52000/docs

---

## Environment Configuration

### Creating Environment File

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

### Required Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456789:ABCdef...` | Yes |
| `AUTH_TOKEN` | Service authentication token | `openssl rand -hex 32` | Yes |
| `POSTGRES_PASSWORD` | Database password | `secure_password` | Yes (prod) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CRYPTO_POLL_INTERVAL_SECONDS` | `15` | Price update frequency |
| `COINGECKO_API_KEY` | - | API key for higher rate limits |

### Generating Secure Tokens

```bash
# Generate AUTH_TOKEN (minimum 32 characters)
openssl rand -hex 32

# Generate strong password
openssl rand -base64 24
```

### Environment Validation

```bash
# Validate environment configuration
make validate-env
```

---

## Development Deployment

Development mode uses SQLite and enables hot reloading for faster iteration.

### Start Development Environment

```bash
# Start in foreground (see logs)
make dev

# Start in background (daemon mode)
make dev-daemon

# View logs
make logs
```

### Development Features

- **SQLite Database**: No PostgreSQL needed
- **Debug Logging**: Detailed logs for troubleshooting
- **Hot Reload**: Code changes reflected immediately (requires proper setup)
- **Relaxed Rate Limits**: Higher limits for testing
- **Local Storage**: Data stored in `./data` directory

### Development Configuration

The `docker-compose.dev.yml` overrides:

```yaml
# Key development settings
environment:
  APP_ENV: development
  LOG_LEVEL: DEBUG
  DATABASE_URL: sqlite+aiosqlite:///./data/crypto_alerts.db
  CRYPTO_POLL_INTERVAL_SECONDS: 30
  ALERT_DEBOUNCE_SECONDS: 10
```

### Testing Changes

```bash
# Rebuild after code changes
make dev-down
make dev-daemon

# Run tests
make test

# Check logs
make logs-crypto
make logs-telegram
```

---

## Production Deployment

Production mode uses PostgreSQL, optimized settings, and proper security configurations.

### Pre-Deployment Checklist

- [ ] Environment file (`.env`) configured with production values
- [ ] Strong `AUTH_TOKEN` set (minimum 32 characters)
- [ ] Strong `POSTGRES_PASSWORD` set
- [ ] `TELEGRAM_BOT_TOKEN` configured
- [ ] Firewall rules configured (only allow port 52000)
- [ ] SSL/TLS certificate ready (if using reverse proxy)
- [ ] Backup strategy planned

### Production Deployment Steps

```bash
# 1. Validate environment
make validate-env

# 2. Build production images
make prod-build

# 3. Start services
make prod

# 4. Verify deployment
make status
make health

# 5. Check logs for errors
make logs
```

### Production Features

- **PostgreSQL Database**: Production-grade database with persistence
- **Resource Limits**: CPU and memory constraints
- **Auto-Restart**: Services restart on failure
- **Optimized Logging**: Compressed logs with rotation
- **Health Checks**: Automatic service monitoring
- **Security Hardening**: Non-root users, read-only filesystems

### Production Configuration

The `docker-compose.prod.yml` includes:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M

restart: always

logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"
    compress: "true"
```

### Updating Production Services

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
make prod-build
make prod-restart

# Verify
make status
make health
```

---

## Monitoring Stack

Optional Prometheus and Grafana integration for metrics and visualization.

### Enable Monitoring

```bash
# Start with monitoring stack
make monitoring-up

# Access dashboards
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

### Grafana Setup

1. **Access Grafana**: http://localhost:3000
2. **Login**:
   - Username: `admin`
   - Password: Set in `.env` (`GRAFANA_ADMIN_PASSWORD`)
3. **Add Data Source**:
   - Type: Prometheus
   - URL: http://prometheus:9090
4. **Import Dashboards**: Available in `config/grafana/dashboards/`

### Available Metrics

- **Price Collection**:
  - Request success/failure rates
  - API response times
  - Price update frequency

- **Alert System**:
  - Alerts triggered
  - Alert delivery success rate
  - Alert processing time

- **Telegram Service**:
  - Message queue size
  - Rate limit status
  - Delivery success rate

### Disable Monitoring

```bash
make monitoring-down
```

---

## Common Operations

### Service Management

```bash
# Start services
make up              # Foreground
make up-daemon       # Background
make start           # Alias for up-daemon

# Stop services
make down
make stop

# Restart services
make restart
make prod-restart    # Production

# Check status
make status
make ps
```

### Viewing Logs

```bash
# All services
make logs

# Specific service
make logs-crypto
make logs-telegram
make logs-postgres

# Follow logs (real-time)
docker-compose logs -f crypto-service

# Last 100 lines
docker-compose logs --tail=100 crypto-service
```

### Health Checks

```bash
# Check all services
make health

# Individual checks
curl http://localhost:52000/health
curl http://localhost:52001/health

# Detailed health info
curl http://localhost:52000/health | jq
```

### Shell Access

```bash
# Access crypto service shell
make shell-crypto

# Access telegram service shell
make shell-telegram

# Access PostgreSQL shell
make shell-postgres
make db-shell
```

---

## Database Management

### Migrations

```bash
# Run migrations
make db-migrate

# Create new migration (from crypto-service shell)
docker-compose exec crypto-service alembic revision --autogenerate -m "description"

# Check migration status
docker-compose exec crypto-service alembic current
```

### Database Access

```bash
# PostgreSQL shell
make db-shell

# Execute SQL directly
docker exec crypto-postgres psql -U crypto_user -d crypto_alerts -c "SELECT * FROM cryptocurrencies;"
```

### Backup and Restore

```bash
# Backup database
make db-backup
# Saves to: backups/backup_YYYYMMDD_HHMMSS.sql

# Restore from latest backup
make db-restore

# Restore specific backup
cat backups/backup_20231107_120000.sql | docker exec -i crypto-postgres psql -U crypto_user crypto_alerts
```

### Database Reset

```bash
# ⚠️  WARNING: Deletes all data!
make clean

# Restart with fresh database
make prod
make db-migrate
```

---

## Troubleshooting

### Services Won't Start

**Check Docker daemon:**
```bash
systemctl status docker
sudo systemctl start docker
```

**Check ports availability:**
```bash
# Check if ports are in use
sudo netstat -tulpn | grep 52000
sudo netstat -tulpn | grep 52001

# Kill process using port
sudo kill -9 $(lsof -t -i:52000)
```

**Check environment file:**
```bash
# Validate .env exists
ls -la .env

# Validate required variables
make validate-env
```

### Service Health Check Failures

**Check logs:**
```bash
make logs-crypto
make logs-telegram
```

**Common issues:**
- Invalid `TELEGRAM_BOT_TOKEN`
- `AUTH_TOKEN` mismatch between services
- Database connection failure
- Network connectivity issues

**Restart unhealthy service:**
```bash
docker-compose restart crypto-service
docker-compose restart telegram-service
```

### Database Connection Issues

**Check PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Test database connection:**
```bash
docker exec crypto-postgres pg_isready -U crypto_user
```

**Check database logs:**
```bash
make logs-postgres
```

**Reset database connection:**
```bash
docker-compose restart postgres
docker-compose restart crypto-service
```

### Telegram Bot Not Responding

**Verify bot token:**
```bash
# Test token with Telegram API
curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe
```

**Check service logs:**
```bash
make logs-telegram
```

**Test service endpoint:**
```bash
# From crypto-service
docker exec crypto-price-alert curl http://telegram-service:52001/health
```

### High Memory Usage

**Check resource usage:**
```bash
docker stats
```

**Limit resources (in docker-compose.prod.yml):**
```yaml
deploy:
  resources:
    limits:
      memory: 512M
```

**Restart services:**
```bash
make prod-restart
```

### Container Keeps Restarting

**Check exit code:**
```bash
docker inspect crypto-price-alert --format='{{.State.ExitCode}}'
```

**View last logs before crash:**
```bash
docker-compose logs --tail=100 crypto-service
```

**Common causes:**
- Missing environment variables
- Invalid configuration
- Database migration needed
- Port already in use

---

## Security Best Practices

### Environment Security

1. **Never commit `.env` file**
   ```bash
   # Verify .gitignore includes .env
   grep ".env" .gitignore
   ```

2. **Use strong tokens**
   ```bash
   # AUTH_TOKEN: minimum 32 characters
   openssl rand -hex 32
   ```

3. **Rotate secrets regularly**
   - Update `AUTH_TOKEN` monthly
   - Update `POSTGRES_PASSWORD` quarterly

### Network Security

1. **Firewall Configuration**
   ```bash
   # Only allow port 52000 (web UI)
   sudo ufw allow 52000/tcp
   sudo ufw deny 52001/tcp  # Block Telegram service port
   sudo ufw deny 5432/tcp   # Block PostgreSQL port
   ```

2. **Use Reverse Proxy**
   - NGINX or Caddy for SSL/TLS
   - Rate limiting
   - DDoS protection

### Container Security

1. **Non-root user**: Already configured in Dockerfiles
2. **Read-only filesystem**: Enable in production
3. **Resource limits**: Set in `docker-compose.prod.yml`

### Database Security

1. **Strong password**
   ```bash
   openssl rand -base64 24
   ```

2. **Backup encryption**
   ```bash
   # Encrypt backup
   gpg -c backups/backup_20231107.sql
   ```

3. **Regular updates**
   ```bash
   docker pull postgres:16-alpine
   make prod-restart
   ```

---

## Backup and Restore

### Automated Backups

**Create backup script** (`scripts/backup.sh`):
```bash
#!/bin/bash
cd /home/user/crypto-price-alert
make db-backup
find backups/ -name "*.sql" -mtime +7 -delete  # Keep 7 days
```

**Setup cron job**:
```bash
# Backup daily at 2 AM
0 2 * * * /home/user/crypto-price-alert/scripts/backup.sh
```

### Manual Backup

```bash
# Full backup
make db-backup

# Backup with custom name
docker exec crypto-postgres pg_dump -U crypto_user crypto_alerts > backups/manual_backup.sql
```

### Restore Procedure

```bash
# 1. Stop services
make down

# 2. Start only database
docker-compose up -d postgres

# 3. Wait for database to be ready
sleep 10

# 4. Restore backup
make db-restore

# 5. Start all services
make prod
```

### Volume Backup

```bash
# Backup Docker volumes
docker run --rm -v crypto-postgres-data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/postgres-volume.tar.gz /data

# Restore volume
docker run --rm -v crypto-postgres-data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/postgres-volume.tar.gz -C /
```

---

## Performance Tuning

### PostgreSQL Optimization

**Edit PostgreSQL configuration** (`config/postgres/postgresql.conf`):
```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Service Optimization

**Adjust polling intervals**:
```bash
# In .env
CRYPTO_POLL_INTERVAL_SECONDS=30  # Reduce API calls
ALERT_DEBOUNCE_SECONDS=60        # Reduce alert frequency
```

### Resource Limits

**Adjust in `docker-compose.prod.yml`**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Increase if needed
      memory: 2G       # Increase if needed
```

### Monitoring Performance

```bash
# Watch resource usage
docker stats

# Check service response times
time curl http://localhost:52000/health
```

---

## Port Reference

| Port | Service | Protocol | Access | Description |
|------|---------|----------|--------|-------------|
| 52000 | crypto-service | HTTP | Public | Main API and Web UI |
| 52001 | telegram-service | HTTP | Internal | Alert delivery service |
| 5432 | postgres | TCP | Internal | PostgreSQL database |
| 9090 | prometheus | HTTP | Optional | Metrics collection |
| 3000 | grafana | HTTP | Optional | Metrics visualization |

---

## Volume Management

### List Volumes

```bash
docker volume ls | grep crypto
```

### Inspect Volume

```bash
docker volume inspect crypto-postgres-data
```

### Cleanup Unused Volumes

```bash
# Remove all unused volumes
docker volume prune

# Remove specific volume (⚠️  data loss!)
docker volume rm crypto-postgres-data
```

---

## Additional Resources

- **Main README**: `/home/user/crypto-price-alert/README.md`
- **Telegram Service**: `/home/user/crypto-price-alert/src/telegram_service/README.md`
- **Crypto Service**: `/home/user/crypto-price-alert/src/crypto_service/README.md`
- **API Documentation**: http://localhost:52000/docs (when running)

---

## Support and Contributing

For issues and questions:
1. Check logs: `make logs`
2. Verify environment: `make validate-env`
3. Check health: `make health`
4. Review this guide
5. Open an issue on the project repository

---

**Last Updated**: November 2025
