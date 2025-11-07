# Crypto Price Alert System - Web UI Guide

## Overview

The Crypto Price Alert System Web UI is a modern, responsive single-page application that allows you to monitor cryptocurrency prices and configure alerts in real-time.

## Accessing the UI

Once the service is running, access the web interface at:

```
http://localhost:52000/
```

## Features

### 1. Dashboard

The dashboard provides an at-a-glance view of your monitored cryptocurrencies.

**Key Features:**
- **Real-time Price Display**: See current prices for all monitored cryptocurrencies
- **24h Price Changes**: Color-coded percentage changes (green for positive, red for negative)
- **Auto-refresh**: Prices update automatically every 15 seconds
- **Statistics**: View total monitored cryptocurrencies and active alerts

### 2. Health Status Indicator

Located in the header, the health indicator shows the system status:
- **Green dot**: System is healthy
- **Yellow dot**: System is degraded
- **Red dot**: System is unhealthy

### 3. Cryptocurrency Management

**Adding a Cryptocurrency:**
1. Select a cryptocurrency from the dropdown menu
2. Click "Add to Watchlist"
3. The cryptocurrency will appear in both the dashboard and management list

**Available Cryptocurrencies:**
- Bitcoin (BTC)
- Ethereum (ETH)
- Cardano (ADA)
- Solana (SOL)
- XRP (XRP)
- Polkadot (DOT)
- Dogecoin (DOGE)
- Avalanche (AVAX)
- Chainlink (LINK)
- Polygon (MATIC)

**Removing a Cryptocurrency:**
1. Find the cryptocurrency in the management list
2. Click the "Remove" button
3. Confirm the removal when prompted

### 4. Alert Management

**Creating an Alert:**

1. Click the "Create Alert" button
2. Fill in the alert form:
   - **Cryptocurrency**: Select which crypto to monitor
   - **Alert Type**: Choose from:
     - **Price Above**: Trigger when price goes above threshold
     - **Price Below**: Trigger when price goes below threshold
     - **Price Crosses Up**: Trigger when price crosses up through threshold
     - **Price Crosses Down**: Trigger when price crosses down through threshold
     - **Price Change %**: Trigger on percentage change
   - **Threshold**: Enter the price threshold value
   - **Telegram Chat ID**: Your Telegram chat ID for notifications
   - **Enable immediately**: Check to activate the alert right away
3. Click "Save Alert"

**Managing Alerts:**

Each alert in the list shows:
- Status indicator (green = enabled, gray = disabled)
- Cryptocurrency and alert type
- Threshold value
- Trigger count and last trigger time

**Alert Actions:**
- **Enable/Disable**: Toggle alert active status
- **Delete**: Remove the alert permanently

### 5. Notifications

The system uses toast notifications to provide feedback:
- **Success** (green): Operations completed successfully
- **Error** (red): Something went wrong
- **Info** (blue): General information

## UI Components Guide

### Dashboard Cards

Each cryptocurrency is displayed in a card showing:
- **Symbol**: Abbreviated name (e.g., BTC)
- **Full Name**: Complete name (e.g., Bitcoin)
- **Current Price**: Real-time price in USD
- **24h Change**: Percentage change (color-coded)
- **Last Update**: When the price was last refreshed

### Alert Cards

Alert cards display:
- **Status Dot**: Visual indicator of alert state
- **Crypto Name**: Which cryptocurrency is being monitored
- **Alert Type**: Type of alert condition
- **Threshold**: The trigger price
- **Statistics**: How many times it has triggered and when

## Workflow Examples

### Example 1: Monitor Bitcoin Price Above $70,000

1. **Add Bitcoin to watchlist:**
   - Select "Bitcoin (BTC)" from dropdown
   - Click "Add to Watchlist"
   - Bitcoin appears in dashboard with current price

2. **Create price alert:**
   - Click "Create Alert"
   - Select "Bitcoin (BTC)" from cryptocurrency dropdown
   - Choose "Price Above" as alert type
   - Enter "70000" as threshold
   - Enter your Telegram chat ID
   - Click "Save Alert"

3. **Monitor:**
   - Dashboard shows Bitcoin price updating every 15 seconds
   - When price crosses $70,000, you'll receive a Telegram notification
   - Alert shows trigger count and last trigger time

### Example 2: Track Ethereum Price Drop

1. **Add Ethereum:**
   - Select "Ethereum (ETH)"
   - Click "Add to Watchlist"

2. **Create below-price alert:**
   - Click "Create Alert"
   - Select "Ethereum (ETH)"
   - Choose "Price Below"
   - Enter your threshold (e.g., "1500")
   - Enter Telegram chat ID
   - Click "Save Alert"

3. **Manage:**
   - View alert in alert list
   - Disable/enable as needed
   - Monitor trigger count

### Example 3: Monitor Multiple Cryptocurrencies

1. **Add multiple cryptos:**
   - Add BTC, ETH, SOL, ADA to watchlist
   - Dashboard shows all prices in grid layout

2. **Create multiple alerts:**
   - Create "Price Above" alert for BTC at $70,000
   - Create "Price Below" alert for ETH at $2,000
   - Create "Price Change %" alert for SOL at 10%

3. **Dashboard overview:**
   - See all prices at a glance
   - Monitor which alerts are active
   - View total statistics in header

## Responsive Design

The UI is fully responsive and works on:
- **Desktop**: Full grid layout with all features
- **Tablet**: Adaptive grid that stacks appropriately
- **Mobile**: Single-column layout optimized for small screens

## Keyboard Shortcuts

- **Enter** in cryptocurrency dropdown: Add cryptocurrency
- **ESC** (future): Close modals and forms

## Auto-Refresh Behavior

- **Price Updates**: Every 15 seconds
- **Health Check**: Every 30 seconds
- **Last Update Time**: Displayed in header

## Troubleshooting

### Prices Not Updating

1. Check health indicator in header
2. Verify backend service is running
3. Check browser console for errors
4. Refresh the page

### Cannot Add Cryptocurrency

1. Ensure cryptocurrency is not already in watchlist
2. Check if backend API is accessible
3. Verify network connection

### Cannot Create Alert

1. Ensure cryptocurrency is already in watchlist (add it first)
2. Verify all required fields are filled
3. Check Telegram chat ID format
4. Ensure threshold is a valid number

### Alert Not Triggering

1. Verify alert is enabled (green status dot)
2. Check threshold value is correct
3. Verify Telegram service is configured
4. Check alert trigger count (may have already triggered)

## Technical Details

### Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **Vanilla JavaScript**: No framework dependencies
- **FastAPI Backend**: RESTful API

### Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### API Endpoints Used

- `GET /health` - System health check
- `GET /api/cryptocurrencies` - List cryptocurrencies
- `POST /api/cryptocurrencies` - Add cryptocurrency
- `DELETE /api/cryptocurrencies/{id}` - Remove cryptocurrency
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/{id}` - Update alert
- `DELETE /api/alerts/{id}` - Delete alert
- `GET /api/prices/current` - Get current prices
- `GET /api/prices/{id}/history` - Get price history

### File Structure

```
static/
├── index.html              # Main HTML page
├── css/
│   └── style.css          # All styling
├── js/
│   ├── api.js             # API client and utilities
│   ├── app.js             # Main application logic
│   ├── cryptocurrencies.js # Crypto management
│   └── alerts.js          # Alert management
└── images/
    └── (future assets)
```

## Dark Mode

The UI features a dark mode theme by default:
- Dark backgrounds for reduced eye strain
- High contrast text for readability
- Color-coded elements for quick scanning
- Gradient accents for visual appeal

## Performance

- **Initial Load**: < 1 second
- **Price Updates**: 15-second intervals
- **Smooth Animations**: Hardware-accelerated CSS transitions
- **Efficient Rendering**: Minimal DOM manipulation

## Future Enhancements

Potential improvements (not yet implemented):
- Light/dark mode toggle
- Price charts with historical data
- Custom alert notifications (sound, browser notification)
- Export alerts configuration
- Multiple user support
- Advanced filtering and search
- Customizable refresh intervals
- Price chart widgets
- Alert history view

## Support

For issues or questions:
1. Check the logs in browser console (F12)
2. Verify backend service is running
3. Check API documentation at `/docs`
4. Review backend logs for errors

## Best Practices

1. **Monitor Responsibly**: Don't add too many cryptocurrencies to avoid performance issues
2. **Set Realistic Thresholds**: Configure alerts at meaningful price levels
3. **Test Alerts**: Create test alerts before relying on them
4. **Regular Monitoring**: Check the dashboard periodically to ensure system health
5. **Telegram Setup**: Ensure your Telegram bot and chat ID are correctly configured

## Getting Started Checklist

- [ ] Access the UI at http://localhost:52000/
- [ ] Verify system health indicator is green
- [ ] Add your first cryptocurrency
- [ ] Wait for price to update (15 seconds)
- [ ] Create your first alert
- [ ] Configure Telegram chat ID
- [ ] Test alert by setting a threshold that will trigger
- [ ] Monitor dashboard for updates

## Conclusion

The Crypto Price Alert System Web UI provides a user-friendly interface for monitoring cryptocurrency prices and managing alerts. With its modern design, real-time updates, and intuitive controls, you can easily stay informed about market movements and receive notifications when your conditions are met.

Happy monitoring!
