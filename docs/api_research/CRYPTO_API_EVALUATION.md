# Cryptocurrency Data API Evaluation Report

**Research Date:** November 7, 2025
**Prepared By:** Research Lead - Cryptocurrency Data API Evaluation
**Purpose:** Comprehensive evaluation of cryptocurrency data APIs for real-time price alerts

---

## Executive Summary

After extensive research of four major cryptocurrency data APIs, **CoinGecko API** emerges as the recommended solution for the crypto price alert system, with **Binance WebSocket API** as a strong alternative for US-based deployments.

**Key Findings:**

- **CoinGecko API** offers the best balance of features for the free tier with 30 calls/minute, comprehensive coverage of 13M+ tokens, and commercial use permission with simple attribution requirements
- **Binance API** provides excellent real-time WebSocket capabilities but has significant US regional restrictions blocking US IP addresses
- **Coinbase Advanced Trade API** offers generous rate limits (30 req/sec) but limited cryptocurrency coverage (~550 markets)
- **CryptoCompare API** has vague free tier limits and requires paid plans ($80-200/month) for reliable commercial use

**Primary Recommendation:** Start with CoinGecko API (free Demo tier) for development and initial deployment, with the option to upgrade to paid tiers as usage scales.

---

## Detailed Comparison Table

| Feature | CoinGecko API | Binance API | Coinbase Advanced Trade | CryptoCompare API |
|---------|---------------|-------------|------------------------|-------------------|
| **Free Tier Available** | ✅ Yes (Demo) | ✅ Yes | ✅ Yes | ⚠️ Limited |
| **Rate Limit (Free)** | 30 calls/min | 6000 weight/min (REST)<br>5 msg/sec (WS) | Public: 10 req/sec<br>Private: 30 req/sec | ~7,500 calls/day<br>(~5 calls/min avg) |
| **Monthly Quota** | 10,000 calls | No explicit limit | No explicit limit | ~50,000 calls |
| **Commercial Use** | ✅ Allowed (with attribution) | ✅ Allowed | ✅ Allowed | ⚠️ Paid plans preferred |
| **Regional Restrictions** | None | ❌ Blocks US IPs<br>(use Binance.US) | None | None |
| **Data Coverage** | 13M+ tokens<br>240+ networks<br>1,600+ exchanges | 439 coins<br>1,606 trading pairs | 550+ markets | 7,287 assets<br>316+ exchanges<br>338K+ pairs |
| **Data Latency** | 10-30 sec cache<br>(improved 2025) | Real-time | Real-time (ticker)<br>5 sec (ticker_batch) | Real-time capable |
| **WebSocket Support** | ✅ Yes (paid tiers) | ✅ Yes (free) | ✅ Yes (free) | ✅ Yes |
| **Authentication Required** | Optional (recommended) | Optional for market data | Optional for market data | Yes (API key) |
| **Pricing (Paid Tiers)** | Starts at paid plans | Free | Free | $80-200/month |
| **Response Format** | JSON | JSON | JSON | JSON |
| **Historical Data** | Full history available | Available | Available | 7 days minute-level |
| **Ban Risk** | Low (clear limits) | High (auto-ban on 429) | Low | Medium |

---

## Detailed API Analysis

### 1. CoinGecko API

**Official Documentation:** https://docs.coingecko.com/
**Pricing Page:** https://www.coingecko.com/en/api/pricing
**API Terms:** https://www.coingecko.com/en/api_terms

#### Rate Limits

**Public API (No API Key):**
- Rate Limit: 5-15 calls per minute (varies by global traffic)
- Source: https://support.coingecko.com/hc/en-us/articles/4538771776153

**Demo Plan (Free with Registration):**
- Rate Limit: ~30 calls per minute (stable)
- Monthly Quota: 10,000 calls
- Source: https://docs.coingecko.com/reference/common-errors-rate-limit

**Paid Plans:**
- Analyst: 500 calls/minute
- Pro: 1,000 calls/minute
- Enterprise: Custom limits

#### Data Freshness & Latency

**2025 Improvements:**
- January 2025: Cache reduced to 20-30 seconds
- March 2025: Cache reduced to 30 seconds (from 60s)
- September 2025: Cache reduced to 10 seconds

**Current Status:**
- Free tier: Updates cached at 1-5 minute intervals
- Pro tier: Updates cached at 30-second intervals
- WebSocket API: Low-latency streaming (paid plans)

Source: https://docs.coingecko.com/changelog/update-frequency-improvements-for-selected-pro-api-endpoints-march-2025

#### Data Coverage

- **Tokens:** 13+ million tokens tracked
- **Networks:** 240+ blockchain networks
- **Exchanges:** 1,600+ exchanges (900+ DEXes, 120 blockchain networks)
- **On-chain DEX Data:** 20+ million coins/tokens
- **Endpoints:** 70+ API endpoints

Source: https://www.coingecko.com/en/api

#### Terms of Service & Commercial Use

**✅ Commercial Use Allowed:**
- You CAN use free API for commercial websites and applications
- You CAN charge for services that incorporate CoinGecko data
- **REQUIRED:** Attribution with "Powered by CoinGecko API" link

**❌ Restrictions:**
- You CANNOT sell, rent, lease, or redistribute API access
- You CANNOT sublicense the API to others

**License Type:** Limited, non-exclusive, non-assignable, non-transferable

Source: https://www.coingecko.com/en/api_terms

#### Code Examples

**Simple Price Endpoint:**
```python
import requests

# Get Bitcoin price in USD
response = requests.get(
    'https://api.coingecko.com/api/v3/simple/price',
    params={
        'ids': 'bitcoin',
        'vs_currencies': 'usd'
    }
)

if response.status_code == 200:
    data = response.json()
    bitcoin_price = data['bitcoin']['usd']
    print(f'Bitcoin: ${bitcoin_price}')
```

**OHLC Data Example:**
```python
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
ohlc = cg.get_coin_ohlc_by_id(
    id="ethereum",
    vs_currency="usd",
    days="30"
)
print(ohlc)
```

**JavaScript Example:**
```javascript
fetch('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30')
  .then(response => response.json())
  .then(data => console.log(data));
```

Source: https://www.coingecko.com/learn/python-query-coingecko-api

#### Key Endpoints

- `/simple/price` - Get current prices
- `/coins/markets` - Get market data
- `/coins/{id}/market_chart` - Historical market chart
- `/coins/{id}/history` - Historical data by date
- `/coins/{id}/ohlc` - OHLC data

#### Pros & Cons

**Advantages:**
- ✅ Most comprehensive token coverage (13M+ tokens)
- ✅ Free tier suitable for commercial use
- ✅ No regional restrictions
- ✅ Clear, stable rate limits
- ✅ Continuous improvements in 2025 (lower latency)
- ✅ Excellent documentation
- ✅ Simple attribution requirement

**Disadvantages:**
- ❌ 30 calls/min may be limiting for high-frequency polling
- ❌ Data cached (10-30 sec delay on free tier)
- ❌ WebSocket requires paid plan
- ❌ Rate limit varies on public (no-key) plan

---

### 2. Binance Public API

**Official Documentation:** https://developers.binance.com/docs/binance-spot-api-docs
**GitHub Repository:** https://github.com/binance/binance-spot-api-docs
**REST API Docs:** https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
**WebSocket Docs:** https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-api.md

#### Rate Limits

**REST API:**
- **Request Weight System:** 6,000 weight per minute per IP
- **Order Limits:** 50 orders per 10 seconds, 160,000 per day
- **Rate Limit Headers:** `X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter)`
- **Violation Response:** HTTP 429 → HTTP 418 (auto-ban)
- **Ban Duration:** 2 minutes to 3 days (escalating)

**WebSocket API:**
- **Connection Cost:** 2 weight per connection
- **Connection Limit:** 300 connections per 5 minutes per IP
- **Message Rate:** 5-10 messages per second (depending on endpoint)
- **Stream Limit:** Maximum 1,024 streams per connection
- **Connection Duration:** 24 hours maximum (auto-disconnect)
- **Ping/Pong:** Server pings every 20 seconds, must respond within 60 seconds

**WebSocket Streams:**
- **Message Rate:** 5 incoming messages per second
- **Disconnection:** Automatic on limit violation
- **IP Ban:** Repeated violations result in IP bans

Sources:
- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits
- https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-api.md

#### Regional Restrictions

**⚠️ CRITICAL: US IP Address Blocking**

- **Global Binance API:** Blocks requests from US IP addresses
- **Error:** "Service unavailable from a restricted location according to 'b. Eligibility'"
- **US Alternative:** Must use Binance.US (separate API)
- **Binance.US Coverage:** 153 trading pairs (vs 1,606 on global)
- **Deployment Impact:** Cannot deploy on US-based cloud servers without proxy

**Binance.US State Restrictions:**
- ❌ Restricted: New York, Texas, Washington
- ⚠️ Limited: Michigan (paused registrations), Kansas, Wisconsin (crypto only, no USD)

Sources:
- https://support.binance.us/hc/en-us/articles/360046786914
- https://www.datawallet.com/crypto/binance-restricted-countries

#### Data Coverage

- **Cryptocurrencies:** 439 coins
- **Trading Pairs:** 1,606 pairs
- **Real-time Data:** Yes (millisecond precision)
- **Endpoint:** `/api/v3/exchangeInfo` for full pair list

Source: https://www.coingecko.com/en/exchanges/binance

#### Data Freshness

- **Latency:** Real-time (millisecond precision)
- **WebSocket Updates:** Immediate on trade execution
- **REST API:** Current orderbook and ticker data
- **Best For:** High-frequency trading, real-time alerts

#### Authentication & Security

**Optional for Market Data:**
- Public endpoints require no authentication
- Market data available without API key

**Signed Requests (for trading):**
- Supported Methods: HMAC-SHA256, RSA-SHA256, Ed25519
- Required Headers: `X-MBX-APIKEY`
- Parameters: `timestamp`, optional `recvWindow` (max 60000ms)

#### Base Endpoints

- **Primary:** `https://api.binance.com`
- **Market Data Only:** `https://data-api.binance.vision` (no auth needed)
- **GCP Region:** `https://api-gcp.binance.com`
- **Performance:** `https://api1.binance.com` through `https://api4.binance.com`

#### Code Examples

**WebSocket - Real-time Price Stream (Node.js):**
```javascript
const WebSocket = require('ws');

// Connect to Bitcoin/USDT trade stream
const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@trade');

ws.on('message', function incoming(data) {
    const trade = JSON.parse(data);
    console.log(`Price: ${trade.p}, Quantity: ${trade.q}, Time: ${trade.T}`);
});

ws.on('error', function error(err) {
    console.error('WebSocket error:', err);
});
```

**WebSocket - Price Ticker Stream:**
```javascript
const WebSocket = require('ws');

// Mini ticker for last price
const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@miniTicker');

ws.on('message', function incoming(data) {
    const ticker = JSON.parse(data);
    console.log(`Symbol: ${ticker.s}, Last Price: ${ticker.c}, 24h Change: ${ticker.P}%`);
});
```

**REST API - Get Current Price:**
```python
import requests

# Get Bitcoin price
response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
data = response.json()
print(f"Bitcoin: ${data['price']}")
```

**Python - WebSocket Stream:**
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Price: {data['p']}")

def on_error(ws, error):
    print(f"Error: {error}")

ws = websocket.WebSocketApp(
    "wss://stream.binance.com:9443/ws/btcusdt@trade",
    on_message=on_message,
    on_error=on_error
)
ws.run_forever()
```

Source: https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md

#### Key Endpoints

**REST API:**
- `/api/v3/ticker/price` - Current price(s)
- `/api/v3/ticker/24hr` - 24-hour price statistics
- `/api/v3/depth` - Order book
- `/api/v3/exchangeInfo` - Exchange trading rules and symbols

**WebSocket Streams:**
- `wss://stream.binance.com:9443/ws/<symbol>@trade` - Trade streams
- `wss://stream.binance.com:9443/ws/<symbol>@miniTicker` - Mini ticker
- `wss://stream.binance.com:9443/ws/<symbol>@ticker` - Full ticker
- `wss://data-stream.binance.vision` - Market data only (no auth)

#### Pros & Cons

**Advantages:**
- ✅ True real-time data (millisecond precision)
- ✅ Excellent WebSocket support (free)
- ✅ High rate limits (6,000 weight/minute)
- ✅ No authentication required for market data
- ✅ Well-documented API
- ✅ Free to use
- ✅ Multiple base endpoints for redundancy

**Disadvantages:**
- ❌ **CRITICAL:** Blocks US IP addresses (global API)
- ❌ US users must use Binance.US (limited pairs)
- ❌ Aggressive IP banning on rate limit violations
- ❌ WebSocket connections limited to 24 hours
- ❌ Lower cryptocurrency coverage vs CoinGecko (439 vs 13M+ tokens)
- ❌ Complex rate limiting system (weight-based)
- ❌ Requires active connection management (ping/pong)

---

### 3. Coinbase Advanced Trade API

**Official Documentation:** https://docs.cdp.coinbase.com/advanced-trade/docs/welcome
**Developer Platform:** https://www.coinbase.com/developer-platform/products/advanced-trade-api
**Rate Limits:** https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api-rate-limits
**WebSocket Docs:** https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-overview

#### Rate Limits

**REST API:**
- **Public Endpoints:** 10 requests per second per IP
- **Private Endpoints:** 30 requests per second per user
- **Throttling Method:** Lazy-fill token bucket implementation
- **Rate Limit Headers:**
  - `CB-RATELIMIT-LIMIT` - Total request limit for window
  - `CB-RATELIMIT-REMAINING` - Requests remaining in window

**WebSocket API:**
- **Connection Rate:** 750 requests per second per IP
- **Authentication:** Optional (recommended for reliability)
- **WebSocket URL:** `wss://advanced-trade-ws.coinbase.com`

**Historical Rate Limit Increases (2025):**
- Initially: 10 req/sec
- Updated: 20 req/sec
- Current: 30 req/sec (private endpoints)

Sources:
- https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api-rate-limits
- https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-rate-limits

#### Data Coverage

- **Markets:** 550+ trading markets
- **USDC Pairs:** 237 new USDC pairs
- **Order Books:** Real-time across 552 markets
- **Free Trading:** 22 stable pairs (no fees)

**Note:** These are trading pairs/markets, not unique cryptocurrencies. Actual unique cryptocurrency count is lower.

Source: https://www.coinbase.com/advanced-trade

#### Data Freshness & Latency

**WebSocket Channels:**
- **ticker:** Real-time price updates on every match
- **ticker_batch:** Price updates every 5 seconds
- **market_trades:** Real-time trade data
- **level2:** Order book updates

**Update Frequency:**
- **ticker channel:** Immediate (on every trade match)
- **ticker_batch channel:** 5-second intervals

Source: https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels

#### Authentication

**Market Data (Public):**
- No authentication required for public channels
- Can connect without API key

**Recommended:**
- Use CDP API key for most reliable connection
- Authentication provides better stability

**User-specific Data:**
- Requires authentication with CDP API key
- Access to private trading data

#### Regional Restrictions

- **US Access:** ✅ Available
- **Global Access:** ✅ Available (varies by region)
- **No IP Blocking:** Unlike Binance, no US IP restrictions

#### Code Examples

**JavaScript - WebSocket Ticker Stream:**
```javascript
const WebSocket = require('ws');

const ws = new WebSocket('wss://advanced-trade-ws.coinbase.com');

ws.on('open', function open() {
    // Subscribe to Bitcoin ticker
    ws.send(JSON.stringify({
        type: 'subscribe',
        product_ids: ['BTC-USD'],
        channels: ['ticker']
    }));
});

ws.on('message', function incoming(data) {
    const message = JSON.parse(data);
    if (message.type === 'ticker') {
        console.log(`${message.product_id}: $${message.price}`);
    }
});
```

**JavaScript - Ticker Batch (5-second updates):**
```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    product_ids: ['BTC-USD', 'ETH-USD'],
    channels: ['ticker_batch']
}));
```

**Python - REST API Current Price:**
```python
import requests

# Get current Bitcoin price
response = requests.get(
    'https://api.coinbase.com/v2/prices/BTC-USD/spot'
)
data = response.json()
print(f"Bitcoin: ${data['data']['amount']}")
```

**Python SDK Example:**
```python
from coinbase.advanced_trade import AdvancedTradeAPI

# Initialize client
client = AdvancedTradeAPI(api_key='your_key', api_secret='your_secret')

# Get product ticker
ticker = client.get_product_ticker('BTC-USD')
print(f"Price: ${ticker['price']}")
```

Source: https://github.com/coinbase/coinbase-advanced-py

#### Key Endpoints

**REST API:**
- `/api/v3/brokerage/products` - List all products
- `/api/v3/brokerage/products/{product_id}` - Get product details
- `/api/v3/brokerage/products/{product_id}/ticker` - Get product ticker
- `/api/v3/brokerage/products/{product_id}/candles` - Historical candles

**WebSocket Channels:**
- `ticker` - Real-time price updates (every match)
- `ticker_batch` - Batched price updates (5 seconds)
- `level2` - Order book updates
- `market_trades` - Trade data
- `user` - User-specific data (requires auth)

#### Pros & Cons

**Advantages:**
- ✅ High rate limits (30 req/sec for private, 10 req/sec public)
- ✅ Very high WebSocket rate limit (750 req/sec)
- ✅ Real-time data via WebSocket
- ✅ No authentication required for market data
- ✅ No regional restrictions (available in US)
- ✅ Free to use
- ✅ Clear rate limit headers
- ✅ Ticker_batch option for lower-frequency updates
- ✅ Official Python SDK available

**Disadvantages:**
- ❌ Limited cryptocurrency coverage (~550 markets vs thousands)
- ❌ Primarily focused on major cryptocurrencies
- ❌ Less comprehensive than CoinGecko for altcoins
- ❌ Documentation less extensive than Binance

---

### 4. CryptoCompare API

**Official Documentation:** https://min-api.cryptocompare.com/documentation
**Pricing Page:** https://min-api.cryptocompare.com/pricing
**Developer Portal:** https://developers.cryptocompare.com/
**GitHub Guides:** https://github.com/CryptoCompareLTD/api-guides

#### Rate Limits

**Free Tier (Approximate):**
- **Per Second:** ~20 calls
- **Per Minute:** ~300 calls
- **Per Hour:** ~3,000 calls
- **Per Day:** ~7,500 calls
- **Per Month:** ~50,000 calls

**Note:** Free tier limits are not explicitly published. User reports indicate "a few thousand calls per day" for non-commercial use.

**Paid Tiers:**
- **Basic:** ~$80/month - ~100,000 calls/month
- **Advanced:** ~$200/month - Higher call volumes
- **Enterprise:** Custom pricing - Unlimited usage

**Rate Limit Tracking:**
- Multiple time windows: second, minute, hour, day, month
- API key dashboard shows usage across all windows
- Cumulative across all time periods

Sources:
- https://github.com/CryptoCompareLTD/api-guides
- https://medium.com/coinmonks/top-5-cryptocurrency-data-apis-comprehensive-comparison-2025-626450b7ff7b

#### Data Coverage

**Market Coverage:**
- **Assets:** 7,287 cryptocurrencies
- **Exchanges:** 316+ exchanges (centralized and some decentralized)
- **Trading Pairs:** 338,335 pairs
- **CCCAGG Index:** Aggregate pricing from 170+ exchanges

**Infrastructure:**
- **Processing Capacity:** 40,000 calls/second, 8,000 trades/second
- **Institutional Grade:** Enterprise-level reliability

Sources:
- https://www.cryptocompare.com/press-release/cryptocompare-adds-commercial-api/
- https://medium.com/coinmonks/top-5-cryptocurrency-data-apis-comprehensive-comparison-2025-626450b7ff7b

#### Data Freshness & Features

**Real-time Capabilities:**
- Real-time price quotes
- Order book snapshots
- Trade history
- OHLCV candlesticks at various intervals
- Low-latency delivery (institutional-grade infrastructure)

**Historical Data:**
- **All Plans:** 7 days of minute-level history + full daily history
- **Enterprise:** Up to 1 year of minute-by-minute data
- **Raw Trade Data:** Available for enterprise clients

**Data Quality:**
- Focus on low-latency delivery
- Robust infrastructure for minimal downtime
- Aggregate indices from multiple exchanges (CCCAGG)

#### Terms of Service & Commercial Use

**Free Tier:**
- Personal/non-commercial use
- API key required
- Limited calls per day (~7,500)

**Commercial Use:**
- Paid plans required for commercial applications
- Plans start at $80/month
- Custom enterprise solutions available

**Features by Tier:**
- **Free:** Basic endpoints, limited requests
- **Paid:** 60+ endpoints, higher rate limits, better data resolution
- **Enterprise:** White-label solutions, unlimited usage, custom data feeds

Source: https://min-api.cryptocompare.com/pricing

#### Code Examples

**Basic Price Request:**
```python
import requests

# Get current price
api_key = 'your_api_key'
headers = {'authorization': f'Apikey {api_key}'}

response = requests.get(
    'https://min-api.cryptocompare.com/data/price',
    headers=headers,
    params={
        'fsym': 'BTC',
        'tsyms': 'USD'
    }
)

data = response.json()
print(f"Bitcoin: ${data['USD']}")
```

**Multiple Currency Prices:**
```python
# Get prices for multiple symbols
response = requests.get(
    'https://min-api.cryptocompare.com/data/pricemulti',
    headers=headers,
    params={
        'fsyms': 'BTC,ETH,XRP',
        'tsyms': 'USD,EUR'
    }
)

data = response.json()
for symbol, prices in data.items():
    print(f"{symbol}: ${prices['USD']}")
```

**Historical OHLCV Data:**
```python
# Get daily OHLCV data
response = requests.get(
    'https://min-api.cryptocompare.com/data/v2/histoday',
    headers=headers,
    params={
        'fsym': 'BTC',
        'tsym': 'USD',
        'limit': 30
    }
)

data = response.json()
for day in data['Data']['Data']:
    print(f"Date: {day['time']}, Close: ${day['close']}")
```

**Check Rate Limit Usage:**
```python
# Monitor your API usage
response = requests.get(
    'https://min-api.cryptocompare.com/stats/rate/limit',
    headers=headers
)

usage = response.json()
print(f"Calls this minute: {usage['minute']['calls_made']['Price']}")
print(f"Calls remaining: {usage['minute']['calls_left']['Price']}")
```

Source: https://www.cryptocompare.com/coins/guides/how-to-use-our-api/

#### Key Endpoints

**Price Data:**
- `/data/price` - Single symbol price
- `/data/pricemulti` - Multiple symbol prices
- `/data/pricemultifull` - Full price data with metadata
- `/data/generateAvg` - Custom average from exchanges

**Historical Data:**
- `/data/v2/histoday` - Daily OHLCV
- `/data/v2/histohour` - Hourly OHLCV
- `/data/v2/histominute` - Minute OHLCV

**Market Data:**
- `/data/top/exchanges` - Top exchanges by volume
- `/data/top/volumes` - Top cryptocurrencies by volume
- `/data/orderbook/l1/top` - Level 1 order book

**Rate Limiting:**
- `/stats/rate/limit` - Check current usage

#### Pros & Cons

**Advantages:**
- ✅ Extensive cryptocurrency coverage (7,287 assets)
- ✅ Comprehensive exchange data (316+ exchanges)
- ✅ Large trading pair coverage (338,335 pairs)
- ✅ Institutional-grade infrastructure
- ✅ High processing capacity (40,000 calls/sec capability)
- ✅ Aggregate pricing indices (CCCAGG)
- ✅ Historical data included (7 days minute-level)
- ✅ Multiple time-window rate limiting
- ✅ WebSocket support available
- ✅ No regional restrictions

**Disadvantages:**
- ❌ Vague free tier limits (not explicitly published)
- ❌ Low daily limit on free tier (~7,500 calls/day = ~5 calls/min)
- ❌ Commercial use requires paid plans ($80-200/month)
- ❌ API key required for all requests
- ❌ Rate limiting across multiple time windows (complex)
- ❌ More expensive than competitors for paid tiers
- ❌ Free tier described as suitable only for "prototypes"

---

## Data Freshness Comparison

### Update Frequency Summary

| API | Free Tier Latency | Paid Tier Latency | Real-time Capability |
|-----|-------------------|-------------------|---------------------|
| **CoinGecko** | 1-5 min cache | 10-30 sec cache | WebSocket (paid) |
| **Binance** | Real-time | Real-time | ✅ WebSocket (free) |
| **Coinbase** | Real-time | Real-time | ✅ WebSocket (free) |
| **CryptoCompare** | Real-time capable | Real-time | WebSocket (available) |

### Real-Time Recommendations

**For Real-Time Alerts (<1 second latency):**
1. **Binance WebSocket** (if not deploying from US)
2. **Coinbase WebSocket** (US-friendly)

**For Near Real-Time (10-30 second latency):**
1. **CoinGecko Pro API** (30-second cache)
2. **Polling any REST API at allowed rate limits**

**For Periodic Updates (1-5 minutes):**
1. **CoinGecko Free/Demo API** (best coverage)
2. **CryptoCompare Free API** (limited calls)

---

## Terms of Service Compliance Summary

### Commercial Use Authorization

| API | Commercial Use | Attribution Required | Redistribution | Cost |
|-----|----------------|---------------------|----------------|------|
| **CoinGecko** | ✅ Allowed | ✅ Yes | ❌ No | Free |
| **Binance** | ✅ Allowed | ❌ No | ❌ No | Free |
| **Coinbase** | ✅ Allowed | ❌ No | ❌ No | Free |
| **CryptoCompare** | ⚠️ Paid plans | ❌ No | ❌ No | $80-200/mo |

### Key Compliance Notes

**CoinGecko:**
- ✅ Free tier explicitly allows commercial use
- Must display "Powered by CoinGecko API" with link
- Cannot resell API access itself
- Limited, non-exclusive license

**Binance:**
- ✅ Open API for public market data
- No special attribution required
- Cannot violate rate limits (risk of IP ban)
- Must respect regional restrictions

**Coinbase:**
- ✅ Public market data freely accessible
- Standard API terms apply
- Professional API support available

**CryptoCompare:**
- ⚠️ Free tier for non-commercial/personal use
- Commercial applications should use paid plans
- Free tier suitable for "prototypes" only
- Paid plans start at $80/month

---

## Implementation Recommendations

### Recommended Architecture

**Phase 1: Development & MVP (Free Tier)**
- **Primary API:** CoinGecko Demo Plan (30 calls/min, 10,000/month)
- **Backup API:** Coinbase Advanced Trade (10 req/sec public)
- **Strategy:** Poll every 2-3 minutes for price updates
- **Deployment:** Any region (no restrictions)

**Phase 2: Production (Light Usage)**
- **Primary API:** CoinGecko Demo or Paid Analyst Plan
- **WebSocket Option:** Coinbase Advanced Trade WebSocket
- **Strategy:** WebSocket for real-time, REST for historical/bulk
- **Cost:** Free or ~$50-100/month (CoinGecko Analyst)

**Phase 3: Scale (Heavy Usage)**
- **Primary API:** CoinGecko Pro Plan (1,000 calls/min)
- **WebSocket:** CoinGecko WebSocket API
- **Alternative:** Binance WebSocket (if deployed outside US)
- **Strategy:** Full WebSocket integration for real-time alerts
- **Cost:** ~$200-500/month depending on volume

### Multi-API Strategy

**Redundancy Setup:**
```python
# Priority fallback chain
PRIMARY_API = 'coingecko'      # Best coverage, 30 calls/min
FALLBACK_API = 'coinbase'      # Real-time, 10 req/sec
EMERGENCY_API = 'cryptocompare' # Comprehensive, but limited free
```

**Benefits:**
- Failover if primary API is down
- Load distribution across APIs
- Rate limit management
- Geographic routing (avoid Binance in US)

---

## Final Recommendation

### Winner: CoinGecko API (Demo/Free Plan)

**Rationale:**

1. **Best Free Tier:** 30 calls/minute is sufficient for polling 15+ cryptocurrencies every minute or 30 cryptocurrencies every 2 minutes

2. **Commercial Use Approved:** Explicitly allows commercial use on free tier with simple attribution requirement

3. **No Regional Restrictions:** Works from anywhere, including US-based cloud servers (unlike Binance)

4. **Comprehensive Coverage:** 13M+ tokens ensures support for any cryptocurrency alert requests

5. **Clear Rate Limits:** Stable 30 calls/min (vs vague limits on CryptoCompare free tier)

6. **Upgrade Path:** Clear progression to paid plans (Analyst, Pro, Enterprise) as usage scales

7. **2025 Improvements:** Continuous latency improvements (10-30 second cache)

8. **Good Documentation:** Extensive docs with code examples in multiple languages

### Alternative Recommendation: Binance WebSocket API

**Best For:** Real-time alerts with millisecond precision

**Conditions:**
- Deploy outside US (Europe, Asia) OR
- Use Binance.US API (limited pairs) OR
- Use proxy/VPN (not recommended for production)

**Advantages:**
- True real-time data
- High rate limits (6,000 weight/min)
- Excellent WebSocket support
- Free

**Disadvantages:**
- US IP blocking is a critical limitation
- Aggressive IP banning on violations
- Limited token coverage vs CoinGecko

### Not Recommended for This Project

**CryptoCompare API:**
- Free tier too limited (~5 calls/min average)
- Requires paid plans for commercial use
- More expensive than alternatives
- Vague free tier documentation

**Coinbase Advanced Trade API:**
- Good for major cryptocurrencies only
- Limited coverage (~550 markets)
- Better as secondary/fallback API

---

## Implementation Checklist

### Getting Started with CoinGecko

**1. Register for Demo Account:**
- Visit: https://www.coingecko.com/en/api
- Register for free Demo API key
- Get stable 30 calls/min rate limit

**2. Add Attribution:**
- Display "Powered by CoinGecko API" in your application
- Link back to https://www.coingecko.com/

**3. Implement Rate Limiting:**
```python
import time
from datetime import datetime

class CoinGeckoRateLimiter:
    def __init__(self, calls_per_minute=30):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # 2 seconds for 30/min
        self.last_call = 0

    def wait_if_needed(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()
```

**4. Handle Rate Limit Errors:**
```python
import requests

def fetch_price_with_retry(coin_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': coin_id, 'vs_currencies': 'usd'}
            )

            if response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

**5. Monitor Usage:**
- Track API calls per minute/day
- Log rate limit headers
- Set up alerts before hitting limits

**6. Plan for Scale:**
- Monitor daily usage against 10,000 call monthly limit
- Upgrade to paid plan when approaching limits
- Consider WebSocket for high-frequency updates

---

## Sources & References

All information in this report was gathered from official sources on November 7, 2025.

### CoinGecko API
- **Main API Page:** https://www.coingecko.com/en/api
- **Pricing:** https://www.coingecko.com/en/api/pricing
- **Documentation:** https://docs.coingecko.com/
- **Rate Limits:** https://docs.coingecko.com/reference/common-errors-rate-limit
- **API Usage:** https://docs.coingecko.com/reference/api-usage
- **Support Article:** https://support.coingecko.com/hc/en-us/articles/4538771776153
- **Terms of Service:** https://www.coingecko.com/en/api_terms
- **Changelog:** https://docs.coingecko.com/changelog
- **2025 Update Improvements:** https://docs.coingecko.com/changelog/update-frequency-improvements-for-selected-pro-api-endpoints-march-2025
- **Code Examples:** https://www.coingecko.com/learn/python-query-coingecko-api

### Binance API
- **Developer Portal:** https://developers.binance.com/docs/binance-spot-api-docs
- **GitHub Docs:** https://github.com/binance/binance-spot-api-docs
- **REST API:** https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- **WebSocket API:** https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-api.md
- **WebSocket Streams:** https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
- **Rate Limits:** https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits
- **Regional Restrictions:** https://support.binance.us/hc/en-us/articles/360046786914
- **Coverage Data:** https://www.coingecko.com/en/exchanges/binance

### Coinbase Advanced Trade API
- **Main Documentation:** https://docs.cdp.coinbase.com/advanced-trade/docs/welcome
- **Developer Platform:** https://www.coinbase.com/developer-platform/products/advanced-trade-api
- **REST Rate Limits:** https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api-rate-limits
- **WebSocket Overview:** https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-overview
- **WebSocket Channels:** https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels
- **WebSocket Rate Limits:** https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-rate-limits
- **Python SDK:** https://github.com/coinbase/coinbase-advanced-py

### CryptoCompare API
- **Main API:** https://min-api.cryptocompare.com/
- **Documentation:** https://min-api.cryptocompare.com/documentation
- **Pricing:** https://min-api.cryptocompare.com/pricing
- **Developer Portal:** https://developers.cryptocompare.com/
- **GitHub Guides:** https://github.com/CryptoCompareLTD/api-guides
- **Usage Guide:** https://www.cryptocompare.com/coins/guides/how-to-use-our-api/
- **Rate Limit Endpoint:** https://developers.cryptocompare.com/documentation/data-api/admin_v2_rate_limit

### Third-Party Analysis
- **2025 API Comparison:** https://medium.com/coinmonks/top-5-cryptocurrency-data-apis-comprehensive-comparison-2025-626450b7ff7b
- **Zuplo CoinGecko Analysis:** https://zuplo.com/blog/2025/03/24/coingecko-api
- **TokenMetrics Overview:** https://www.tokenmetrics.com/blog/coingecko-api

### Regional Restrictions Data
- **Binance Restrictions:** https://www.datawallet.com/crypto/binance-restricted-countries
- **Binance US States:** https://support.binance.us/hc/en-us/articles/360046786914

---

## Appendix: Quick Reference

### API Endpoints Summary

**CoinGecko:**
```
GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd
GET https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=usd&days=7
```

**Binance:**
```
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
WS  wss://stream.binance.com:9443/ws/btcusdt@trade
WS  wss://stream.binance.com:9443/ws/btcusdt@miniTicker
```

**Coinbase:**
```
GET https://api.coinbase.com/v2/prices/BTC-USD/spot
WS  wss://advanced-trade-ws.coinbase.com
```

**CryptoCompare:**
```
GET https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD
GET https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH&tsyms=USD
GET https://min-api.cryptocompare.com/stats/rate/limit
```

### Rate Limit Quick Reference

| API | Recommended Polling Interval | Max Free Calls/Day |
|-----|------------------------------|-------------------|
| CoinGecko | Every 2 minutes | ~14,400 (10K/month quota) |
| Binance | Every 10 seconds (or WebSocket) | ~518,400 (6K/min) |
| Coinbase | Every 10 seconds (public) | ~86,400 (10/sec) |
| CryptoCompare | Every 12 minutes | ~7,500 |

---

**Report Completed:** November 7, 2025
**Next Review Date:** February 2026 (or when requirements change)
**Maintained By:** Development Team - Crypto Price Alert System
