/**
 * Main Application Logic
 * Initializes and coordinates all modules
 */

const App = {
    /**
     * Initialize the application
     */
    init: async function() {
        console.log('Initializing Crypto Price Alert System...');

        // Check health status
        await this.checkHealth();

        // Initialize modules
        try {
            await CryptoManager.init();
            await AlertManager.init();

            console.log('Application initialized successfully');
            UI.showToast('Welcome to Crypto Price Alert System!', 'success');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            UI.showToast('Failed to initialize application', 'error');
        }

        // Start health check interval
        this.startHealthCheck();
    },

    /**
     * Check application health
     */
    checkHealth: async function() {
        try {
            const health = await API.health.check();
            this.updateHealthStatus(health);
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateHealthStatus({ status: 'unhealthy' });
        }
    },

    /**
     * Update health status indicator
     */
    updateHealthStatus: function(health) {
        const statusEl = document.getElementById('health-status');
        const dotEl = statusEl.querySelector('.health-dot');
        const textEl = statusEl.querySelector('.health-text');

        const status = health.status || 'unknown';

        // Remove all status classes
        dotEl.classList.remove('healthy', 'degraded', 'unhealthy');

        // Add appropriate status class
        switch (status) {
            case 'healthy':
                dotEl.classList.add('healthy');
                textEl.textContent = 'System Healthy';
                break;
            case 'degraded':
                dotEl.classList.add('degraded');
                textEl.textContent = 'System Degraded';
                break;
            case 'unhealthy':
                dotEl.classList.add('unhealthy');
                textEl.textContent = 'System Unhealthy';
                break;
            default:
                textEl.textContent = 'Status Unknown';
        }
    },

    /**
     * Start periodic health checks
     */
    startHealthCheck: function() {
        // Check health every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
    },

    /**
     * Handle global errors
     */
    handleError: function(error) {
        console.error('Application error:', error);
        UI.showToast('An error occurred. Please try again.', 'error');
    },
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init().catch(error => App.handleError(error));
});

// Handle global errors
window.addEventListener('error', (event) => {
    App.handleError(event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    App.handleError(event.reason);
});

// Export for debugging
window.App = App;
