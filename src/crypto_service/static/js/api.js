/**
 * API Client for Crypto Price Alert System
 * Handles all HTTP requests to the backend API
 */

const API_BASE = '/api';

/**
 * Generic API call wrapper with error handling
 */
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        // Handle 204 No Content
        if (response.status === 204) {
            return { success: true };
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.detail || `API error: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

/**
 * API Client Object
 */
const API = {
    // ============================================
    // Health Check
    // ============================================
    health: {
        check: () => fetch('/health').then(r => r.json()),
    },

    // ============================================
    // Cryptocurrencies
    // ============================================
    cryptocurrencies: {
        /**
         * List all monitored cryptocurrencies
         */
        list: (params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = `/cryptocurrencies${queryString ? '?' + queryString : ''}`;
            return apiCall(endpoint);
        },

        /**
         * Get a specific cryptocurrency
         */
        get: (cryptoId) => apiCall(`/cryptocurrencies/${cryptoId}`),

        /**
         * Add a new cryptocurrency to the watchlist
         */
        add: (data) => apiCall('/cryptocurrencies', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

        /**
         * Remove a cryptocurrency from the watchlist
         */
        remove: (cryptoId) => apiCall(`/cryptocurrencies/${cryptoId}`, {
            method: 'DELETE',
        }),
    },

    // ============================================
    // Alerts
    // ============================================
    alerts: {
        /**
         * List all alerts with optional filters
         */
        list: (params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = `/alerts${queryString ? '?' + queryString : ''}`;
            return apiCall(endpoint);
        },

        /**
         * Get a specific alert
         */
        get: (alertId) => apiCall(`/alerts/${alertId}`),

        /**
         * Create a new alert
         */
        create: (data) => apiCall('/alerts', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

        /**
         * Update an existing alert
         */
        update: (alertId, data) => apiCall(`/alerts/${alertId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

        /**
         * Delete an alert
         */
        delete: (alertId) => apiCall(`/alerts/${alertId}`, {
            method: 'DELETE',
        }),
    },

    // ============================================
    // Prices
    // ============================================
    prices: {
        /**
         * Get current prices for all or specific cryptocurrencies
         */
        current: (cryptoIds = null) => {
            const params = cryptoIds ? { crypto_ids: cryptoIds } : {};
            const queryString = new URLSearchParams(params).toString();
            const endpoint = `/prices/current${queryString ? '?' + queryString : ''}`;
            return apiCall(endpoint);
        },

        /**
         * Get current price for a specific cryptocurrency
         */
        getCurrent: (cryptoId) => apiCall(`/prices/${cryptoId}/current`),

        /**
         * Get price history for a cryptocurrency
         */
        history: (cryptoId, params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = `/prices/${cryptoId}/history${queryString ? '?' + queryString : ''}`;
            return apiCall(endpoint);
        },
    },
};

/**
 * UI Helper Functions
 */
const UI = {
    /**
     * Show toast notification
     */
    showToast: (message, type = 'info') => {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');

        toastMessage.textContent = message;
        toast.className = `toast ${type} show`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    },

    /**
     * Show loading overlay
     */
    showLoading: () => {
        document.getElementById('loading-overlay').style.display = 'flex';
    },

    /**
     * Hide loading overlay
     */
    hideLoading: () => {
        document.getElementById('loading-overlay').style.display = 'none';
    },

    /**
     * Show confirmation modal
     */
    confirm: (title, message) => {
        return new Promise((resolve) => {
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-title');
            const messageEl = document.getElementById('confirm-message');
            const yesBtn = document.getElementById('confirm-yes');
            const noBtn = document.getElementById('confirm-no');

            titleEl.textContent = title;
            messageEl.textContent = message;
            modal.style.display = 'flex';

            const handleYes = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(true);
            };

            const handleNo = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(false);
            };

            const cleanup = () => {
                yesBtn.removeEventListener('click', handleYes);
                noBtn.removeEventListener('click', handleNo);
            };

            yesBtn.addEventListener('click', handleYes);
            noBtn.addEventListener('click', handleNo);
        });
    },

    /**
     * Format currency
     */
    formatCurrency: (value) => {
        if (value === null || value === undefined) return 'N/A';
        const num = parseFloat(value);
        if (num >= 1) {
            return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else {
            return `$${num.toFixed(6)}`;
        }
    },

    /**
     * Format percentage
     */
    formatPercentage: (value) => {
        if (value === null || value === undefined) return 'N/A';
        const num = parseFloat(value);
        const sign = num >= 0 ? '+' : '';
        return `${sign}${num.toFixed(2)}%`;
    },

    /**
     * Format date/time
     */
    formatDateTime: (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    },

    /**
     * Format relative time (e.g., "5 minutes ago")
     */
    formatRelativeTime: (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    },

    /**
     * Get alert type display name
     */
    getAlertTypeLabel: (alertType) => {
        const labels = {
            'PRICE_ABOVE': 'Price Above',
            'PRICE_BELOW': 'Price Below',
            'PRICE_CROSSES_UP': 'Crosses Up',
            'PRICE_CROSSES_DOWN': 'Crosses Down',
            'PRICE_CHANGE_PERCENT': 'Change %',
        };
        return labels[alertType] || alertType;
    },
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, UI };
}
