/**
 * Cryptocurrency Management Module
 * Handles cryptocurrency CRUD operations and UI updates
 */

const CryptoManager = {
    // Cache for cryptocurrency data
    cryptos: [],
    prices: {},

    /**
     * Initialize cryptocurrency management
     */
    init: async function() {
        this.setupEventListeners();
        await this.loadCryptocurrencies();
        this.startPriceUpdates();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners: function() {
        const addBtn = document.getElementById('add-crypto-btn');
        const cryptoSelect = document.getElementById('crypto-select');

        addBtn.addEventListener('click', () => this.addCryptocurrency());
        cryptoSelect.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addCryptocurrency();
        });
    },

    /**
     * Load all cryptocurrencies from API
     */
    loadCryptocurrencies: async function() {
        try {
            const response = await API.cryptocurrencies.list();
            this.cryptos = response.cryptocurrencies || [];
            this.renderCryptoGrid();
            this.renderCryptoList();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load cryptocurrencies:', error);
            UI.showToast('Failed to load cryptocurrencies', 'error');
        }
    },

    /**
     * Add a new cryptocurrency
     */
    addCryptocurrency: async function() {
        const select = document.getElementById('crypto-select');
        const value = select.value;

        if (!value) {
            UI.showToast('Please select a cryptocurrency', 'error');
            return;
        }

        const [crypto_id, symbol, name] = value.split('|');

        try {
            UI.showLoading();
            const crypto = await API.cryptocurrencies.add({
                crypto_id,
                symbol,
                name,
            });

            this.cryptos.push(crypto);
            this.renderCryptoGrid();
            this.renderCryptoList();
            this.updateStats();

            select.value = '';
            UI.showToast(`${name} added successfully!`, 'success');
        } catch (error) {
            console.error('Failed to add cryptocurrency:', error);
            UI.showToast(error.message || 'Failed to add cryptocurrency', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * Remove a cryptocurrency
     */
    removeCryptocurrency: async function(cryptoId, cryptoName) {
        const confirmed = await UI.confirm(
            'Remove Cryptocurrency',
            `Are you sure you want to remove ${cryptoName} from your watchlist?`
        );

        if (!confirmed) return;

        try {
            UI.showLoading();
            await API.cryptocurrencies.remove(cryptoId);

            this.cryptos = this.cryptos.filter(c => c.crypto_id !== cryptoId);
            this.renderCryptoGrid();
            this.renderCryptoList();
            this.updateStats();

            UI.showToast(`${cryptoName} removed successfully`, 'success');
        } catch (error) {
            console.error('Failed to remove cryptocurrency:', error);
            UI.showToast('Failed to remove cryptocurrency', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * Render cryptocurrency grid (dashboard)
     */
    renderCryptoGrid: function() {
        const grid = document.getElementById('crypto-grid');

        if (this.cryptos.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <p>No cryptocurrencies being monitored yet.</p>
                    <p>Add one below to get started!</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.cryptos.map(crypto => {
            const price = UI.formatCurrency(crypto.current_price);
            const change = crypto.price_change_percentage_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const changeText = UI.formatPercentage(change);
            const lastUpdate = UI.formatRelativeTime(crypto.last_updated);

            return `
                <div class="crypto-card" data-crypto-id="${crypto.crypto_id}">
                    <div class="crypto-header">
                        <div>
                            <div class="crypto-symbol">${crypto.symbol}</div>
                            <div class="crypto-name">${crypto.name}</div>
                        </div>
                    </div>
                    <div class="crypto-price">${price}</div>
                    <div class="crypto-change ${changeClass}">${changeText}</div>
                    <div class="crypto-meta">
                        <span>Updated: ${lastUpdate}</span>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * Render cryptocurrency list (management section)
     */
    renderCryptoList: function() {
        const list = document.getElementById('crypto-list');

        if (this.cryptos.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <p>No cryptocurrencies in watchlist</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.cryptos.map(crypto => {
            const price = UI.formatCurrency(crypto.current_price);
            const change = crypto.price_change_percentage_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const changeText = UI.formatPercentage(change);

            return `
                <div class="list-item">
                    <div class="list-item-content">
                        <div class="list-item-title">
                            ${crypto.symbol} - ${crypto.name}
                        </div>
                        <div class="list-item-meta">
                            Price: ${price}
                            <span class="crypto-change ${changeClass}">${changeText}</span>
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-danger btn-small"
                                onclick="CryptoManager.removeCryptocurrency('${crypto.crypto_id}', '${crypto.name}')">
                            Remove
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * Update dashboard statistics
     */
    updateStats: function() {
        document.getElementById('crypto-count').textContent = this.cryptos.length;
    },

    /**
     * Update cryptocurrency prices
     */
    updatePrices: async function() {
        try {
            const response = await API.prices.current();
            const prices = response.prices || [];

            // Update crypto objects with new prices
            prices.forEach(priceData => {
                const crypto = this.cryptos.find(c => c.crypto_id === priceData.crypto_id);
                if (crypto) {
                    const oldPrice = crypto.current_price;
                    crypto.current_price = priceData.price;
                    crypto.last_updated = priceData.timestamp;

                    // Calculate 24h change if we have old price
                    if (oldPrice && oldPrice !== priceData.price) {
                        const change = ((priceData.price - oldPrice) / oldPrice) * 100;
                        crypto.price_change_percentage_24h = change;
                    }
                }
            });

            this.renderCryptoGrid();
            this.renderCryptoList();

            // Update last refresh time
            const now = new Date();
            document.getElementById('last-update').textContent =
                `Updated: ${now.toLocaleTimeString()}`;

        } catch (error) {
            console.error('Failed to update prices:', error);
        }
    },

    /**
     * Start automatic price updates
     */
    startPriceUpdates: function() {
        // Update prices every 15 seconds
        setInterval(() => this.updatePrices(), 15000);

        // Initial update
        this.updatePrices();
    },

    /**
     * Get cryptocurrency by ID
     */
    getCryptoById: function(cryptoId) {
        return this.cryptos.find(c => c.crypto_id === cryptoId);
    },

    /**
     * Get all cryptocurrencies for dropdown
     */
    getCryptosForDropdown: function() {
        return this.cryptos.map(crypto => ({
            value: crypto.crypto_id,
            label: `${crypto.symbol} - ${crypto.name}`,
        }));
    },
};

// Make available globally
window.CryptoManager = CryptoManager;
