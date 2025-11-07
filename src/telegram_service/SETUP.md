# Telegram Alert Service - Setup Guide

This guide will help you set up and run the Telegram Alert Service.

## Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python3 --version
   ```

2. **Telegram Bot Token**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` command
   - Follow instructions to create your bot
   - Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

3. **Get Your Chat ID** (for testing)
   - Start a conversation with your bot
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789}` in the JSON response

## Step-by-Step Setup

### 1. Navigate to Service Directory

```bash
cd /home/user/crypto-price-alert/src/telegram_service
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Required settings in `.env`:**

```bash
# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Generate a secure auth token
# Run: openssl rand -hex 32
AUTH_TOKEN=your_64_character_hex_token_here
```

**Generate auth token:**
```bash
openssl rand -hex 32
```

### 5. Verify Configuration

```bash
# Check environment variables
cat .env

# Make sure TELEGRAM_BOT_TOKEN and AUTH_TOKEN are set
```

### 6. Run the Service

```bash
# Development mode (with auto-reload)
python -m uvicorn main:app --reload --port 52001

# Production mode
python -m uvicorn main:app --host 0.0.0.0 --port 52001
```

### 7. Verify Service is Running

Open a new terminal and test:

```bash
# Test health check
curl http://localhost:52001/health

# Expected response: {"status":"healthy", ...}
```

## Testing the Service

### Option 1: Use the Test Script

```bash
# Set test chat ID in .env
echo "TEST_CHAT_ID=your_telegram_chat_id" >> .env

# Run the test script
python test_api.py
```

### Option 2: Manual cURL Test

```bash
# Health check
curl http://localhost:52001/health

# Send a test message
curl -X POST http://localhost:52001/api/v1/alerts/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{
    "chat_id": "YOUR_CHAT_ID",
    "message": "Test message from Telegram Alert Service!",
    "parse_mode": "HTML"
  }'
```

### Option 3: Use Python

```python
import httpx

async def test_send():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:52001/api/v1/alerts/send",
            headers={
                "Authorization": "Bearer YOUR_AUTH_TOKEN",
                "Content-Type": "application/json"
            },
            json={
                "chat_id": "YOUR_CHAT_ID",
                "message": "Hello from Python!",
                "parse_mode": "HTML"
            }
        )
        print(response.json())

import asyncio
asyncio.run(test_send())
```

## Docker Setup

### Build Docker Image

```bash
docker build -t telegram-alert-service:latest .
```

### Run Docker Container

```bash
docker run -d \
  --name telegram-alert-service \
  -p 52001:52001 \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -e AUTH_TOKEN=your_auth_token_here \
  telegram-alert-service:latest
```

### View Logs

```bash
docker logs -f telegram-alert-service
```

### Stop Container

```bash
docker stop telegram-alert-service
docker rm telegram-alert-service
```

## Monitoring

### Health Check

```bash
curl http://localhost:52001/health | jq
```

### Prometheus Metrics

```bash
curl http://localhost:52001/metrics
```

### View Logs

The service outputs structured JSON logs:

```bash
# If running directly
# Logs appear in terminal

# If running with Docker
docker logs -f telegram-alert-service
```

## Troubleshooting

### Issue: "Failed to validate Telegram bot token"

**Solution:**
1. Check token format is correct (no extra spaces)
2. Verify token with BotFather
3. Check internet connectivity
4. Try: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### Issue: "Missing authorization header"

**Solution:**
1. Ensure you're including the header: `Authorization: Bearer <token>`
2. Verify AUTH_TOKEN in .env matches the one you're using
3. Check for typos in the token

### Issue: "Bad Request: chat not found"

**Solution:**
1. Verify chat_id is correct
2. Start a conversation with your bot first
3. Send a message to the bot before trying to send alerts

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 52001
lsof -i :52001

# Kill the process
kill -9 <PID>

# Or use a different port
python -m uvicorn main:app --port 52002
```

### Issue: Module not found

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram Bot API token |
| `AUTH_TOKEN` | Yes | - | Bearer authentication token |
| `APP_ENV` | No | `development` | Environment name |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `SERVICE_PORT` | No | `52001` | HTTP port |
| `RATE_LIMIT_MESSAGES_PER_SECOND` | No | `25.0` | Rate limit |
| `RATE_LIMIT_BURST_SIZE` | No | `50` | Burst capacity |
| `QUEUE_MAX_SIZE` | No | `1000` | Max queue size |
| `TELEGRAM_RETRY_ATTEMPTS` | No | `3` | Max retries |
| `TELEGRAM_API_TIMEOUT_SECONDS` | No | `30` | API timeout |

## Production Deployment

For production deployment:

1. **Use strong auth tokens**
   ```bash
   openssl rand -hex 32
   ```

2. **Set environment to production**
   ```bash
   APP_ENV=production
   LOG_LEVEL=INFO
   ```

3. **Use Docker**
   - Better isolation
   - Resource limits
   - Health checks
   - Easy updates

4. **Set up monitoring**
   - Prometheus for metrics
   - Grafana for dashboards
   - Alert manager for alerts

5. **Enable HTTPS** (if exposing publicly)
   - Use reverse proxy (nginx, Caddy)
   - SSL certificates (Let's Encrypt)

## Next Steps

1. ✅ Service is running
2. ✅ Health check passes
3. ✅ Test message sent successfully
4. 🔄 Integrate with crypto-price-alert service
5. 🔄 Set up monitoring
6. 🔄 Deploy to production

## Support

For issues:
1. Check logs for detailed error messages
2. Verify all environment variables are set
3. Test with `/health` endpoint
4. Review this troubleshooting section
5. Check main README.md for more details

## Quick Commands

```bash
# Start service
python -m uvicorn main:app --reload

# Test health
curl http://localhost:52001/health

# View metrics
curl http://localhost:52001/metrics

# Run tests
python test_api.py

# Build Docker image
docker build -t telegram-alert-service .

# Run Docker container
docker run -p 52001:52001 --env-file .env telegram-alert-service
```
