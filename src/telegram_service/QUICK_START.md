# Telegram Alert Service - Quick Start

## 5-Minute Setup

### 1. Get Telegram Bot Token (2 minutes)

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose a name and username
4. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Setup Environment (1 minute)

```bash
cd /home/user/crypto-price-alert/src/telegram_service
cp .env.example .env
```

Edit `.env`:
```bash
TELEGRAM_BOT_TOKEN=<paste-your-token>
AUTH_TOKEN=$(openssl rand -hex 32)
```

### 3. Install & Run (2 minutes)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
python -m uvicorn main:app --reload
```

Service now running at: `http://localhost:52001`

## Test It

### 1. Health Check
```bash
curl http://localhost:52001/health
```

Expected: `{"status":"healthy",...}`

### 2. Get Your Chat ID

1. Start conversation with your bot on Telegram
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find: `"chat":{"id":123456789}`

### 3. Send Test Message

```bash
export AUTH_TOKEN="your-token-from-env"
export CHAT_ID="your-chat-id"

curl -X POST http://localhost:52001/api/v1/alerts/send \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"message\": \"Hello from Telegram Alert Service!\",
    \"parse_mode\": \"HTML\"
  }"
```

You should receive the message on Telegram!

## Docker Quick Start

```bash
# Build
docker build -t telegram-alert-service .

# Run
docker run -d \
  --name telegram-alert-service \
  -p 52001:52001 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e AUTH_TOKEN=your_auth_token \
  telegram-alert-service

# Check logs
docker logs -f telegram-alert-service

# Test
curl http://localhost:52001/health
```

## Integration Example

In your main service:

```python
import httpx
import os

TELEGRAM_SERVICE_URL = "http://localhost:52001"
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

async def send_alert(chat_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_SERVICE_URL}/api/v1/alerts/send",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={
                "chat_id": chat_id,
                "message": message,
                "parse_mode": "HTML",
                "priority": "high"
            }
        )
        return response.json()

# Usage
await send_alert("123456789", "🚨 BTC Alert: Price hit $45,000!")
```

## Common Commands

```bash
# Start service
python -m uvicorn main:app --reload

# Start on different port
python -m uvicorn main:app --port 8000

# Production mode
python -m uvicorn main:app --host 0.0.0.0 --port 52001

# Run tests
python test_api.py

# View logs (JSON format)
# Logs appear in terminal

# Check metrics
curl http://localhost:52001/metrics
```

## Troubleshooting

**Service won't start?**
- Check virtual environment: `source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`

**Token validation fails?**
- Verify token format (no spaces)
- Test: `curl https://api.telegram.org/bot<TOKEN>/getMe`

**Message not received?**
- Check chat_id is correct
- Start conversation with bot first
- Check logs for errors

**401 Unauthorized?**
- Verify AUTH_TOKEN matches in request
- Check Authorization header format: `Bearer <token>`

## Next Steps

1. ✅ Service running
2. ✅ Test message sent
3. 📖 Read full README.md
4. 🔧 Configure for production
5. 🚀 Deploy with Docker Compose

## Documentation

- **README.md** - Full documentation
- **SETUP.md** - Detailed setup guide
- **IMPLEMENTATION_NOTES.md** - Technical details

## Support

Health check: `curl http://localhost:52001/health`
Metrics: `curl http://localhost:52001/metrics`
Logs: Check terminal output (JSON format)
