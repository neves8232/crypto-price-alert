# Troubleshooting Guide

Common issues and solutions for the Crypto Price Alert System.

## Table of Contents

1. [Services Won't Start](#services-wont-start)
2. [Telegram Bot Issues](#telegram-bot-issues)
3. [Alert Issues](#alert-issues)
4. [Database Issues](#database-issues)
5. [Price Update Issues](#price-update-issues)
6. [Performance Issues](#performance-issues)
7. [Network Issues](#network-issues)
8. [Docker Issues](#docker-issues)
9. [Debug Mode](#debug-mode)
10. [Getting Help](#getting-help)

---

## Services Won't Start

### Symptom: `make dev` or `make prod` fails

**Check 1: Docker daemon running**
```bash
# Check Docker status
sudo systemctl status docker

# Start Docker if stopped
sudo systemctl start docker

# Enable Docker auto-start
sudo systemctl enable docker
```

**Check 2: Port availability**
```bash
# Check if ports are in use
sudo netstat -tulpn | grep 52000
sudo netstat -tulpn | grep 52001
sudo netstat -tulpn | grep 5432

# Kill process using port (if necessary)
sudo kill -9 $(lsof -t -i:52000)
```

**Check 3: Environment file exists**
```bash
# Verify .env file exists
ls -la .env

# If missing, copy template
cp .env.example .env

# Edit with your values
nano .env
```

**Check 4: Validate environment**
```bash
# Check required variables are set
make validate-env

# Or manually check
grep "TELEGRAM_BOT_TOKEN" .env
grep "AUTH_TOKEN" .env
grep "POSTGRES_PASSWORD" .env  # For production
```

**Check 5: Docker Compose version**
```bash
# Check version
docker-compose --version

# Should be 2.0.0 or higher
# Update if needed:
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

**Check 6: Disk space**
```bash
# Check available space
df -h

# Clean up Docker if needed
docker system prune -a
```

---

## Telegram Bot Issues

### Symptom: Not receiving alerts

**Check 1: Verify bot token**
```bash
# Test token with Telegram API
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Should return bot information
# If error, token is invalid
```

**Expected response**:
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "My Crypto Bot",
    "username": "my_crypto_bot"
  }
}
```

**Check 2: Verify chat ID**
```bash
# Send a message to your bot on Telegram
# Then check logs for your chat ID
make logs-telegram | grep "chat_id"
```

**Check 3: Check service health**
```bash
# Check Telegram service status
docker-compose ps telegram-service

# Check logs for errors
make logs-telegram

# Check health endpoint (from crypto-service)
docker exec crypto-price-alert curl http://telegram-service:52001/health
```

**Check 4: Verify authentication token**
```bash
# Tokens must match between services
# In .env:
AUTH_TOKEN=same_token_for_both_services
```

**Check 5: Check rate limiting**
```bash
# View Telegram service metrics
curl http://localhost:52003/metrics | grep telegram_rate_limit
```

### Symptom: Bot exists but won't respond

**Solution 1: Start the bot**
- Open Telegram
- Find your bot (search by username)
- Click "Start" button
- Bot is now activated for your account

**Solution 2: Restart Telegram service**
```bash
docker-compose restart telegram-service

# Check logs
make logs-telegram
```

---

## Alert Issues

### Symptom: Alert not triggering

**Check 1: Alert is enabled**
```bash
# Get alert details
curl "http://localhost:52000/api/alerts/YOUR_ALERT_ID"

# Check "enabled" field is true
```

**Check 2: Price meets condition**
```bash
# Get current price
curl "http://localhost:52000/api/prices/current"

# Compare with alert threshold
curl "http://localhost:52000/api/alerts/YOUR_ALERT_ID" | jq '.threshold'
```

**Check 3: Debounce period**
```bash
# Check last_triggered_at
curl "http://localhost:52000/api/alerts/YOUR_ALERT_ID" | jq '.last_triggered_at'

# Alert won't trigger again within 30 seconds (default)
```

**Check 4: Cryptocurrency is monitored**
```bash
# List monitored cryptocurrencies
curl "http://localhost:52000/api/cryptocurrencies"

# Add if missing
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{"crypto_id":"bitcoin","symbol":"BTC","name":"Bitcoin"}'
```

**Check 5: Alert type correct**
```bash
# PRICE_ABOVE: Triggers while price > threshold
# PRICE_BELOW: Triggers while price < threshold
# PRICE_CROSSES_UP: Triggers once when crossing up
# PRICE_CROSSES_DOWN: Triggers once when crossing down
```

**Check 6: Check logs**
```bash
# Search for alert evaluation
make logs-crypto | grep alert_engine

# Look for your alert_id
make logs-crypto | grep YOUR_ALERT_ID
```

### Symptom: Too many alerts

**Solution 1: Increase debounce period**
```bash
# Edit .env
ALERT_DEBOUNCE_SECONDS=60  # Increase from 30 to 60

# Restart services
make restart
```

**Solution 2: Use CROSSES alerts instead**
```bash
# Instead of PRICE_ABOVE (continuous)
# Use PRICE_CROSSES_UP (one-time)

curl -X PUT "http://localhost:52000/api/alerts/YOUR_ALERT_ID" \
  -H "Content-Type: application/json" \
  -d '{"alert_type":"PRICE_CROSSES_UP"}'
```

**Solution 3: Disable alert temporarily**
```bash
curl -X PUT "http://localhost:52000/api/alerts/YOUR_ALERT_ID" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

---

## Database Issues

### Symptom: Database connection errors

**Check 1: PostgreSQL running** (production)
```bash
# Check container status
docker-compose ps postgres

# Check logs
make logs-postgres

# Test connection
docker exec crypto-postgres pg_isready -U crypto_user
```

**Check 2: Connection string correct**
```bash
# For production (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://crypto_user:password@postgres:5432/crypto_alerts

# For development (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/crypto_alerts.db
```

**Check 3: Database initialized**
```bash
# Run migrations
make db-migrate

# Or manually
docker exec crypto-price-alert alembic upgrade head
```

**Solution 1: Restart database**
```bash
docker-compose restart postgres
docker-compose restart crypto-service
```

**Solution 2: Reset database** (⚠️ DATA LOSS!)
```bash
# Backup first!
make db-backup

# Clean and restart
make clean
make prod
make db-migrate
```

### Symptom: Migration errors

**Check current migration**
```bash
docker exec crypto-price-alert alembic current
```

**Rollback migration**
```bash
docker exec crypto-price-alert alembic downgrade -1
```

**Recreate migration**
```bash
docker exec crypto-price-alert alembic revision --autogenerate -m "description"
```

---

## Price Update Issues

### Symptom: Prices not updating

**Check 1: CoinGecko API connection**
```bash
# Test CoinGecko API directly
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# Should return current Bitcoin price
```

**Check 2: Rate limit exceeded**
```bash
# Check logs for 429 errors
make logs-crypto | grep "429"
make logs-crypto | grep "rate_limit"

# View metrics
curl http://localhost:52002/metrics | grep crypto_api_requests_total
```

**Solution: Use API key**
```bash
# Get free API key from CoinGecko
# Add to .env:
COINGECKO_API_KEY=your_api_key_here

# Restart
make restart
```

**Check 3: Price collector running**
```bash
# Check logs for price updates
make logs-crypto | grep price_collector

# Should see regular updates every 15 seconds
```

**Check 4: Cryptocurrency ID correct**
```bash
# Verify crypto_id matches CoinGecko
# Check: https://www.coingecko.com/en/coins/bitcoin
# URL shows the correct ID: "bitcoin"
```

**Solution: Adjust poll interval**
```bash
# Edit .env (if rate limited)
CRYPTO_POLL_INTERVAL_SECONDS=30  # Increase from 15 to 30

# Restart
make restart
```

### Symptom: Stale prices

**Check last update time**
```bash
curl "http://localhost:52000/api/cryptocurrencies/bitcoin" | jq '.last_updated'
```

**Check scheduler running**
```bash
make logs-crypto | grep scheduler
make logs-crypto | grep "Polling crypto prices"
```

**Restart services**
```bash
make restart
```

---

## Performance Issues

### Symptom: Slow API responses

**Check 1: Resource usage**
```bash
# Monitor container resources
docker stats

# Should see:
# - crypto-service: < 50% CPU, < 512MB RAM
# - telegram-service: < 25% CPU, < 256MB RAM
```

**Check 2: Database queries**
```bash
# Check database metrics
curl http://localhost:52002/metrics | grep database_queries_total

# Look for slow queries in logs
make logs-crypto | grep "slow_query"
```

**Solution 1: Increase resource limits**
```yaml
# Edit docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
```

**Solution 2: Reduce monitored cryptocurrencies**
```bash
# Remove unused cryptocurrencies
curl -X DELETE "http://localhost:52000/api/cryptocurrencies/unused_coin"
```

### Symptom: High memory usage

**Check memory**
```bash
docker stats --no-stream

# Look for containers using > 1GB
```

**Restart containers**
```bash
docker-compose restart crypto-service
docker-compose restart telegram-service
```

**Check for memory leaks**
```bash
# Monitor over time
watch -n 5 'docker stats --no-stream'
```

---

## Network Issues

### Symptom: Can't access Web UI

**Check 1: Service running**
```bash
docker-compose ps crypto-service

# Should show "Up" status
```

**Check 2: Port accessible**
```bash
# From host machine
curl http://localhost:52000/health

# Should return health status
```

**Check 3: Firewall rules**
```bash
# Check firewall status
sudo ufw status

# Allow port if blocked
sudo ufw allow 52000/tcp
```

**Check 4: Docker network**
```bash
# List networks
docker network ls

# Inspect network
docker network inspect crypto-alert-net
```

### Symptom: Inter-service communication failing

**Check services on same network**
```bash
docker network inspect crypto-alert-net | grep Name

# Should see both services
```

**Test connectivity**
```bash
# From crypto-service to telegram-service
docker exec crypto-price-alert curl http://telegram-service:52001/health

# Should return health status
```

**Check DNS resolution**
```bash
docker exec crypto-price-alert nslookup telegram-service
```

---

## Docker Issues

### Symptom: Container keeps restarting

**Check exit code**
```bash
docker inspect crypto-price-alert --format='{{.State.ExitCode}}'

# Exit codes:
# 0: Normal exit
# 1: Application error
# 137: Out of memory (OOM killed)
# 143: SIGTERM (graceful shutdown)
```

**View last logs before crash**
```bash
docker logs --tail=100 crypto-price-alert
```

**Common causes**:
- Missing environment variables
- Invalid configuration
- Database not ready
- Port already in use

### Symptom: Build failures

**Clear build cache**
```bash
docker-compose build --no-cache
```

**Check Dockerfile syntax**
```bash
docker build -t test -f Dockerfile .
```

**Check disk space**
```bash
df -h
```

### Symptom: Volume permission issues

**Check volume ownership**
```bash
docker volume inspect crypto-postgres-data
```

**Reset volumes** (⚠️ DATA LOSS!)
```bash
make clean
```

---

## Debug Mode

### Enable debug logging

**Edit .env**:
```bash
LOG_LEVEL=DEBUG
```

**Restart services**:
```bash
make restart
```

**View debug logs**:
```bash
make logs | grep DEBUG
```

### Enable verbose Docker logging

```bash
# View all Docker events
docker events

# In another terminal
make restart
```

### Interactive debugging

**Access container shell**:
```bash
# Crypto service
make shell-crypto

# Telegram service
make shell-telegram

# PostgreSQL
make shell-postgres
```

**Run Python interactively**:
```bash
docker exec -it crypto-price-alert python3

>>> from crypto_service.database import get_db
>>> # Test code here
```

---

## Getting Help

### Before asking for help

1. **Check this guide** for your issue
2. **Check logs** for error messages
3. **Verify environment** configuration
4. **Test health endpoints**
5. **Search existing issues** on GitHub

### Information to include

When reporting an issue, include:

```markdown
**Environment**:
- OS: [e.g., Ubuntu 22.04]
- Docker version: [e.g., 20.10.21]
- Docker Compose version: [e.g., 2.12.0]

**Configuration**:
- Deployment mode: [dev/prod]
- Database: [SQLite/PostgreSQL]

**Issue Description**:
Clear description of the problem

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**:
What should happen

**Actual Behavior**:
What actually happens

**Logs**:
```
# Paste relevant logs here
# Remove sensitive information!
```

**Additional Context**:
Any other relevant information
```

### Support Channels

- **Documentation**: [Full Documentation](../README.md)
- **GitHub Issues**: [Report Bug](https://github.com/yourusername/crypto-price-alert/issues)
- **GitHub Discussions**: [Ask Question](https://github.com/yourusername/crypto-price-alert/discussions)
- **Email**: support@crypto-price-alert.com

---

## Quick Diagnostics

**Run full health check**:
```bash
#!/bin/bash
echo "=== System Health Check ==="

echo "1. Docker Status:"
systemctl is-active docker

echo "2. Container Status:"
docker-compose ps

echo "3. Port Availability:"
netstat -tulpn | grep -E "52000|52001|5432"

echo "4. Service Health:"
curl -s http://localhost:52000/health | jq '.status'

echo "5. Recent Errors:"
docker-compose logs --tail=50 | grep -i error

echo "=== Check Complete ==="
```

**Save as** `scripts/health-check.sh` and run:
```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

---

**Last Updated**: November 7, 2025
