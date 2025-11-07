# User Guide

Complete guide for using the Crypto Price Alert System.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Your Telegram Bot](#setting-up-your-telegram-bot)
3. [Finding Your Telegram Chat ID](#finding-your-telegram-chat-id)
4. [Adding Cryptocurrencies](#adding-cryptocurrencies)
5. [Creating Alerts](#creating-alerts)
6. [Managing Your Alerts](#managing-your-alerts)
7. [Understanding Alert Types](#understanding-alert-types)
8. [Advanced Alert Configuration](#advanced-alert-configuration)
9. [Monitoring Prices](#monitoring-prices)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Telegram account (for receiving alerts)
- 5 minutes for setup

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crypto-price-alert.git
cd crypto-price-alert

# Copy environment template
cp .env.example .env

# Edit .env file (instructions below)
nano .env

# Start the system
make dev  # For development mode with SQLite
# OR
make prod  # For production mode with PostgreSQL
```

### Accessing the System

Once running, you can access:

- **Web UI**: http://localhost:52000
- **API Documentation**: http://localhost:52000/docs
- **Health Status**: http://localhost:52000/health

---

## Setting Up Your Telegram Bot

To receive price alerts, you need to create a Telegram bot.

### Step 1: Create Bot with BotFather

1. **Open Telegram** on your phone or computer

2. **Search for "@BotFather"** (official Telegram bot for creating bots)

3. **Start a conversation** by clicking "Start"

4. **Create a new bot**:
   ```
   /newbot
   ```

5. **Choose a name** for your bot:
   ```
   My Crypto Alerts
   ```

6. **Choose a username** (must end with "bot"):
   ```
   my_crypto_alerts_bot
   ```

7. **Save your bot token**:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```
   ⚠️ **Keep this token secret!** Anyone with this token can control your bot.

### Step 2: Configure Bot in System

1. Open the `.env` file in your project directory:
   ```bash
   nano .env
   ```

2. Add your bot token:
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```

3. Generate authentication token:
   ```bash
   openssl rand -hex 32
   ```

4. Add the generated token to `.env`:
   ```bash
   AUTH_TOKEN=your_generated_token_here
   ```

5. Save and close the file

6. Restart the system:
   ```bash
   make restart
   ```

### Step 3: Test Your Bot

1. Find your bot on Telegram (search for the username you chose)

2. Click "Start" to activate the bot

3. Your bot is now ready to send you alerts!

---

## Finding Your Telegram Chat ID

To receive alerts, the system needs your Telegram Chat ID.

### Method 1: Using a Bot (Easiest)

1. **Open Telegram** and search for "@userinfobot"

2. **Click "Start"**

3. The bot will reply with your user information:
   ```
   Id: 123456789
   First name: John
   Username: @johndoe
   ```

4. **Copy your ID** (the number after "Id:")

5. **Use this ID** when creating alerts

### Method 2: Using Web Telegram

1. Go to https://web.telegram.org

2. Open any chat

3. Look at the URL:
   ```
   https://web.telegram.org/z/#123456789
   ```

4. Your Chat ID is the number in the URL

### Method 3: Using @RawDataBot

1. Search for "@RawDataBot" on Telegram

2. Click "Start"

3. The bot sends you raw JSON data

4. Find your ID in the response:
   ```json
   {
     "from": {
       "id": 123456789,
       ...
     }
   }
   ```

### Method 4: Using the System's API

If you send a test message to your bot:

1. Send any message to your bot on Telegram

2. Check the system logs:
   ```bash
   make logs-telegram
   ```

3. Look for a log entry containing your chat ID

---

## Adding Cryptocurrencies

Before creating alerts, you need to add cryptocurrencies to your watchlist.

### Using the Web UI

1. **Open the Web UI**: http://localhost:52000

2. **Navigate to "Cryptocurrencies"** section

3. **Click "Add Cryptocurrency"**

4. **Fill in the form**:
   - **Crypto ID**: Use the CoinGecko ID (e.g., "bitcoin", "ethereum")
   - **Symbol**: Short code (e.g., "BTC", "ETH")
   - **Name**: Full name (e.g., "Bitcoin", "Ethereum")

5. **Click "Add"**

6. The system will start monitoring the price automatically

### Finding CoinGecko IDs

To find the correct CoinGecko ID for a cryptocurrency:

1. Visit https://www.coingecko.com

2. Search for your cryptocurrency

3. Look at the URL:
   ```
   https://www.coingecko.com/en/coins/bitcoin
   ```
   The ID is "bitcoin"

**Common Crypto IDs**:
- Bitcoin: `bitcoin`
- Ethereum: `ethereum`
- Binance Coin: `binancecoin`
- Cardano: `cardano`
- Solana: `solana`
- Polkadot: `polkadot`
- Dogecoin: `dogecoin`
- Ripple: `ripple`

### Using the API

```bash
curl -X POST "http://localhost:52000/api/cryptocurrencies" \
  -H "Content-Type: application/json" \
  -d '{
    "crypto_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin"
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:52000/api/cryptocurrencies",
    json={
        "crypto_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin"
    }
)

if response.status_code == 201:
    print("✓ Bitcoin added to watchlist")
else:
    print(f"✗ Error: {response.json()['message']}")
```

---

## Creating Alerts

### Using the Web UI

1. **Open the Web UI**: http://localhost:52000

2. **Navigate to "Alerts"** section

3. **Click "Create Alert"**

4. **Fill in the alert form**:
   - **User ID**: Your identifier (e.g., "user123")
   - **Cryptocurrency**: Select from dropdown
   - **Alert Type**: Choose alert condition
   - **Threshold**: Price threshold
   - **Telegram Chat ID**: Your Telegram Chat ID
   - **Enabled**: Check to activate immediately

5. **Click "Create"**

6. Your alert is now active!

### Using the API

```bash
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
```

### Alert Creation Example

Create an alert for Bitcoin reaching $50,000:

```python
import requests

# Create alert
response = requests.post(
    "http://localhost:52000/api/alerts",
    json={
        "user_id": "john_doe",
        "crypto_id": "bitcoin",
        "alert_type": "PRICE_ABOVE",
        "threshold": 50000.00,
        "telegram_chat_id": "123456789",
        "enabled": True,
        "metadata": {
            "custom_message": "BTC reached $50k! 🚀"
        }
    }
)

alert = response.json()
print(f"Alert created: {alert['alert_id']}")
print(f"Will trigger when BTC price is above ${alert['threshold']}")
```

---

## Managing Your Alerts

### Viewing Your Alerts

**Web UI**: Navigate to the "Alerts" section

**API**:
```bash
# List all your alerts
curl "http://localhost:52000/api/alerts?user_id=john_doe"

# List only enabled alerts
curl "http://localhost:52000/api/alerts?user_id=john_doe&enabled=true"

# List alerts for specific cryptocurrency
curl "http://localhost:52000/api/alerts?crypto_id=bitcoin"
```

### Updating an Alert

**Change the threshold**:
```bash
curl -X PUT "http://localhost:52000/api/alerts/alert_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 55000.00
  }'
```

**Disable an alert**:
```bash
curl -X PUT "http://localhost:52000/api/alerts/alert_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

**Re-enable an alert**:
```bash
curl -X PUT "http://localhost:52000/api/alerts/alert_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true
  }'
```

### Deleting an Alert

**Web UI**: Click the "Delete" button next to the alert

**API**:
```bash
curl -X DELETE "http://localhost:52000/api/alerts/alert_abc123"
```

---

## Understanding Alert Types

The system supports five types of alerts:

### 1. PRICE_ABOVE

**Triggers when**: Price is continuously above the threshold

**Use case**: Know when a coin is above a certain price

**Example**: Alert me whenever BTC is above $50,000

**Behavior**:
- Triggers immediately when price goes above threshold
- Continues triggering (respecting debounce period)
- Stops triggering when price drops below threshold

**Configuration**:
```json
{
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00
}
```

### 2. PRICE_BELOW

**Triggers when**: Price is continuously below the threshold

**Use case**: Know when a coin drops below a certain price

**Example**: Alert me whenever ETH is below $2,000

**Behavior**:
- Triggers immediately when price goes below threshold
- Continues triggering (respecting debounce period)
- Stops triggering when price rises above threshold

**Configuration**:
```json
{
  "alert_type": "PRICE_BELOW",
  "threshold": 2000.00
}
```

### 3. PRICE_CROSSES_UP

**Triggers when**: Price crosses above threshold (one-time)

**Use case**: Get notified when a price breaks through a resistance level

**Example**: Alert me once when BTC crosses $45,000 upward

**Behavior**:
- Triggers **only once** when price crosses from below to above
- Does NOT trigger if price is already above threshold
- Resets when price drops below and crosses again

**Configuration**:
```json
{
  "alert_type": "PRICE_CROSSES_UP",
  "threshold": 45000.00
}
```

**Visual Example**:
```
Price Timeline:
$44,000 → $44,500 → $45,100 → $45,500 → $44,800 → $45,200
                      ↑                              ↑
                  Triggers here              Triggers here
                  (crossed up)               (crossed up again)
```

### 4. PRICE_CROSSES_DOWN

**Triggers when**: Price crosses below threshold (one-time)

**Use case**: Get notified when a price breaks through a support level

**Example**: Alert me once when ETH crosses $3,000 downward

**Behavior**:
- Triggers **only once** when price crosses from above to below
- Does NOT trigger if price is already below threshold
- Resets when price rises above and crosses again

**Configuration**:
```json
{
  "alert_type": "PRICE_CROSSES_DOWN",
  "threshold": 3000.00
}
```

### 5. PRICE_CHANGE_PERCENT

**Triggers when**: Price changes by a certain percentage

**Use case**: Know when there's significant price movement

**Example**: Alert me on 5% price change

**Configuration**:
```json
{
  "alert_type": "PRICE_CHANGE_PERCENT",
  "threshold": 0,
  "metadata": {
    "percentage": 5.0
  }
}
```

**Note**: For this alert type, use the `metadata.percentage` field instead of `threshold`.

---

## Advanced Alert Configuration

### Custom Messages

Add custom messages to your alerts:

```json
{
  "alert_type": "PRICE_ABOVE",
  "threshold": 50000.00,
  "metadata": {
    "custom_message": "🚀 Bitcoin is mooning! Time to celebrate! 🎉"
  }
}
```

### Alert Metadata

The `metadata` field allows advanced configuration:

```json
{
  "metadata": {
    "custom_message": "Your custom alert message",
    "step_value": 500,
    "percentage": 5.0,
    "notification_channels": ["telegram"],
    "priority": "high"
  }
}
```

### Multiple Alerts for Same Cryptocurrency

You can create multiple alerts for the same cryptocurrency:

**Example**: Monitor BTC at different levels
```bash
# Alert when BTC > $50k
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": 50000.00,
    "telegram_chat_id": "123456789"
  }'

# Alert when BTC > $55k
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_ABOVE",
    "threshold": 55000.00,
    "telegram_chat_id": "123456789"
  }'

# Alert when BTC < $45k
curl -X POST "http://localhost:52000/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "crypto_id": "bitcoin",
    "alert_type": "PRICE_BELOW",
    "threshold": 45000.00,
    "telegram_chat_id": "123456789"
  }'
```

### Alert Debouncing

To prevent spam, alerts have a debounce period (default: 30 seconds).

This means:
- After an alert triggers, it won't trigger again for 30 seconds
- Even if conditions are still met
- This prevents dozens of notifications during volatile periods

**Configure debounce period** in `.env`:
```bash
ALERT_DEBOUNCE_SECONDS=60  # Increase to 60 seconds
```

---

## Monitoring Prices

### Current Prices

**Web UI**: View current prices on the dashboard

**API**:
```bash
curl "http://localhost:52000/api/prices/current"
```

**Response**:
```json
{
  "prices": [
    {
      "crypto_id": "bitcoin",
      "symbol": "BTC",
      "price": 45123.45,
      "timestamp": "2025-11-07T10:30:00Z"
    }
  ],
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### Price Update Frequency

Prices are updated every 15 seconds by default.

**To change update frequency**, edit `.env`:
```bash
CRYPTO_POLL_INTERVAL_SECONDS=30  # Update every 30 seconds
```

**Note**: Lower values mean more API calls to CoinGecko. Free tier allows 30 calls/minute.

### Price Sources

The system uses **CoinGecko API** for price data:
- Reliable and comprehensive
- 30 calls/minute on free tier
- Covers 13M+ cryptocurrencies

---

## Troubleshooting

### Not Receiving Alerts

**Check 1: Verify Bot Token**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```
Should return bot information. If not, your token is invalid.

**Check 2: Verify Chat ID**
- Send a message to your bot
- Check system logs:
  ```bash
  make logs-telegram
  ```
- Look for your chat ID in the logs

**Check 3: Check Alert is Enabled**
```bash
curl "http://localhost:52000/api/alerts?user_id=your_user_id&enabled=true"
```

**Check 4: Verify Service Health**
```bash
curl "http://localhost:52000/health"
```

**Check 5: Check Telegram Service Logs**
```bash
make logs-telegram
```

### Alert Not Triggering

**Issue**: Alert conditions are met but no notification

**Solutions**:

1. **Check debounce period**: Alert may have triggered recently
   ```bash
   # Check last_triggered_at timestamp
   curl "http://localhost:52000/api/alerts/your_alert_id"
   ```

2. **Check alert type**: Ensure you're using the correct alert type
   - `PRICE_ABOVE`: Triggers while price is above
   - `PRICE_CROSSES_UP`: Triggers once when crossing up

3. **Check price data**: Verify price is updating
   ```bash
   curl "http://localhost:52000/api/prices/current"
   ```

4. **Check logs**:
   ```bash
   make logs-crypto
   ```

### System Not Starting

**Issue**: Docker containers won't start

**Solutions**:

1. **Check Docker is running**:
   ```bash
   sudo systemctl status docker
   ```

2. **Check ports are available**:
   ```bash
   sudo netstat -tulpn | grep 52000
   ```

3. **Validate environment file**:
   ```bash
   make validate-env
   ```

4. **Check logs for errors**:
   ```bash
   make logs
   ```

### Price Not Updating

**Issue**: Prices are stale or not updating

**Possible causes**:

1. **CoinGecko API rate limit**: Check logs for "429" errors
2. **Network connectivity**: Check internet connection
3. **Invalid crypto_id**: Verify cryptocurrency ID is correct

**Check service logs**:
```bash
make logs-crypto | grep "price_collector"
```

---

## FAQ

### Q: How many alerts can I create?

**A**: There's no hard limit, but we recommend:
- **Free tier**: Up to 25 cryptocurrencies, 100 alerts
- **Each cryptocurrency**: Creates API calls every 15 seconds
- **CoinGecko free tier**: Allows 30 calls/minute

### Q: Can I use multiple Telegram accounts?

**A**: Yes! Simply use different `telegram_chat_id` values for each user's alerts.

### Q: How accurate are the prices?

**A**: Prices are fetched from CoinGecko:
- **Free tier**: Updates cached at 1-5 minute intervals
- **Pro tier**: Updates cached at 30-second intervals
- The system polls every 15 seconds by default

### Q: Can I create alerts for any cryptocurrency?

**A**: Yes, as long as it's listed on CoinGecko (13M+ cryptocurrencies supported).

### Q: What happens if the system restarts?

**A**: All alerts and cryptocurrency data are saved in the database. They will resume automatically when the system restarts.

### Q: Can I export my alerts?

**A**: Yes, use the API:
```bash
curl "http://localhost:52000/api/alerts?user_id=your_user_id" > my_alerts.json
```

### Q: Can I change the Telegram bot after setup?

**A**: Yes:
1. Update `TELEGRAM_BOT_TOKEN` in `.env`
2. Restart the system: `make restart`
3. Update your alerts with new chat IDs if needed

### Q: How do I get price history?

**A**: Price history is planned for future versions. Currently, only current prices are available.

### Q: Can I use email notifications?

**A**: Email notifications are planned for version 0.2.0. Currently, only Telegram is supported.

### Q: Is there a mobile app?

**A**: A mobile app is planned for version 0.2.0. Currently, use the web UI or Telegram for alerts.

### Q: Can I backup my data?

**A**: Yes:
```bash
make db-backup
```
This creates a backup in the `backups/` directory.

### Q: What's the minimum system requirements?

**A**:
- CPU: 2 cores
- RAM: 2 GB
- Disk: 10 GB
- Docker 20.10+

### Q: Can I run this on a Raspberry Pi?

**A**: Yes! The system is lightweight and runs well on Raspberry Pi 3B+ or newer.

---

## Support

Need help? Contact us:

- **Documentation**: [Full Documentation](https://docs.crypto-price-alert.com)
- **Troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/crypto-price-alert/issues)
- **Email**: support@crypto-price-alert.com

---

**Last Updated**: November 7, 2025
