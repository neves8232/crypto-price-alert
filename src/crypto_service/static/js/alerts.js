/**
 * Alert Management Module
 * Handles alert CRUD operations and UI updates
 */

const AlertManager = {
    // Cache for alert data
    alerts: [],
    editingAlertId: null,

    /**
     * Initialize alert management
     */
    init: async function() {
        this.setupEventListeners();
        await this.loadAlerts();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners: function() {
        const createBtn = document.getElementById('create-alert-btn');
        const cancelBtn = document.getElementById('cancel-alert-btn');
        const alertForm = document.getElementById('alert-form');

        createBtn.addEventListener('click', () => this.showAlertForm());
        cancelBtn.addEventListener('click', () => this.hideAlertForm());
        alertForm.addEventListener('submit', (e) => this.handleAlertSubmit(e));
    },

    /**
     * Load all alerts from API
     */
    loadAlerts: async function() {
        try {
            const response = await API.alerts.list();
            this.alerts = response.alerts || [];
            this.renderAlertList();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load alerts:', error);
            UI.showToast('Failed to load alerts', 'error');
        }
    },

    /**
     * Show alert creation/edit form
     */
    showAlertForm: function(alertId = null) {
        const formContainer = document.getElementById('alert-form-container');
        const form = document.getElementById('alert-form');
        const title = document.getElementById('alert-form-title');

        // Populate cryptocurrency dropdown
        this.populateCryptoDropdown();

        if (alertId) {
            // Edit mode
            const alert = this.alerts.find(a => a.alert_id === alertId);
            if (!alert) return;

            this.editingAlertId = alertId;
            title.textContent = 'Edit Alert';

            // Populate form with alert data
            document.getElementById('alert-crypto').value = alert.crypto_id;
            document.getElementById('alert-type').value = alert.alert_type;
            document.getElementById('alert-threshold').value = alert.threshold;
            document.getElementById('alert-telegram-chat').value = alert.telegram_chat_id;
            document.getElementById('alert-enabled').checked = alert.enabled;
        } else {
            // Create mode
            this.editingAlertId = null;
            title.textContent = 'Create New Alert';
            form.reset();
            document.getElementById('alert-enabled').checked = true;
        }

        formContainer.style.display = 'block';
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    /**
     * Hide alert form
     */
    hideAlertForm: function() {
        const formContainer = document.getElementById('alert-form-container');
        const form = document.getElementById('alert-form');

        formContainer.style.display = 'none';
        form.reset();
        this.editingAlertId = null;
    },

    /**
     * Populate cryptocurrency dropdown
     */
    populateCryptoDropdown: function() {
        const select = document.getElementById('alert-crypto');
        const cryptos = CryptoManager.getCryptosForDropdown();

        select.innerHTML = '<option value="">Select cryptocurrency...</option>';

        cryptos.forEach(crypto => {
            const option = document.createElement('option');
            option.value = crypto.value;
            option.textContent = crypto.label;
            select.appendChild(option);
        });
    },

    /**
     * Handle alert form submission
     */
    handleAlertSubmit: async function(e) {
        e.preventDefault();

        const formData = {
            crypto_id: document.getElementById('alert-crypto').value,
            alert_type: document.getElementById('alert-type').value,
            threshold: parseFloat(document.getElementById('alert-threshold').value),
            telegram_chat_id: document.getElementById('alert-telegram-chat').value,
            enabled: document.getElementById('alert-enabled').checked,
            metadata: {},
        };

        // Validate
        if (!formData.crypto_id || !formData.alert_type || !formData.threshold || !formData.telegram_chat_id) {
            UI.showToast('Please fill in all required fields', 'error');
            return;
        }

        try {
            UI.showLoading();

            if (this.editingAlertId) {
                // Update existing alert
                const updateData = {
                    threshold: formData.threshold,
                    enabled: formData.enabled,
                    metadata: formData.metadata,
                };
                const alert = await API.alerts.update(this.editingAlertId, updateData);

                // Update in local cache
                const index = this.alerts.findIndex(a => a.alert_id === this.editingAlertId);
                if (index !== -1) {
                    this.alerts[index] = alert;
                }

                UI.showToast('Alert updated successfully!', 'success');
            } else {
                // Create new alert
                // Add user_id (for demo, using 'default-user')
                formData.user_id = 'default-user';

                const alert = await API.alerts.create(formData);
                this.alerts.push(alert);

                UI.showToast('Alert created successfully!', 'success');
            }

            this.renderAlertList();
            this.updateStats();
            this.hideAlertForm();

        } catch (error) {
            console.error('Failed to save alert:', error);
            UI.showToast(error.message || 'Failed to save alert', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * Toggle alert enabled/disabled
     */
    toggleAlert: async function(alertId) {
        const alert = this.alerts.find(a => a.alert_id === alertId);
        if (!alert) return;

        try {
            UI.showLoading();

            const updated = await API.alerts.update(alertId, {
                enabled: !alert.enabled,
            });

            // Update in local cache
            const index = this.alerts.findIndex(a => a.alert_id === alertId);
            if (index !== -1) {
                this.alerts[index] = updated;
            }

            this.renderAlertList();
            UI.showToast(
                `Alert ${updated.enabled ? 'enabled' : 'disabled'}`,
                'success'
            );

        } catch (error) {
            console.error('Failed to toggle alert:', error);
            UI.showToast('Failed to update alert', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * Delete an alert
     */
    deleteAlert: async function(alertId) {
        const alert = this.alerts.find(a => a.alert_id === alertId);
        if (!alert) return;

        const crypto = CryptoManager.getCryptoById(alert.crypto_id);
        const cryptoName = crypto ? crypto.name : alert.crypto_id;

        const confirmed = await UI.confirm(
            'Delete Alert',
            `Are you sure you want to delete the ${UI.getAlertTypeLabel(alert.alert_type)} alert for ${cryptoName}?`
        );

        if (!confirmed) return;

        try {
            UI.showLoading();
            await API.alerts.delete(alertId);

            this.alerts = this.alerts.filter(a => a.alert_id !== alertId);
            this.renderAlertList();
            this.updateStats();

            UI.showToast('Alert deleted successfully', 'success');
        } catch (error) {
            console.error('Failed to delete alert:', error);
            UI.showToast('Failed to delete alert', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * Render alert list
     */
    renderAlertList: function() {
        const list = document.getElementById('alert-list');

        if (this.alerts.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <p>No alerts configured yet.</p>
                    <p>Create one to get started!</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.alerts.map(alert => {
            const crypto = CryptoManager.getCryptoById(alert.crypto_id);
            const cryptoName = crypto ? `${crypto.symbol} - ${crypto.name}` : alert.crypto_id;
            const alertTypeLabel = UI.getAlertTypeLabel(alert.alert_type);
            const threshold = UI.formatCurrency(alert.threshold);
            const statusClass = alert.enabled ? 'enabled' : 'disabled';
            const statusText = alert.enabled ? 'Enabled' : 'Disabled';
            const lastTriggered = alert.last_triggered_at
                ? UI.formatDateTime(alert.last_triggered_at)
                : 'Never';
            const triggerCount = alert.trigger_count || 0;

            return `
                <div class="list-item alert-item">
                    <div class="alert-status ${statusClass}" title="${statusText}"></div>

                    <div class="alert-info">
                        <div class="list-item-title">
                            ${cryptoName}
                            <span class="alert-type">${alertTypeLabel}</span>
                        </div>
                        <div class="alert-threshold">${threshold}</div>
                        <div class="alert-triggers">
                            Triggered: ${triggerCount} times | Last: ${lastTriggered}
                        </div>
                    </div>

                    <div class="list-item-actions">
                        <button class="btn ${alert.enabled ? 'btn-secondary' : 'btn-success'} btn-small"
                                onclick="AlertManager.toggleAlert('${alert.alert_id}')">
                            ${alert.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button class="btn btn-danger btn-small"
                                onclick="AlertManager.deleteAlert('${alert.alert_id}')">
                            Delete
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
        const activeCount = this.alerts.filter(a => a.enabled).length;
        document.getElementById('alert-count').textContent = activeCount;
    },
};

// Make available globally
window.AlertManager = AlertManager;
